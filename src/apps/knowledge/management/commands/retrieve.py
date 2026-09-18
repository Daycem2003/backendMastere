# retrieve -- cosine-similarity search over ingested knowledge chunks.
import os
from django.core.management.base import BaseCommand
from src.apps.knowledge.retrieval import (
    DEFAULT_DIM,
    DEFAULT_MIN_SCORE,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA,
    DEFAULT_TOP,
    embed_query,
    search,
)


class Command(BaseCommand):

    help = "Cosine similarity search over the knowledge base (retrieval only)."

    def add_arguments(self, parser):
        parser.add_argument("query", nargs="*", help="One query (space-separated words).")
        parser.add_argument("--queries", action="append", nargs="+",
                            help="Extra query as a single quoted arg (repeatable).")
        parser.add_argument("--queries-file",
                            help="File with one query per line (blank lines ignored).")
        parser.add_argument("--top", type=int, default=DEFAULT_TOP)
        parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE,
                            help=("Drop results below this cosine similarity "
                                  "(default %s, calibrated; pass 0 to disable)." % DEFAULT_MIN_SCORE))
        parser.add_argument("--no-min-score", action="store_true",
                            help="Disable the score floor (return whatever top-N matches).")
        parser.add_argument("--deterministic", dest="deterministic", action="store_true", default=True,
                            help="Force temperature=0 for bit-exact embeddings (on by default).")
        parser.add_argument("--no-deterministic", dest="deterministic", action="store_false",
                            help="Use Ollama's default (slightly non-deterministic) embedding numerics.")
        parser.add_argument("--seed", default=None, help="Fixed seed for deterministic embeddings.")
        parser.add_argument("--filename", help="Restrict to one source file name.")
        parser.add_argument("--model", default=DEFAULT_MODEL)
        parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
        parser.add_argument("--ollama", default=DEFAULT_OLLAMA)
        parser.add_argument("--asymmetric", action="store_true",
                            help="Prefix the query with a Qwen-style instruction (off by default).")
        parser.add_argument("--instruction", default=None,
                            help="Custom instruction text when --asymmetric is set.")
        parser.add_argument("--preview", type=int, default=200,
                            help="Characters of chunk text to show (default 200).")
        parser.add_argument("--full", action="store_true", help="Print full chunk text.")
        parser.add_argument("--embed-info", action="store_true",
                            help="Show the query embedding head + dim.")

    def handle(self, *args, **opts):
        pos = list(opts.get("query") or [])
        extra = []
        if opts.get("queries"):
            for grp in opts["queries"]:
                extra.extend(grp)
        if opts.get("queries_file"):
            try:
                with open(opts["queries_file"], encoding="utf-8") as fp:
                    extra.extend(line.strip() for line in fp if line.strip())
            except OSError as exc:
                self.stderr.write("Could not read --queries-file: %s" % exc)
                return
        queries = pos + extra
        queries = [q for q in queries if q]
        if not queries:
            self.stderr.write("No query supplied. Pass a positional query, --queries, or --queries-file.")
            return

        # --no-min-score explicitly overrides the calibrated default.
        min_score = None if opts.get("no_min_score") else opts["min_score"]
        deterministic = opts["deterministic"]
        mode = "asymmetric (instructed)" if opts["asymmetric"] else "symmetric (raw)"
        self.stdout.write(
            "Retrieval: model=%s dim=%d top=%d %s ollama=%s"
            % (opts["model"], opts["dim"], opts["top"], mode, opts["ollama"]))
        self.stdout.write(
            "Filename filter: %s   min-score: %s   deterministic(temp=0): %s seed=%s"
            % (opts.get("filename") or "(none)", min_score, deterministic, opts.get("seed")))

        grand = 0
        for q in queries:
            self.stdout.write("\n==== QUERY: %s ====" % q)
            results = search(
                q,
                top_n=opts["top"],
                min_score=min_score,
                filename=opts.get("filename"),
                model=opts["model"],
                dim=opts["dim"],
                ollama=opts["ollama"],
                use_instruction=opts["asymmetric"],
                task=opts["instruction"],
                deterministic=deterministic,
                seed=opts.get("seed"),
            )
            if opts["embed_info"]:
                qvec = embed_query(
                    q, model=opts["model"], dim=opts["dim"], ollama=opts["ollama"],
                    use_instruction=opts["asymmetric"], task=opts["instruction"],
                    deterministic=deterministic, seed=opts.get("seed"),
                )
                head = [round(float(x), 4) for x in qvec[:8]]
                self.stdout.write("   query-emb dim=%d head8=%s" % (len(qvec), head))
            if not results:
                self.stdout.write("     (no chunks)")
                continue
            grand += len(results)
            for r in results:
                self.stdout.write(
                    "    #%-2d  sim=%+.4f  p%-2d    [%-30s] (%s)"
                    % (r.rank, r.score, r.page, r.source_file[:30], r.extraction_method))
                text = r.text if opts["full"] else r.preview(opts["preview"])
                self.stdout.write("      " + " ".join(text.split()))

        self.stdout.write("\nTotal: %d query(ies), %d chunk(s) returned." % (len(queries), grand))
