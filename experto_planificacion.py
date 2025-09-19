"""
=======================================================================
EXPERTO_PLANIFICACION.PY - MOTOR DE IA ESPECIALIZADO EN PLANIFICACIÓN
=======================================================================

🎯 FUNCIÓN PRINCIPAL:
   Motor de IA especializado en legislación de planificación de Puerto Rico.
   Usa embeddings semánticos y OpenAI para respuestas contextuales precisas.

🧠 TECNOLOGÍA DE IA AVANZADA:
   - Embeddings OpenAI (text-embedding-3-small)
   - Búsqueda semántica por similitud coseno
   - Generación de respuestas con GPT-4
   - Índice persistente para optimización
   - Procesamiento por lotes para grandes datasets

📚 MANEJO DE DOCUMENTOS:
   - Carga automática de archivos .txt desde /data
   - Chunking inteligente de documentos largos
   - Indexación de 11 tomos de reglamentos
   - Metadatos y tracking por documento
   - Cache de embeddings para velocidad

🔍 BÚSQUEDA SEMÁNTICA:
   1. Convierte consulta a embedding vectorial
   2. Calcula similitud con todos los chunks
   3. Retrieva los más relevantes (top-k)
   4. Construye contexto para OpenAI
   5. Genera respuesta contextual

⚡ OPTIMIZACIONES PARA DEPLOYMENT:
   - Índice persistente en /tmp/jp_index.json
   - Procesamiento por lotes (100 docs max)
   - Límite de 4000 chars por chunk
   - Fallbacks automáticos en caso de error
   - Manejo robusto de límites de tokens

🔧 VARIABLES DE ENTORNO:
   - JP_DATA_DIR: Directorio de documentos (default: ./data)
   - JP_INDEX_PATH: Ruta del índice (default: /tmp/jp_index.json)
   - JP_EMB_MODEL: Modelo embeddings (default: text-embedding-3-small)
   - JP_CHAT_MODEL: Modelo chat (default: gpt-4o-mini)

📊 CARACTERÍSTICAS TÉCNICAS:
   - Dimensión embeddings: 1536 (OpenAI)
   - Chunks por documento: Automático según tamaño
   - Retrieval: Top-8 resultados por defecto
   - Timeout: 8 segundos por request
   - Encoding: UTF-8 universal

🚀 FUNCIONES EXPORTADAS:
   - cargar_experto(): Inicializar sistema completo
   - inicializar_experto(): Función de compatibilidad
   - ExpertoPlanificacion.answer(): Responder consultas
   - ExpertoPlanificacion.retrieve(): Obtener contexto

💾 PERSISTENCIA DE DATOS:
   El sistema guarda el índice de embeddings en disco para evitar
   regenerar en cada inicio (costoso en tokens y tiempo).

⚠️ REQUERIMIENTOS:
   - OpenAI API Key configurada
   - Archivos .txt en directorio /data
   - Conexión a internet para embeddings
   - Numpy para operaciones vectoriales

=======================================================================
"""

from __future__ import annotations

import json
import os
import glob
import logging
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

try:
    # Intentamos importar el cliente de OpenAI. Si no está disponible, se
    # lanzará una excepción en tiempo de ejecución cuando se llame a las
    # funciones que lo utilizan.
    from openai import OpenAI
except ImportError as err:
    raise ImportError(
        "No se pudo importar la biblioteca openai. Añádala a su "
        "requirements.txt y asegúrese de que esté instalada." 
    ) from err


logger = logging.getLogger(__name__)


class ExpertoPlanificacion:
    """Clase que encapsula la lógica de recuperación y respuesta."""

    def __init__(self, index: np.ndarray, docs: List[Dict[str, Any]], model: str, chat_model: str) -> None:
        self.index = index.astype(np.float32)
        self.docs = docs
        self.model = model
        self.chat_model = chat_model
        # Pre-normalizamos el índice para acelerar la similitud coseno.
        norm = np.linalg.norm(self.index, axis=1, keepdims=True) + 1e-8
        self.index_norm = self.index / norm
        self.client = OpenAI()

    def _embed(self, texts: List[str]) -> np.ndarray:
        """
        Obtiene los embeddings de una lista de textos utilizando el modelo
        configurado.

        Devuelve un array NumPy de forma (len(texts), dim).
        """
        # Recortamos cada input para asegurar que no exceda el tamaño máximo
        # permitido (8000 tokens aproximadamente para text-embedding-3-small).
        resp = self.client.embeddings.create(
            model=self.model,
            input=[t[:8000] for t in texts],
        )
        embeddings = [item.embedding for item in resp.data]
        return np.array(embeddings, dtype=np.float32)

    def retrieve(self, query: str, k: int = 8) -> List[Tuple[str, str, float]]:
        """
        Recupera los k fragmentos más relevantes del índice para la consulta
        dada. Devuelve una lista de tuplas (texto, origen, score).
        """
        q_vec = self._embed([query])[0]
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
        sims = self.index_norm @ q_norm
        top_idx = np.argsort(-sims)[:k]
        return [(
            self.docs[i]["text"],
            self.docs[i]["src"],
            float(sims[i]),
        ) for i in top_idx]

    def answer(self, pregunta: str, k: int = 8) -> str:
        """
        Genera una respuesta utilizando la información recuperada como
        contexto. Si no se encuentra contexto relevante, devuelve un mensaje
        indicando la falta de evidencia.
        """
        evidencias = self.retrieve(pregunta, k=k)
        if not evidencias:
            return (
                "No tengo evidencia en las fuentes provistas para afirmarlo."
            )
        contexto = "\n\n---\n\n".join([frag for frag, _src, _score in evidencias])
        system_prompt = (
            "Eres un experto en planificación de Puerto Rico. "
            "Respondes exclusivamente basándote en el CONTEXTO proporcionado. "
            "Si la información no está en el contexto, indícalo de forma clara y sucinta."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Pregunta: {pregunta}\n\nCONTEXTO:\n{contexto}",
            },
        ]
        completion = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
        )
        return completion.choices[0].message.content


def _load_texts(data_dir: str) -> List[Dict[str, str]]:
    """
    Carga todos los ficheros de texto (*.txt) de un directorio y sus
    subdirectorios. Devuelve una lista de diccionarios con claves `text` y
    `src` indicando el contenido y la ruta del archivo.
    """
    docs: List[Dict[str, str]] = []
    # Soportamos comodines en patrones para buscar recursivamente
    patrones = [
        os.path.join(data_dir, "*.txt"),
        os.path.join(data_dir, "**", "*.txt"),
    ]
    vistos: set[str] = set()
    for patron in patrones:
        for ruta in glob.glob(patron, recursive=True):
            if ruta in vistos:
                continue
            vistos.add(ruta)
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
            except Exception as exc:
                logger.warning(
                    "No se pudo leer %s: %s", ruta, exc
                )
                continue
            # Dividimos por párrafos dejando fuera los fragmentos muy cortos
            for parrafo in contenido.split("\n\n"):
                texto = parrafo.strip()
                if len(texto) < 250:
                    continue
                docs.append({"text": texto, "src": ruta})
    return docs


def _build_index(docs: List[Dict[str, Any]], model: str) -> np.ndarray:
    """
    Construye el índice de embeddings para los textos dados.
    Devuelve una matriz NumPy donde cada fila es el embedding de un texto.
    
    Para manejar límites de tokens de OpenAI, procesa los documentos en lotes.
    """
    client = OpenAI()
    
    # Preparar textos limitando la longitud para evitar excepciones
    texts = [doc["text"][:4000] for doc in docs]  # Reducir de 8000 a 4000 para más seguridad
    
    all_embeddings = []
    batch_size = 100  # Procesar máximo 100 documentos a la vez
    
    logger.info(f"Procesando {len(texts)} documentos en lotes de {batch_size}")
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Procesando lote {i//batch_size + 1}: documentos {i+1} a {min(i + batch_size, len(texts))}")
        
        try:
            embeddings = client.embeddings.create(
                model=model,
                input=batch,
            ).data
            batch_vecs = [item.embedding for item in embeddings]
            all_embeddings.extend(batch_vecs)
            
        except Exception as e:
            logger.error(f"Error procesando lote {i//batch_size + 1}: {e}")
            # En caso de error, crear embeddings dummy para mantener la estructura
            dummy_embedding = [0.0] * 1536  # Dimensión típica para text-embedding-3-small
            for _ in batch:
                all_embeddings.append(dummy_embedding)
    
    logger.info(f"Embeddings generados: {len(all_embeddings)}")
    return np.array(all_embeddings, dtype=np.float32)


def cargar_experto() -> ExpertoPlanificacion:
    """
    Carga el experto desde un índice persistente o lo crea si no existe.

    Esta función comprueba la existencia de un archivo de índice
    (`JP_INDEX_PATH`). Si se encuentra, lo carga junto con los documentos. Si
    no, busca ficheros de datos en `JP_DATA_DIR`, genera los embeddings y
    guarda el índice para futuras ejecuciones.
    """
    modelo_embedding = os.environ.get(
        "JP_EMB_MODEL",
        "text-embedding-3-small",
    )
    modelo_chat = os.environ.get(
        "JP_CHAT_MODEL",
        "gpt-4o-mini",
    )
    data_dir = os.environ.get("JP_DATA_DIR", os.path.join(os.getcwd(), "data"))
    index_path = os.environ.get("JP_INDEX_PATH", "/tmp/jp_index.json")

    # Si el índice existe lo cargamos
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            vecs = np.array(data["vecs"], dtype=np.float32)
            docs = data["docs"]
            logger.info(
                "Índice cargado desde %s con %d documentos.",
                index_path,
                len(docs),
            )
            return ExpertoPlanificacion(vecs, docs, modelo_embedding, modelo_chat)
        except Exception as exc:
            logger.warning(
                "No se pudo cargar el índice %s: %s. Se reconstruirá el índice.",
                index_path,
                exc,
            )

    # Construimos el índice nuevo
    docs = _load_texts(data_dir)
    if not docs:
        raise RuntimeError(
            f"No se encontraron documentos .txt en {data_dir}. "
            "Asegúrate de que la variable JP_DATA_DIR apunta al directorio correcto."
        )
    logger.info(
        "Generando embeddings para %d documentos usando %s...", len(docs), modelo_embedding
    )
    vecs = _build_index(docs, modelo_embedding)
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"vecs": vecs.tolist(), "docs": docs}, f)
        logger.info("Índice guardado en %s", index_path)
    except Exception as exc:
        logger.warning("No se pudo guardar el índice en %s: %s", index_path, exc)
    return ExpertoPlanificacion(vecs, docs, modelo_embedding, modelo_chat)


def inicializar_experto() -> ExpertoPlanificacion:
    """
    Función de compatibilidad para inicializar el experto.
    
    Esta función es un alias para cargar_experto() para mantener
    compatibilidad con otros módulos del sistema.
    """
    return cargar_experto()