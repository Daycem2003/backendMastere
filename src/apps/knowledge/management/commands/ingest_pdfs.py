"""ingest_pdfs -- ingestion-only pipeline for the knowledge base.

Pipeline per PDF:
    1. PyMuPDF (fitz) native text extraction, page by page.
    2. Arabic-quality gate: route a page to Tesseract OCR (ara+eng) when its
        native text is either empty/too short (scanned page) OR garbled.
        "Garbled" = a high fraction of *unexpected* codepoints (C1 controls,
        stray Cyrillic, etc.) -- the signature of a broken/embedded subset-font
        ToUnicode map, where PyMuPDF emits junk instead of real Arabic. OCR
        recovers the real glyphs. Garbled pages are tagged extractionMethod="ocr".
    3. Sentences are packed into ~chunk_chars windows with an overlapping tail
        (overlap_chars), Arabic + Latin aware.
    4. Chunks are embedded with the local Ollama embedding model (default
        qwen3-embedding:4b, 2560-d native); the first dim (1024) coordinates are
        kept (Matryoshka / MRL) and re-normalised, then written to the vector
        column.
    5. Raw text + source page + filename + embedding are persisted.

This command is *ingestion only* -- no query / generation.
"""

import hashlib
import json
import math
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path

import fitz
from PIL import Image
import pytesseract
from django.core.management.base import BaseCommand
from django.db import connection
from pgvector.psycopg2 import register_vector

from src.apps.knowledge.models import KnowledgeChunk, KnowledgeDocument

DEFAULT_PDF_DIR = "/Users/dali/Documents/mastersdocs"
DEFAULT_MODEL = os.environ.get("KNOWLEDGE_EMBED_MODEL", "qwen3-embedding:4b")
DEFAULT_DIM = int(os.environ.get("KNOWLEDGE_EMBED_DIM", "1024"))
DEFAULT_OLLAMA = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
# Deterministic embedding: qwen3-embedding:4b drifts ~4e-4 between calls at its
# default numerics, which makes absolute cosine scores wobble. Forcing
# temperature=0 (in retrieve too) keeps the corpus and queries in one stable
# embedding space. Keep ingest and retrieval aligned; on by default.
DEFAULT_DETERMINISTIC = os.environ.get("KNOWLEDGE_EMBED_DETERMINISTIC", "1") not in ("0", "false", "no", "")


def build_embed_options(deterministic=DEFAULT_DETERMINISTIC, seed=None):
    if not deterministic:
        return None
    opts = {"temperature": 0.0}
    if seed is not None and seed != "":
        try:
            opts["seed"] = int(seed)
        except ValueError:
            pass
    return opts

# Sentence boundary: mixed Arabic + Latin; single-char trailing lookbehind is
# safe, newlines are hard separators.
_SENT_SPLIT_RE = re.compile(r'(?<=[.!??\u061f\u060c\uff0c\u3002;\u061b])\s+|\n+')

# --- Arabic text-quality gate -------------------------------------------
# Mojibake from broken/missing subset-font ToUnicode maps shows up as a high
# fraction of *unexpected* codepoints (C1 controls 0x0C-0x1F, stray Cyrillic,
# African/Mongolian blocks, ...). A clean extracted Arabic text layer has an
# unexpected-codepoint fraction near zero.

_ARABIC_RANGES = [
     (0x0600, 0x077F), (0x0890, 0x089F), (0x08A0, 0x08FF),
     (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
]
_EXPECTED_NON_ARABIC = [
     (0x0020, 0x007E), (0x00A0, 0x00FF), (0x2000, 0x2027), (0x2190, 0x21FF),
]


def _in_any_range(ordc, ranges):
    for lo, hi in ranges:
        if lo <= ordc <= hi:
            return True
    return False


def _is_arabic(c):
    return _in_any_range(ord(c), _ARABIC_RANGES)


def _is_expected(c):
    if c.isspace():
        return True
    o = ord(c)
    return _in_any_range(o, _ARABIC_RANGES) or _in_any_range(o, _EXPECTED_NON_ARABIC)


def assess_text_quality(text, odd_max=0.05):
    """Estimate whether native PDF text is usable or garbled.

    `garbled` is True when the fraction of unexpected codepoints exceeds
    odd_max (and the page is not trivially short -- short pages are handled by
    the scanned-page rule). Both fractions are returned for reporting.
    """
    chars = [c for c in text if not c.isspace()]
    n = len(chars)
    if n == 0:
        return {"arabic_fraction": 0.0, "odd_fraction": 0.0, "garbled": False, "n_chars": 0}
    arabic = sum(1 for c in chars if _is_arabic(c))
    odd = sum(1 for c in chars if not _is_expected(c))
    af = arabic / n
    of = odd / n
    garbled = of > odd_max and n >= 10
    return {"arabic_fraction": round(af, 3), "odd_fraction": round(of, 3), "garbled": garbled, "n_chars": n}


class Command(BaseCommand):

    help = "Ingest PDFs from --pdf-dir into the knowledge base (extraction + chunking + embedding)."

    def add_arguments(self, parser):
        parser.add_argument("--pdf-dir", default=DEFAULT_PDF_DIR, help="Directory to scan for *.pdf")
        parser.add_argument("--limit", type=int, default=None, help="Process at most N files (by sorted name)")
        parser.add_argument("--names", nargs="*", default=None, help="Only files whose name contains one of these substrings")
        parser.add_argument("--chunk-chars", type=int, default=800, help="Target characters per chunk")
        parser.add_argument("--overlap-chars", type=int, default=160, help="Overlapping tail in characters")
        parser.add_argument("--ocr-min-chars", type=int, default=40, help="Page native text below this triggers OCR")
        parser.add_argument("--odd-max", type=float, default=0.05,
                             help="Fraction of unexpected codepoints above which a page is treated as garbled -> OCR")
        parser.add_argument("--ocr-langs", default="ara+eng", help="Tesseract language list")
        parser.add_argument("--ocr-dpi", type=int, default=300, help="Render DPI for OCR pages")
        parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama embedding model")
        parser.add_argument("--dim", type=int, default=DEFAULT_DIM, help="MRL truncation dimension")
        parser.add_argument("--embed-batch", type=int, default=16, help="Texts per embedding request")
        parser.add_argument("--deterministic", dest="deterministic", action="store_true", default=True,
                            help="Force temperature=0 for bit-exact embeddings (on by default).")
        parser.add_argument("--no-deterministic", dest="deterministic", action="store_false",
                            help="Use Ollama's default (slightly non-deterministic) embedding numerics.")
        parser.add_argument("--seed", default=None, help="Fixed seed for deterministic embeddings.")
        parser.add_argument("--dry-run", action="store_true", help="Everything except DB writes")
        parser.add_argument("--force", action="store_true", help="Re-ingest even if sha256 already present")

      # ---------- helpers ----------

    def _register_vector_adapter(self):
        connection.ensure_connection()
        try:
            register_vector(connection.connection)
        except Exception:
            pass

    def _list_pdfs(self, pdf_dir, limit, names):
        pdfs = sorted(Path(pdf_dir).glob("*.pdf"), key=lambda p: p.name)
        if names:
            pdfs = [p for p in pdfs if any(n.lower() in p.name.lower() for n in names)]
        if limit is not None:
            pdfs = pdfs[:limit]
        return pdfs

    def _sha256(self, path):
        h = hashlib.sha256()
        with open(path, "rb") as fp:
            for block in iter(lambda: fp.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()

    def _extract_pdf_pages(self, path, ocr_min_chars, ocr_langs, ocr_dpi, odd_max):
        doc = fitz.open(path)
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            stripped = text.strip()
            native_chars = len(stripped)
            q = assess_text_quality(stripped, odd_max=odd_max)
            reason = "clean"
            need_ocr = False
            if native_chars < ocr_min_chars:
                need_ocr, reason = True, "scanned"
            elif q["garbled"]:
                need_ocr, reason = True, "garbled"
            if need_ocr:
                try:
                    pix = page.get_pixmap(dpi=ocr_dpi)
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    out = pytesseract.image_to_string(img, lang=ocr_langs, config="--psm 6")
                    stripped = out or ""
                except Exception as exc:
                    self.stderr.write("        ! OCR failed on page %d of %s: %s" % (i, path.name, exc))
            pages.append({
                  "page": i,
                  "text": stripped,
                  "method": "ocr" if need_ocr else "text",
                  "reason": reason,
                  "char_count": len(stripped),
                  "native_chars": native_chars,
                  "arabic_fraction": q["arabic_fraction"],
                  "odd_fraction": q["odd_fraction"],
               })
        doc.close()
        return pages

    def _chunk_sentences(self, text, chunk_chars, overlap_chars):
        parts = [p.strip() for p in _SENT_SPLIT_RE.split(text.strip()) if p.strip()]
        if not parts:
            return []
        result = []
        tokens = []
        tail_n = max(1, round(overlap_chars / 6.0))
        for sent in parts:
            toks = sent.split()
            projected = sum((len(t) + 1) for t in tokens) + sum((len(t) + 1) for t in toks)
            if tokens and projected > chunk_chars:
                result.append(" ".join(tokens))
                overlap = tokens[-tail_n:] if tail_n < len(tokens) else []
                tokens = list(overlap)
            tokens.extend(toks)
        if tokens:
            result.append(" ".join(tokens))
        return [c for c in result if c.strip()]

    def _embed(self, texts, model, batch, options=None):
        out = []
        for start in range(0, len(texts), batch):
            chunk = texts[start:start + batch]
            out.extend(self._post_embeddings(chunk, model, options=options))
            time.sleep(0.05)
        return out

    def _post_embeddings(self, chunk, model, attempts=3, options=None):
        body = {"model": model, "input": chunk}
        if options:
            body["options"] = options
        payload = json.dumps(body).encode("utf-8")
        endpoints = [DEFAULT_OLLAMA + "/api/embed", DEFAULT_OLLAMA + "/api/embeddings"]
        last_err = None
        for _ in range(attempts):
            for ep in endpoints:
                try:
                    req = urllib.request.Request(ep, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=300) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    if "embeddings" in data:
                        return list(data["embeddings"])
                    if "embedding" in data:
                        return [data["embedding"]]
                except urllib.error.HTTPError as exc:
                    if exc.code == 404:
                        continue
                    last_err = exc
                except Exception as exc:
                    last_err = exc
            time.sleep(0.3)
        raise RuntimeError("embedding request failed: %s" % last_err)

    @staticmethod
    def _renormalize(v, dim):
        v = list(v)[:dim]
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def _print_samples(self, flat_chunks, embeddings):
        for i in range(min(3, len(flat_chunks))):
            c = flat_chunks[i]
            preview = c["text"][:160].replace("\n", " ")
            self.stdout.write("        sample[p%s %s len=%d]: %s" % (c["page"], c["method"], c["char_count"], preview))
            if embeddings and i < len(embeddings):
                emb = embeddings[i]
                head = [round(float(x), 4) for x in emb[:6]]
                norm = math.sqrt(sum(x * x for x in emb))
                self.stdout.write("                      emb[:6]=%s | |v|=%.4f" % (head, norm))

      # ---------- main ----------

    def handle(self, *args, **opts):
        self._register_vector_adapter()
        pdf_dir = Path(opts["pdf_dir"])
        if not pdf_dir.is_dir():
            self.stderr.write("PDF dir not found: %s" % pdf_dir)
            return
        pdfs = self._list_pdfs(pdf_dir, opts["limit"], opts["names"])
        if not pdfs:
            self.stdout.write("No PDFs matched in %s" % pdf_dir)
            return
        self.stdout.write("Found %d PDF(s) in %s" % (len(pdfs), pdf_dir))
        self.stdout.write("Embedding: model=%s dim=%d (MRL) ollama=%s" % (opts["model"], opts["dim"], DEFAULT_OLLAMA))
        self.stdout.write("Quality gate: ocr_min_chars=%d odd_max=%.3f dpi=%d langs=%s" % (
            opts["ocr_min_chars"], opts["odd_max"], opts["ocr_dpi"], opts["ocr_langs"]))
        if opts["dry_run"]:
            self.stdout.write("[--dry-run] no database writes will be performed\n")

        total_chunks = 0
        total_pages = 0
        for idx, pdf in enumerate(pdfs, start=1):
            self.stdout.write("\n=== [%d/%d] %s ===" % (idx, len(pdfs), pdf.name))
            size = pdf.stat().st_size
            sha = self._sha256(pdf)
            self.stdout.write("  sha256=%s size=%d bytes" % (sha[:16], size))

            pages = self._extract_pdf_pages(
                 pdf,
                 opts["ocr_min_chars"],
                 opts["ocr_langs"],
                 opts["ocr_dpi"],
                 opts["odd_max"],
               )
            total_pages += len(pages)
            text_pages = sum(1 for p in pages if p["reason"] == "clean")
            ocr_scanned = sum(1 for p in pages if p["reason"] == "scanned")
            ocr_garbled = sum(1 for p in pages if p["reason"] == "garbled")
            ocr_pages = len(pages) - text_pages
            self.stdout.write(
                   "  pages=%d text(clean)=%d ocr=%d [scanned=%d, garbled->ocr=%d]"
                   % (len(pages), text_pages, ocr_pages, ocr_scanned, ocr_garbled))
            for p in pages:
                if p["reason"] in ("scanned", "garbled"):
                    self.stdout.write(
                          "     p%s: %s arabic=%.2f odd=%.2f native_chars=%d -> OCR recovered %d chars"
                          % (p["page"], p["reason"], p["arabic_fraction"], p["odd_fraction"],
                               p["native_chars"], p["char_count"]))

            flat_chunks = []
            flat_chars = 0
            for page in pages:
                for cs in self._chunk_sentences(page["text"], opts["chunk_chars"], opts["overlap_chars"]):
                    flat_chars += len(cs)
                    flat_chunks.append({"page": page["page"], "text": cs, "method": page["method"], "char_count": len(cs)})
            avg = (flat_chars // len(flat_chunks)) if flat_chunks else 0
            self.stdout.write("  chunks=%d total_chars=%d avg_chars=%d" % (len(flat_chunks), flat_chars, avg))

            text_for_embed = [c["text"] for c in flat_chunks]
            embeddings = []
            if not opts["dry_run"]:
                self.stdout.write("  embedding %d chunks via Ollama (%s)..." % (len(text_for_embed), opts["model"]))
                raw = self._embed(text_for_embed, opts["model"], opts["embed_batch"],
                                    options=build_embed_options(opts["deterministic"], opts.get("seed")))
                embeddings = [self._renormalize(v, opts["dim"]) for v in raw]
                self.stdout.write("  embedded=%d dim(first)=%d" % (len(embeddings), len(embeddings[0]) if embeddings else 0))

            self._print_samples(flat_chunks, embeddings)
            if opts["dry_run"] or not flat_chunks:
                continue

            existing = KnowledgeDocument.objects.filter(sha256=sha).first()
            if existing and not opts["force"]:
                self.stdout.write("  SKIP: already ingested (sha256 match) -- use --force to re-ingest")
                continue

            summary = {
                  "pages_total": len(pages),
                  "pages_text": text_pages,
                  "pages_ocr": ocr_pages,
                  "pages_ocr_scanned": ocr_scanned,
                  "pages_ocr_garbled": ocr_garbled,
                  "odd_max": opts["odd_max"],
                  "ocr_min_chars": opts["ocr_min_chars"],
                  "chunk_chars": opts["chunk_chars"],
                  "overlap_chars": opts["overlap_chars"],
                  "model": opts["model"],
                  "dim": opts["dim"],
                  "total_chars": flat_chars if flat_chunks else 0,
               }
            if existing:
                existing.chunks.all().delete()
                existing.filename = pdf.name
                existing.source_path = str(pdf.resolve())
                existing.size_bytes = size
                existing.num_pages = len(pages)
                existing.status = "DONE" if embeddings else "CHUNKED"
                existing.extraction_summary = summary
                existing.embedding_model = opts["model"] if embeddings else ""
                existing.embedding_dim = opts["dim"] if embeddings else 0
                existing.chunk_count = len(flat_chunks)
                existing.save()
                doc = existing
            else:
                doc = KnowledgeDocument.objects.create(
                    pubkey=secrets.token_hex(16),
                    filename=pdf.name,
                    source_path=str(pdf.resolve()),
                    size_bytes=size,
                    sha256=sha,
                    num_pages=len(pages),
                    status="DONE" if embeddings else "CHUNKED",
                    extraction_summary=summary,
                    embedding_model=opts["model"] if embeddings else "",
                    embedding_dim=opts["dim"] if embeddings else 0,
                    chunk_count=len(flat_chunks),
                   )

            chunks_to_save = [
                KnowledgeChunk(
                    pubkey=secrets.token_hex(16),
                    document=doc,
                    page=c["page"],
                    text=c["text"],
                    char_count=c["char_count"],
                    extraction_method=c["method"],
                    embedding=emb,
                   )
                for c, emb in zip(flat_chunks, embeddings)
               ]
            KnowledgeChunk.objects.bulk_create(chunks_to_save, batch_size=50)
            total_chunks += len(chunks_to_save)
            self.stdout.write("  wrote document %s + %d chunks to DB" % (doc.pubkey[:12], len(chunks_to_save)))

        connection.close()
        self.stdout.write("\nDONE. files=%d pages=%d chunks_written=%d" % (len(pdfs), total_pages, total_chunks))
