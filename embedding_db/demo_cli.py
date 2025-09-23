import argparse, json
from retrieve import HybridRetriever
from answer import AnswerEngine

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", type=str, help="Pregunta")
    args = ap.parse_args()

    retriever = HybridRetriever()
    engine = AnswerEngine(retriever=retriever)
    res = engine.answer(args.query)
    print("\n=== RESPUESTA ===\n", res["text"])
    print("\n=== CITAS ===")
    for c in res["citations"]:
        print("-", c)

if __name__ == "__main__":
    main()
