import os, json, numpy as np, faiss
from typing import List, Dict
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_EMBED, DB_PATH, FAISS_PATH
from db import get_conn, fts_search

class HybridRetriever:
    def __init__(self, db_path=DB_PATH, faiss_path=FAISS_PATH):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_path = db_path
        self.faiss_path = faiss_path
        self.index = faiss.read_index(self.faiss_path)
        metas_path = os.path.join(os.path.dirname(self.faiss_path), "metas.jsonl")
        self.metas = [json.loads(l) for l in open(metas_path, "r", encoding="utf-8")]

    def embed(self, text: str) -> np.ndarray:
        e = self.client.embeddings.create(model=MODEL_EMBED, input=[text]).data[0].embedding
        v = np.array([e], dtype="float32")
        faiss.normalize_L2(v)
        return v

    def search_vectors(self, query: str, k=12) -> List[Dict]:
        qv = self.embed(query)
        D, I = self.index.search(qv, k)
        out = []
        for score, i in zip(D[0], I[0]):
            if i == -1: continue
            m = self.metas[i]
            out.append({"score": float(score), **m})
        return out

    def search_lexical(self, query: str, k=12) -> List[Dict]:
        # Usa FTS5 con query literal; permite "permiso NEAR/3 construcción"
        with get_conn(self.db_path) as con:
            rows = fts_search(con, query, limit=k)
        # map to chunk_ids only
        return [{"score": 0.0, "chunk_id": r["chunk_id"], "doc_id": r["doc_id"], "heading_path": r["heading_path"], "page_start": r["page_start"], "page_end": r["page_end"], "snippet": r["snip"]} for r in rows]

    def fetch_texts(self, chunk_ids: List[str]) -> Dict[str, str]:
        # Recupera texto desde FTS por chunk_id
        with get_conn(self.db_path) as con:
            qmarks = ",".join("?"*len(chunk_ids))
            cur = con.execute(f"SELECT chunk_id, chunk_text FROM fts_chunks WHERE rowid IN (SELECT rowid FROM fts_chunks WHERE chunk_id IN ({qmarks}))", chunk_ids)
            return {r["chunk_id"]: r["chunk_text"] for r in cur.fetchall()}

    def hybrid(self, query: str, k_vec=12, k_lex=12, final_k=6) -> List[Dict]:
        vec = self.search_vectors(query, k=k_vec)
        lex = self.search_lexical(query, k=k_lex)
        # Fusión simple: favorece diversidad por chunk_id
        seen, fused = set(), []
        for cand in vec + lex:
            cid = cand["chunk_id"]
            if cid in seen: continue
            seen.add(cid)
            fused.append(cand)
            if len(fused) >= (k_vec//2 + k_lex//2):
                break
        # Traer textos
        texts = self.fetch_texts([c["chunk_id"] for c in fused[:final_k]])
        for c in fused:
            c["text"] = texts.get(c["chunk_id"], "")
        return fused[:final_k]
