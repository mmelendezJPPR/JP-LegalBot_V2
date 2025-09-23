from typing import Dict, List
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_CHAT
from prompts import SYSTEM_RAG, USER_TEMPLATE
from retrieve import HybridRetriever

class AnswerEngine:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def format_context(self, items: List[Dict]) -> str:
        lines = []
        for i, it in enumerate(items, 1):
            cite = it.get("heading_path") or it.get("doc_id", "")
            pg = ""
            ps, pe = it.get("page_start"), it.get("page_end")
            if ps or pe:
                pg = f", págs. {ps or ''}-{pe or ''}"
            lines.append(f"[{i}] ({cite}{pg})\n{it.get('text','')[:1800]}")
        return "\n\n".join(lines)

    def answer(self, query: str, k=6) -> Dict:
        ctx = self.retriever.hybrid(query, final_k=k)
        context_text = self.format_context(ctx)
        user_msg = USER_TEMPLATE.format(query=query, context=context_text)

        resp = self.client.chat.completions.create(
            model=MODEL_CHAT,
            messages=[
                {"role": "system", "content": SYSTEM_RAG},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2
        )
        text = resp.choices[0].message.content

        citations = []
        for it in ctx:
            cite = it.get("heading_path") or it.get("doc_id","")
            ps, pe = it.get("page_start"), it.get("page_end")
            pg = f", págs. {ps or ''}-{pe or ''}" if (ps or pe) else ""
            citations.append(f"[{cite}{pg}]")

        return {"text": text, "citations": citations, "context_items": ctx}
