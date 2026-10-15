"""
==============================================================================
🧠 Escribe si puedes — Backend API (Python Flask)
Núcleo de Programación Funcional: Detección de Gibberish, Pomodoro, 
Sugerencias Temáticas y Corrección de Estilo Asistida por IA Local (Qwen 2.5 3B)
Estudiantes: Diego Guadalupe Torres Bravo y Christopher Emmanuel Jimenez Cuevas
==============================================================================
"""

import json
import os
import random
import urllib.request
import re
from typing import NamedTuple
from flask import Flask, request, jsonify, send_from_directory

# Inicialización de la aplicación Flask sirviendo la interfaz web desde la carpeta 'Frontend'
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Frontend'))
if not os.path.exists(FRONTEND_DIR):
    # Fallback si se ejecuta en una estructura alternativa
    FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# ==============================================================================
# 🧩 MODELOS INMUTABLES Y CONFIGURACIONES (NamedTuple & frozenset)
# ==============================================================================

class NivelConfig(NamedTuple):
    id: int
    nombre: str
    descripcion: str
    tolerancia_inactividad_seg: float  # Segundos antes de borrar el texto
    meta_palabras: int                 # Meta para superar el nivel
    tiempo_pomodoro_min: int           # Duración del bloque de concentración
    tiempo_descanso_min: int           # Duración de la pausa segura


class TemaSugerido(NamedTuple):
    nivel_id: int
    texto: str
    categoria: str


class SugerenciaEstilo(NamedTuple):
    original: str
    sugerencia: str
    motivo: str


# Conjunto inmutable de vocales en español con lookup O(1)
VOCALES_VALIDAS: frozenset[str] = frozenset({'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú', 'ü'})

# Configuración inmutable de los 3 niveles del juego
CONFIGURACION_NIVELES: tuple[NivelConfig, ...] = (
    NivelConfig(
        id=1,
        nombre="Calentamiento y Soltura",
        descripcion="Para romper el hielo. Tolerancia amplia para pensar tus ideas sin presión extrema.",
        tolerancia_inactividad_seg=7.5,
        meta_palabras=75,
        tiempo_pomodoro_min=5,
        tiempo_descanso_min=2
    ),
    NivelConfig(
        id=2,
        nombre="Enfoque y Fluidez",
        descripcion="Ritmo constante de escritura. La vacilación empieza a costar caro.",
        tolerancia_inactividad_seg=4.5,
        meta_palabras=150,
        tiempo_pomodoro_min=10,
        tiempo_descanso_min=3
    ),
    NivelConfig(
        id=3,
        nombre="Modo Máximo Desafío",
        descripcion="Escritura en trance creativo puro. Detenerte más de 2.5 segundos destruirá tu avance.",
        tolerancia_inactividad_seg=2.5,
        meta_palabras=250,
        tiempo_pomodoro_min=15,
        tiempo_descanso_min=5
    ),
)

# Catálogo inmutable de 18 temas predefinidos para respaldo (fallback cuando Ollama no responde)
TEMAS_PREDEFINIDOS: tuple[TemaSugerido, ...] = (
    # Nivel 1: Cotidiano, memorias y percepciones inmediatas
    TemaSugerido(1, "Describe con sumo detalle el primer sonido que escuchaste al despertar esta mañana y qué recuerdo involuntario trajo a tu mente.", "Cotidiano"),
    TemaSugerido(1, "Escribe sobre una taza de café o té olvidada sobre la mesa y lo que sucedió a su alrededor mientras se enfriaba.", "Cotidiano"),
    TemaSugerido(1, "Narra la caminata más breve que hiciste esta semana y un objeto aparentemente insignificante que llamó tu atención en el camino.", "Cotidiano"),
    TemaSugerido(1, "Describe la vista desde tu ventana en un día nublado y la atmósfera emocional que percibes en la calle vacía.", "Cotidiano"),
    TemaSugerido(1, "Escribe sobre un aroma familiar que de repente percibiste en un lugar inesperado y a qué momento de tu vida te transportó.", "Cotidiano"),
    TemaSugerido(1, "Relata una pequeña conversación curiosa que escuchaste sin querer en el transporte público o en una fila.", "Cotidiano"),

    # Nivel 2: Personaje curioso o situación con misterio/conflicto
    TemaSugerido(2, "Un relojero veterano descubre que uno de los relojes antiguos de su taller comienza a marcar los minutos hacia atrás cada medianoche.", "Situación"),
    TemaSugerido(2, "Dos desconocidos quedan atrapados en un elevador antiguo y uno de ellos sostiene una carta sellada que no se atreve a abrir.", "Personaje"),
    TemaSugerido(2, "Un fotógrafo urbano revisa sus fotos del día y nota a la misma persona misteriosa en el fondo de todas las tomas.", "Situación"),
    TemaSugerido(2, "Una joven encuentra una llave de bronce dentro de un libro usado con una nota manuscrita que dice: 'úsala antes del anochecer'.", "Personaje"),
    TemaSugerido(2, "Un cocinero recibe un pedido anónimo para preparar la comida favorita de alguien a quien no ve desde hace diez años.", "Situación"),
    TemaSugerido(2, "Un viajero pierde el último tren en una estación rural y entabla una extraña charla con el encargado del faro vecino.", "Personaje"),

    # Nivel 3: Abstracto, filosófico o poético
    TemaSugerido(3, "Si los recuerdos tuvieran peso físico y se acumularan en una habitación cerrada, ¿cómo se sentiría entrar después de veinte años?", "Abstracto"),
    TemaSugerido(3, "Explora la paradoja del silencio absoluto: ¿es la ausencia total de sonido o la presencia ensordecedora de los propios pensamientos?", "Abstracto"),
    TemaSugerido(3, "El tiempo decide detenerse solo para ti durante un parpadeo prolongado. Describe la textura y el color de ese segundo congelado.", "Abstracto"),
    TemaSugerido(3, "Reflexiona sobre los caminos no elegidos y cómo las versiones invisibles de nosotros mismos habitan en las decisiones que descartamos.", "Filosófico"),
    TemaSugerido(3, "Imagina que las palabras olvidadas por la humanidad flotan en el aire como partículas de polvo esperando ser pronunciadas una última vez.", "Poético"),
    TemaSugerido(3, "Describe la arquitectura de una ciudad construida enteramente de reflejos, ecos del pasado y sombras que cobran vida propia.", "Abstracto"),
)


# ==============================================================================
# 🛡️ FUNCIONES PURAS: Motor Antifraude (Filtros Rápidos por Palabra)
# ==============================================================================

def es_repeticion_mecanica(palabra: str) -> bool:
    """Detecta si un caracter se repite 3 o más veces consecutivas (ej: 'holllla', 'aaaa')."""
    return bool(re.search(r'(.)\1{2,}', palabra.lower()))


def tiene_estructura_fonetica_valida(palabra: str) -> bool:
    """Verifica que palabras con más de 2 letras contengan al menos una vocal o estructura válida."""
    palabra_limpia = re.sub(r'[^a-záéíóúüñ]', '', palabra.lower())
    if len(palabra_limpia) <= 1:
        return True  # Monosílabos o letras sueltas de transición
    vocales_en_palabra = tuple(c for c in palabra_limpia if c in VOCALES_VALIDAS)

    # Si tiene más de 3 letras y cero vocales (ej: 'asdfg', 'jkllñ'), es tecleo aleatorio
    if len(palabra_limpia) >= 3 and len(vocales_en_palabra) == 0:
        return False

    # Proporción de vocales razonable (entre 15% y 85%)
    ratio_vocales = len(vocales_en_palabra) / len(palabra_limpia)
    return 0.15 <= ratio_vocales <= 0.90


def clasificar_palabra(palabra: str) -> tuple[bool, str]:
    """
    Función pura que evalúa si una palabra individual pasa los filtros rápidos.
    Detecta repetición mecánica y ausencia de estructura fonética.
    Este es el primer nivel de defensa (velocidad < 1ms por palabra).
    """
    palabra_limpia = palabra.strip('.,;:¡!¿?()[]{}"\'').lower()

    if not palabra_limpia:
        return True, "vacia"

    if es_repeticion_mecanica(palabra_limpia):
        return False, "Repetición anormal de caracteres consecutivos"

    if not tiene_estructura_fonetica_valida(palabra_limpia):
        return False, "Patrón de tecleo sin estructura lingüística (gibberish)"

    return True, "valida"


# ==============================================================================
# 🤖 ANÁLISIS DE COHERENCIA SEMÁNTICA CON OLLAMA (qwen2.5:3b)
# ==============================================================================

def analizar_coherencia_con_ollama(texto: str, timeout_seg: float = 5.0) -> dict:
    """
    Segundo nivel de análisis: consulta al modelo local qwen2.5:3b para evaluar
    si el texto completo es semánticamente coherente o es relleno/tecleo sin sentido.
    """
    if not texto or len(texto.strip().split()) < 5:
        return {"coherente": True, "confianza": "baja", "motivo": None, "fuente": "sin_contexto"}

    fragmento = ' '.join(texto.strip().split()[-300:])

    prompt = (
        "Eres un detector de texto coherente en español. Tu única tarea es evaluar "
        "si el siguiente fragmento fue escrito por un humano con sentido, o si es "
        "tecleo aleatorio/relleno sin significado.\n\n"
        f"Fragmento:\n\"\"\"{fragmento}\"\"\"\n\n"
        "Responde ÚNICAMENTE con un JSON válido sin markdown, con este formato exacto:\n"
        '{"coherente": true/false, "confianza": "alta"/"media"/"baja", "motivo": "...o null"}\n'
        "No agregues nada más."
    )

    try:
        req_data = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,   # Baja temperatura: respuesta determinista
                "num_predict": 80
            }
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=req_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=timeout_seg) as response:
            if response.status == 200:
                res_raw = json.loads(response.read().decode('utf-8'))
                respuesta_texto = res_raw.get('response', '').strip()

                json_match = re.search(r'\{.*?\}', respuesta_texto, re.DOTALL)
                if json_match:
                    resultado_modelo = json.loads(json_match.group())
                    return {
                        "coherente": bool(resultado_modelo.get("coherente", True)),
                        "confianza": resultado_modelo.get("confianza", "media"),
                        "motivo": resultado_modelo.get("motivo"),
                        "fuente": "ollama"
                    }

    except Exception as e:
        print(f"⚠️ Coherencia Ollama: timeout o error ({type(e).__name__}: {e}). Usando fallback.")

    return {"coherente": True, "confianza": "baja", "motivo": None, "fuente": "fallback"}


def validar_buffer_texto(texto: str) -> dict:
    """Pipeline de validación en dos niveles."""
    if not texto.strip():
        return {
            "valido": True,
            "palabras_totales": 0,
            "palabras_validas": 0,
            "palabras_basura": 0,
            "porcentaje_calidad": 100.0,
            "alerta": None,
            "coherencia_ia": None,
        }

    # Nivel 1: Filtros rápidos por palabra
    palabras_crudas = tuple(texto.split())
    evaluaciones = tuple(clasificar_palabra(p) for p in palabras_crudas)

    validas = tuple(p for p, (ok, _) in zip(palabras_crudas, evaluaciones) if ok)
    basuras = tuple((p, motivo) for p, (ok, motivo) in zip(palabras_crudas, evaluaciones) if not ok)

    total = len(palabras_crudas)
    total_validas = len(validas)
    total_basuras = len(basuras)

    calidad = round((total_validas / total) * 100.0, 1) if total > 0 else 100.0

    alerta = None
    if total_basuras > 0:
        ultima_basura, motivo = basuras[-1]
        alerta = f"Se detectó texto no válido: '{ultima_basura}' ({motivo})."

    # Nivel 2: Coherencia con Ollama
    coherencia_ia = None
    if total_validas >= 10:
        coherencia_ia = analizar_coherencia_con_ollama(texto)
        if not coherencia_ia["coherente"] and coherencia_ia["confianza"] in ("alta", "media"):
            motivo_ia = coherencia_ia.get("motivo") or "El modelo local detectó texto sin coherencia semántica."
            alerta = f"[Análisis IA] {motivo_ia}"
            calidad = min(calidad, 40.0)

    return {
        "valido": calidad >= 70.0,
        "palabras_totales": total,
        "palabras_validas": total_validas,
        "palabras_basura": total_basuras,
        "porcentaje_calidad": calidad,
        "alerta": alerta,
        "coherencia_ia": coherencia_ia,
    }


# ==============================================================================
# 💡 GENERACIÓN Y SUGERENCIA DE TEMAS DE ESCRITURA (Qwen 2.5 3B)
# ==============================================================================

def obtener_temas_por_nivel(nivel_id: int) -> tuple[TemaSugerido, ...]:
    """Función pura que filtra los temas predefinidos según el nivel solicitado."""
    temas = tuple(t for t in TEMAS_PREDEFINIDOS if t.nivel_id == nivel_id)
    return temas if temas else TEMAS_PREDEFINIDOS


def seleccionar_tema_fallback(nivel_id: int, tema_actual: str = "") -> str:
    """Selecciona un tema predefinido garantizando que no se repita con el actual."""
    temas_disponibles = obtener_temas_por_nivel(nivel_id)
    candidatos = tuple(t.texto for t in temas_disponibles if t.texto != tema_actual)
    if not candidatos:
        candidatos = tuple(t.texto for t in temas_disponibles)
    return random.choice(candidatos) if candidatos else "Escribe libremente lo primero que llegue a tu mente sin juzgar el resultado."


def construir_prompt_tema(nivel_id: int) -> str:
    """Función pura que construye el prompt para disparadores temáticos según el nivel."""
    match nivel_id:
        case 1:
            enfoque = "un disparador de escritura creativo sobre algo COTIDIANO, sensorial o una memoria simple (máximo 2 oraciones breves y sugerentes)"
        case 2:
            enfoque = "una premisa narrativa intrigante sobre un PERSONAJE curioso o una SITUACIÓN con misterio/conflicto inmediato (máximo 2 oraciones breves)"
        case 3:
            enfoque = "un tema ABSTRACTO, filosófico o poético que desafíe la imaginación y el pensamiento lateral (máximo 2 oraciones breves y profundas)"
        case _:
            enfoque = "una idea creativa e inspiradora para comenzar a escribir sin bloqueo (máximo 2 oraciones)"

    return (
        f"Eres un mentor de escritura creativa. Genera {enfoque} en español para que un escritor empiece a redactar de inmediato.\n\n"
        "Reglas estrictas:\n"
        "- Escribe ÚNICAMENTE la idea/disparador en 1 o 2 oraciones directas.\n"
        "- NO uses saludos, ni comillas introductorias, ni frases como 'Aquí tienes una idea:' o 'Disparador:'.\n"
        "- Redacta directamente en tono inspirador."
    )


def limpiar_texto_sugerencia(texto_raw: str) -> str:
    """Función pura que limpia comillas y prefijos innecesarios devueltos por el LLM."""
    limpio = texto_raw.strip().strip('"\'''«»')
    limpio = re.sub(r'^(aquí tienes|tema|disparador|idea|propuesta):\s*', '', limpio, flags=re.IGNORECASE)
    return limpio.strip()


def generar_sugerencia_tema_ia(nivel_id: int, tema_actual: str = "", timeout_seg: float = 8.0) -> dict:
    """
    Genera una idea para arrancar a escribir usando Qwen 2.5 3B.
    Si Ollama tarda más de timeout_seg (8s) o falla, extrae un tema del catálogo inmutable.
    """
    prompt = construir_prompt_tema(nivel_id)
    try:
        req_data = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85,  # Alta temperatura para variedad creativa
                "num_predict": 70
            }
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=req_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=timeout_seg) as response:
            if response.status == 200:
                res_raw = json.loads(response.read().decode('utf-8'))
                texto_gen = limpiar_texto_sugerencia(res_raw.get('response', ''))
                if texto_gen and len(texto_gen) >= 15:
                    return {
                        "sugerencia": texto_gen,
                        "fuente": "ollama",
                        "nivel_id": nivel_id
                    }
    except Exception as e:
        print(f"⚠️ Sugerencia tema Ollama fallback ({type(e).__name__}: {e})")

    return {
        "sugerencia": seleccionar_tema_fallback(nivel_id, tema_actual),
        "fuente": "fallback",
        "nivel_id": nivel_id
    }


# ==============================================================================
# ✏️ CORRECCIÓN DE ESTILO Y DETECCIÓN DE MEJORAS (Qwen 2.5 3B)
# ==============================================================================

def normalizar_para_busqueda(texto: str) -> str:
    """Función pura que normaliza espacios para comparar fragmentos."""
    return re.sub(r'\s+', ' ', texto.strip().lower())


def verificar_fragmento_en_texto(fragmento: str, texto_completo: str) -> bool:
    """
    Función pura que valida estrictamente si el fragmento original citado por la IA
    existe de forma real en el texto del usuario (evita alucinaciones).
    """
    if not fragmento or not texto_completo:
        return False
    frag_norm = normalizar_para_busqueda(fragmento)
    texto_norm = normalizar_para_busqueda(texto_completo)

    if frag_norm in texto_norm:
        return True

    # Comprobación eliminando signos de puntuación iniciales y finales
    frag_sin_signos = re.sub(r'^[.,;:¡!¿?()"\']+|[.,;:¡!¿?()"\']+$', '', frag_norm)
    return len(frag_sin_signos) >= 3 and frag_sin_signos in texto_norm


def parsear_sugerencias_estilo(respuesta_raw: str) -> tuple[dict, ...]:
    """Función pura que extrae la lista de correcciones desde el JSON del LLM."""
    try:
        match_array = re.search(r'\[\s*\{.*?\}\s*\]', respuesta_raw, re.DOTALL)
        if match_array:
            data = json.loads(match_array.group())
            if isinstance(data, list):
                return tuple(item for item in data if isinstance(item, dict))

        match_obj = re.search(r'\{\s*"original".*?\}', respuesta_raw, re.DOTALL)
        if match_obj:
            data = json.loads(match_obj.group())
            if isinstance(data, dict):
                return (data,)
    except Exception:
        pass
    return ()


def filtrar_sugerencias_estilo_validas(
    sugerencias_crudas: tuple[dict, ...],
    texto_usuario: str,
    max_items: int = 3
) -> tuple[SugerenciaEstilo, ...]:
    """
    Función pura que descarta sugerencias con citas alucinadas y devuelve
    como máximo max_items sugerencias autenticadas en el texto.
    """
    validas: list[SugerenciaEstilo] = []
    for item in sugerencias_crudas:
        orig = str(item.get("original", "")).strip()
        sug = str(item.get("sugerencia", "")).strip()
        mot = str(item.get("motivo", "")).strip()

        if orig and sug and mot and verificar_fragmento_en_texto(orig, texto_usuario):
            validas.append(SugerenciaEstilo(original=orig, sugerencia=sug, motivo=mot))
            if len(validas) >= max_items:
                break
    return tuple(validas)


def construir_prompt_estilo(texto: str) -> str:
    """Función pura que arma el prompt de corrección de estilo para Qwen."""
    fragmento = ' '.join(texto.strip().split()[-400:])
    return (
        "Eres un corrector de estilo en español. Analiza el siguiente texto y detecta hasta 3 oportunidades de mejora "
        "(repeticiones de palabras, frases redundantes, errores gramaticales u ortográficos o falta de fluidez).\n\n"
        f"Texto del estudiante:\n\"\"\"{fragmento}\"\"\"\n\n"
        "Reglas obligatorias:\n"
        "1. El campo 'original' DEBE ser una cita EXACTA y textual de palabras que aparezcan en el texto (sin inventar).\n"
        "2. El campo 'sugerencia' debe mostrar cómo reescribir ese fragmento de forma más elegante o correcta.\n"
        "3. El campo 'motivo' debe explicar brevemente la razón de la sugerencia (1 oración concisa).\n"
        "4. Responde ÚNICAMENTE con un JSON array válido con este formato:\n"
        '[{"original": "fragmento exacto", "sugerencia": "versión mejorada", "motivo": "explicación breve"}]\n'
        "Si el texto no tiene errores evidentes o es muy breve, responde con un array vacío: []"
    )


def analizar_estilo_con_qwen(texto: str, timeout_seg: float = 18.0) -> dict:
    """
    Consulta a Ollama de forma asíncrona/aislada para corrección de estilo.
    No afecta la calificación matemática.
    """
    palabras = texto.strip().split()
    if len(palabras) < 10:
        return {
            "disponible": True,
            "sugerencias": [],
            "mensaje": "Escribe un texto más extenso (al menos 10 palabras) para recibir sugerencias de estilo."
        }

    prompt = construir_prompt_estilo(texto)
    try:
        req_data = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,   # Baja temperatura para evitar alucinaciones
                "num_predict": 220
            }
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=req_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=timeout_seg) as response:
            if response.status == 200:
                res_raw = json.loads(response.read().decode('utf-8'))
                respuesta_texto = res_raw.get('response', '').strip()
                sugerencias_crudas = parsear_sugerencias_estilo(respuesta_texto)
                sugerencias_validadas = filtrar_sugerencias_estilo_validas(sugerencias_crudas, texto)

                return {
                    "disponible": True,
                    "sugerencias": [
                        {"original": s.original, "sugerencia": s.sugerencia, "motivo": s.motivo}
                        for s in sugerencias_validadas
                    ],
                    "mensaje": "Análisis de estilo completado." if sugerencias_validadas else "¡Excelente redacción! No se detectaron problemas evidentes de repetición o sintaxis."
                }
    except Exception as e:
        print(f"⚠️ Corrección de estilo Ollama ({type(e).__name__}: {e})")

    return {
        "disponible": False,
        "sugerencias": [],
        "mensaje": "La corrección de estilo asistida por IA local no está disponible en este momento."
    }


# ==============================================================================
# 🏆 EVALUACIÓN FINAL PURA (Gamificación)
# ==============================================================================

def calcular_evaluacion_final(
    palabras_validas: int,
    palabras_basura: int,
    pausas_al_limite: int,
    tiempo_segundos: float,
    nivel_id: int
) -> dict:
    """Función pura que computa la calificación final estructurada y feedback motivador."""
    minutos = max(tiempo_segundos / 60.0, 0.1)
    wpm = round(palabras_validas / minutos, 1)

    nivel = next((n for n in CONFIGURACION_NIVELES if n.id == nivel_id), CONFIGURACION_NIVELES[0])

    meta_alcanzada = min(palabras_validas / max(nivel.meta_palabras, 1), 1.0)
    puntaje_meta = meta_alcanzada * 50.0

    ratio_calidad = (palabras_validas / max(palabras_validas + palabras_basura, 1))
    puntaje_calidad = ratio_calidad * 30.0

    penalizacion_pausas = min(pausas_al_limite * 2.0, 20.0)
    puntaje_fluidez = max(20.0 - penalizacion_pausas, 0.0)

    puntaje_total = round(min(puntaje_meta + puntaje_calidad + puntaje_fluidez, 100.0), 1)

    match puntaje_total:
        case p if p >= 95.0:
            estrellas = 5
            rango = "Maestro de la Fluidez — Mente Imparable"
        case p if p >= 85.0:
            estrellas = 4
            rango = "Escritor Enfocado — Alta Concentración"
        case p if p >= 70.0:
            estrellas = 3
            rango = "Redactor Prometedor — Buen Ritmo"
        case p if p >= 50.0:
            estrellas = 2
            rango = "En Entrenamiento — Vence la Duda"
        case _:
            estrellas = 1
            rango = "Calentamiento Necesario — No Te Detengas"

    return {
        "puntaje_total": puntaje_total,
        "estrellas": estrellas,
        "rango": rango,
        "wpm": wpm,
        "palabras_validas": palabras_validas,
        "palabras_descartadas": palabras_basura,
        "pausas_criticas": pausas_al_limite,
        "tiempo_total_seg": round(tiempo_segundos, 1),
        "cumplio_meta": palabras_validas >= nivel.meta_palabras,
    }


# ==============================================================================
# 🤖 RESEÑA LITERARIA FINAL CON OLLAMA (qwen2.5:3b)
# ==============================================================================

def generar_resena_con_qwen(texto: str, wpm: float, palabras_validas: int, timeout_seg: float = 35.0) -> dict:
    """Consulta al modelo local qwen2.5:3b para obtener crítica literaria de la redacción."""
    if palabras_validas < 10 or not texto.strip():
        return {
            "disponible": True,
            "modelo": "qwen2.5:3b",
            "comentario": "¡Buen inicio! Redacta al menos 10 palabras para que Qwen 2.5 pueda analizar tu estilo literario y flujo de ideas."
        }

    prompt = (
        f"Eres un mentor de redacción creativa en español. Un estudiante completó una sesión de escritura rápida "
        f"produciendo {palabras_validas} palabras a una velocidad de {wpm} palabras por minuto (WPM).\n\n"
        f"Texto producido:\n\"\"\"{texto.strip()[:1500]}\"\"\"\n\n"
        f"En máximo 3 oraciones concisas y motivadoras: 1) Destaca el tema o atmósfera del texto, "
        f"2) Menciona una virtud de la redacción, 3) Da una sugerencia para mejorar la fluidez creativa. "
        f"Responde directamente en tono cercano y constructivo."
    )

    try:
        req_data = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150
            }
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=req_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=timeout_seg) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                comentario = res_data.get('response', '').strip()
                return {
                    "disponible": True,
                    "modelo": "qwen2.5:3b",
                    "comentario": comentario or "Texto evaluado con éxito por el modelo local."
                }
    except Exception as e:
        print(f"⚠️ Aviso Ollama: No fue posible conectar con qwen2.5:3b ({e})")

    return {
        "disponible": False,
        "modelo": "qwen2.5:3b",
        "comentario": "Ollama local no respondió a tiempo. Tu calificación matemática y métricas de desempeño se calcularon al 100%."
    }


# ==============================================================================
# 🌐 ENDPOINTS DE LA API REST (FLASK)
# ==============================================================================

@app.after_request
def agregar_cabeceras_cors(response):
    """Permite peticiones seguras locales sin necesidad de librerías externas."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route('/')
def index():
    """Sirve la interfaz web principal desde la carpeta Frontend."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/niveles', methods=['GET'])
def obtener_niveles():
    """Retorna la lista de niveles y parámetros de configuración inmutables."""
    return jsonify({
        "niveles": [
            {
                "id": n.id,
                "nombre": n.nombre,
                "descripcion": n.descripcion,
                "tolerancia_seg": n.tolerancia_inactividad_seg,
                "meta_palabras": n.meta_palabras,
                "pomodoro_min": n.tiempo_pomodoro_min,
                "descanso_min": n.tiempo_descanso_min
            }
            for n in CONFIGURACION_NIVELES
        ]
    })


@app.route('/api/validar', methods=['POST'])
def validar_texto():
    """Analiza el texto del usuario en dos niveles (fonético + coherencia Ollama)."""
    datos = request.get_json() or {}
    texto = datos.get("texto", "")
    resultado = validar_buffer_texto(texto)
    return jsonify(resultado)


@app.route('/api/tema', methods=['POST'])
def sugerir_tema():
    """Genera o recupera una idea disparadora para comenzar a escribir según el nivel."""
    datos = request.get_json() or {}
    nivel_id = int(datos.get("nivel_id", 1))
    tema_anterior = str(datos.get("tema_anterior", ""))
    resultado = generar_sugerencia_tema_ia(nivel_id, tema_anterior)
    return jsonify(resultado)


@app.route('/api/calificar', methods=['POST'])
def calificar_sesion():
    """Calcula el reporte final de desempeño y genera reseña literaria con Qwen 2.5 3B."""
    datos = request.get_json() or {}
    palabras_validas = int(datos.get("palabras_validas", 0))
    palabras_basura = int(datos.get("palabras_basura", 0))
    pausas_al_limite = int(datos.get("pausas_al_limite", 0))
    tiempo_segundos = float(datos.get("tiempo_segundos", 0.0))
    nivel_id = int(datos.get("nivel_id", 1))
    texto = datos.get("texto", "")

    reporte = calcular_evaluacion_final(
        palabras_validas=palabras_validas,
        palabras_basura=palabras_basura,
        pausas_al_limite=pausas_al_limite,
        tiempo_segundos=tiempo_segundos,
        nivel_id=nivel_id
    )

    reporte["resena_ia"] = generar_resena_con_qwen(
        texto=texto,
        wpm=reporte["wpm"],
        palabras_validas=palabras_validas
    )

    return jsonify(reporte)


@app.route('/api/estilo', methods=['POST'])
def revisar_estilo():
    """
    Endpoint desacoplado para corrección de estilo asistida por Qwen 2.5 3B.
    Se ejecuta de forma asíncrona tras abrir el modal de calificación.
    """
    datos = request.get_json() or {}
    texto = str(datos.get("texto", ""))
    resultado = analizar_estilo_con_qwen(texto)
    return jsonify(resultado)


if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    print(f"🚀 Servidor 'Escribe si puedes' ejecutándose en http://localhost:{puerto}")
    app.run(debug=True, port=puerto, host="0.0.0.0")
