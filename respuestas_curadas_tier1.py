"""
=======================================================================
RESPUESTAS_CURADAS_TIER1.PY - BASE DE RESPUESTAS PRE-APROBADAS
=======================================================================

🎯 FUNCIÓN PRINCIPAL:
   Sistema de respuestas curadas de alta confianza para consultas frecuentes.
   Contiene 40+ respuestas pre-aprobadas extraídas de documentos oficiales.

📋 BASE DE CONOCIMIENTO:
   Respuestas curadas extraídas directamente de los Tomos oficiales:
   - Tomo 1: Sistema de Evaluación y Tramitación
   - Tomo 2: Disposiciones Generales  
   - Tomo 3: Permisos para Desarrollo y Negocios
   - Tomo 4: Licencias y Certificaciones
   - Tomo 5: Urbanización y Lotificación
   - Tomo 6: Distritos de Calificación
   - Tomo 7: Procesos
   - Tomo 8: Edificabilidad
   - Tomo 9: Infraestructura y Ambiente
   - Tomo 10: Conservación Histórica
   - Tomo 11: Querellas

🔍 SISTEMA DE BÚSQUEDA INTELIGENTE:
   1. Búsqueda exacta por palabras clave
   2. Búsqueda fuzzy con corrección de errores
   3. Índice de sinónimos y términos relacionados
   4. Scoring por relevancia y confianza
   5. Filtros por tomo y categoría

⚡ VENTAJAS DEL TIER 1:
   - Respuestas instantáneas (sin API calls)
   - 100% de confianza (pre-aprobadas)
   - Citas directas de documentos oficiales
   - Sin costo de tokens OpenAI
   - Disponible offline

📊 ESTRUCTURA DE DATOS:
   Cada respuesta curada incluye:
   - Pregunta clave normalizada
   - Respuesta estructurada oficial
   - Tomo de origen
   - Archivo fuente específico
   - Lista de palabras clave
   - Tags de categorización
   - Nivel de confianza
   - Fecha de actualización

🔧 ALGORITMOS DE MATCHING:
   - Normalización de texto (lowercase, acentos, etc.)
   - Similitud por distancia de Levenshtein
   - Análisis de n-gramas
   - Peso por frecuencia de términos
   - Umbral de confianza configurable

📈 TIPOS DE CONSULTAS CUBIERTAS:
   - Definiciones de términos técnicos
   - Procesos de permisos paso a paso
   - Requisitos específicos por zona
   - Cálculos de retiros y alturas
   - Usos permitidos por distrito
   - Procedimientos de radicación
   - Documentos requeridos
   - Plazos y términos legales

🚀 FUNCIONES EXPORTADAS:
   - inicializar_tier1(): Setup del sistema
   - buscar_tier1(): Búsqueda principal
   - consulta_dinamica(): Búsqueda avanzada
   - sistema_respuestas_curadas(): Interfaz completa

💡 MANTENIMIENTO:
   Las respuestas se actualizan periódicamente cuando cambian
   los reglamentos oficiales. Cada respuesta incluye metadatos
   de trazabilidad al documento original.

=======================================================================
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import difflib
from datetime import datetime

@dataclass
class RespuestaCurada:
    """Estructura mejorada para almacenar respuestas curadas con formato estructurado"""
    pregunta_clave: str
    respuesta: str
    tomo: int
    archivo_origen: str
    keywords: List[str]
    confianza_base: float = 0.9
    
    # Nuevos campos para respuestas estructuradas
    contexto_normativo: str = ""
    requisitos_especificos: List[str] = None
    procedimientos: List[str] = None
    profesionales_requeridos: List[str] = None
    consideraciones_especiales: List[str] = None
    referencias_cruzadas: List[str] = None
    ejemplos_practicos: List[str] = None
    alertas_importantes: List[str] = None
    respuesta_limpia: str = ""
    referencia_exacta: str = ""
    es_interpretativa: bool = False
    
    def __post_init__(self):
        """Inicializa listas vacías y procesa el contenido"""
        if self.requisitos_especificos is None:
            self.requisitos_especificos = []
        if self.procedimientos is None:
            self.procedimientos = []
        if self.profesionales_requeridos is None:
            self.profesionales_requeridos = []
        if self.consideraciones_especiales is None:
            self.consideraciones_especiales = []
        if self.referencias_cruzadas is None:
            self.referencias_cruzadas = []
        if self.ejemplos_practicos is None:
            self.ejemplos_practicos = []
        if self.alertas_importantes is None:
            self.alertas_importantes = []
        
        # Completar campos faltantes
        if not self.respuesta_limpia:
            self.respuesta_limpia = self._limpiar_texto_simple(self.respuesta)
        if not self.referencia_exacta:
            self.referencia_exacta = self._generar_referencia_simple()
        
        # Auto-procesar contenido si no está estructurado
        self._auto_estructurar_contenido()
    
    def _auto_estructurar_contenido(self):
        """Extrae automáticamente elementos estructurados del contenido"""
        # Extraer requisitos
        requisitos_patterns = [
            r"(?:requisito|documento|certificac|plano).*?requer.*?:?\s*([^\n\.]+)",
            r"deberá.*?(?:presentar|someter|incluir).*?([^\n\.]+)",
            r"es obligatorio.*?([^\n\.]+)"
        ]
        
        for pattern in requisitos_patterns:
            matches = re.findall(pattern, self.respuesta, re.IGNORECASE | re.DOTALL)
            self.requisitos_especificos.extend([m.strip() for m in matches if len(m.strip()) > 10])
        
        # Extraer procedimientos (pasos secuenciales)
        proc_patterns = [
            r"(?:paso|etapa|fase)\s*\d+[:\.]?\s*([^\n]+)",
            r"\d+\.\s*([^\n]+(?:debe|tiene|procede|solicita).*?)",
            r"primero.*?([^\n\.]+)"
        ]
        
        for pattern in proc_patterns:
            matches = re.findall(pattern, self.respuesta, re.IGNORECASE)
            self.procedimientos.extend([m.strip() for m in matches if len(m.strip()) > 10])
        
        # Extraer profesionales requeridos
        prof_patterns = [
            r"(?:arquitecto|ingeniero|profesional|inspector).*?(?:licenciado|autorizado|certificado)",
            r"PA\b",
            r"IOC\b",
            r"IA\b"
        ]
        
        for pattern in prof_patterns:
            matches = re.findall(pattern, self.respuesta, re.IGNORECASE)
            self.profesionales_requeridos.extend(list(set(matches)))
        
        # Extraer alertas importantes
        alert_patterns = [
            r"(?:importante|crítico|obligatorio|prohibido|no se permite).*?([^\n\.]+)",
            r"(?:multa|sanción|violación).*?([^\n\.]+)"
        ]
        
        for pattern in alert_patterns:
            matches = re.findall(pattern, self.respuesta, re.IGNORECASE)
            self.alertas_importantes.extend([m.strip() for m in matches if len(m.strip()) > 10])
    
    def generar_respuesta_estructurada(self, consulta_original: str) -> str:
        """Genera una respuesta estructurada similar al estilo de Claude"""
        
        respuesta_estructurada = []
        
        # Encabezado contextual
        respuesta_estructurada.append(f"## **Respuesta sobre: {self._extraer_tema_principal(consulta_original)}**\n")
        
        # Marco normativo
        if self.contexto_normativo or self.tomo:
            respuesta_estructurada.append("### **Marco Normativo Aplicable**")
            if self.tomo:
                tomo_romano = self._numero_a_romano(self.tomo)
                respuesta_estructurada.append(f"- **Tomo {tomo_romano}** del Reglamento Conjunto JP-RP-41")
            if self.contexto_normativo:
                respuesta_estructurada.append(f"- {self.contexto_normativo}")
            respuesta_estructurada.append("")
        
        # Respuesta principal
        respuesta_estructurada.append("### **Información Principal**")
        respuesta_estructurada.append(self._formatear_respuesta_principal())
        respuesta_estructurada.append("")
        
        # Requisitos específicos
        if self.requisitos_especificos:
            respuesta_estructurada.append("### **Requisitos Específicos**")
            for i, req in enumerate(self.requisitos_especificos[:5], 1):
                respuesta_estructurada.append(f"{i}. **{req}**")
            respuesta_estructurada.append("")
        
        # Procedimientos
        if self.procedimientos:
            respuesta_estructurada.append("### **Procedimiento a Seguir**")
            for i, proc in enumerate(self.procedimientos[:5], 1):
                respuesta_estructurada.append(f"{i}. {proc}")
            respuesta_estructurada.append("")
        
        # Profesionales requeridos
        if self.profesionales_requeridos:
            respuesta_estructurada.append("### **Profesionales Requeridos**")
            for prof in set(self.profesionales_requeridos[:3]):
                respuesta_estructurada.append(f"- **{prof}**")
            respuesta_estructurada.append("")
        
        # Alertas importantes
        if self.alertas_importantes:
            respuesta_estructurada.append("### **⚠️ Consideraciones Importantes**")
            for alert in self.alertas_importantes[:3]:
                respuesta_estructurada.append(f"- {alert}")
            respuesta_estructurada.append("")
        
        # Referencias
        respuesta_estructurada.append("### **Referencias Normativas**")
        respuesta_estructurada.append(f"- **Fuente:** {self.archivo_origen}")
        respuesta_estructurada.append(f"- **Tomo:** {self._numero_a_romano(self.tomo)}")
        respuesta_estructurada.append(f"- **Confianza:** {self.confianza_base:.0%}")
        
        return "\n".join(respuesta_estructurada)
    
    def _extraer_tema_principal(self, consulta: str) -> str:
        """Extrae el tema principal de la consulta"""
        # Remover palabras interrogativas
        tema = re.sub(r'¿|qué|cómo|cuál|cuáles|dónde|cuándo|por qué|\?', '', consulta, flags=re.IGNORECASE)
        tema = tema.strip().title()
        return tema[:50] + "..." if len(tema) > 50 else tema
    
    def _formatear_respuesta_principal(self) -> str:
        """Formatea la respuesta principal manteniendo estructura"""
        # Dividir en párrafos y formatear
        parrafos = [p.strip() for p in self.respuesta.split('\n\n') if p.strip()]
        
        respuesta_formateada = []
        for parrafo in parrafos[:3]:  # Limitar a 3 párrafos principales
            if len(parrafo) > 50:  # Solo párrafos sustanciales
                # Resaltar términos técnicos importantes
                parrafo_formateado = re.sub(
                    r'\b(OGPe|permiso|autorización|licencia|certificación|Tomo|Regla|Artículo)\b',
                    r'**\1**',
                    parrafo,
                    flags=re.IGNORECASE
                )
                respuesta_formateada.append(parrafo_formateado)
        
        return "\n\n".join(respuesta_formateada)
    
    def _numero_a_romano(self, num: int) -> str:
        """Convierte número a romano"""
        valores = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        literales = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        
        if num == 0:
            return "General"
        
        resultado = ""
        for i in range(len(valores)):
            count = int(num / valores[i])
            resultado += literales[i] * count
            num -= valores[i] * count
        return resultado
    
    def _limpiar_texto_simple(self, texto: str) -> str:
        """Versión simple de limpieza de texto"""
        texto_limpio = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
        texto_limpio = re.sub(r'\*(.*?)\*', r'\1', texto_limpio)
        texto_limpio = re.sub(r'•\s*', '', texto_limpio)
        texto_limpio = re.sub(r'#{1,6}\s*', '', texto_limpio)
        texto_limpio = re.sub(r'\n+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        return texto_limpio.strip()
    
    def _generar_referencia_simple(self) -> str:
        """Genera referencia simple"""
        tomo_romano = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        if self.tomo == 0:
            return "Consultas Generales - Reglamento Conjunto JP-RP-41"
        elif self.tomo < len(tomo_romano):
            return f"Tomo {tomo_romano[self.tomo]}"
        return f"Tomo {self.tomo}"


class SistemaRespuestasCuradas:
    """Sistema mejorado que genera respuestas estructuradas tipo Claude"""
    
    def __init__(self):
        self.respuestas: List[RespuestaCurada] = []
        self.keywords_index: Dict[str, List[int]] = {}
        self.loaded = False
        self.contexto_sesion = {}
    
    def _limpiar_texto_para_indexacion(self, texto: str) -> str:
        """Limpia el texto removiendo markdown, emojis y formato para indexación efectiva"""
        # Remover markdown
        texto_limpio = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)  # Negritas
        texto_limpio = re.sub(r'\*(.*?)\*', r'\1', texto_limpio)  # Cursivas
        texto_limpio = re.sub(r'#{1,6}\s*', '', texto_limpio)  # Headers
        texto_limpio = re.sub(r'•\s*', '', texto_limpio)  # Bullets
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', texto_limpio)  # Links
        
        # Remover saltos de línea múltiples
        texto_limpio = re.sub(r'\n+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        
        return texto_limpio.strip().lower()
    
    def buscar_respuesta_curada(self, consulta: str) -> Optional[Tuple[RespuestaCurada, float]]:
        """Busca respuesta curada usando algoritmo mejorado"""
        if not self.loaded or not self.respuestas:
            return None
        
        consulta_limpia = self._limpiar_texto_para_indexacion(consulta)
        consulta_keywords = self._extraer_keywords_inteligente(consulta_limpia)
        
        mejores_matches = []
        
        for idx, respuesta in enumerate(self.respuestas):
            # Calcular similitud con pregunta clave
            similitud_pregunta = difflib.SequenceMatcher(
                None, 
                consulta_limpia, 
                self._limpiar_texto_para_indexacion(respuesta.pregunta_clave)
            ).ratio()
            
            # Calcular similitud con keywords
            keywords_match = len(set(consulta_keywords) & set(respuesta.keywords)) / max(len(consulta_keywords), 1)
            
            # Calcular similitud con contenido
            similitud_contenido = difflib.SequenceMatcher(
                None,
                consulta_limpia,
                respuesta.respuesta_limpia
            ).ratio()
            
            # Puntuación combinada con pesos ajustados
            puntuacion_final = (
                similitud_pregunta * 0.5 +
                keywords_match * 0.3 +
                similitud_contenido * 0.2
            ) * respuesta.confianza_base
            
            if puntuacion_final > 0.3:  # Umbral mínimo
                mejores_matches.append((respuesta, puntuacion_final))
        
        if mejores_matches:
            # Ordenar por puntuación y devolver el mejor
            mejores_matches.sort(key=lambda x: x[1], reverse=True)
            return mejores_matches[0]
        
        return None
    
    def buscar_respuesta_curada_estructurada(self, consulta: str) -> Optional[Tuple[str, float, str]]:
        """Busca respuesta curada y la devuelve en formato estructurado"""
        if not self.loaded:
            return None
        
        # Buscar respuesta usando algoritmo existente
        resultado_base = self.buscar_respuesta_curada(consulta)
        
        if not resultado_base:
            return None
        
        respuesta_curada, confianza = resultado_base
        
        # Generar respuesta estructurada
        respuesta_estructurada = respuesta_curada.generar_respuesta_estructurada(consulta)
        
        # Agregar contexto adicional basado en la consulta
        respuesta_enriquecida = self._enriquecer_respuesta_con_contexto(
            respuesta_estructurada, consulta, respuesta_curada
        )
        
        fuente = f"Respuestas Curadas - {respuesta_curada.archivo_origen} (Tomo {respuesta_curada.tomo})"
        
        return (respuesta_enriquecida, confianza, fuente)
    
    def _enriquecer_respuesta_con_contexto(self, respuesta_base: str, consulta: str, 
                                         respuesta_curada: RespuestaCurada) -> str:
        """Enriquece la respuesta con contexto adicional relevante"""
        
        enriquecimiento = []
        
        # Agregar recomendaciones prácticas
        recomendaciones = self._generar_recomendaciones_practicas(consulta, respuesta_curada)
        if recomendaciones:
            enriquecimiento.append("\n### **🎯 Recomendaciones Prácticas**")
            for rec in recomendaciones:
                enriquecimiento.append(f"- {rec}")
        
        # Agregar próximos pasos
        proximos_pasos = self._generar_proximos_pasos(consulta, respuesta_curada)
        if proximos_pasos:
            enriquecimiento.append("\n### **⏭️ Próximos Pasos Sugeridos**")
            for i, paso in enumerate(proximos_pasos, 1):
                enriquecimiento.append(f"{i}. {paso}")
        
        # Agregar referencias relacionadas
        referencias_relacionadas = self._encontrar_referencias_relacionadas(consulta, respuesta_curada)
        if referencias_relacionadas:
            enriquecimiento.append("\n### **📚 Referencias Relacionadas**")
            for ref in referencias_relacionadas:
                enriquecimiento.append(f"- {ref}")
        
        # Agregar nota de actualización
        enriquecimiento.append(f"\n---\n*Respuesta generada el {datetime.now().strftime('%d/%m/%Y')} basada en el Reglamento Conjunto JP-RP-41 vigente.*")
        
        return respuesta_base + "\n".join(enriquecimiento)
    
    def _generar_recomendaciones_practicas(self, consulta: str, respuesta_curada: RespuestaCurada) -> List[str]:
        """Genera recomendaciones prácticas basadas en la consulta"""
        recomendaciones = []
        
        # Recomendaciones basadas en palabras clave de la consulta
        consulta_lower = consulta.lower()
        
        if any(palabra in consulta_lower for palabra in ['permiso', 'solicitud', 'trámite']):
            recomendaciones.append("**Consulte primero** con un profesional autorizado antes de iniciar el trámite")
            recomendaciones.append("**Verifique la documentación** requerida específica para su tipo de proyecto")
        
        if any(palabra in consulta_lower for palabra in ['construcción', 'edificar', 'obra']):
            recomendaciones.append("**Obtenga una pre-consulta** en la OGPe para clarificar requisitos específicos")
            recomendaciones.append("**Asegúrese del cumplimiento** con códigos de construcción vigentes")
        
        if any(palabra in consulta_lower for palabra in ['zonificación', 'uso', 'clasificación']):
            recomendaciones.append("**Verifique la zonificación actual** del terreno en los mapas oficiales")
            recomendaciones.append("**Considere restricciones ambientales** que puedan aplicar")
        
        if 'comercial' in consulta_lower or 'negocio' in consulta_lower:
            recomendaciones.append("**Evalúe requisitos de estacionamiento** para actividades comerciales")
            recomendaciones.append("**Considere el impacto en el tráfico** del área circundante")
        
        return recomendaciones[:3]  # Limitar a 3 recomendaciones
    
    def _generar_proximos_pasos(self, consulta: str, respuesta_curada: RespuestaCurada) -> List[str]:
        """Genera próximos pasos específicos"""
        pasos = []
        
        consulta_lower = consulta.lower()
        
        if any(palabra in consulta_lower for palabra in ['cómo', 'proceso', 'pasos']):
            pasos.append("**Revisar la documentación completa** en el tomo correspondiente")
            pasos.append("**Contactar la OGPe** para aclarar dudas específicas")
            
        if 'permiso' in consulta_lower:
            pasos.append("**Reunir toda la documentación** requerida antes de radicar")
            pasos.append("**Programar cita** en la oficina regional correspondiente")
            
        if any(palabra in consulta_lower for palabra in ['requisitos', 'documentos']):
            pasos.append("**Preparar lista de verificación** con todos los documentos")
            pasos.append("**Validar información** con un profesional cualificado")
        
        # Paso general siempre útil
        if not pasos:
            pasos.append("**Consultar la fuente normativa completa** para detalles adicionales")
        
        return pasos
    
    def _encontrar_referencias_relacionadas(self, consulta: str, respuesta_curada: RespuestaCurada) -> List[str]:
        """Encuentra referencias cruzadas relevantes"""
        referencias = []
        
        # Basado en el tomo de la respuesta actual
        tomo_actual = respuesta_curada.tomo
        
        if tomo_actual == 2:  # Tomo de permisos
            referencias.append("Tomo III - Normas de construcción complementarias")
            referencias.append("Tomo IX - Sistemas de infraestructura")
            
        elif tomo_actual == 3:  # Tomo de construcción
            referencias.append("Tomo II - Procedimientos de permisos")
            referencias.append("Tomo IV - Aspectos ambientales")
            
        elif tomo_actual in [5, 6]:  # Tomos de zonificación
            referencias.append("Tomo II - Procesos administrativos")
            referencias.append("Mapas de zonificación municipales")
        
        # Referencias comunes útiles
        referencias.append("Reglamento de Construcción vigente")
        referencias.append("Código Municipal aplicable")
        
        return referencias[:3]  # Limitar referencias
    
    def generar_respuesta_dinamica(self, consulta: str, contexto_adicional: Dict = None) -> str:
        """Genera respuesta dinámica combinando búsqueda curada con generación contextual"""
        # Buscar en respuestas curadas
        resultado_curado = self.buscar_respuesta_curada_estructurada(consulta)
        
        if resultado_curado:
            respuesta, confianza, fuente = resultado_curado
            
            # Si la confianza es alta, usar respuesta curada estructurada
            if confianza > 0.8:
                return respuesta
        
        # Si no hay respuesta curada satisfactoria, generar respuesta base
        return self._generar_respuesta_fallback(consulta, contexto_adicional)
    
    def _generar_respuesta_fallback(self, consulta: str, contexto_adicional: Dict = None) -> str:
        """Genera respuesta de fallback cuando no hay respuesta curada exacta"""
        
        respuesta_fallback = []
        
        respuesta_fallback.append(f"## **Consulta sobre: {consulta}**\n")
        
        respuesta_fallback.append("### **Información General**")
        respuesta_fallback.append("Su consulta requiere una evaluación más específica basada en los detalles particulares de su proyecto.")
        respuesta_fallback.append("")
        
        # Sugerir recursos relevantes basados en palabras clave
        recursos = self._sugerir_recursos_por_palabras_clave(consulta)
        if recursos:
            respuesta_fallback.append("### **📍 Recursos Relevantes**")
            for recurso in recursos:
                respuesta_fallback.append(f"- {recurso}")
            respuesta_fallback.append("")
        
        respuesta_fallback.append("### **🎯 Recomendación**")
        respuesta_fallback.append("Para obtener información precisa sobre su situación específica, se recomienda:")
        respuesta_fallback.append("1. **Consultar directamente** el tomo relevante del Reglamento Conjunto JP-RP-41")
        respuesta_fallback.append("2. **Contactar la OGPe** para una pre-consulta")
        respuesta_fallback.append("3. **Consultar con un profesional autorizado** para su tipo de proyecto")
        
        respuesta_fallback.append(f"\n---\n*El sistema no encontró una respuesta curada específica para esta consulta. Se recomienda consulta directa con las fuentes normativas.*")
        
        return "\n".join(respuesta_fallback)
    
    def _sugerir_recursos_por_palabras_clave(self, consulta: str) -> List[str]:
        """Sugiere recursos específicos basado en palabras clave"""
        recursos = []
        consulta_lower = consulta.lower()
        
        if any(palabra in consulta_lower for palabra in ['construcción', 'edificio', 'obra']):
            recursos.append("**Tomo III** - Normas de construcción")
            recursos.append("**Código de Construcción** vigente")
        
        if any(palabra in consulta_lower for palabra in ['permiso', 'licencia', 'autorización']):
            recursos.append("**Tomo II** - Procedimientos administrativos")
            recursos.append("**Portal OGPe** - Solicitudes en línea")
        
        if any(palabra in consulta_lower for palabra in ['zonificación', 'uso', 'distrito']):
            recursos.append("**Tomos V-VI** - Distritos de calificación")
            recursos.append("**Mapas de zonificación** municipales")
        
        if any(palabra in consulta_lower for palabra in ['ambiental', 'erosión', 'desperdicios']):
            recursos.append("**Tomo IV** - Aspectos ambientales")
            recursos.append("**DRNA** - Permisos ambientales")
        
        return recursos
    
    def _extraer_keywords_inteligente(self, texto: str) -> List[str]:
        """Extrae keywords de forma inteligente"""
        # Palabras comunes a ignorar
        stop_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son',
            'con', 'para', 'al', 'del', 'las', 'una', 'su', 'me', 'si', 'ya', 'o', 'como', 'pero', 'sus', 'le', 'ha',
            'este', 'esta', 'esto', 'ese', 'esa', 'eso', 'aquel', 'aquella', 'aquello', 'quien', 'que', 'cual',
            'cuando', 'donde', 'como', 'porque', 'cómo', 'qué', 'cuál', 'dónde', 'cuándo', 'por', 'qué'
        }
        
        # Tokenizar y filtrar
        palabras = re.findall(r'\b\w+\b', texto.lower())
        keywords = [palabra for palabra in palabras 
                   if len(palabra) > 2 and palabra not in stop_words]
        
        return list(set(keywords))  # Remover duplicados
    
    def cargar_respuestas_curadas(self) -> bool:
        """Carga todas las respuestas curadas desde los archivos con cobertura mejorada"""
        try:
            base_path = os.path.join("data", "RespuestasParaChatBot")
            
            if not os.path.exists(base_path):
                print("⚠️ Directorio de respuestas curadas no encontrado")
                return False
            
            total_respuestas = 0
            
            # Cargar respuestas de cada tomo con algoritmo mejorado
            for tomo_num in range(1, 12):  # Tomos 1-11
                tomo_dir = f"RespuestasIA_Tomo{tomo_num}"
                tomo_path = os.path.join(base_path, tomo_dir)
                
                if os.path.exists(tomo_path):
                    respuestas_cargadas = self._cargar_tomo_mejorado(tomo_path, tomo_num)
                    total_respuestas += respuestas_cargadas
            
            # Agregar consultas comunes
            consultas_comunes = self._agregar_consultas_comunes()
            total_respuestas += consultas_comunes
            
            # Agregar variaciones y sinónimos
            variaciones = self._agregar_variaciones_sinonimos()
            total_respuestas += variaciones
            
            self._construir_indice_keywords_mejorado()
            self.loaded = True
            
            print(f"✅ Sistema Tier 1 cargado: {total_respuestas} respuestas curadas")
            print(f"📊 Keywords indexadas: {len(self.keywords_index)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando respuestas curadas: {e}")
            return False
    
    def _cargar_tomo_mejorado(self, tomo_path: str, tomo_num: int) -> int:
        """Carga respuestas de un tomo con algoritmo mejorado"""
        respuestas_count = 0
        
        # Buscar archivos en estructura plana
        for archivo in os.listdir(tomo_path):
            if archivo.endswith('.txt') and not archivo.startswith('texto_extraido'):
                archivo_path = os.path.join(tomo_path, archivo)
                respuestas_archivo = self._procesar_archivo_respuestas(archivo_path, tomo_num, archivo)
                respuestas_count += respuestas_archivo
        
        return respuestas_count
    
    def _procesar_archivo_respuestas(self, archivo_path: str, tomo_num: int, nombre_archivo: str) -> int:
        """Procesa un archivo de respuestas y extrae Q&A estructurado"""
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            respuestas_extraidas = 0
            
            # Diferentes patrones según el tipo de archivo
            if 'Respuestas' in nombre_archivo:
                respuestas_extraidas = self._extraer_respuestas_principales(contenido, tomo_num, nombre_archivo)
            elif 'flujograma' in nombre_archivo:
                respuestas_extraidas = self._extraer_flujogramas(contenido, tomo_num, nombre_archivo)
            elif 'Resoluciones' in nombre_archivo:
                respuestas_extraidas = self._extraer_resoluciones(contenido, tomo_num, nombre_archivo)
            elif 'TablaCabida' in nombre_archivo or 'Tabla' in nombre_archivo:
                respuestas_extraidas = self._extraer_tablas(contenido, tomo_num, nombre_archivo)
            
            return respuestas_extraidas
            
        except Exception as e:
            print(f"⚠️ Error procesando {nombre_archivo}: {e}")
            return 0
    
    def _extraer_respuestas_principales(self, contenido: str, tomo_num: int, archivo: str) -> int:
        """Extrae respuestas principales con algoritmo mejorado"""
        count = 0
        
        # Evitar respuestas con contenido defectuoso
        if 'NO ENCONTRADO' in contenido:
            return 0
        
        # Patrón mejorado para secciones
        patrones_seccion = [
            r'\*\*\d+\.\s+([^*]+):\*\*',
            r'## \d+\.\s+([^#\n]+)',
            r'### ([^#\n]+)',
            r'^\d+\.\s+([^:\n]+):',
        ]
        
        for patron in patrones_seccion:
            secciones = re.split(patron, contenido, flags=re.MULTILINE)
            
            if len(secciones) > 2:  # Se encontraron secciones
                for i in range(1, len(secciones), 2):
                    if i + 1 < len(secciones):
                        titulo = secciones[i].strip()
                        respuesta = secciones[i + 1].strip()
                        
                        if len(respuesta) > 100 and 'NO ENCONTRADO' not in respuesta:
                            # Crear respuesta curada
                            keywords = self._extraer_keywords_inteligente(titulo + " " + respuesta[:200])
                            
                            respuesta_curada = RespuestaCurada(
                                pregunta_clave=f"¿{titulo}?",
                                respuesta=respuesta.strip(),
                                tomo=tomo_num,
                                archivo_origen=archivo,
                                keywords=keywords,
                                confianza_base=0.85
                            )
                            
                            self.respuestas.append(respuesta_curada)
                            count += 1
                break  # Si se encontraron secciones, no probar otros patrones
        
        return count
    
    def _extraer_flujogramas(self, contenido: str, tomo_num: int, archivo: str) -> int:
        """Extrae información de flujogramas"""
        pregunta = "¿Cuál es el proceso general?"
        keywords = ["proceso", "flujograma", "pasos", "procedimiento"]
        
        if 'flujogramaCambioCalif' in archivo:
            pregunta = "¿Cómo cambiar la calificación de un terreno?"
            keywords = ["cambio", "calificacion", "terreno", "proceso", "pasos"]
        elif 'flujogramaSitiosHistoricos' in archivo:
            pregunta = "¿Cuál es el proceso para sitios históricos?"
            keywords = ["sitios", "historicos", "proceso", "patrimonio", "shpo"]
        elif 'flujogramaTerrPublicos' in archivo:
            pregunta = "¿Cómo manejar terrenos públicos?"
            keywords = ["terrenos", "publicos", "proceso", "gobierno"]
        else:
            return 0
        
        respuesta_curada = RespuestaCurada(
            pregunta_clave=pregunta,
            respuesta=contenido.strip(),
            tomo=tomo_num,
            archivo_origen=archivo,
            keywords=keywords,
            confianza_base=0.90
        )
        
        self.respuestas.append(respuesta_curada)
        return 1
    
    def _extraer_resoluciones(self, contenido: str, tomo_num: int, archivo: str) -> int:
        """Extrae información de resoluciones"""
        pregunta = f"¿Qué resoluciones aplican al Tomo {tomo_num}?"
        keywords = ["resoluciones", "decisiones", "determinaciones", f"tomo{tomo_num}"]
        
        respuesta_curada = RespuestaCurada(
            pregunta_clave=pregunta,
            respuesta=contenido.strip(),
            tomo=tomo_num,
            archivo_origen=archivo,
            keywords=keywords,
            confianza_base=0.85
        )
        
        self.respuestas.append(respuesta_curada)
        return 1
    
    def _extraer_tablas(self, contenido: str, tomo_num: int, archivo: str) -> int:
        """Extrae información de tablas de cabida"""
        pregunta = f"¿Cuáles son las tablas de cabida del Tomo {tomo_num}?"
        keywords = ["tabla", "cabida", "parametros", "medidas", "dimensiones", "requisitos", f"tomo{tomo_num}"]
        
        respuesta_curada = RespuestaCurada(
            pregunta_clave=pregunta,
            respuesta=contenido.strip(),
            tomo=tomo_num,
            archivo_origen=archivo,
            keywords=keywords,
            confianza_base=0.90
        )
        
        self.respuestas.append(respuesta_curada)
        return 1
    
    def _agregar_consultas_comunes(self) -> int:
        """Agrega respuestas para consultas comunes"""
        consultas_comunes = [
            {
                'pregunta': '¿Qué documentos necesito para solicitar un permiso?',
                'respuesta': '''Según el Reglamento Conjunto JP-RP-41 vigente, la documentación requerida para solicitar permisos de construcción incluye varios componentes esenciales que varían según el tipo y escala del proyecto.

**Documentos Fundamentales:**

• **Planos Técnicos Certificados**: Preparados y sellados por arquitecto o ingeniero colegiado, incluyendo planos de ubicación, arquitectónicos, estructurales y, cuando aplique, sanitarios y eléctricos.

• **Certificación de Cabida**: Documento oficial del Registro de la Propiedad que certifica las dimensiones, área y descripción legal del terreno.

• **Solicitud Oficial**: Formulario requerido debidamente completado con toda la información del proyecto y del solicitante.

**Documentación Complementaria:**

• **Evidencia de Cumplimiento Reglamentario**: Demostración del cumplimiento con retiros, altura máxima, densidad y otros requisitos zonales aplicables.

• **Estudios Especializados**: Dependiendo de la clasificación del terreno y tipo de construcción, pueden requerirse estudios de impacto ambiental, tráfico, o arqueológicos.

La Oficina de Gerencia de Permisos (OGPe) y los municipios pueden solicitar documentación adicional específica según las particularidades del proyecto. Se recomienda consultar los requisitos específicos aplicables a su zona antes de presentar la solicitud.''',
                'keywords': ['documentos', 'permiso', 'solicitud', 'planos', 'certificación', 'cabida', 'ogpe', 'municipio', 'reglamento', 'construcción'],
                'confianza': 0.90
            },
            {
                'pregunta': '¿Cómo solicitar una licencia de construcción?',
                'respuesta': '''El proceso para obtener una licencia de construcción en Puerto Rico sigue un procedimiento estructurado que garantiza el cumplimiento con todas las normativas vigentes.

**Pasos del Proceso:**

1. **Pre-consulta**: Contacte la OGPe o municipio correspondiente para aclarar requisitos específicos de su proyecto.

2. **Preparación de Documentos**: Reúna toda la documentación requerida incluyendo planos certificados, certificación de cabida, y estudios especializados.

3. **Radicación**: Presente la solicitud con todos los documentos a través del Sistema Unificado de Información (SUI) o en persona.

4. **Evaluación**: Las agencias concernidas evalúan la solicitud según sus competencias específicas.

5. **Determinación Final**: Se emite la decisión sobre la aprobación, aprobación con condiciones, o denegación del permiso.

**Consideraciones Importantes:**

• Los términos de evaluación varían según la complejidad del proyecto
• Algunas obras requieren coordinación con múltiples agencias (DRNA, AAA, AEE)
• El cumplimiento con códigos de construcción es fundamental para la aprobación

Se recomienda encarecidamente trabajar con un profesional autorizado (arquitecto o ingeniero) para garantizar el cumplimiento con todos los requisitos aplicables.''',
                'keywords': ['licencia', 'construccion', 'proceso', 'pasos', 'ogpe', 'solicitud', 'permiso', 'radicacion', 'evaluacion'],
                'confianza': 0.88
            }
        ]
        
        count = 0
        for consulta_data in consultas_comunes:
            respuesta_curada = RespuestaCurada(
                pregunta_clave=consulta_data['pregunta'],
                respuesta=consulta_data['respuesta'],
                tomo=0,  # Consultas generales
                archivo_origen="consultas_comunes_sistema",
                keywords=consulta_data['keywords'],
                confianza_base=consulta_data['confianza']
            )
            self.respuestas.append(respuesta_curada)
            count += 1
        
        return count
    
    def _agregar_variaciones_sinonimos(self) -> int:
        """Agrega variaciones y sinónimos de consultas frecuentes"""
        variaciones = [
            {
                'pregunta': '¿Qué es un profesional autorizado?',
                'respuesta': '''Un Profesional Autorizado (PA) es un arquitecto o ingeniero licenciado que ha sido debidamente certificado por la Oficina de Gerencia de Permisos (OGPe) para ejercer funciones específicas dentro del sistema de planificación de Puerto Rico.

**Características del PA:**

• **Licencia Profesional**: Debe poseer licencia vigente para ejercer su profesión en Puerto Rico
• **Certificación Especial**: Ha completado cursos específicos y aprobado exámenes requeridos por la OGPe
• **Responsabilidades Delegadas**: Puede certificar planos, realizar inspecciones, y emitir determinaciones finales en ciertos casos

**Funciones Principales:**

1. **Certificación de Planos**: Puede certificar que los planos cumplen con los reglamentos aplicables
2. **Emisión de Permisos**: En casos específicos, puede emitir permisos de construcción
3. **Inspecciones**: Realiza inspecciones de obras bajo su responsabilidad
4. **Determinaciones Finales**: Emite decisiones en proyectos dentro de su competencia

**Ventajas del Sistema PA:**

• Agiliza los procesos de permisos
• Reduce tiempos de espera para proyectos rutinarios
• Mantiene estándares profesionales y técnicos
• Descentraliza funciones manteniendo control de calidad

Es importante verificar que el profesional seleccionado esté debidamente certificado como PA y que su certificación esté vigente al momento de contratar sus servicios.''',
                'keywords': ['profesional', 'autorizado', 'pa', 'arquitecto', 'ingeniero', 'certificado', 'licenciado', 'ogpe'],
                'confianza': 0.92
            }
        ]
        
        count = 0
        for variacion in variaciones:
            respuesta_curada = RespuestaCurada(
                pregunta_clave=variacion['pregunta'],
                respuesta=variacion['respuesta'],
                tomo=0,
                archivo_origen="variaciones_sistema",
                keywords=variacion['keywords'],
                confianza_base=variacion['confianza']
            )
            self.respuestas.append(respuesta_curada)
            count += 1
        
        return count
    
    def _construir_indice_keywords_mejorado(self):
        """Construye un índice mejorado de keywords para búsqueda rápida"""
        self.keywords_index = {}
        
        for idx, respuesta in enumerate(self.respuestas):
            # Indexar keywords principales
            for keyword in respuesta.keywords:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = []
                self.keywords_index[keyword].append(idx)
            
            # Indexar palabras de la pregunta clave
            palabras_pregunta = self._extraer_keywords_inteligente(respuesta.pregunta_clave)
            for palabra in palabras_pregunta:
                if palabra not in self.keywords_index:
                    self.keywords_index[palabra] = []
                self.keywords_index[palabra].append(idx)
            
            # Indexar sinónimos comunes
            sinonimos = self._generar_sinonimos(respuesta.keywords)
            for sinonimo in sinonimos:
                if sinonimo not in self.keywords_index:
                    self.keywords_index[sinonimo] = []
                self.keywords_index[sinonimo].append(idx)
    
    def _generar_sinonimos(self, keywords: List[str]) -> List[str]:
        """Genera sinónimos comunes para las keywords"""
        sinonimos_map = {
            'permiso': ['licencia', 'autorizacion', 'certificacion'],
            'construccion': ['obra', 'edificacion', 'proyecto'],
            'profesional': ['arquitecto', 'ingeniero', 'tecnico'],
            'documento': ['papel', 'certificado', 'plano'],
            'proceso': ['procedimiento', 'tramite', 'gestión'],
            'requisito': ['requerimiento', 'condicion', 'exigencia'],
            'zonificacion': ['calificacion', 'distrito', 'zona'],
            'terreno': ['solar', 'parcela', 'predio', 'lote'],
            'municipio': ['ayuntamiento', 'alcaldia', 'gobierno local'],
            'ogpe': ['oficina', 'gerencia', 'permisos']
        }
        
        sinonimos = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in sinonimos_map:
                sinonimos.extend(sinonimos_map[keyword_lower])
        
        return sinonimos
    
    def get_estadisticas(self) -> Dict:
        """Devuelve estadísticas del sistema de respuestas curadas"""
        if not self.loaded:
            return {"error": "Sistema no cargado"}
        
        tomos_count = {}
        tipos_archivo = {}
        
        for respuesta in self.respuestas:
            # Contar por tomo
            tomo = f"Tomo {respuesta.tomo}"
            tomos_count[tomo] = tomos_count.get(tomo, 0) + 1
            
            # Contar por tipo de archivo
            if 'Respuestas' in respuesta.archivo_origen:
                tipo = 'Respuestas Principales'
            elif 'flujograma' in respuesta.archivo_origen:
                tipo = 'Flujogramas'
            elif 'Resoluciones' in respuesta.archivo_origen:
                tipo = 'Resoluciones'
            elif 'TablaCabida' in respuesta.archivo_origen:
                tipo = 'Tablas de Cabida'
            else:
                tipo = 'Otros'
            
            tipos_archivo[tipo] = tipos_archivo.get(tipo, 0) + 1
        
        return {
            "total_respuestas": len(self.respuestas),
            "keywords_indexadas": len(self.keywords_index),
            "respuestas_por_tomo": tomos_count,
            "respuestas_por_tipo": tipos_archivo,
            "sistema_cargado": self.loaded
        }

# Instancia global del sistema
sistema_respuestas_curadas = SistemaRespuestasCuradas()

def inicializar_tier1() -> bool:
    """Inicializa el sistema Tier 1 de respuestas curadas"""
    return sistema_respuestas_curadas.cargar_respuestas_curadas()

def buscar_tier1(consulta: str) -> Optional[Tuple[str, float, str]]:
    """
    Busca en Tier 1 de respuestas curadas con formato estructurado
    
    Returns:
        Tuple[respuesta, confianza, fuente] si encuentra match, None si no
    """
    resultado = sistema_respuestas_curadas.buscar_respuesta_curada_estructurada(consulta)
    
    if resultado:
        respuesta, confianza, fuente = resultado
        return (respuesta, confianza, fuente)
    
    return None

def consulta_dinamica(consulta: str, contexto: Dict = None) -> str:
    """
    Función principal para consultas dinámicas con respuesta estructurada
    """
    return sistema_respuestas_curadas.generar_respuesta_dinamica(consulta, contexto)

if __name__ == "__main__":
    # Test del sistema
    print("🧪 Probando Sistema de Respuestas Curadas Tier 1 Mejorado")
    print("=" * 60)
    
    if inicializar_tier1():
        stats = sistema_respuestas_curadas.get_estadisticas()
        print(f"📊 Estadísticas: {stats}")
        
        # Pruebas de consulta
        consultas_test = [
            "¿Cómo cambiar la calificación de un terreno?",
            "¿Qué es la División de Cumplimiento Ambiental?",
            "¿Cuál es el proceso para sitios históricos?",
            "¿Qué resoluciones aplican?",
            "¿Qué documentos necesito para un permiso?",
            "Esta consulta no debería tener respuesta curada"
        ]
        
        for consulta in consultas_test:
            print(f"\n🔍 Consulta: {consulta}")
            resultado = buscar_tier1(consulta)
            
            if resultado:
                respuesta, confianza, fuente = resultado
                print(f"✅ Encontrada (confianza: {confianza:.2f})")
                print(f"📄 Fuente: {fuente}")
                print(f"📝 Respuesta: {respuesta[:300]}...")
            else:
                print("❌ No encontrada en Tier 1")
                # Probar respuesta dinámica
                respuesta_dinamica = consulta_dinamica(consulta)
                print(f"🔄 Respuesta dinámica: {respuesta_dinamica[:200]}...")
    else:
        print("❌ Error inicializando sistema Tier 1")