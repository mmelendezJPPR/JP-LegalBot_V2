# Embeddings + Base de Datos Kit (FAISS + SQLite)

Este kit te añade **embeddings** (FAISS) y una **base de datos SQLite** para memoria persistente y FAQs.
Se integra fácil con tu proyecto actual.

## 🧩 Componentes
- **SQLite (`app.db`)**: guarda facts aprobados, FAQs y logs mínimos.
- **FAISS (`index/faiss.index`)**: almacena los vectores de:
  - *chunks* del documento (de `/data/*.txt`)
  - *knowledge_facts* (hechos aprobados)
  - *faqs* (preguntas frecuentes)

## 🚀 Flujo
1. **Preparar entorno** (instalar dependencias, setear OPENAI_API_KEY).
2. **Construir índice** desde `/data/*.txt`: chunking → embeddings → FAISS + SQLite FTS5.
3. **Responder** con RAG: recuperar top-k y generar respuesta con citas.
4. **Aprender**: extraer hechos candidatos, **promover** aprobados a `knowledge_facts` y re-embed.

## 📦 Estructura
```
embedding_db_kit/
  README.md
  requirements.txt
  .env.example
  init_db.sql
  config.py
  db.py
  prompts.py
  chunker.py
  build_index.py
  retrieve.py
  answer.py
  learn.py
  demo_cli.py
```
> Copia estos archivos a tu repo (o importa los módulos).

## ✅ Requisitos
- Python 3.10+
- OpenAI API Key
- `pip install -r requirements.txt`

## ⚙️ Pasos
1. Copia tus archivos `TOMO*.txt` a `data/` (o ajusta la ruta en `build_index.py`).
2. Configura `.env`:
   ```
   OPENAI_API_KEY=TU_KEY
   MODEL_EMBED=text-embedding-3-small
   MODEL_CHAT=gpt-4o-mini
   ```
3. Inicializa DB:
   ```bash
   python -m sqlite3 app.db < init_db.sql
   ```
4. Construye índice:
   ```bash
   python build_index.py --data_dir ../JP_LegalBot-main/data --out_index index/faiss.index --db app.db
   ```
5. Prueba consultas:
   ```bash
   python demo_cli.py "¿Qué dice sobre permisos de construcción?"
   ```

## 🔁 Aprendizaje
- `learn.py` implementa el pipeline de **hechos candidatos** → promoción → re-embed.
- Puedes llamar desde tu app después de responder al usuario.

## 🧱 Integración rápida en tu app
En tu `sistema_hibrido.py` (o donde orquestes):
```python
from embedding_db_kit.retrieve import HybridRetriever
from embedding_db_kit.answer import AnswerEngine

retriever = HybridRetriever(db_path="app.db", faiss_path="index/faiss.index")
engine = AnswerEngine(retriever=retriever)

respuesta = engine.answer("tu pregunta")
print(respuesta["text"])
print(respuesta["citations"])
```

## 📌 Notas
- Este kit usa **SQLite FTS5** para búsqueda léxica + **FAISS** para semántica.
- Si luego deseas **pgvector/Postgres**, reemplaza `faiss` y `db.py` por tu adaptador.
- El chunking conserva metadatos de página/heading si tus `TOMO*.txt` los contienen.
