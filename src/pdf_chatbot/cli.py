from __future__ import annotations

import argparse
from pathlib import Path

from .core import KnowledgeBase


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask citation-backed questions about PDF files")
    parser.add_argument("pdf", nargs="+", type=Path)
    parser.add_argument("--question", "-q", help="Ask once instead of opening the interactive prompt")
    args = parser.parse_args()

    knowledge_base = KnowledgeBase()
    for path in args.pdf:
        count = knowledge_base.add_pdf_bytes(path.read_bytes(), path.name)
        print(f"Indexed {count} chunks from {path}")

    def ask(question: str) -> None:
        response = knowledge_base.answer(question)
        print(f"\n{response['answer']}\n")
        for citation in response["citations"]:
            print(f"- {citation['source']} p.{citation['page']} (score {citation['score']})")

    if args.question:
        ask(args.question)
        return
    while question := input("\nQuestion (blank to exit): ").strip():
        ask(question)


if __name__ == "__main__":
    main()

