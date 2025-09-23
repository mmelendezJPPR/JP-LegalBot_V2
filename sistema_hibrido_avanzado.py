import os
import sqlite3
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
import re
from pathlib import Path
import pickle
import json
from datetime import datetime

class SistemaHibridoAvanzado:
    """Sistema RAG híbrido avanzado para JP_LegalBot con aprendizaje continuo"""
    
    def __init__(self, db_path: str = "embedding_db/hybrid_knowledge.db"):
        print("🔧 Inicializando Sistema Híbrido Avanzado...")
        self.db_path = db_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.faiss_index = None
        self.chunk_embeddings = []
        self.chunk_texts = []
        self.chunk_metadata = []
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        print(f"📁 Directorio creado: {os.path.dirname(db_path)}")
        
        # Inicializar base de datos
        self._initialize_database()
        
        # Cargar o construir índice FAISS
        self._load_or_build_index()
        print("✅ Sistema Híbrido Avanzado listo!")
    
    def _initialize_database(self):
        """Inicializa la base de datos SQLite con tablas optimizadas"""
        print("🗄️ Inicializando base de datos...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla para chunks con FTS5
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                content,
                tomo,
                capitulo,
                articulo,
                tipo_seccion,
                fuente
            )
        ''')
        
        # Tabla para hechos aprendidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_text TEXT NOT NULL,
                citation TEXT,
                confidence REAL,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabla para FAQs automáticas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_pattern TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                citations TEXT,
                frequency INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para optimización
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_confidence ON knowledge_facts(confidence DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_faqs_frequency ON auto_faqs(frequency DESC)')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada")
    
    def _load_or_build_index(self):
        """Carga índice FAISS existente o construye uno nuevo"""
        faiss_path = "embedding_db/faiss_index.bin"
        
        if os.path.exists(faiss_path):
            print("🔄 Cargando índice FAISS existente...")
            try:
                self.faiss_index = faiss.read_index(faiss_path)
                self._load_chunk_data()
                print(f"✅ Índice cargado con {self.faiss_index.ntotal} vectores")
            except Exception as e:
                print(f"⚠️ Error cargando índice: {e}")
                print("🔨 Construyendo nuevo índice...")
                self._build_faiss_index()
        else:
            print("🔨 Construyendo nuevo índice FAISS...")
            self._build_faiss_index()
    
    def _build_faiss_index(self):
        """Construye índice FAISS desde archivos TOMO*.txt"""
        print("📚 Procesando documentos TOMO...")
        
        # Buscar archivos TOMO en el directorio data
        data_dir = Path("data")
        tomo_files = list(data_dir.glob("TOMO*.txt"))
        
        if not tomo_files:
            print("⚠️ No se encontraron archivos TOMO*.txt en /data")
            return
        
        print(f"📖 Encontrados {len(tomo_files)} archivos TOMO")
        
        all_chunks = []
        all_metadata = []
        
        for file_path in tomo_files:
            print(f"📖 Procesando {file_path.name}...")
            chunks, metadata = self._process_tomo_file(file_path)
            all_chunks.extend(chunks)
            all_metadata.extend(metadata)
            print(f"   ✅ {len(chunks)} chunks extraídos")
        
        if not all_chunks:
            print("❌ No se encontraron chunks para procesar")
            return
        
        print(f"🧠 Generando embeddings para {len(all_chunks)} chunks...")
        embeddings = self.model.encode(all_chunks, show_progress_bar=True)
        
        # Crear índice FAISS
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product para similitud coseno
        
        # Normalizar embeddings para similitud coseno
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings.astype('float32'))
        
        # Guardar datos
        self.chunk_texts = all_chunks
        self.chunk_metadata = all_metadata
        self.chunk_embeddings = embeddings
        
        # Persistir índice y datos
        os.makedirs("embedding_db", exist_ok=True)
        faiss.write_index(self.faiss_index, "embedding_db/faiss_index.bin")
        self._save_chunk_data()
        
        # Poblar base de datos FTS5
        self._populate_fts_database(all_chunks, all_metadata)
        
        print(f"✅ Índice FAISS construido con {len(all_chunks)} chunks")
    
    def _process_tomo_file(self, file_path: Path) -> Tuple[List[str], List[Dict]]:
        """Procesa un archivo TOMO y extrae chunks con metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error leyendo {file_path}: {e}")
            return [], []
        
        chunks = []
        metadata = []
        
        # Split en chunks inteligentes con overlap
        chunk_size = 4000
        overlap = 600
        
        text_chunks = self._split_with_overlap(content, chunk_size, overlap)
        
        for i, chunk in enumerate(text_chunks):
            # Extraer metadata del chunk
            chunk_metadata = self._extract_metadata(chunk, file_path.stem)
            
            chunks.append(chunk)
            metadata.append(chunk_metadata)
        
        return chunks, metadata
    
    def _split_with_overlap(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split texto con overlap inteligente"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Buscar punto de corte inteligente (final de párrafo)
            cut_point = end
            for i in range(end - 200, end):
                if i >= 0 and text[i] in '.!?\n':
                    cut_point = i + 1
                    break
            
            chunks.append(text[start:cut_point])
            start = cut_point - overlap
        
        return chunks
    
    def _extract_metadata(self, chunk: str, filename: str) -> Dict:
        """Extrae metadata inteligente del chunk"""
        metadata = {
            'fuente': filename,
            'tomo': filename,
            'capitulo': None,
            'articulo': None,
            'tipo_seccion': 'general'
        }
        
        # Detectar capítulos
        cap_match = re.search(r'CAP[ÍI]TULO\s+([IVXLCDM]+|\d+)', chunk, re.IGNORECASE)
        if cap_match:
            metadata['capitulo'] = cap_match.group(1)
            metadata['tipo_seccion'] = 'capitulo'
        
        # Detectar artículos
        art_match = re.search(r'ART[ÍI]CULO\s+(\d+)', chunk, re.IGNORECASE)
        if art_match:
            metadata['articulo'] = art_match.group(1)
            metadata['tipo_seccion'] = 'articulo'
        
        # Detectar secciones especiales
        if re.search(r'DEFINICIONES|DEFINICIÓN', chunk, re.IGNORECASE):
            metadata['tipo_seccion'] = 'definiciones'
        elif re.search(r'PROCEDIMIENTO|PROCESO|TRÁMITE', chunk, re.IGNORECASE):
            metadata['tipo_seccion'] = 'procedimiento'
        elif re.search(r'ZONIFICACIÓN|ZONA|DISTRITO', chunk, re.IGNORECASE):
            metadata['tipo_seccion'] = 'zonificacion'
        
        return metadata
    
    def _populate_fts_database(self, chunks: List[str], metadata: List[Dict]):
        """Puebla la base de datos FTS5 con los chunks"""
        print("🗃️ Poblando base de datos FTS5...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM fts_chunks')  # Limpiar datos anteriores
        
        for chunk, meta in zip(chunks, metadata):
            cursor.execute('''
                INSERT INTO fts_chunks (content, tomo, capitulo, articulo, tipo_seccion, fuente)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                chunk,
                meta.get('tomo', ''),
                meta.get('capitulo', ''),
                meta.get('articulo', ''),
                meta.get('tipo_seccion', ''),
                meta.get('fuente', '')
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos FTS5 poblada con {len(chunks)} chunks")
    
    def _save_chunk_data(self):
        """Guarda datos de chunks para recuperación rápida"""
        print("💾 Guardando datos de chunks...")
        
        data = {
            'texts': self.chunk_texts,
            'metadata': self.chunk_metadata,
            'embeddings': self.chunk_embeddings.tolist() if hasattr(self.chunk_embeddings, 'tolist') else self.chunk_embeddings
        }
        
        with open("embedding_db/chunk_data.pkl", "wb") as f:
            pickle.dump(data, f)
        print("✅ Datos guardados")
    
    def _load_chunk_data(self):
        """Carga datos de chunks guardados"""
        try:
            with open("embedding_db/chunk_data.pkl", "rb") as f:
                data = pickle.load(f)
            
            self.chunk_texts = data['texts']
            self.chunk_metadata = data['metadata']
            self.chunk_embeddings = np.array(data['embeddings'])
            
            print(f"✅ Datos cargados: {len(self.chunk_texts)} chunks")
        except Exception as e:
            print(f"⚠️ Error cargando datos: {e}")
            self._build_faiss_index()
    
    def hybrid_search(self, query: str, k_semantic: int = 8, k_lexical: int = 8, final_k: int = 5) -> List[Dict]:
        """Búsqueda híbrida combinando semántica y léxica"""
        
        # 1. Búsqueda semántica con FAISS
        semantic_results = self._semantic_search(query, k_semantic)
        
        # 2. Búsqueda léxica con FTS5
        lexical_results = self._lexical_search(query, k_lexical)
        
        # 3. Combinar y rerank
        combined_results = self._combine_and_rerank(
            query, semantic_results, lexical_results, final_k
        )
        
        return combined_results
    
    def _semantic_search(self, query: str, k: int) -> List[Dict]:
        """Búsqueda semántica usando FAISS"""
        if not self.faiss_index or not self.chunk_texts:
            return []
        
        # Generar embedding de la query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Buscar en FAISS
        scores, indices = self.faiss_index.search(query_embedding.astype('float32'), k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunk_texts):
                results.append({
                    'text': self.chunk_texts[idx],
                    'metadata': self.chunk_metadata[idx],
                    'score': float(score),
                    'type': 'semantic'
                })
        
        return results
    
    def _lexical_search(self, query: str, k: int) -> List[Dict]:
        """Búsqueda léxica usando FTS5"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Preparar query FTS5
        fts_query = self._prepare_fts_query(query)
        
        try:
            cursor.execute('''
                SELECT content, tomo, capitulo, articulo, tipo_seccion, fuente, rank
                FROM fts_chunks 
                WHERE fts_chunks MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (fts_query, k))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'text': row[0],
                    'metadata': {
                        'tomo': row[1],
                        'capitulo': row[2],
                        'articulo': row[3],
                        'tipo_seccion': row[4],
                        'fuente': row[5]
                    },
                    'score': -row[6],  # FTS5 rank es negativo
                    'type': 'lexical'
                })
            
        except Exception as e:
            print(f"⚠️ Error en búsqueda FTS5: {e}")
            results = []
        finally:
            conn.close()
        
        return results
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepara query para FTS5 con operadores especiales"""
        # Remover caracteres especiales problemáticos
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Split en términos
        terms = query.split()
        
        if len(terms) == 1:
            return f'"{terms[0]}"'
        
        # Para múltiples términos, usar AND implícito
        return ' '.join(f'"{term}"' for term in terms if len(term) > 2)
    
    def _combine_and_rerank(self, query: str, semantic: List[Dict], lexical: List[Dict], final_k: int) -> List[Dict]:
        """Combina resultados semánticos y léxicos con reranking inteligente"""
        
        # Crear diccionario de resultados únicos
        unique_results = {}
        
        # Agregar resultados semánticos
        for result in semantic:
            text_key = result['text'][:100]  # Usar primeros 100 chars como key
            if text_key not in unique_results:
                unique_results[text_key] = result
                unique_results[text_key]['semantic_score'] = result['score']
                unique_results[text_key]['lexical_score'] = 0
            else:
                unique_results[text_key]['semantic_score'] = max(
                    unique_results[text_key].get('semantic_score', 0),
                    result['score']
                )
        
        # Agregar resultados léxicos
        for result in lexical:
            text_key = result['text'][:100]
            if text_key not in unique_results:
                unique_results[text_key] = result
                unique_results[text_key]['semantic_score'] = 0
                unique_results[text_key]['lexical_score'] = result['score']
            else:
                unique_results[text_key]['lexical_score'] = max(
                    unique_results[text_key].get('lexical_score', 0),
                    result['score']
                )
        
        # Calcular score combinado
        for result in unique_results.values():
            semantic_score = result.get('semantic_score', 0)
            lexical_score = result.get('lexical_score', 0)
            
            # Combinar scores con pesos
            combined_score = (0.7 * semantic_score) + (0.3 * lexical_score)
            
            # Bonus por tipo de sección relevante
            if self._is_relevant_section(query, result['metadata']):
                combined_score *= 1.2
            
            result['final_score'] = combined_score
        
        # Ordenar por score final y devolver top k
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )
        
        return sorted_results[:final_k]
    
    def _is_relevant_section(self, query: str, metadata: Dict) -> bool:
        """Determina si una sección es especialmente relevante para la query"""
        query_lower = query.lower()
        section_type = metadata.get('tipo_seccion', '').lower()
        
        relevance_map = {
            'procedimiento': ['trámite', 'proceso', 'solicitud', 'permiso'],
            'zonificacion': ['zona', 'distrito', 'uso', 'clasificación'],
            'definiciones': ['qué es', 'definir', 'significa'],
            'articulo': ['artículo', 'art']
        }
        
        for section, keywords in relevance_map.items():
            if section == section_type:
                return any(keyword in query_lower for keyword in keywords)
        
        return False

    def get_context_for_query(self, query: str, max_tokens: int = 3000) -> Tuple[str, List[str]]:
        """Obtiene contexto optimizado para una query específica"""
        
        # Buscar resultados híbridos
        results = self.hybrid_search(query, final_k=6)
        
        if not results:
            return "No se encontró información relevante.", []
        
        # Construir contexto optimizado
        context_parts = []
        citations = []
        current_tokens = 0
        
        for i, result in enumerate(results):
            text = result['text']
            metadata = result['metadata']
            
            # Estimación simple de tokens (4 chars ≈ 1 token)
            estimated_tokens = len(text) // 4
            
            if current_tokens + estimated_tokens > max_tokens:
                break
            
            # Formato del contexto
            source_info = f"[TOMO {metadata.get('tomo', 'N/A')}"
            if metadata.get('capitulo'):
                source_info += f", Cap. {metadata['capitulo']}"
            if metadata.get('articulo'):
                source_info += f", Art. {metadata['articulo']}"
            source_info += "]"
            
            context_parts.append(f"{source_info}\n{text}\n")
            citations.append(source_info)
            current_tokens += estimated_tokens
        
        context = "\n---\n".join(context_parts)
        
        return context, citations

# Función de integración con el sistema actual
def crear_sistema_hibrido_avanzado():
    """Crea instancia del sistema híbrido avanzado"""
    return SistemaHibridoAvanzado()

if __name__ == "__main__":
    # Test del sistema
    print("🚀 Inicializando Sistema Híbrido Avanzado...")
    sistema = SistemaHibridoAvanzado()
    
    # Test de búsqueda
    test_query = "¿Qué permisos necesito para construir una casa?"
    print(f"\n🔍 Probando búsqueda: '{test_query}'")
    
    context, citations = sistema.get_context_for_query(test_query)
    print(f"\n📄 Contexto encontrado ({len(context)} chars):")
    print(context[:500] + "..." if len(context) > 500 else context)
    print(f"\n📚 Citas: {citations}")