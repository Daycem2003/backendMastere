# ask -- grounded, cited answers to a question over the knowledge base.
#
# Pipeline: retrieval.search(top-N) -> generation.generate_answer (qwen3.8:27b-mlx
# via Ollama) -> print answer + citations (source file / page / method / sim).
#
# Command-line testing only; no API endpoint yet.
import os
from django.core.management.base import BaseCommand

from src.apps.knowledge.generation import generate_answer


class Command(BaseCommand):

    help = "Ask a grounded, cited question to the knowledge base (synthesis via Ollama)."

    def add_arguments(self, parser):
        parser.add_argument("query", nargs="+", help="The question to ask.")
        parser.add_argument("--top", type=int, default=5,
                            help="Retrieved chunks to feed the generator (default 5).")
        parser.add_argument("--min-score", type=float, default=None,
                            help="Drop retrieved chunks below this cosine "
                                 "similarity (default: retrieval default).")
        parser.add_argument("--no-min-score", action="store_true",
                            help="Disable the min-score floor when retrieving "
                                 "context.")
        parser.add_argument("--gen-model", default=os.environ.get(
            "KNOWLEDGE_GEN_MODEL", "qwen3.8:27b-mlx"),
            help="Ollama generation model.")
        parser.add_argument("--temperature", type=float, default=0.0,
                            help="Generation temperature (default 0.0).")
        parser.add_argument("--seed", default=None, help="Fixed generation seed.")
        parser.add_argument("--max-tokens", type=int, default=None,
                            help="Cap generated tokens.")
        parser.add_argument("--excerpt", type=int, default=900,
                            help="Max chars of each passage shown to the "
                                 "generator.")
        parser.add_argument("--filename", default=None,
                            help="Restrict retrieval to a single source file.")
        parser.add_argument("--no-deterministic", action="store_true",
                            help="Disable temperature=0 on the embedding step.")
        parser.add_argument("--asymmetric", action="store_true",
                            help="Prefix the retrieval query with the "
                                 "Qwen-style instruction.")
        parser.add_argument("--instruction", default=None,
                            help="Custom retrieval instruction when "
                                 "--asymmetric is set.")
        parser.add_argument("--verbose", action="store_true",
                            help="Also print the generated prompt and raw output.")

    def handle(self, *args, **opts):
        query = " ".join(opts["query"]).strip()
        if not query:
            self.stderr.write("No query supplied.")
            return

        min_score = None if opts["no_min_score"] else opts["min_score"]
        self.stdout.write(
            "ASK q=%r gen=%s top=%d temp=%s min-score=%s ollama=%s" % (
                query, opts["gen_model"], opts["top"],
                opts["temperature"], str(min_score),
                os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")))

        if opts["verbose"] and opts["verbose"]:
            pass  # placeholder, verbose handled by generate_answer via context

        ans = generate_answer(
            query,
            top_n=opts["top"],
            min_score=min_score,
            gen_model=opts["gen_model"],
            temperature=opts["temperature"],
            seed=opts["seed"],
            max_tokens=opts["max_tokens"],
            excerpt_chars=opts["excerpt"],
            filename=opts["filename"],
            deterministic=not opts["no_deterministic"],
            use_instruction=opts["asymmetric"],
            task=opts["instruction"],
        )

        self.stdout.write("\n--- ANSWER ---")
        self.stdout.write(" " + (ans.answer if ans.answer.strip() else "(empty answer)"))

        if opts["verbose"]:
            self.stdout.write("\n--- PROMPT (\u2248%d chars) ---" % len(ans.prompt))
            self.stdout.write(ans.prompt)

        self.stdout.write("\n--- CITATIONS USED (%d) ---" % len(ans.citations))
        if ans.citations:
            for c in ans.citations:
                self.stdout.write("    " + c.render())
        else:
            self.stdout.write("    (none -- answer carries no [n] citation; "
                              "treat as NON-grounded)")

        self.stdout.write("\n--- CONTEXT FED TO MODEL (%d chunk%s) ---" % (
            len(ans.context), "" if len(ans.context) == 1 else "s"))
        for c in ans.context:
            self.stdout.write("    " + c.render())

        self.stdout.write("\n[grounded: %s] model=%s temp=%s" % (
            ans.is_grounded(), ans.model, opts["temperature"]))

        if opts["verbose"]:
            self.stdout.write("\n--- RAW MODEL OUTPUT ---")
            self.stdout.write(ans.raw_output)
