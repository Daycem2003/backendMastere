# generation.py -- cited answer synthesis over retrieved knowledge chunks.
#
# Takes the top-N retrieved chunks for a query, asks a local generation model
# (qwen3.8:27b-mlx via Ollama) to answer the question *grounded* in those
# passages, and forces inline citations of the form [n] so each claim can be
# traced back to a source file + page. Nothing here touches the DB beyond
# reusing retrieval.search(); this is synthesis only.
#
# Determinism: temperature is forced to 0 (27b on mlx is not bit-exact, but
# temperature=0 + a fixed seed removes sampling variance and makes answers
# highly reproducible for a given corpus + query).
#
# Citation strategy: the prompt hands the model numbered passage blocks
# ([1], [2], ...), each annotated with source file + page. The model must cite
# with [n]. We post-process the answer, collect the distinct [n] markers it
# actually used, and resolve each back to a passage (file/page/method/score/
# excerpt). An answer with no [n] markers is flagged as not grounded.

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from src.apps.knowledge.retrieval import (
    DEFAULT_MIN_SCORE,
    DEFAULT_OLLAMA,
)

# --- generation model settings -------------------------------------------
DEFAULT_GEN_MODEL = os.environ.get("KNOWLEDGE_GEN_MODEL", "qwen3.8:27b-mlx")
DEFAULT_GEN_TOP = int(os.environ.get("KNOWLEDGE_GEN_TOP", "5"))
DEFAULT_EXCERPT = int(os.environ.get("KNOWLEDGE_GEN_EXCERPT", "900"))
DEFAULT_GEN_TEMPERATURE = float(os.environ.get("KNOWLEDGE_GEN_TEMPERATURE", "0.0"))
DEFAULT_GEN_SEED = os.environ.get("KNOWLEDGE_GEN_SEED")
DEFAULT_GEN_MAX_TOKENS = int(os.environ.get("KNOWLEDGE_GEN_MAX_TOKENS", "700")) or None

SYSTEM_PROMPT = (
    "You are a grounded assistant for a Tunisian public university's master's "
    "(M1/M2) admissions process. Answer questions strictly from the PASSAGES "
    "provided below. Rules:\n"
    "1. Answer in the SAME language as the question (French or Arabic).\n"
    "2. Use ONLY the supplied passages. Do not invent facts, dates, fees or "
    "document names that are not present in them.\n"
    "3. After every claim, cite its source with a bracketed passage number "
    "like [1], [2] (cite all passages you relied on).\n"
    "4. If the passages do NOT contain the answer, say so explicitly "
    "('non mentionne dans les documents' / 'مذكور غير') and cite nothing.\n"
    "5. Be concise and factual. No preamble."
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_ORPHAN_THINK_RE = re.compile(r"^\s*<think>.*", re.DOTALL | re.IGNORECASE)
_CITE_RE = re.compile(r"\[(\d+)\]")


@dataclass
class Citation:
    n: int
    source_file: str
    page: int
    extraction_method: str
    score: float
    excerpt: str

    def render(self):
        return ("[%d] %s p.%d (%s, sim=%+.4f): %s" % (
            self.n, self.source_file, self.page,
            self.extraction_method, self.score,
            " ".join(self.excerpt.split())))


@dataclass
class GeneratedAnswer:
    query: str
    answer: str
    model: str
    deterministic: bool
    citations: list = field(default_factory=list)
    context: list = field(default_factory=list)
    grounded: bool = True
    prompt: str = ""
    raw_output: str = ""

    def is_grounded(self):
        return bool(self.citations) and self.grounded


def build_context_blocks(chunks, excerpt_chars=DEFAULT_EXCERPT):
    """Number the retrieved chunks and render prompt blocks + a citation map."""
    blocks = []
    cite_map = {}
    for idx, c in enumerate(chunks, start=1):
        excerpt = " ".join((c.text or "").split())
        if len(excerpt) > excerpt_chars:
            excerpt = excerpt[:excerpt_chars].rstrip() + " ..."
        block = ("[%d] source: %s | page %d | extracted via %s | cosine=%+.4f\n%s" % (
            idx, c.source_file, c.page, c.extraction_method, c.score, excerpt))
        blocks.append(block)
        cite_map[idx] = Citation(
            n=idx,
            source_file=c.source_file,
            page=c.page,
            extraction_method=c.extraction_method,
            score=c.score,
            excerpt=excerpt,
        )
    return blocks, cite_map


def collect_citations(text, cite_map):
    """Resolve the distinct [n] markers present in the answer to citations."""
    seen = []
    found = set()
    for m in _CITE_RE.finditer(text):
        n = int(m.group(1))
        if n in cite_map and n not in found:
            found.add(n)
            seen.append(cite_map[n])
    seen.sort(key=lambda c: c.n)
    return seen


def clean_output(raw):
    text = raw or ""
    text = _THINK_RE.sub("", text)
    text = _ORPHAN_THINK_RE.sub("", text)
    return text.strip()


def ollama_generate(prompt, model, ollama, temperature=0.0, seed=None,
                    max_tokens=None, attempts=2):
    endpoint = ollama + "/api/generate"
    options = {"temperature": float(temperature)}
    if seed is not None and seed != "":
        try:
            options["seed"] = int(seed)
        except ValueError:
            pass
    if max_tokens:
        options["num_predict"] = int(max_tokens)
    body = {"model": model, "prompt": prompt, "stream": False, "options": options}
    payload = json.dumps(body).encode("utf-8")
    last_err = None
    for _ in range(attempts):
        try:
            req = urllib.request.Request(
                endpoint, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=900) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "") or ""
        except urllib.error.HTTPError as exc:
            last_err = "HTTP %s: %s" % (
                exc.code, exc.read().decode("utf-8", "replace")[:300])
        except Exception as exc:
            last_err = "%s: %s" % (type(exc).__name__, exc)
        time.sleep(0.5)
    raise RuntimeError("generation request failed: %s" % last_err)


def generate_answer(query, top_n=DEFAULT_GEN_TOP, min_score=DEFAULT_MIN_SCORE,
                    gen_model=DEFAULT_GEN_MODEL, ollama=DEFAULT_OLLAMA,
                    temperature=DEFAULT_GEN_TEMPERATURE, seed=DEFAULT_GEN_SEED,
                    max_tokens=DEFAULT_GEN_MAX_TOKENS, excerpt_chars=DEFAULT_EXCERPT,
                    deterministic=True, embed_deterministic=True,
                    embed_seed=None, use_instruction=False, task=None,
                    filename=None):
    """Retrieve the top-N chunks for `query` and synthesize a cited answer.

    Returns a GeneratedAnswer. `grounded`/`citations` reflect only the [n]
    markers the model actually used; a non-grounded answer carries no citations
    and should be surfaced to the user as "no support in the document".
    """
    from src.apps.knowledge.retrieval import search
    chunks = search(
        query,
        top_n=top_n,
        min_score=min_score,
        filename=filename,
        deterministic=embed_deterministic,
        seed=embed_seed,
        use_instruction=use_instruction,
        task=task,
    )
    blocks, cite_map = build_context_blocks(chunks, excerpt_chars)
    context_text = "\n\n".join(blocks) if blocks else "(aucun passage pertinent)"
    _fmt = (
        SYSTEM_PROMPT
          + "\n\n--- QUESTION ---\n%s\n"
          + "\n--- PASSAGES ---\n%s\n"
          + "\nReponds maintenant: concis, cite [n] pour chaque affirmation.\n")
    prompt = _fmt % (query, context_text)
    raw = ollama_generate(prompt, gen_model, ollama, temperature=float(temperature),
                          seed=seed, max_tokens=max_tokens)
    answer = clean_output(raw)
    citations = collect_citations(answer, cite_map)
    grounded = bool(citations)
    return GeneratedAnswer(
        query=query,
        answer=answer,
        model=gen_model,
        deterministic=deterministic,
        citations=citations,
        context=chunks,
        grounded=grounded,
        prompt=prompt,
        raw_output=raw,
    )
