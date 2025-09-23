import json, uuid
from typing import Dict
from openai import OpenAI
from .config import OPENAI_API_KEY, MODEL_CHAT, DB_PATH, FAISS_PATH
from .db import get_conn, insert_knowledge_fact
from .prompts import POST_EXTRACT_FACTS
from .retrieve import HybridRetriever
import faiss, numpy as np, os

client = OpenAI(api_key=OPENAI_API_KEY)

def extract_candidate_facts(answer_text: str, citations: list) -> list:
    prompt = POST_EXTRACT_FACTS
    msg = f"Respuesta:\n{answer_text}\n\nCitas:\n{json.dumps(citations, ensure_ascii=False)}"
    resp = client.chat.completions.create(
        model=MODEL_CHAT,
        messages=[{"role":"system","content":prompt},{"role":"user","content":msg}],
        temperature=0.0
    )
    raw = resp.choices[0].message.content
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "facts" in data:
            return data["facts"]
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []

def promote_and_reembed(facts: list, threshold=0.8):
    # Cargar índice FAISS y metas
    faiss_path = FAISS_PATH
    index = faiss.read_index(faiss_path)
    metas_path = os.path.join(os.path.dirname(faiss_path), "metas.jsonl")
    metas = [json.loads(l) for l in open(metas_path, "r", encoding="utf-8")]

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    new_metas = []
    new_vecs = []

    with get_conn(DB_PATH) as con:
        for f in facts:
            if f.get("source_type") != "DOCUMENTO": 
                continue
            if float(f.get("confidence", 0)) < threshold:
                continue
            fact_id = str(uuid.uuid4())
            insert_knowledge_fact(con, fact_id, f["content"], f.get("citation",""), f.get("type","otro"))
            # embed y agregar al índice
            e = client.embeddings.create(model="text-embedding-3-small", input=[f["content"]]).data[0].embedding
            v = np.array([e], dtype="float32")
            faiss.normalize_L2(v)
            index.add(v)
            new_metas.append({"chunk_id": fact_id, "doc_id": "knowledge_fact", "page_start": None, "page_end": None, "heading_path": f.get("citation","")})
            new_vecs.append(v)

    # append metas
    with open(metas_path, "a", encoding="utf-8") as out:
        for m in new_metas:
            out.write(json.dumps(m, ensure_ascii=False) + "\n")

    faiss.write_index(index, faiss_path)
    return len(new_metas)

