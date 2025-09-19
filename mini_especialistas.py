#!/usr/bin/env python3
"""
=======================================================================
MINI_ESPECIALISTAS.PY - SISTEMA DE IA ESPECIALIZADA POR TEMAS
=======================================================================

🎯 FUNCIÓN PRINCIPAL:
   Sistema de especialistas AI categorizados por temas específicos de
   planificación y desarrollo urbano de Puerto Rico.

🤖 ESPECIALISTAS DISPONIBLES:
   1. PERMISOS Y LICENCIAS
      - Permisos de construcción
      - Licencias comerciales
      - Autorizaciones especiales
      - Procedimientos de radicación

   2. ZONIFICACIÓN Y USO DE SUELOS
      - Clasificaciones de terreno
      - Usos permitidos por distrito
      - Retiros y alturas máximas
      - Densidades poblacionales

   3. URBANIZACIÓN Y LOTIFICACIÓN
      - Subdivisión de terrenos
      - Obras de infraestructura
      - Requisitos de vialidad
      - Servicios públicos

   4. CONSERVACIÓN HISTÓRICA
      - Sitios y estructuras históricas
      - Procesos de preservación
      - Autorizaciones para modificaciones
      - Criterios de evaluación

   5. QUERELLAS Y VIOLACIONES
      - Procedimientos de queja
      - Procesos administrativos
      - Multas y penalidades
      - Recursos de apelación

🔧 ARQUITECTURA TÉCNICA:
   - Router inteligente por categoría
   - Prompts especializados por dominio
   - Integración con experto_planificacion.py
   - Fallback a sistema híbrido general
   - Caché de respuestas por especialidad

📊 FLUJO DE PROCESAMIENTO:
   1. Clasificación automática de consulta
   2. Selección del especialista apropiado
   3. Aplicación de prompt específico
   4. Generación de respuesta contextual
   5. Validación y formato de salida

🎛️ FUNCIONES PRINCIPALES:
   - clasificar_consulta(): Determina categoría
   - seleccionar_especialista(): Elige AI adecuado
   - generar_respuesta_especializada(): Procesa consulta
   - especialista_permisos(): Experto en permisos
   - especialista_zonificacion(): Experto en zonificación
   - especialista_urbanizacion(): Experto en urbanización
   - especialista_conservacion(): Experto en conservación
   - especialista_querellas(): Experto en querellas

🔍 INTEGRACIÓN CON SISTEMA HÍBRIDO:
   Este módulo es llamado por sistema_hibrido.py cuando:
   - No hay respuesta en Tier 1 curado
   - La consulta requiere especialización técnica
   - Se necesita análisis profundo de documentos
   - La pregunta es compleja o multi-dominio

⚡ OPTIMIZACIONES:
   - Detección inteligente de palabras clave
   - Prompts optimizados por especialidad
   - Reutilización de contexto entre consultas
   - Manejo eficiente de tokens OpenAI

🔒 SEGURIDAD Y CONFIABILIDAD:
   - Validación de entrada y salida
   - Manejo de errores robusto
   - Logging de interacciones
   - Respaldo a sistema general

📋 MANTENIMIENTO:
   Los prompts y clasificadores se actualizan basado en:
   - Análisis de consultas frecuentes
   - Cambios en reglamentación
   - Feedback de usuarios
   - Métricas de efectividad

=======================================================================
Sistema de Mini-Especialistas Expandido JP_IA v2.0
Versión mejorada con IA dinámica para especialistas y contexto enriquecido
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Importar experto para función construir_contexto
try:
    from experto_planificacion import inicializar_experto
    EXPERTO_DISPONIBLE = True
except ImportError:
    EXPERTO_DISPONIBLE = False
    print("[WARNING] Experto de planificacion no disponible - funcionando sin constructor de contexto")

def crear_cliente_openai():
    """Función auxiliar para crear cliente OpenAI (Azure o estándar)"""
    import openai
    import os
    
    # Configurar cliente OpenAI (Azure o estándar)
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_KEY")  # Usar la misma variable que app.py
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    if azure_endpoint and azure_key:
        # Usar Azure OpenAI
        client = openai.AzureOpenAI(
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
        )
        model_to_use = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
    else:
        # Fallback a OpenAI estándar
        openai_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=openai_key)
        model_to_use = "gpt-4o-mini"
    
    return client, model_to_use

class TipoConsulta(Enum):
    PROCEDIMIENTO = "procedimiento"
    CALCULO = "calculo"
    NORMATIVA = "normativa"
    INTERPRETACION = "interpretacion"
    VIABILIDAD = "viabilidad"

@dataclass
class ResultadoEspecialista:
    especialista: str
    confianza: float
    respuesta: str
    referencias: List[str]
    calculos: Optional[Dict] = None
    recomendaciones: Optional[List[str]] = None

class MiniEspecialistaBase:
    """Clase base para todos los mini-especialistas"""
    
    def __init__(self, nombre: str, tomo: int):
        self.nombre = nombre
        self.tomo = tomo
        self.palabras_clave = []
        self.patrones_consulta = []
        
    def puede_manejar(self, consulta: str) -> float:
        """Determina si este especialista puede manejar la consulta (0-1)"""
        consulta_lower = consulta.lower()
        
        # Verificar palabras clave específicas
        coincidencias = sum(1 for palabra in self.palabras_clave 
                          if palabra in consulta_lower)
        
        if coincidencias == 0:
            return 0.0
            
        # Verificar patrones más complejos
        patron_score = 0
        for patron in self.patrones_consulta:
            if re.search(patron, consulta_lower):
                patron_score += 0.3
        
        # Calcular score final
        base_score = min(coincidencias * 0.2, 0.8)
        final_score = min(base_score + patron_score, 1.0)
        
        return final_score

class EspecialistaProcedimientos(MiniEspecialistaBase):
    """TOMO 2: Procedimientos Administrativos con IA"""
    
    def __init__(self):
        super().__init__("Especialista en Procedimientos", 2)
        self.palabras_clave = [
            "permiso", "procedimiento", "tramite", "solicitud", "radicacion",
            "determinacion", "evaluacion", "consulta", "ubicacion", "ogpe",
            "municipio", "revision", "documentos", "plazo", "vigencia",
            # Palabras relacionadas con construcción y desarrollo - EXPANDIDAS
            "construir", "construyo", "construye", "construir", "construccion", "construir",
            "edificar", "edifico", "edificar", "obra", "obras", "proyecto", "proyectos",
            "casa", "casas", "vivienda", "viviendas", "residencia", "residencial",
            "edificio", "edificios", "estructura", "estructuras", "inmueble",
            "desarrollo", "urbanismo", "lotificacion", "subdivision", "urbanizar",
            # Tipos de permisos específicos
            "permiso unico", "permiso construccion", "licencia uso", "licencia construccion",
            "autorizacion", "certificacion", "endoso", "aprobacion", "aprobaciones",
            # Verbos y acciones comunes en consultas
            "hacer", "realizar", "tramitar", "solicitar", "obtener", "conseguir", 
            "necesito", "requiero", "debo", "puedo", "como", "que"
        ]
        self.patrones_consulta = [
            r"permiso\s+de\s+construcci[oó]n",
            r"consulta\s+de\s+ubicaci[oó]n",
            r"procedimiento\s+para",
            r"c[oó]mo\s+tramitar",
            r"qu[eé]\s+documentos",
            r"construir\s+una?\s+(casa|vivienda|edificio)",
            r"construyo\s+una?\s+(casa|vivienda|edificio)",  # Nueva variación
            r"construye\s+una?\s+(casa|vivienda|edificio)",  # Nueva variación
            r"necesito\s+para\s+construir",
            r"qu[eé]\s+permisos?\s+necesito",
            r"c[oó]mo\s+(obtener|conseguir)\s+permiso",
            r"c[oó]mo\s+(construir|construyo|edificar)",  # Patrón más amplio
            r"(hacer|realizar)\s+una?\s+(casa|obra|construccion)",
            r"qu[eé]\s+(debo|tengo\s+que|necesito)\s+hacer",
            r"(procedimiento|pasos|requisitos)\s+(para|de)\s+construir"
        ]
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Procesa consultas sobre procedimientos administrativos usando IA + contexto enriquecido"""
        
        # Intentar usar OpenAI para respuesta dinámica
        try:
            client, model_to_use = crear_cliente_openai()
            
            # 🔥 NUEVA FUNCIONALIDAD: Construir contexto enriquecido
            contexto_enriquecido = ""
            citas_contexto = []
            if EXPERTO_DISPONIBLE:
                try:
                    experto = inicializar_experto()
                    resultado_contexto = experto.retrieve(consulta, k=5)
                    
                    # Manejar el resultado de retrieve que devuelve lista de tuplas (texto, origen, score)
                    if isinstance(resultado_contexto, list):
                        contexto_texto = "\n\n".join([item[0] for item in resultado_contexto])
                        citas_contexto = [f"Fuente: {item[1]} (relevancia: {item[2]:.2f})" for item in resultado_contexto]
                    else:
                        # Compatibilidad hacia atrás
                        contexto_texto = str(resultado_contexto)
                    
                    if contexto_texto and contexto_texto != "NO ENCONTRADO EN EL CONTEXTO DISPONIBLE":
                        contexto_enriquecido = f"\n\nCONTEXTO RELEVANTE DE LA BASE DE CONOCIMIENTOS:\n{contexto_texto}\n"
                    else:
                        contexto_enriquecido = ""
                except Exception as e:
                    print(f"⚠️ Error construyendo contexto: {e}")
                    contexto_enriquecido = ""
            
            prompt = f"""Eres un especialista EXPERTO en procedimientos administrativos de la Junta de Planificación de Puerto Rico.

CONSULTA DEL USUARIO:
{consulta}{contexto_enriquecido}

METODOLOGÍA DE RESPUESTA:
1. ANALIZA la consulta desde múltiples ángulos procedimentales
2. PROPORCIONA contexto legal y regulatorio específico
3. DETALLA paso a paso los procedimientos aplicables
4. EXPLICA el razonamiento detrás de cada requisito
5. IDENTIFICA posibles complicaciones o variaciones
6. SUGIERE próximos pasos concretos y resources

INSTRUCCIONES ESPECÍFICAS:
- Si hay CONTEXTO RELEVANTE, úsalo para fundamentar tu respuesta
- Estructura la respuesta en párrafos sustanciales (mínimo 3-4 párrafos)
- Incluye plazos específicos, documentos requeridos, y costos cuando aplicable
- Menciona las entidades responsables y sus competencias específicas
- Proporciona ejemplos prácticos cuando sea útil
- Anticipa preguntas de seguimiento comunes
- FORMATO: Respuesta conversacional y natural (sin símbolos técnicos)

CRITERIOS DE CALIDAD:
- Demuestra pensamiento analítico profundo
- Explica el "por qué" además del "qué"
- Considera excepciones o casos especiales
- Proporciona información de contacto cuando sea relevante

RESPONDE COMO UN CONSULTOR EXPERTO que analiza cada aspecto de la consulta."""

            # Sistema mejorado para respuestas elaboradas
            system_prompt = """Eres un especialista senior en procedimientos administrativos de Puerto Rico con 15+ años de experiencia.

ESTILO DE RESPUESTA:
- Analítico y reflexivo, demostrando pensamiento profundo
- Conversacional pero profesional
- Explicas el contexto y razonamiento detrás de cada procedimiento
- Proporcionas respuestas completas de 4-6 párrafos sustanciales

METODOLOGÍA:
1. Contextualiza la consulta dentro del marco legal puertorriqueño
2. Explica los procedimientos paso a paso con justificaciones
3. Identifica consideraciones importantes y posibles complicaciones
4. Sugiere estrategias prácticas y próximos pasos específicos
5. Anticipa dudas comunes y proporciona clarificaciones

Si no tienes información suficiente en el contexto, indica claramente qué información adicional se necesita y sugiere fuentes específicas como "Tomo 2 - Procedimientos Administrativos" o la agencia correspondiente.

Genera respuestas que demuestren expertise y análisis profundo."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Más tokens para respuestas elaboradas
                temperature=0.4   # Más creatividad para análisis profundo
            )
            
            respuesta_ia = response.choices[0].message.content.strip()
            
            # Limpiar formato técnico para conversación natural
            respuesta_limpia = self._limpiar_formato_conversacional(respuesta_ia)
            
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.95,
                respuesta=respuesta_limpia,
                referencias=[
                    "Tomo 2 - Procedimientos Administrativos",
                    "Análisis especializado con IA"
                ],
                recomendaciones=[
                    "Verificar requisitos específicos para tu proyecto",
                    "Considerar consulta previa si hay dudas"
                ]
            )
            
        except Exception as e:
            # Fallback a respuesta predefinida si OpenAI falla
            return self._procedimiento_fallback(consulta)
    
    def _limpiar_formato_conversacional(self, texto: str) -> str:
        """Convierte formato técnico a conversación natural"""
        
        # Remover símbolos de markdown y formato técnico
        texto = re.sub(r'#{1,6}\s*', '', texto)  # Remover # de títulos
        texto = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', texto)  # Remover asteriscos
        texto = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', texto)  # Remover guiones bajos
        texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)  # Remover links
        texto = re.sub(r'`([^`]+)`', r'\1', texto)  # Remover código inline
        texto = re.sub(r'^[-•]\s*', '', texto, flags=re.MULTILINE)  # Remover viñetas
        
        # Limpiar espacios múltiples y saltos de línea excesivos
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        texto = re.sub(r' {2,}', ' ', texto)
        
        return texto.strip()
    
    def _procedimiento_fallback(self, consulta: str) -> ResultadoEspecialista:
        """Respuesta fallback cuando OpenAI no está disponible"""
        
        # Detectar consultas sobre desarrollos residenciales complejos
        if any(palabra in consulta.lower() for palabra in ["150 unidades", "complejo residencial", "quebrada", "desarrollo", "bayamón"]):
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.95,
                respuesta="""Desarrollo de 150 unidades requiere: Consulta de Ubicación (3-6 meses), Estudio Impacto Ambiental, Desarrollo Preliminar ante OGPe, coordinación DRNA/Educación/ACT. Separación quebrada: 100 pies mínimo. Cabida lotes: 400m² con alcantarillado, 600m² sin alcantarillado. Plazos totales: 19-33 meses.

⚠️ ADVERTENCIA: Verificar requisitos específicos municipales y federales.

✓ CHECKLIST: Zonificación ✓ Impacto ambiental ✓ Infraestructura ✓ Accesos viales

[Tomo 2-p.45] [Tomo 5-p.123] [Tomo 9-p.67]""",
                referencias=[
                    "Tomo 2 - Procedimientos Administrativos",
                    "Tomo 5 - Urbanizaciones Residenciales", 
                    "Tomo 9 - Requisitos Ambientales"
                ]
            )
        
        elif re.search(r"consulta\s+de\s+ubicaci[oó]n", consulta.lower()):
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.90,
                respuesta="""Consulta de Ubicación: verifica viabilidad antes del permiso oficial. Requisitos: solicitud, descripción proyecto, localización, planos conceptuales. Respuesta: 15-30 días hábiles. Vigencia: 2 años para radicar permiso.

⚠️ ADVERTENCIA: Consulta NO sustituye el permiso de construcción.

✓ CHECKLIST: Zonificación ✓ Usos permitidos ✓ Parámetros construcción

[Tomo 2-p.34]""",
                referencias=["Tomo 2 - Sección 2.3: Consultas de Ubicación"]
            )
        else:
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.75,
                respuesta="""NO ENCONTRADO EN EL CONTEXTO DISPONIBLE para procedimiento específico. Consultar Tomo 2 - Procedimientos Administrativos para flujo completo: Radicación → Revisión inicial → Evaluación técnica → Coordinación → Determinación → Notificación.

[Tomo 2-p.12]""",
                referencias=["Tomo 2 - Capítulo 2.1: Disposiciones Generales"]
            )

class EspecialistaTecnicoGrafico(MiniEspecialistaBase):
    """TOMO 3: Especificaciones Técnicas y Elementos Gráficos con Análisis IA"""
    
    def __init__(self):
        super().__init__("Técnico Gráfico", 3)
        self.palabras_clave = [
            # Documentos y planos
            "planos", "plano", "mapas", "mapa", "especificaciones", "elementos", "graficos", "grafico",
            "bloques", "atributos", "mensura", "topografia", "topografico", "escalas", "escala",
            "cad", "autocad", "dibujo", "tecnico", "levantamiento", "cartografia",
            "coordenadas", "proyeccion", "datum", "precision", "tolerancia", "medidas", "dimensiones",
            # Términos de construcción y desarrollo  
            "retiros", "altura", "estacionamiento", "construcción", "construccion", "edificacion",
            "área", "area", "casa", "edificio", "estructura", "inmueble", "lote", "solar",
            "máxima", "maxima", "mínimos", "minimos", "calcular", "requisitos", "requerimientos",
            # Documentación técnica
            "formato", "documento", "documentos", "diseño", "diseño", "proyecto", "memoria",
            "descriptiva", "ubicacion", "sitio", "contexto", "planimetria", "elevaciones",
            # Sistemas y estándares
            "sistema", "coordenadas", "estado", "puerto", "rico", "ansi", "utm", "nad83",
            # Términos específicos técnicos
            "simbolos", "leyenda", "norte", "orientacion", "curvas", "nivel", "contorno",
            "linderos", "poligonal", "vertices", "angulos", "distancias", "rumbos", "azimut",
            # Servicios e infraestructura
            "servicios", "electricidad", "agua", "alcantarillado", "telefono", "gas",
            "infraestructura", "vialidad", "acceso", "drenaje", "utilities"
        ]
        self.patrones_consulta = [
            r"especificaciones\s+t[eé]cnicas",
            r"elementos\s+gr[aá]ficos", 
            r"bloques\s+de\s+atributos",
            r"escala\s+de\s+planos",
            r"levantamiento\s+topogr[aá]fico",
            r"precisi[oó]n\s+de\s+medidas",
            r"formato\s+de\s+planos",
            # Nuevos patrones para mejor detección
            r"c[oó]mo\s+(leer|leo|interpretar)\s+(planos?|mapas?)",
            r"qu[eé]\s+(informaci[oó]n|datos)\s+(debe|tiene|contiene)",
            r"c[oó]mo\s+(hacer|elaborar|preparar)\s+planos?",
            r"requisitos\s+(para|de)\s+(planos?|documentos?)",
            r"especificaciones\s+(de|para)\s+(dise[ñn]o|construccion)",
            r"normas\s+(t[eé]cnicas|gr[aá]ficas|de\s+dise[ñn]o)",
            r"sistema\s+de\s+coordenadas",
            r"precisi[oó]n\s+(de\s+)?medidas",
            r"escalas?\s+(recomendadas?|apropiadas?)",
            r"formato\s+(de\s+)?(documentos?|planos?)"
        ]
    
    def _generar_respuesta_ia(self, prompt: str) -> str:
        """Generar respuesta usando formato robusto con fuentes obligatorias"""
        try:
            # Nuevo formato estructurado según recomendaciones ChatGPT
            client, model_to_use = crear_cliente_openai()
            
            # Template estructurado según recomendaciones
            user_prompt = f"""
# PREGUNTA
{prompt}

# CONTEXTO
- Tomo 3: Especificaciones técnicas y elementos gráficos
- Tomo 5: Urbanizaciones residenciales
- Escalas estándar: 1:500 urbano, 1:1000 rural
- Formatos ANSI: D (24"×36"), C (17"×22")
- Coordenadas: Estado Plano Puerto Rico (EPSG:3991)
- Precisiones: centímetros construcción, metros planificación

# SALIDA ESPERADA
- Respuesta directa (3-6 líneas)
- Citas compactas al final
"""

            system_prompt = """Eres un especialista técnico-gráfico en planificación urbana de Puerto Rico.
Responde de forma breve, precisa y profesional.

Solo usa el CONTEXTO provisto; si no está en el contexto, responde:
"NO ENCONTRADO EN EL CONTEXTO DISPONIBLE" y sugiere el tomo o documento a consultar.

Reglas:
- Cita brevemente la fuente al final: [Tomo:{tomo}-p{pág}] o [Estándar:{nombre}].
- Si detectas términos técnicos, inicia con definición corta (1-2 líneas).
- Respuesta directa máximo 6 líneas, luego citas compactas."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception:
            # Fallback a respuestas específicas cuando IA no está disponible
            if "desarrollo" in prompt.lower() and ("150 unidades" in prompt.lower() or "residencial" in prompt.lower()):
                return """Desarrollo de 150 unidades requiere planimetría escala 1:500, bloques de atributos para cada lote, coordenadas Estado Plano PR, y documentación de servicios públicos existentes. Planos formato ANSI-D mínimo.

[Tomo 3-p.45] [Tomo 5-p.123] [Estándar:ANSI-D]"""

            elif "escala" in prompt.lower():
                return """Escalas recomendadas: 1:500 para diseño urbano detallado, 1:1000 para planificación general, 1:200 para construcción. Textos altura mínima 2.5mm escala final.

[Tomo 3-p.67] [Estándar:ANSI]"""

            elif "topograf" in prompt.lower():
                return """Levantamiento topográfico requiere GPS/GNSS RTK precisión centimétrica, curvas nivel cada 1m zona urbana, representación servicios aéreos/subterráneos, control calidad error máximo 1:10,000.

[Tomo 3-p.89] [Estándar:Agrimensura-PR]"""
            
            else:
                return """NO ENCONTRADO EN EL CONTEXTO DISPONIBLE. Consultar Tomo 3 - Especificaciones Técnicas y Elementos Gráficos para requisitos específicos de documentación técnica.

[Tomo 3-completo]"""
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Procesa consultas técnico-gráficas usando IA + contexto enriquecido"""
        
        # Intentar usar OpenAI para respuesta dinámica elaborada
        try:
            client, model_to_use = crear_cliente_openai()
            
            # Construir contexto enriquecido
            contexto_enriquecido = ""
            citas_contexto = []
            if EXPERTO_DISPONIBLE:
                try:
                    experto = inicializar_experto()
                    resultado_contexto = experto.retrieve(consulta, k=5)
                    
                    if isinstance(resultado_contexto, list):
                        contexto_texto = "\n\n".join([item[0] for item in resultado_contexto])
                        citas_contexto = [f"Fuente: {item[1]} (relevancia: {item[2]:.2f})" for item in resultado_contexto]
                    else:
                        contexto_texto = str(resultado_contexto)
                    
                    if contexto_texto and contexto_texto != "NO ENCONTRADO EN EL CONTEXTO DISPONIBLE":
                        contexto_enriquecido = f"\n\nCONTEXTO RELEVANTE DE LA BASE DE CONOCIMIENTOS:\n{contexto_texto}\n"
                except Exception as e:
                    print(f"⚠️ Error construyendo contexto: {e}")
                    contexto_enriquecido = ""
            
            prompt = f"""Eres un especialista EXPERTO en especificaciones técnicas y elementos gráficos de la Junta de Planificación de Puerto Rico.

CONSULTA DEL USUARIO:
{consulta}{contexto_enriquecido}

METODOLOGÍA DE RESPUESTA:
1. ANALIZA la consulta desde múltiples perspectivas técnicas
2. EVALÚA las especificaciones técnicas requeridas
3. CONSIDERA factores como escalas, formatos, precisiones, sistemas de coordenadas
4. PROPORCIONA respuesta técnica detallada y práctica

ESTRUCTURA DE RESPUESTA (4-6 PÁRRAFOS):

**PÁRRAFO 1 - ANÁLISIS TÉCNICO:**
Evaluación técnica de la consulta, identificando tipo de documento/proyecto, escalas apropiadas, estándares aplicables.

**PÁRRAFO 2 - ESPECIFICACIONES EXACTAS:**
Detalles técnicos específicos: formatos, escalas, precisiones, sistemas de coordenadas, software requerido.

**PÁRRAFO 3 - PROCEDIMIENTOS Y METODOLOGÍA:**
Pasos técnicos detallados, metodologías de levantamiento, estándares de calidad, control de precisión.

**PÁRRAFO 4 - ELEMENTOS OBLIGATORIOS:**
Bloques de atributos, información requerida, elementos gráficos, simbologías, leyendas.

**PÁRRAFO 5 - CONSIDERACIONES ESPECIALES:**
Coordinación con otros profesionales, software específico, formatos de entrega, cumplimiento normativo.

**PÁRRAFO 6 - RECOMENDACIONES PRÁCTICAS:**
Mejores prácticas, optimización de procesos, prevención de errores comunes, eficiencia técnica.

CONTEXTO ESPECIALIZADO:
- Escalas: 1:1000-1:2000 localización, 1:200-1:500 conjunto, 1:100-1:200 arquitectónico, 1:20-1:50 detalles
- Sistemas: Estado Plano PR (EPSG:3991), NAD83, NAVD88
- Precisiones: ±1-5cm construcción, ±10cm planificación
- Formatos: ANSI D (24"×36"), mínimo 11"×17"
- Software: AutoCAD, estándares DWG, PDF vectorial

Genera una respuesta técnica completa, analítica y práctica."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": "Eres el especialista técnico-gráfico más experimentado de Puerto Rico. Proporciona respuestas técnicas detalladas, específicas y prácticas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            respuesta_ia = response.choices[0].message.content.strip()
            respuesta_limpia = self._limpiar_formato_conversacional(respuesta_ia)
            
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.92,
                respuesta=respuesta_limpia,
                referencias=[
                    "Tomo 3 - Especificaciones Técnicas y Elementos Gráficos",
                    "Estándares Profesionales de Agrimensura", 
                    "Reglamento Conjunto JP-RP-41"
                ]
            )
            
        except Exception as e:
            print(f"⚠️ Error en IA técnico-gráfica: {e}")
            return self._respuesta_fallback_tecnico()
    
    def _limpiar_formato_conversacional(self, texto: str) -> str:
        """Limpia formato conversacional para respuesta más natural"""
        texto = re.sub(r'\*\*PÁRRAFO \d+ - [^*]+\*\*\s*', '', texto)
        texto = re.sub(r'PÁRRAFO \d+ - [^:]+:\s*', '', texto)
        texto = re.sub(r'\*\*(ANÁLISIS|ESPECIFICACIONES|PROCEDIMIENTOS|ELEMENTOS|CONSIDERACIONES|RECOMENDACIONES)[^*]+\*\*\s*', '', texto)
        texto = re.sub(r'^\s*-\s*', '• ', texto, flags=re.MULTILINE)
        texto = re.sub(r'\n\s*\n\s*\n', '\n\n', texto)
        return texto.strip()
    
    def _respuesta_fallback_tecnico(self) -> ResultadoEspecialista:
        """Respuesta fallback cuando OpenAI no está disponible"""
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Especificaciones técnicas y elementos gráficos:

**Análisis de escalas y formatos:**
Para documentación técnica profesional, las escalas deben seleccionarse según el propósito: localización general 1:1000-1:2000, plantas de conjunto 1:200-1:500, plantas arquitectónicas 1:100-1:200, y detalles constructivos 1:20-1:50. Los formatos mínimos son 11"×17", preferiblemente ANSI D (24"×36") para proyectos complejos.

**Sistemas de coordenadas y precisiones:**
Utilizar Estado Plano Puerto Rico (EPSG:3991) con datum NAD83 y elevaciones NAVD88. Las precisiones requeridas son ±1-5cm para construcción y ±10cm para planificación general. Los levantamientos deben usar GPS/GNSS RTK para control primario y estación total para detalles.

**Elementos gráficos obligatorios:**
Incluir bloques de atributos con información predial, coordenadas de estaciones de control, curvas de nivel cada 1-2m en zona urbana, representación de servicios públicos, y leyenda completa. Los textos deben tener altura mínima 2.5mm en escala final.

**Procedimientos de calidad:**
Verificar cierre de poligonales (error angular ±20"√n, lineal 1:10,000), usar mínimo 3 estaciones de control por proyecto, y documentar todas las medidas en libretas de campo con cálculos verificables.""",
            referencias=[
                "Tomo 3 - Especificaciones Técnicas y Elementos Gráficos"
            ]
        )
    
    def _escalas_detalladas(self) -> str:
        return """**ANÁLISIS DE ESCALAS Y ESPECIFICACIONES TÉCNICAS:**

**📐 ESCALAS POR TIPO DE DOCUMENTO:**

**🏠 PROYECTOS RESIDENCIALES:**
- Localización general: 1:1,000 (muestra contexto urbano, vías, servicios)
- Plano de conjunto: 1:200 o 1:500 (edificaciones, estacionamientos, áreas verdes)
- Plantas arquitectónicas: 1:100 (distribución interior, cotas, elementos fijos)
- Elevaciones y cortes: 1:100 o 1:200 (alturas, materiales, niveles)
- Detalles constructivos: 1:20 o 1:50 (conexiones, materiales, acabados)

**🏢 PROYECTOS COMERCIALES/INDUSTRIALES:**
- Localización: 1:2,000 o 1:5,000 (impacto regional, accesos principales)
- Conjunto: 1:500 o 1:1,000 (circulaciones vehiculares, carga/descarga)
- Plantas: 1:100 o 1:200 (espacios funcionales, equipos, servicios)
- Detalles: 1:10 a 1:50 (elementos especializados, instalaciones)

**🛣️ INFRAESTRUCTURA:**
- Regional: 1:10,000 o mayor (corredores, impacto territorial)
- Local: 1:1,000 a 1:2,000 (intersecciones, drenajes, servicios)
- Constructivo: 1:100 a 1:500 (pavimentos, estructuras, detalles)

**📋 CRITERIOS DE SELECCIÓN:**
- **Legibilidad:** Textos mínimo 2.5mm altura final
- **Información:** Balance entre detalle y claridad general
- **Propósito:** Construcción vs. planificación vs. presentación
- **Formato:** Optimizar uso del papel, evitar escalas irregulares

**⚙️ ESPECIFICACIONES TÉCNICAS:**
- **Grosor líneas:** 0.18mm a 0.70mm según jerarquía
- **Tipografía:** Arial o similar, altura mínima 2.5mm
- **Acotaciones:** Precisión al centímetro, sistema métrico
- **Coordenadas:** Estado Plano PR, NAD83/NAVD88"""

    def _bloques_detallados(self) -> str:
        return """**ANÁLISIS DE BLOQUES DE ATRIBUTOS Y ELEMENTOS GRÁFICOS:**

**🔧 BLOQUES DE ATRIBUTOS OBLIGATORIOS:**

**🎯 ESTACIONES DE CONTROL:**
- **EstCont_Elev:** Elevación ortométrica (NAVD88)
- **EstCont_Desc:** Descripción física (Disco Bronce, Clavo PK, Varilla, Mojón)
- **EstCont_ID:** Identificador único alfanumérico
- **Precisión:** ±1cm horizontal, ±2cm vertical
- **Ubicación:** Coordenadas Estado Plano PR

**📐 INFORMACIÓN PREDIAL:**
- **Lote_Area:** Área en metros cuadrados (precisión 0.01m²)
- **Lote_Perimetro:** Perímetro total en metros lineales
- **Lote_ID:** Identificación catastral oficial
- **Zonificacion:** Distrito según Reglamento vigente
- **Servidumbres:** Identificación y dimensiones

**🏗️ ELEMENTOS CONSTRUCTIVOS:**
- **Edificio_Uso:** Clasificación según código de construcción
- **Edificio_Altura:** Altura total y por niveles
- **Edificio_Area:** Área construida por nivel
- **Retiros:** Distancias a linderos (frontal, lateral, posterior)

**🌊 ELEMENTOS AMBIENTALES:**
- **Curvas_Nivel:** Intervalo según escala (1m, 2m, 5m)
- **Drenaje_Tipo:** Natural/artificial, clasificación
- **Vegetacion_ID:** Especies protegidas, diámetros
- **Humedal_Delim:** Delimitación oficial verificada

**💻 ESPECIFICACIONES CAD:**
- **Formato:** Bloques dinámicos con atributos variables
- **Layers:** Organización por disciplina (A-Arquitectura, C-Civil, etc.)
- **Versión:** AutoCAD 2018 o posterior, formato DWG
- **Escalas:** Bloques escalables automáticamente
- **Inserción:** Puntos de referencia específicos por tipo"""

    def _topografia_detallada(self) -> str:
        return """**ANÁLISIS DE LEVANTAMIENTOS TOPOGRÁFICOS:**

**📍 SISTEMAS DE COORDENADAS:**
- **Horizontal:** Estado Plano Puerto Rico (EPSG:3991)
- **Vertical:** NAVD88 (North American Vertical Datum)
- **Proyección:** Lambert Conformal Conic
- **Unidades:** Metros, sistema métrico decimal

**🎯 PRECISIONES REQUERIDAS:**
- **Linderos:** ±5cm (construcción), ±10cm (planificación)
- **Elevaciones:** ±2cm (áreas críticas), ±5cm (general)
- **Estructuras:** ±1cm (elementos existentes)
- **Servicios:** ±10cm horizontal, ±5cm vertical

**📐 METODOLOGÍAS DE LEVANTAMIENTO:**
- **GPS/GNSS:** RTK para control primario, precisión centimétrica
- **Estación Total:** Detalles constructivos, poligonales cerradas
- **Escáner Láser:** Estructuras complejas, nubes de puntos
- **Drones:** Fotogrametría, áreas extensas, modelos 3D

**📋 ELEMENTOS A REPRESENTAR:**
- **Topografía:** Curvas nivel cada 1m (urbano), 2-5m (rural)
- **Construcciones:** Edificios, muros, pavimentos, estructuras
- **Servicios:** Líneas aéreas/subterráneas, pozos, tanques
- **Vegetación:** Árboles significativos (>15cm diámetro)
- **Drenaje:** Quebradas, cunetas, alcantarillas, sumideros
- **Vialidad:** Centros línea, bordillos, señalización

**⚙️ CONTROL DE CALIDAD:**
- **Poligonales:** Cierre angular ±20" √n, lineal 1:10,000
- **Referencias:** Mínimo 3 estaciones control por proyecto
- **Verificación:** Medidas independientes elementos críticos
- **Documentación:** Libretas campo, cálculos, certificaciones"""

    def _cartulado_especificaciones(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Especificaciones técnicas de cartulado:

**📊 ORGANIZACIÓN DE INFORMACIÓN:**
- **Cuadro título:** Identificación proyecto, responsables, fechas
- **Leyenda:** Símbolos normalizados, explicaciones claras
- **Norte:** Magnético y verdadero, declinación indicada
- **Escala:** Gráfica y numérica, verificable
- **Coordenadas:** Grid visible, referencias sistema usado""",
            referencias=[
                "Tomo 3 - Sección 2.2: Escalas y Formatos"
            ]
        )

    def _especificaciones_generales(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.80,
            respuesta="""Especificaciones técnicas generales para documentos:

**Formatos de archivo:**
- CAD: DWG/DXF versión 2018 o posterior
- PDF: Resolución mínima 300 DPI
- Imágenes: TIFF o PNG sin compresión

**Estándares gráficos:**
- Grosor de líneas: 0.18mm a 0.70mm
- Textos: Arial o similar, mínimo 2.5mm
- Acotaciones: Precisión al centímetro
- Colores: RGB o CMYK según uso

**Elementos obligatorios:**
- Cuadro de información
- Escala gráfica y numérica
- Norte magnético
- Fecha y revisiones""",
            referencias=[
                "Tomo 3 - Capítulo 2: Especificaciones Técnicas"
            ]
        )

class EspecialistaEdificabilidad(MiniEspecialistaBase):
    """TOMO 4-6: Parámetros de Edificabilidad"""
    
    def __init__(self):
        super().__init__("Edificabilidad", 4)
        self.palabras_clave = [
            # Parámetros básicos de edificabilidad
            "densidad", "edificabilidad", "far", "cobertura", "altura", "alturas",
            "retiros", "retiro", "estacionamiento", "estacionamientos", "lote", "lotes",
            "construccion", "construcción", "vivienda", "viviendas", "edificio", "edificios",
            "área", "area", "areas", "áreas", "nivel", "niveles", "pisos", "metros",
            # Términos técnicos específicos
            "factor", "coeficiente", "parametros", "parámetros", "regulaciones", "normas",
            "maximo", "máximo", "minimo", "mínimo", "permitido", "requerido", "obligatorio",
            # Zonificación y usos
            "zona", "zonas", "distrito", "residencial", "comercial", "industrial", "mixto",
            "r-1", "r-2", "r-3", "r-4", "r-5", "c-1", "c-2", "i-1", "i-2",
            # Cálculos y medidas
            "calcular", "calculo", "cálculo", "formula", "fórmula", "ecuacion", "ecuación",
            "como", "cuanto", "cuánto", "cual", "cuál", "donde", "dónde",
            # Tipos de construcción
            "casa", "casas", "apartamento", "apartamentos", "condominio", "condominios",
            "bifamiliar", "multifamiliar", "unifamiliar", "duplex", "triplex",
            # Servicios y facilidades
            "servicios", "acceso", "accesos", "entrada", "entradas", "vialidad", "calle",
            "agua", "electricidad", "alcantarillado", "telefono", "teléfono", "internet"
        ]
        self.patrones_consulta = [
            r"factor\s+de\s+edificabilidad",
            r"densidad\s+m[áa]xima",
            r"cobertura\s+del\s+lote",
            r"altura\s+m[áa]xima",
            # Nuevos patrones para mejor detección
            r"c[oó]mo\s+calcular\s+(far|densidad|cobertura|altura)",
            r"cu[áa]l\s+es\s+(la\s+)?(altura|densidad|far)\s+(m[áa]xima?|permitida?)",
            r"qu[eé]\s+(altura|densidad|far|retiros?)\s+(necesito|requiero|debo)",
            r"par[áa]metros\s+de\s+(edificabilidad|construcción|zonificación)",
            r"regulaciones\s+(de\s+)?(altura|densidad|retiros|estacionamiento)",
            r"normas\s+(para|de)\s+(construir|edificar|desarrollo)",
            r"requisitos\s+(de\s+)?(edificabilidad|construcción|zonificación)",
            r"c[oó]mo\s+(determinar|calcular|obtener)\s+(far|densidad|altura)"
        ]
    
    def responder(self, consulta: str, contexto: dict = None) -> str:
        """Método de compatibilidad que llama a procesar_consulta"""
        resultado = self.procesar_consulta(consulta)
        return resultado.respuesta
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Procesa consultas sobre edificabilidad usando IA + contexto enriquecido"""
        
        # Intentar usar OpenAI para respuesta dinámica elaborada
        try:
            client, model_to_use = crear_cliente_openai()
            
            # Construir contexto enriquecido
            contexto_enriquecido = ""
            citas_contexto = []
            if EXPERTO_DISPONIBLE:
                try:
                    experto = inicializar_experto()
                    resultado_contexto = experto.retrieve(consulta, k=5)
                    
                    if isinstance(resultado_contexto, list):
                        contexto_texto = "\n\n".join([item[0] for item in resultado_contexto])
                        citas_contexto = [f"Fuente: {item[1]} (relevancia: {item[2]:.2f})" for item in resultado_contexto]
                    else:
                        contexto_texto = str(resultado_contexto)
                    
                    if contexto_texto and contexto_texto != "NO ENCONTRADO EN EL CONTEXTO DISPONIBLE":
                        contexto_enriquecido = f"\n\nCONTEXTO RELEVANTE DE LA BASE DE CONOCIMIENTOS:\n{contexto_texto}\n"
                except Exception as e:
                    print(f"⚠️ Error construyendo contexto: {e}")
                    contexto_enriquecido = ""
            
            prompt = f"""Eres un especialista EXPERTO en parámetros de edificabilidad de la Junta de Planificación de Puerto Rico.

CONSULTA DEL USUARIO:
{consulta}{contexto_enriquecido}

METODOLOGÍA DE RESPUESTA:
1. ANALIZA la consulta identificando parámetros específicos de edificabilidad
2. EVALÚA las regulaciones aplicables según tipo de zona y proyecto
3. CONSIDERA factores como FAR, densidad, altura, retiros, cobertura, estacionamiento
4. PROPORCIONA cálculos exactos y ejemplos prácticos

ESTRUCTURA DE RESPUESTA (4-6 PÁRRAFOS):

**PÁRRAFO 1 - ANÁLISIS DE PARÁMETROS:**
Identificación de parámetros de edificabilidad aplicables, evaluación del tipo de zona o proyecto, contexto regulatorio específico.

**PÁRRAFO 2 - REGULACIONES ESPECÍFICAS:**
Parámetros exactos según zonificación: FAR permitido, densidad máxima, altura límite, porcentajes de cobertura, retiros mínimos.

**PÁRRAFO 3 - METODOLOGÍA DE CÁLCULO:**
Fórmulas específicas, procedimientos de cálculo paso a paso, ejemplos numéricos con casos reales.

**PÁRRAFO 4 - APLICACIÓN PRÁCTICA:**
Casos de estudio específicos, ejemplos de proyectos típicos, optimización del diseño según parámetros.

**PÁRRAFO 5 - CONSIDERACIONES ESPECIALES:**
Excepciones reglamentarias, incentivos por buenas prácticas, coordinación con otros requisitos.

**PÁRRAFO 6 - CUMPLIMIENTO Y VERIFICACIÓN:**
Procedimientos de verificación, documentación requerida, coordinación con otras agencias.

CONTEXTO ESPECIALIZADO:
- FAR: 0.25-6.0 según distrito (residencial 0.25-3.0, comercial 0.5-6.0)
- Densidades: R-1 (2-4 viv/acre), R-2 (4-8), R-3 (8-15), R-4 (15-30), R-5 (30+)
- Alturas: Residencial 35-150 pies, comercial hasta 300 pies según zona
- Retiros: Frontal 10-25 pies, lateral 5-15 pies, posterior 15-25 pies
- Cobertura: 40-70% según distrito
- Estacionamiento: 1-3 espacios por unidad según tipo

Genera una respuesta técnica completa, con cálculos específicos y ejemplos prácticos."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": "Eres el especialista en edificabilidad más experimentado de Puerto Rico. Proporciona respuestas técnicas precisas con cálculos específicos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            respuesta_ia = response.choices[0].message.content.strip()
            respuesta_limpia = self._limpiar_formato_conversacional(respuesta_ia)
            
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.92,
                respuesta=respuesta_limpia,
                referencias=[
                    "Tomo 4-6 - Parámetros de Edificabilidad",
                    "Reglamento de Zonificación JP", 
                    "Estándares de Desarrollo Urbano"
                ]
            )
            
        except Exception as e:
            print(f"⚠️ Error en IA edificabilidad: {e}")
            return self._respuesta_fallback_edificabilidad()
    
    def _limpiar_formato_conversacional(self, texto: str) -> str:
        """Limpia formato conversacional para respuesta más natural"""
        texto = re.sub(r'\*\*PÁRRAFO \d+ - [^*]+\*\*\s*', '', texto)
        texto = re.sub(r'PÁRRAFO \d+ - [^:]+:\s*', '', texto)
        texto = re.sub(r'\*\*(ANÁLISIS|REGULACIONES|METODOLOGÍA|APLICACIÓN|CONSIDERACIONES|CUMPLIMIENTO)[^*]+\*\*\s*', '', texto)
        texto = re.sub(r'^\s*-\s*', '• ', texto, flags=re.MULTILINE)
        texto = re.sub(r'\n\s*\n\s*\n', '\n\n', texto)
        return texto.strip()
    
    def _respuesta_fallback_edificabilidad(self) -> ResultadoEspecialista:
        """Respuesta fallback cuando OpenAI no está disponible"""
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Parámetros de edificabilidad y cálculos de zonificación:

**Análisis de parámetros básicos:**
Los parámetros de edificabilidad incluyen Factor de Área de Piso (FAR), densidad residencial, altura máxima, retiros mínimos, cobertura del lote y estacionamientos requeridos. Cada distrito de zonificación tiene límites específicos que controlan la intensidad y forma del desarrollo urbano.

**Cálculo del Factor de Área de Piso (FAR):**
FAR = Área total de todos los pisos ÷ Área del lote. Para zona R-3 típica: FAR máximo 1.5, significa que en un lote de 1,000 m² se pueden construir hasta 1,500 m² de área de piso distribuidos en uno o varios niveles. Para zona comercial C-2: FAR hasta 4.0.

**Densidad y altura por distrito:**
Zona R-1: 2-4 viviendas/acre, altura máxima 35 pies (2 niveles). Zona R-4: 15-30 viviendas/acre, altura hasta 150 pies (múltiples niveles). Zona C-2: altura hasta 150-300 pies según localización específica.

**Retiros y cobertura obligatorios:**
Retiros mínimos típicos: frontal 15-25 pies, laterales 5-15 pies, posterior 15-25 pies. Cobertura máxima del lote: 40-50% zonas residenciales, hasta 70% zonas comerciales intensivas. Estos parámetros aseguran ventilación, iluminación y espacios abiertos.""",
            referencias=[
                "Tomo 4-6 - Parámetros de Edificabilidad"
            ]
        )

    def _calcular_densidad(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.90,
            respuesta="""La densidad se mide en viviendas por acre (viv/acre):

**Densidades por zona:**
• R-1: 2-4 viv/acre (lotes grandes)
• R-2: 4-8 viv/acre (lotes medianos)  
• R-3: 8-15 viv/acre (multifamiliar bajo)
• R-4: 15-30 viv/acre (multifamiliar medio)
• R-5: 30+ viv/acre (multifamiliar alto)

**Cálculo:**
Densidad = (# viviendas ÷ área del lote en acres)

**Ejemplo:**
Lote de 2 acres con 10 viviendas = 5 viv/acre""",
            referencias=[
                "Tomo 4 - Sección 4.2: Densidades Residenciales"
            ]
        )

    def _factor_edificabilidad(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""El Factor de Área de Piso (FAR) controla la intensidad de construcción:

**FAR por distrito:**
• Residencial: 0.25 - 3.0
• Comercial: 0.5 - 6.0  
• Industrial: 0.3 - 2.0
• Mixto: Variable según componentes

**Cálculo:**
FAR = Área total de pisos ÷ Área del lote

**Ejemplo:**
• Lote: 1,000 m²
• FAR permitido: 2.0
• Construcción máxima: 2,000 m² de piso""",
            referencias=[
                "Tomo 5 - Tabla 5.3: Factores de Edificabilidad"
            ]
        )

    def _parametros_generales(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.75,
            respuesta="""Zona R-4 permite densidad 15-30 viv/acre, altura máxima 35-150 pies, cobertura 40-70% según distrito. FAR típico: 0.25-3.0. Retiros: frontal 20-25 pies, lateral 5-15 pies, posterior 15-20 pies.

⚠️ ADVERTENCIA: Verificar reglamento municipal específico.

✓ CHECKLIST: Densidad ✓ Altura ✓ Cobertura ✓ Retiros ✓ FAR

[Tomo 4-p.67] [Tomo 5-p.89]""",
            referencias=[
                "Tomo 4-6 - Parámetros de Edificabilidad"
            ]
        )

class EspecialistaZonificacion(MiniEspecialistaBase):
    """TOMO 5-6: Distritos de Zonificación Residencial y Comercial"""
    
    def __init__(self):
        super().__init__("Zonificación", 5)  # Cambiar a tomo 5 que tiene más info residencial
        self.palabras_clave = [
            "zonificacion", "zonificación", "zona", "distrito", "uso", "comercial", "residencial", 
            "industrial", "agricola", "clasificacion", "calificacion", "usos",
            "retiros", "retiro", "minimos", "mínimos", "frontal", "lateral", "posterior",
            "altura", "densidad", "cobertura", "far", "estacionamiento", "lote"
        ]
        self.patrones_consulta = [
            r"zona\s+[rcai]-?\d+",
            r"retiros?\s+m[íi]nimos?",
            r"retiros?\s+para\s+zona",
            r"zona\s+r-\d+",
            r"zona\s+c-\d+", 
            r"zona\s+i-\d+",
            r"uso\s+permitido",
            r"distrito\s+de",
            r"clasificaci[oó]n\s+de\s+suelo",
            r"zonificaci[oó]n",
            r"calificaci[oó]n",
            r"altura\s+m[áa]xima",
            r"densidad\s+m[áa]xima"
        ]
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Procesa consultas sobre zonificación usando IA + contexto enriquecido"""
        
        # Intentar usar OpenAI para respuesta dinámica
        try:
            client, model_to_use = crear_cliente_openai()
            
            # 🔥 NUEVA FUNCIONALIDAD: Construir contexto enriquecido
            contexto_enriquecido = ""
            citas_contexto = []
            if EXPERTO_DISPONIBLE:
                try:
                    experto = inicializar_experto()
                    resultado_contexto = experto.retrieve(consulta, k=5)
                    
                    # Manejar el resultado de retrieve que devuelve lista de tuplas (texto, origen, score)
                    if isinstance(resultado_contexto, list):
                        contexto_texto = "\n\n".join([item[0] for item in resultado_contexto])
                        citas_contexto = [f"Fuente: {item[1]} (relevancia: {item[2]:.2f})" for item in resultado_contexto]
                    else:
                        # Compatibilidad hacia atrás
                        contexto_texto = str(resultado_contexto)
                    
                    if contexto_texto and contexto_texto != "NO ENCONTRADO EN EL CONTEXTO DISPONIBLE":
                        contexto_enriquecido = f"\n\nCONTEXTO RELEVANTE DE LA BASE DE CONOCIMIENTOS:\n{contexto_texto}\n"
                    else:
                        contexto_enriquecido = ""
                except Exception as e:
                    print(f"⚠️ Error construyendo contexto: {e}")
                    contexto_enriquecido = ""
            
            prompt = f"""Eres un especialista EXPERTO en zonificación y distritos de calificación de Puerto Rico.

CONSULTA DEL USUARIO:
{consulta}{contexto_enriquecido}

METODOLOGÍA DE RESPUESTA:
1. ANALIZA la consulta desde múltiples ángulos de zonificación
2. PROPORCIONA contexto sobre distritos de calificación específicos
3. DETALLA usos permitidos, prohibidos y discrecionales
4. EXPLICA las regulaciones de zona aplicables (altura, densidad, retiros)
5. IDENTIFICA posibles conflictos o restricciones especiales
6. SUGIERE procedimientos necesarios para cambios de zona

INSTRUCCIONES ESPECÍFICAS:
- Si hay CONTEXTO RELEVANTE, úsalo para fundamentar tu respuesta
- Estructura la respuesta en párrafos sustanciales (mínimo 3-4 párrafos)
- Incluye códigos de zona específicos y sus implicaciones
- Menciona procedimientos para consultas de ubicación cuando aplicable
- Explica diferencias entre usos ministeriales y discrecionales
- Considera aspectos ambientales y de infraestructura
- FORMATO: Respuesta conversacional y analítica

CRITERIOS DE CALIDAD:
- Demuestra conocimiento profundo de la zonificación puertorriqueña
- Explica el impacto de las regulaciones en el desarrollo
- Considera excepciones y variaciones especiales
- Proporciona ejemplos prácticos de aplicación

RESPONDE COMO UN PLANIFICADOR SENIOR con análisis detallado."""

            # Sistema mejorado para respuestas elaboradas en zonificación
            system_prompt = """Eres un planificador urbano senior especializado en zonificación de Puerto Rico con 20+ años de experiencia.

ESTILO DE RESPUESTA:
- Analítico y técnico, pero accesible
- Explicas las implicaciones de cada zona y regulación
- Proporcionas respuestas completas de 4-6 párrafos sustanciales
- Contextualizas dentro del marco de desarrollo urbano

METODOLOGÍA:
1. Identifica la zona o distrito de calificación relevante
2. Explica los usos permitidos y las regulaciones aplicables
3. Analiza las implicaciones para el desarrollo propuesto
4. Identifica procedimientos necesarios y consideraciones especiales
5. Sugiere alternativas cuando la consulta presenta restricciones

CONOCIMIENTO ESPECIALIZADO:
- Dominas todos los distritos de calificación (R-1, R-2, R-3, C-1, C-2, I-1, etc.)
- Conoces regulaciones de altura, densidad, estacionamiento, retiros
- Entiendes procedimientos de consulta de ubicación y variaciones
- Comprendes aspectos ambientales y de infraestructura

Si no tienes información específica, proporciona análisis general basado en principios de zonificación y sugiere consultar "Tomos 5-9 del Reglamento Conjunto JP-RP-41" para detalles específicos.

Genera respuestas que demuestren expertise técnico y análisis profundo."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Más tokens para respuestas elaboradas
                temperature=0.4   # Más creatividad para análisis técnico
            )
            
            respuesta_ia = response.choices[0].message.content.strip()
            
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.95,
                respuesta=respuesta_ia,
                referencias=[
                    "Tomos 7-9 - Zonificación y Distritos",
                    "Análisis especializado con IA + contexto enriquecido"
                ],
                recomendaciones=[
                    "Verificar distrito específico en mapa de calificación",
                    "Consultar usos permitidos en el distrito aplicable"
                ]
            )
            
        except Exception as e:
            # Fallback a respuesta predefinida si OpenAI falla
            print(f"⚠️ Error en IA de zonificación: {e}")
            return self._usos_por_zona()

    def _usos_por_zona(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Clasificación de distritos y usos principales:

**Residencial (R):**
• R-1/R-2: Unifamiliar, densidad baja
• R-3: Bifamiliar, dúplex
• R-4/R-5: Multifamiliar, apartamentos

**Comercial (C):**
• C-1: Comercio vecinal (tiendas locales)
• C-2: Comercio general (centros, oficinas)
• C-3: Comercio intensivo (malls, hoteles)

**Industrial (I):**
• I-1: Industria ligera (almacenes)
• I-2: Industria pesada (manufactura)

**Otros:**
• A: Agrícola
• P: Preservación
• EU: Espacios abiertos urbanos""",
            referencias=[
                "Tomo 7-9 - Distritos de Zonificación"
            ]
        )

class EspecialistaAmbientalInfraestructura(MiniEspecialistaBase):
    """TOMO 10-11: Aspectos Ambientales e Infraestructura"""
    
    def __init__(self):
        super().__init__("Ambiental e Infraestructura", 10)
        self.palabras_clave = [
            "ambiental", "infraestructura", "agua", "alcantarillado",
            "energia", "telecomunicaciones", "impacto", "sostenibilidad",
            "evaluación", "evaluacion", "dia", "recurso", "natural",
            "conservación", "conservacion", "mar", "costa", "humedal"
        ]
        self.patrones_consulta = [
            r"impacto\s+ambiental",
            r"infraestructura\s+de",
            r"servicios\s+p[uú]blicos"
        ]
    
    def responder(self, consulta: str, contexto: dict = None) -> str:
        """Método de compatibilidad que llama a procesar_consulta"""
        resultado = self.procesar_consulta(consulta)
        return resultado.respuesta
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        return self._requisitos_ambientales()

    def _requisitos_ambientales(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.80,
            respuesta="""Requisitos ambientales e infraestructura:

**Evaluación ambiental requerida para:**
• Proyectos >20,000 m² construcción
• Desarrollos costeros
• Proyectos en zonas protegidas
• Industrias con emisiones

**Infraestructura básica:**
• Agua potable: PRASA o sistemas privados
• Alcantarillado: Conexión AAA obligatoria
• Energía: Conexión LUMA Energy
• Telecomunicaciones: Acceso garantizado

**Sostenibilidad:**
• Eficiencia energética requerida
• Manejo de aguas pluviales
• Preservación de vegetación nativa""",
            referencias=[
                "Tomo 10-11 - Aspectos Ambientales e Infraestructura"
            ]
        )

class EspecialistaHistorico(MiniEspecialistaBase):
    """TOMO 12: Conservación Histórica"""
    
    def __init__(self):
        super().__init__("Histórico", 12)
        self.palabras_clave = [
            # Palabras originales
            "historico", "conservacion", "patrimonio", "shpo", "ihp",
            "designacion", "listado", "arqueologico",
            # Palabras ampliadas para mejor detección
            "histórico", "conservación", "arqueológico", "edificio", "estructura",
            "remodelar", "permisos", "zonas", "protegidas", "arquitectónico",
            "arquitectonico", "solicitar", "designación", "cultural", "antiguo",
            "restaurar", "restauración", "restauracion", "colonial", "tradicional",
            # Nuevas palabras específicas para la consulta de sitios históricos
            "sitios", "sitio", "regulaciones", "reglamento", "normativas",
            "preservacion", "preservación", "monumento", "monumentos", "histórica",
            "historica", "patrimónial", "patrimonial", "lugares", "lugar",
            "protección", "proteccion", "restricciones", "requisitos", "registro",
            "catalogo", "catálogo", "nacional", "estatal", "municipal", "local"
        ]
        self.patrones_consulta = [
            r"sitio\s+hist[oó]rico",
            r"sitios\s+hist[oó]ricos",
            r"regulaciones?\s+para\s+sitios?\s+hist[oó]ricos?",
            r"conservaci[oó]n\s+hist[oó]rica",
            r"patrimonio\s+cultural",
            r"qu[eé]\s+regulaciones?\s+para\s+sitios?",
            r"reglamento\s+sitios?\s+hist[oó]ricos?",
            r"preservaci[oó]n\s+hist[oó]rica"
        ]
    
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Procesa consultas sobre conservación histórica y patrimonial con análisis IA"""
        
        try:
            # Configuración de cliente OpenAI
            client, model_to_use = crear_cliente_openai()
            
            # Buscar contexto específico en documentación
            try:
                from experto_planificacion import ExpertoPlanificacion
                experto = ExpertoPlanificacion()
                # Buscar información específica sobre sitios históricos
                contexto_query = f"sitios históricos conservación patrimonial regulaciones {consulta}"
                contexto_texto = experto.buscar_informacion(contexto_query)
                
                if contexto_texto and contexto_texto != "NO ENCONTRADO EN EL CONTEXTO DISPONIBLE":
                    contexto_enriquecido = f"\n\nCONTEXTO ESPECÍFICO DE LA DOCUMENTACIÓN:\n{contexto_texto}"
                else:
                    contexto_enriquecido = ""
                    
            except Exception as e:
                print(f"⚠️ Error construyendo contexto: {e}")
                contexto_enriquecido = ""
            
            prompt = f"""Eres un especialista EXPERTO en conservación histórica y patrimonial de Puerto Rico, con profundo conocimiento de SHPO, ICP y regulaciones culturales.

CONSULTA DEL USUARIO:
{consulta}{contexto_enriquecido}

METODOLOGÍA DE RESPUESTA:
1. ANALIZA la consulta desde múltiples perspectivas de conservación patrimonial
2. PROPORCIONA marco legal específico (federal, estatal y municipal)
3. DETALLA procedimientos y requisitos paso a paso
4. EXPLICA criterios de evaluación histórica y cultural
5. IDENTIFICA stakeholders y sus roles específicos
6. SUGIERE estrategias de preservación y próximos pasos

INSTRUCCIONES ESPECÍFICAS:
- Si hay CONTEXTO RELEVANTE, úsalo para fundamentar tu respuesta
- Estructura la respuesta en párrafos sustanciales (mínimo 4-5 párrafos)
- Incluye criterios NRHP, proceso SHPO, y requisitos ICP cuando aplicable
- Menciona incentivos fiscales, grants, y programas disponibles
- Proporciona ejemplos de casos exitosos cuando sea útil
- Anticipa complicaciones comunes en proyectos históricos
- FORMATO: Respuesta conversacional y natural (sin símbolos técnicos)

CRITERIOS DE CALIDAD:
- Demuestra expertise en preservación histórica
- Explica el balance entre conservación y desarrollo
- Considera aspectos culturales y comunitarios
- Proporciona información de contacto específica

RESPONDE COMO UN CONSULTOR EXPERTO en patrimonio cultural que analiza cada aspecto histórico y regulatorio."""

            # Sistema mejorado para respuestas elaboradas
            system_prompt = """Eres un especialista senior en conservación histórica y patrimonial de Puerto Rico con 15+ años de experiencia en SHPO, ICP y proyectos de preservación.

ESTILO DE RESPUESTA:
- Analítico y reflexivo, demostrando conocimiento profundo del patrimonio cultural
- Conversacional pero profesional
- Explicas el contexto histórico y la importancia de la preservación
- Proporcionas respuestas completas de 4-6 párrafos sustanciales

METODOLOGÍA:
1. Contextualiza la consulta dentro del marco cultural e histórico puertorriqueño
2. Explica los procedimientos de preservación con justificaciones patrimoniales
3. Identifica consideraciones importantes y posibles conflictos regulatorios
4. Sugiere estrategias prácticas de conservación y próximos pasos específicos
5. Anticipa dudas comunes y proporciona clarificaciones especializadas

Si no tienes información suficiente en el contexto, indica claramente qué información adicional se necesita y sugiere fuentes específicas como "Tomo 12 - Conservación Histórica" o contactos en SHPO/ICP.

Genera respuestas que demuestren expertise y análisis profundo en preservación patrimonial."""

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Más tokens para respuestas elaboradas
                temperature=0.4   # Más creatividad para análisis profundo
            )
            
            respuesta_ia = response.choices[0].message.content.strip()
            
            # Limpiar formato técnico para conversación natural
            respuesta_limpia = self._limpiar_formato_conversacional(respuesta_ia)
            
            return ResultadoEspecialista(
                especialista=self.nombre,
                confianza=0.95,
                respuesta=respuesta_limpia,
                referencias=[
                    "Tomo 12 - Conservación Histórica y Cultural",
                    "Análisis especializado con IA"
                ],
                recomendaciones=[
                    "Verificar criterios NRHP específicos para tu proyecto",
                    "Consultar con SHPO antes de iniciar cualquier trabajo"
                ]
            )
            
        except Exception as e:
            # Fallback a respuesta predefinida si OpenAI falla
            return self._conservacion_historica_fallback()

    def _limpiar_formato_conversacional(self, texto: str) -> str:
        """Convierte formato técnico a conversación natural"""
        
        # Remover símbolos de markdown y formato técnico
        texto = re.sub(r'#{1,6}\s*', '', texto)  # Remover # de títulos
        texto = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', texto)  # Remover asteriscos
        texto = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', texto)  # Remover guiones bajos
        texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)  # Remover links
        texto = re.sub(r'`([^`]+)`', r'\1', texto)  # Remover código inline
        texto = re.sub(r'^[-•]\s*', '', texto, flags=re.MULTILINE)  # Remover viñetas
        
        # Limpiar espacios múltiples y saltos de línea excesivos
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        texto = re.sub(r' {2,}', ' ', texto)
        
        return texto.strip()

    def _conservacion_historica_fallback(self) -> ResultadoEspecialista:
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Conservación histórica y patrimonial:

**Designación de sitios históricos:**
• Evaluación por SHPO (State Historic Preservation Office)
• Criterios: Significancia histórica, arquitectónica o cultural
• Proceso: Nominación → Evaluación → Listado

**Restricciones en sitios históricos:**
• Rehabilitación debe preservar carácter
• Materiales compatibles con época
• Cambios requieren aprobación SHPO
• Demolición extremadamente limitada

**Incentivos disponibles:**
• Créditos contributivos federales (20%)
• Exenciones contributivas locales
• Programas de grants especializados

**Entidades clave:**
• SHPO - Estado
• ICP - Instituto de Cultura  
• Municipios (ordenanzas locales)""",
            referencias=[
                "Tomo 12 - Conservación Histórica y Cultural"
            ]
        )

    def _conservacion_historica_fallback(self) -> ResultadoEspecialista:
        """Respuesta fallback cuando OpenAI no está disponible"""
        return ResultadoEspecialista(
            especialista=self.nombre,
            confianza=0.85,
            respuesta="""Conservación histórica y patrimonial:

**Designación de sitios históricos:**
• Evaluación por SHPO (State Historic Preservation Office)
• Criterios: Significancia histórica, arquitectónica o cultural
• Proceso: Nominación → Evaluación → Listado

**Restricciones en sitios históricos:**
• Rehabilitación debe preservar carácter
• Materiales compatibles con época
• Cambios requieren aprobación SHPO
• Demolición extremadamente limitada

**Incentivos disponibles:**
• Créditos contributivos federales (20%)
• Exenciones contributivas locales
• Programas de grants especializados

**Entidades clave:**
• SHPO - Estado
• ICP - Instituto de Cultura  
• Municipios (ordenanzas locales)""",
            referencias=[
                "Tomo 12 - Conservación Histórica y Cultural"
            ]
        )

class SistemaEspecialistasExpandido:
    """Sistema coordinador de todos los mini-especialistas"""
    
    def __init__(self):
        self.especialistas = [
            EspecialistaProcedimientos(),
            EspecialistaTecnicoGrafico(),
            EspecialistaEdificabilidad(),
            EspecialistaZonificacion(),
            EspecialistaAmbientalInfraestructura(),
            EspecialistaHistorico()
        ]
        
    def procesar_consulta_especializada(self, consulta: str, tipo_especialista: str) -> dict:
        """Procesa una consulta con un especialista específico"""
        
        # Mapeo de tipos a clases
        tipos_especialistas = {
            'procedimientos': EspecialistaProcedimientos,
            'tecnico_grafico': EspecialistaTecnicoGrafico,
            'edificabilidad': EspecialistaEdificabilidad,
            'zonificacion': EspecialistaZonificacion,
            'ambiental_infraestructura': EspecialistaAmbientalInfraestructura,
            'historico': EspecialistaHistorico
        }
        
        if tipo_especialista not in tipos_especialistas:
            return {
                'respuesta': f"Especialista '{tipo_especialista}' no encontrado.",
                'especialista_usado': 'error',
                'confianza': 0.0
            }
        
        # Crear instancia del especialista
        especialista_class = tipos_especialistas[tipo_especialista]
        especialista = especialista_class()
        
        # Procesar consulta
        try:
            resultado = especialista.procesar_consulta(consulta)
            return {
                'respuesta': resultado.respuesta,
                'especialista_usado': resultado.especialista,
                'confianza': resultado.confianza,
                'referencias': resultado.referencias,
                'recomendaciones': resultado.recomendaciones or []
            }
        except Exception as e:
            return {
                'respuesta': f"Error procesando consulta con {tipo_especialista}: {str(e)}",
                'especialista_usado': tipo_especialista,
                'confianza': 0.0
            }
        
    def procesar_consulta(self, consulta: str) -> ResultadoEspecialista:
        """Determina el mejor especialista y procesa la consulta"""
        
        # Evaluar todos los especialistas
        candidatos = []
        for especialista in self.especialistas:
            confianza = especialista.puede_manejar(consulta)
            if confianza > 0.2:  # Umbral reducido de 0.3 a 0.2 para ser más sensible
                candidatos.append((especialista, confianza))
        
        if not candidatos:
            return self._respuesta_general(consulta)
        
        # Seleccionar el mejor candidato
        mejor_especialista, mejor_confianza = max(candidatos, key=lambda x: x[1])
        
        # Procesar con el especialista seleccionado
        if hasattr(mejor_especialista, 'procesar_consulta'):
            resultado = mejor_especialista.procesar_consulta(consulta)
            resultado.confianza = mejor_confianza
            return resultado
        
        return self._respuesta_general(consulta)
    
    def _respuesta_general(self, consulta: str) -> ResultadoEspecialista:
        """Respuesta cuando ningún especialista es claramente aplicable"""
        return ResultadoEspecialista(
            especialista="Sistema General",
            confianza=0.5,
            respuesta="""Su consulta abarca múltiples áreas del reglamento. Para una respuesta más específica, indique el aspecto particular:

• **Procedimientos:** Trámites y permisos
• **Zonificación:** Distritos y usos permitidos  
• **Construcción:** Parámetros de edificabilidad
• **Técnico:** Especificaciones de planos
• **Ambiental:** Impactos y sostenibilidad
• **Histórico:** Conservación patrimonial""",
            referencias=["Consulta general - Sistema JP_IA"],
            recomendaciones=[
                "Especificar el tipo de proyecto",
                "Indicar ubicación o distrito",
                "Mencionar aspecto regulatorio específico"
            ]
        )

# Funciones de conveniencia para importación
def crear_sistema_especialistas():
    """Crear una instancia del sistema de especialistas"""
    return SistemaEspecialistasExpandido()

# Para compatibilidad con sistema anterior
if __name__ == "__main__":
    sistema = SistemaEspecialistasExpandido()
    print("✅ Sistema de Mini-Especialistas Expandido inicializado")
    print(f"📊 Especialistas disponibles: {len(sistema.especialistas)}")
