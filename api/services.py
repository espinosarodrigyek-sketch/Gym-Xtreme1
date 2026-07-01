import requests
import random
import logging
import time

logger = logging.getLogger(__name__)

FREE_EXERCISE_API_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
IMAGE_BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"


# Translator function using MyMemory API (free, no key required)
# Cache para evitar traducciones repetidas
_cache_traducciones = {}
_traduccion_disponible = True

def traducir_texto_google(texto, idioma_origen='en', idioma_destino='es'):
    """Traduce texto usando MyMemory API (gratis)"""
    global _traduccion_disponible
    
    if not texto:
        return texto
    
    if not _traduccion_disponible:
        return texto
    
    cache_key = f"{texto[:50]}_{idioma_origen}_{idioma_destino}"
    if cache_key in _cache_traducciones:
        return _cache_traducciones[cache_key]
    
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            'q': texto,
            'langpair': f'{idioma_origen}|{idioma_destino}'
        }
        response = requests.get(url, params=params, timeout=3)
        data = response.json()
        
        if data.get('responseStatus') == 200:
            resultado = data.get('responseData', {}).get('translatedText', texto)
            _cache_traducciones[cache_key] = resultado
            return resultado
        elif data.get('responseStatus') == 429:
            logger.warning("MyMemory quota exceeded")
            _traduccion_disponible = False
            return texto
        else:
            logger.warning(f"Translation failed: {data}")
            return texto
    except requests.exceptions.Timeout:
        logger.warning("MyMemory translation timeout")
        _traduccion_disponible = False
        return texto
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"MyMemory connection failed: {e}")
        _traduccion_disponible = False
        return texto
    except Exception as e:
        logger.error(f"Error translating: {e}")
        _traduccion_disponible = False
        return texto


def traducir_descripcion_api(descripcion):
    """Traduce la descripción del ejercicio de inglés a español"""
    global _traduccion_disponible
    
    if not descripcion:
        return descripcion
    
    if not _traduccion_disponible:
        return descripcion
    
    # Dividir en pasos (por guiones)
    pasos = descripcion.split(' - ')
    pasos_traducidos = []
    
    for paso in pasos:
        paso = paso.strip()
        if paso:
            # Intentar traducir con MyMemory
            traduccion = traducir_texto_google(paso)
            
            # Si la traducción es igual al texto original o es el texto original, usar diccionario
            if traduccion == paso or "MYMEMORY" in traduccion.upper():
                # Usar el diccionario local como fallback
                traduccion = _traducir_con_diccionario(paso)
            
            pasos_traducidos.append(traduccion)
    
    return ' - '.join(pasos_traducidos)


def _traducir_con_diccionario(texto):
    """Traduce texto usando el diccionario local como fallback"""
    if not texto:
        return texto
    
    resultado = texto
    
    # Lista de reemplazos comunes
    REEMPLAZOS = [
        # Verbos
        ("Lie back", "Acuéstate boca arriba"),
        ("Lie down", "Acuéstate"),
        ("Sit down", "Siéntate"),
        ("Stand up", "Levántate"),
        ("Stand", "Párate"),
        ("Hold", "Sostén"),
        ("Grip", "Agarra"),
        ("Lift", "Levanta"),
        ("Lower", "Baja"),
        ("Raise", "Eleva"),
        ("Push", "Empuja"),
        ("Pull", "Jala"),
        ("Press", "Presiona"),
        ("Squeeze", "Aprieta"),
        ("Contract", "Contrae"),
        ("Extend", "Extiende"),
        ("Bend", "Flexiona"),
        ("Keep", "Mantén"),
        ("Return", "Regresa"),
        ("Repeat", "Repite"),
        ("Begin", "Comienza"),
        ("Start", "Inicia"),
        
        # Partes del cuerpo
        ("your chest", "tu pecho"),
        ("your back", "tu espalda"),
        ("your shoulders", "tus hombros"),
        ("your arms", "tus brazos"),
        ("your legs", "tus piernas"),
        ("your feet", "tus pies"),
        ("your hands", "tus manos"),
        ("your head", "tu cabeza"),
        ("your knees", "tus rodillas"),
        ("your hips", "tus caderas"),
        
        # Equipamiento
        ("the floor", "el piso"),
        ("the bench", "el banco"),
        ("the bar", "la barra"),
        ("the rack", "el soporte"),
        ("a flat bench", "un banco plano"),
        
        # Posiciones
        ("starting position", "posición inicial"),
        ("This will be your starting position", "Esta será tu posición inicial"),
        
        # Direcciones
        ("slowly", "lentamente"),
        ("down", "abajo"),
        ("up", "arriba"),
        ("back", "atrás"),
        
        # Conectores
        ("Then", "Luego"),
        ("then", "luego"),
        ("After", "Después"),
        ("after", "después"),
        ("until", "hasta"),
        
        # Respiración
        ("breathe in", "inhala"),
        ("breathe out", "exhala"),
        ("inhale", "inhala"),
        ("exhale", "exhala"),
        
        # Misc
        ("repetitions", "repeticiones"),
        ("seconds", "segundos"),
    ]
    
    import re
    for eng, esp in REEMPLAZOS:
        pattern = re.compile(re.escape(eng), re.IGNORECASE)
        resultado = pattern.sub(esp, resultado)
    
    return resultado


# Diccionario de traducción inglés -> español para ejercicios
TRADUCCIONES_EJERCICIOS = {
    # Ejercicios de pecho
    "Barbell Bench Press - Medium Grip": "Press de Banca con Barra - Agarre Medio",
    "Barbell Guillotine Bench Press": "Press de Banca Guillotina",
    "Barbell Incline Bench Press - Medium Grip": "Press Inclinado con Barra",
    "Dumbbell Bench Press": "Press de Banca con Mancuernas",
    "Incline Dumbbell Press": "Press Inclinado con Mancuernas",
    "Dumbbell Flyes": "Aperturas con Mancuernas",
    "Cable Crossover": "Cruce de Cables",
    "Push-Up": "Flexiones",
    "Chest Dip": "Fondos para Pecho",
    "Machine Chest Press": "Máquina de Pecho",
    "Pec Deck Machine": "Máquina Pec Deck",
    
    # Ejercicios de espalda
    "Pull-Up": "Dominadas",
    "Chin-Up": "Dominadas agarre inverso",
    "Lat Pulldown": "Jalón al Pecho",
    "Seated Cable Row": "Remo con Cable Sentado",
    "Bent Over Barbell Row": "Remo con Barra",
    "Dumbbell Row": "Remo con Mancuerna",
    "T-Bar Row": "Remo en T",
    "Lat Pulldown - Behind Neck": "Jalón Detrás del Cuello",
    "Cable Straight Arm Pulldown": "Jalón de Cables Brazos Rectos",
    "Barbell Full Squat": "Sentadilla Completa con Barra",
    "Barbell Hack Squat": "Sentadilla Hack con Barra",
    "Barbell Squat": "Sentadilla con Barra",
    "Front Squat": "Sentadilla Frontal",
    "Leg Press": "Prensa de Piernas",
    "Leg Extension": "Extensión de Piernas",
    "Leg Curl": "Curl de Piernas",
    "Lunge": "Zancadas",
    "Calf Raise": "Elevación de Talones",
    "Romanian Deadlift": "Peso Muerto Rumano",
    "Hip Thrust": "Empuje de Cadera",
    "Deadlift": "Peso Muerto",
    "Shoulder Press": "Press de Hombros",
    "Dumbbell Shoulder Press": "Press de Hombros con Mancuernas",
    "Lateral Raise": "Elevaciones Lateral",
    "Bicep Curl": "Curl de Bíceps",
    "Tricep Pushdown": "Extensión de Tríceps",
    "Crunch": "Crunch",
    "Plank": "Plancha",
    
    # Ejercicios de hombros
    "Overhead Press": "Press Militar",
    "Seated Dumbbell Press": "Press Sentado con Mancuernas",
    "Arnold Press": "Press Arnold",
    "Lateral Raise": "Elevaciones Lateral",
    "Front Raise": "Elevaciones Frontal",
    "Rear Delt Flyes": "Aperturas Posterior",
    "Upright Row": "Remo Vertical",
    "Face Pull": "Face Pull",
    "Shrug": "Encogimientos",
    
    # Ejercicios de brazos
    "Barbell Curl": "Curl con Barra",
    "Dumbbell Curl": "Curl con Mancuernas",
    "Hammer Curl": "Curl Martillo",
    "Preacher Curl": "Curl Predicador",
    "Concentration Curl": "Curl Concentrado",
    "Cable Curl": "Curl con Cable",
    "Tricep Pushdown": "Extensiones de Tríceps",
    "Tricep Dip": "Fondos de Tríceps",
    "Skull Crusher": "Crushers de Cráneo",
    "Overhead Tricep Extension": "Extensión por Encima de la Cabeza",
    "Close Grip Bench Press": "Press Agarre Cerrado",
    
    # Ejercicios de piernas
    "Barbell Squat": "Sentadilla con Barra",
    "Front Squat": "Sentadilla Frontal",
    "Leg Press": "Prensa de Piernas",
    "Leg Extension": "Extensión de Piernas",
    "Leg Curl": "Curl de Piernas",
    "Lunge": "Zancadas",
    "Walking Lunge": "Zancadas Caminando",
    "Bulgarian Split Squat": "Sentadilla Búlgara",
    "Calf Raise": "Elevación de Talones",
    "Romanian Deadlift": "Peso Muerto Rumano",
    "Leg Raise": "Elevación de Piernas",
    "Hip Thrust": "Empuje de Cadera",
    "Glute Bridge": "Puente de Glúteos",
    
    # Ejercicios de abdomen
    "Crunch": "Crunch",
    "Sit-Up": "Sentadilla",
    "Leg Raise": "Elevación de Piernas",
    "Plank": "Plancha",
    "Side Plank": "Plancha Lateral",
    "Ab Wheel Rollout": "Rueda Abdominal",
    "Cable Crunch": "Crunch con Cable",
    "Hanging Leg Raise": "Elevación de Piernas Colgado",
    "Russian Twist": "Giro Ruso",
    "Bicycle Crunch": "Crunch Bicicleta",
    
    # Niveles
    "beginner": "principiante",
    "intermediate": "intermedio",
    "expert": "avanzado",
    
    # Equipamiento
    "barbell": "barra",
    "dumbbell": "mancuerna",
    "machine": "máquina",
    "cable": "cable",
    "body only": "solo cuerpo",
    "ez bar": "barra EZ",
    "smith machine": "máquina Smith",
    "bands": "bandas",
    "kettlebell": "kettlebell",
    
    # Músculos
    "chest": "pecho",
    "back": "espalda",
    "lats": "dorsales",
    "shoulders": "hombros",
    "biceps": "bíceps",
    "triceps": "tríceps",
    "forearms": "antebrazos",
    "quadriceps": "cuádriceps",
    "hamstrings": "isquiotibiales",
    "glutes": "glúteos",
    "calves": "pantorrillas",
    "abdominals": "abdominales",
    "abs": "abdominales",
    "legs": "piernas",
    "arms": "brazos",
    "full body": "cuerpo completo",
    
    # Categorías
    "strength": "fuerza",
    "cardio": "cardio",
    "stretching": "estiramiento",
    "plyometrics": "pliométricos",
    
    # Fuerza
    "push": "empuje",
    "pull": "jalar",
    "compound": "compuesto",
    "isolation": "aislamiento",
}


def traducir_texto(texto):
    """Traduce texto de inglés a español usando el diccionario"""
    if not texto:
        return texto
    
    # Si es una lista, traducir cada elemento
    if isinstance(texto, list):
        return [traducir_texto(t) for t in texto]
    
    # Si es string, buscar traducción
    if isinstance(texto, str):
        return TRADUCCIONES_EJERCICIOS.get(texto, texto)
    
    return texto


def traducir_descripcion(descripcion):
    """Traduce las instrucciones del ejercicio de inglés a español"""
    if not descripcion:
        return descripcion
    
    #替换函数
    def replace_text(text, replacements):
        import re
        for eng, esp in replacements:
            pattern = re.compile(re.escape(eng), re.IGNORECASE)
            text = pattern.sub(esp, text)
        return text
    
    # Primera tanda: frases completas y más largas
    REEMPLAZOS_LARGOS = [
        # Posiciones iniciales
        ("This will be your starting position", "Esta será tu posición inicial"),
        ("This will be your starting position.", "Esta será tu posición inicial."),
        ("This will be your starting position -", "Esta será tu posición inicial -"),
        
        # Partes del cuerpo
        ("your middle chest", "la parte media de tu pecho"),
        ("your chest", "tu pecho"),
        ("your back", "tu espalda"),
        ("your shoulders", "tus hombros"),
        ("your arms", "tus brazos"),
        ("your legs", "tus piernas"),
        ("your feet", "tus pies"),
        ("your hands", "tus manos"),
        ("your head", "tu cabeza"),
        ("your neck", "tu cuello"),
        ("your knees", "tus rodillas"),
        ("your hips", "tus caderas"),
        ("your waist", "tu cintura"),
        ("your abs", "tu abdomen"),
        ("your hamstrings", "tus isquiotibiales"),
        ("your calves", "tus pantorrillas"),
        ("your thighs", "tus muslos"),
        ("your glutes", "tus glúteos"),
        
        # Equipamiento
        ("the squat rack", "el soporte para sentadillas"),
        ("the power rack", "el rack de potencia"),
        ("the rack", "el soporte"),
        ("the bar", "la barra"),
        ("the barbell", "la barra"),
        ("a squat rack", "un soporte para sentadillas"),
        ("the floor", "el piso"),
        ("the ground", "el suelo"),
        ("a flat bench", "un banco plano"),
        ("an incline bench", "un banco inclinado"),
        ("a decline bench", "un banco declinado"),
        ("the bench", "el banco"),
        ("the dumbbell", "la mancuerna"),
        ("the dumbbells", "las mancuernas"),
        ("dumbbells", "mancuernas"),
        ("the weight", "el peso"),
        ("the weights", "los pesos"),
        ("the machine", "la máquina"),
        ("the cable", "el cable"),
        
        # Verbos y acciones principales
        ("begin to", "comienza a"),
        ("Begin", "Comienza"),
        ("begin", "comienza"),
        ("Start", "Inicia"),
        ("start", "inicia"),
        ("lie back", "acuéstate boca arriba"),
        ("Lie back", "Acuéstate boca arriba"),
        ("lie down", "acuéstate"),
        ("Lie down", "Acuéstate"),
        ("sit down", "siéntate"),
        ("Sit down", "Siéntate"),
        ("stand up", "levántate"),
        ("Stand up", "Levántate"),
        ("stand", "párate"),
        ("Stand", "Párate"),
        ("hold", "sostén"),
        ("Hold", "Sostén"),
        ("grip", "agarra"),
        ("Grip", "Agarra"),
        ("grab", "agarra"),
        ("Grab", "Agarra"),
        ("lift", "levanta"),
        ("Lift", "Levanta"),
        ("raise", "eleva"),
        ("Raise", "Eleva"),
        ("lower", "baja"),
        ("Lower", "Baja"),
        ("push", "empuja"),
        ("Push", "Empuja"),
        ("pull", "jala"),
        ("Pull", "Jala"),
        ("press", "presiona"),
        ("Press", "Presiona"),
        ("squeeze", "aprieta"),
        ("Squeeze", "Aprieta"),
        ("contract", "contrae"),
        ("Contract", "Contrae"),
        ("extend", "extiende"),
        ("Extend", "Extiende"),
        ("flex", "flexiona"),
        ("Flex", "Flexiona"),
        ("rotate", "rota"),
        ("Rotate", "Rota"),
        ("twist", "gira"),
        ("Twist", "Gira"),
        ("keep", "mantén"),
        ("Keep", "Mantén"),
        ("maintain", "mantén"),
        ("Maintain", "Mantén"),
        ("return", "regresa"),
        ("Return", "Regresa"),
        ("repeat", "repite"),
        ("Repeat", "Repite"),
        
        # Conectores y transiciones
        ("Then", "Luego"),
        ("then", "luego"),
        ("Next", "Después"),
        ("next", "después"),
        ("After a", "Después de una"),
        ("After the", "Después de"),
        ("After", "Después"),
        ("after a", "después de una"),
        ("after the", "después de"),
        ("after", "después"),
        ("Before", "Antes"),
        ("before", "antes"),
        ("While", "Mientras"),
        ("while", "mientras"),
        ("When", "Cuando"),
        ("when", "cuando"),
        ("Until", "Hasta"),
        ("until", "hasta"),
        ("From", "Desde"),
        ("from", "desde"),
        
        # Direcciones y posiciones
        ("straight", "recto"),
        ("straight up", "recto hacia arriba"),
        ("straight over", "recto sobre"),
        ("fully", "completamente"),
        ("slowly", "lentamente"),
        ("slow and", "lento y"),
        ("quickly", "rápidamente"),
        ("controlled", "controlado"),
        ("down", "abajo"),
        ("up", "arriba"),
        ("back", "atrás"),
        ("forward", "adelante"),
        ("together", "juntos"),
        ("apart", "separados"),
        
        # Terminología de ejercicio
        ("starting position", "posición inicial"),
        ("top of the", "parte superior de la"),
        ("bottom of the", "parte inferior de la"),
        ("top", "arriba"),
        ("bottom", "abajo"),
        ("middle", "medio"),
        
        # Ejercicios específicos
        ("the repetition", "la repetición"),
        ("repetitions", "repeticiones"),
        ("reps", "repeticiones"),
        ("the prescribed amount", "la cantidad prescrita"),
        ("the recommended amount", "la cantidad recomendada"),
        ("amount of repetitions", "cantidad de repeticiones"),
        
        # Medidas
        ("inch", "pulgada"),
        ("inches", "pulgadas"),
        ("degree", "grado"),
        ("degrees", "grados"),
        
        # Respiración
        ("breathe in", "inhala"),
        ("breathe out", "exhala"),
        ("inhale", "inhala"),
        ("exhale", "exhala"),
        ("exhaling", "exhalando"),
        ("inhaling", "inhaland"),
        ("take a breath", "toma aire"),
        
        # Misceláneos
        ("step under", "pasa debajo"),
        ("step away", "aléjate"),
        ("step forward", "avanza"),
        ("cross", "cruza"),
        ("across", "sobre"),
        ("place", "coloca"),
        ("position", "posición"),
        ("shoulder-width", "ancho de hombros"),
        ("medium width", "ancho medio"),
        ("wide stance", "posición wide"),
        ("narrow stance", "posición estrecha"),
        ("pointed out", "apuntando hacia afuera"),
        ("locked", "bloqueados"),
        ("lock", "bloquea"),
        ("brief pause", "breve pausa"),
        ("pause", "pausa"),
        ("squeeze", "aprieta"),
        ("contracted", "contraído"),
        ("movement", "movimiento"),
        ("exercise", "ejercicio"),
        ("feet", "pies"),
        
        # Números
        ("one", "uno"),
        ("two", "dos"),
        ("three", "tres"),
        ("four", "cuatro"),
        ("five", "cinco"),
        ("six", "seis"),
        ("seven", "siete"),
        ("eight", "ocho"),
        ("nine", "nueve"),
        ("ten", "diez"),
    ]
    
    # Aplicar reemplazos
    resultado = replace_text(descripcion, REEMPLAZOS_LARGOS)
    
    # Segunda tanda: palabras restantes
    REEMPLAZOS_CORTOS = [
        ("the", "el"),
        ("a", "un"),
        ("an", "un"),
        ("and", "y"),
        ("or", "o"),
        ("with", "con"),
        ("without", "sin"),
        ("for", "para"),
        ("in", "en"),
        ("on", "sobre"),
        ("at", "en"),
        ("to", "a"),
        ("by", "por"),
        ("as", "como"),
        ("is", "es"),
        ("are", "son"),
        ("was", "era"),
        ("were", "eran"),
        ("your", "tu"),
        ("you", "tú"),
        ("this", "esta"),
        ("that", "esa"),
        ("it", "lo"),
        ("its", "su"),
        ("be", "ser"),
        ("been", "sido"),
        ("being", "siendo"),
        ("have", "tener"),
        ("has", "tiene"),
        ("had", "tenía"),
        ("having", "teniendo"),
        ("do", "hacer"),
        ("does", "hace"),
        ("did", "hizo"),
        ("doing", "haciendo"),
        ("can", "poder"),
        ("could", "podría"),
        ("will", "voluntad"),
        ("would", "would"),
    ]
    
    # No aplicamos los cortos directamente porque还有很多英语保留
    # Solo las palabras más comunes que quedaron
    
    return resultado


class FreeExerciseDB:
    """Servicio para consumir ejercicios desde free-exercise-db (GitHub)"""
    
    _cache = None
    _cache_loaded = False
    
    @classmethod
    def recargar_cache(cls):
        """Fuerza la recarga del cache de ejercicios (útil para debugging)"""
        cls._cache = None
        cls._cache_loaded = False
        logger.info("Cache de ejercicios reseteado")
        cls._load_exercises()
    
    @classmethod
    def _load_exercises(cls):
        """Carga los ejercicios desde la API externa"""
        if cls._cache_loaded and cls._cache:
            return
        
        try:
            logger.info("Cargando ejercicios desde free-exercise-db...")
            response = requests.get(FREE_EXERCISE_API_URL, timeout=30)
            response.raise_for_status()
            cls._cache = response.json()
            cls._cache_loaded = True
            logger.info(f"Cargados {len(cls._cache)} ejercicios desde la API")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout cargando ejercicios de free-exercise-db: el servidor no respondió")
            cls._cache = []
            cls._cache_loaded = True
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión: no se pudo conectar a free-exercise-db. Verifica tu conexión a internet.")
            cls._cache = []
            cls._cache_loaded = True
        except Exception as e:
            logger.error(f"Error cargando ejercicios: {e}")
            cls._cache = []
            cls._cache_loaded = True
    
    @classmethod
    def buscar_ejercicios(cls, termino, limite=20):
        """
        Busca ejercicios por término de búsqueda
        Retorna lista de ejercicios matching
        """
        cls._load_exercises()
        
        logger.info(f"Buscando ejercicios con término: '{termino}', cache tiene {len(cls._cache) if cls._cache else 0} ejercicios")
        
        if not cls._cache:
            logger.warning("El cache de ejercicios está vacío")
            return {'success': False, 'error': 'No se pudieron cargar los ejercicios', 'ejercicios': []}
        
        termino_lower = termino.lower().strip()
        resultados = []
        
        for ejercicio in cls._cache:
            nombre = ejercicio.get('name', '')
            if not nombre:
                continue
            
            nombre_lower = nombre.lower()
            
            # Buscar en nombre
            if termino_lower in nombre_lower:
                resultados.append(ejercicio)
                continue
            
            # Buscar en músculos primarios
            primaria = ejercicio.get('primaryMuscles', [])
            if any(termino_lower in m.lower() for m in primaria):
                resultados.append(ejercicio)
                continue
            
            # Buscar en músculos secundarios
            secundaria = ejercicio.get('secondaryMuscles', [])
            if any(termino_lower in m.lower() for m in secundaria):
                resultados.append(ejercicio)
                continue
            
            # Buscar en equipamiento
            equipo = ejercicio.get('equipment', '')
            if equipo and termino_lower in equipo.lower():
                resultados.append(ejercicio)
                continue
        
        # Limitar resultados
        resultados = resultados[:limite]
        
        # Convertir al formato esperado
        ejercicios_formateados = [cls._formatear_ejercicio(ej) for ej in resultados]
        
        return {
            'success': True,
            'count': len(ejercicios_formateados),
            'ejercicios': ejercicios_formateados
        }
    
    @classmethod
    def _formatear_ejercicio(cls, ejercicio):
        """Convierte el formato de free-exercise-db al formato esperado"""
        images = ejercicio.get('images', [])
        image_url = ''
        
        if images and len(images) > 0:
            img_path = images[0]
            image_url = IMAGE_BASE_URL + img_path
        
        # Músculos (traducidos)
        primaria = ejercicio.get('primaryMuscles', [])
        secundaria = ejercicio.get('secondaryMuscles', [])
        
        # Traducir músculos
        primaria_traducida = [traducir_texto(m) for m in primaria]
        secundaria_traducida = [traducir_texto(m) for m in secundaria]
        
        # Categoría (traducida)
        categoria = traducir_texto(ejercicio.get('category', 'strength'))
        
        # Equipment (traducido)
        equipment = traducir_texto(ejercicio.get('equipment', ''))
        
        # Instructions (convertir a descripción) - traducir con API
        instructions = ejercicio.get('instructions', [])
        descripcion_original = ' - '.join(instructions) if instructions else ''
        # Usar la nueva función de traducción con MyMemory API
        descripcion = traducir_descripcion_api(descripcion_original)
        
        # Nivel (traducido)
        nivel = traducir_texto(ejercicio.get('level', 'intermediate'))
        
        # Fuerza y mecánico (traducidos)
        fuerza = traducir_texto(ejercicio.get('force', ''))
        mecanico = traducir_texto(ejercicio.get('mechanic', ''))
        
        # Nombre del ejercicio (traducido si existe)
        nombre_original = ejercicio.get('name', '')
        nombre = traducir_texto(nombre_original)
        
        return {
            'id': ejercicio.get('id', ''),
            'uuid': ejercicio.get('id', ''),
            'nombre': nombre,
            'descripcion': descripcion,
            'categoria': categoria,
            'categoria_id': 0,
            'muscles': [{'id': i, 'name': m, 'name_en': p} for i, (m, p) in enumerate(zip(primaria_traducida, primaria))],
            'muscles_secondary': [{'id': i + len(primaria), 'name': m, 'name_en': s} for i, (m, s) in enumerate(zip(secundaria_traducida, secundaria))],
            'equipment': [equipment] if equipment else [],
            'images': [image_url] if image_url else [],
            'variations': 0,
            'level': nivel,
            'force': fuerza,
            'mechanic': mecanico,
        }
    
    @classmethod
    def obtener_ejercicios_aleatorios(cls, limite=12):
        """Obtiene ejercicios aleatorios"""
        cls._load_exercises()
        
        if not cls._cache:
            return {'success': False, 'error': 'No se pudieron cargar los ejercicios', 'ejercicios': []}
        
        # Mezclar y tomar
        random.shuffle(cls._cache)
        seleccionados = cls._cache[:limite]
        
        ejercicios_formateados = [cls._formatear_ejercicio(ej) for ej in seleccionados]
        
        return {
            'success': True,
            'count': len(ejercicios_formateados),
            'ejercicios': ejercicios_formateados
        }
    
    @classmethod
    def obtener_por_musculo(cls, musculo, limite=20):
        """Obtiene ejercicios por grupo muscular"""
        cls._load_exercises()
        
        if not cls._cache:
            return {'success': False, 'error': 'No se pudieron cargar los ejercicios', 'ejercicios': []}
        
        musculo_lower = musculo.lower()
        resultados = []
        
        for ejercicio in cls._cache:
            primaria = ejercicio.get('primaryMuscles', [])
            if any(musculo_lower in m.lower() for m in primaria):
                resultados.append(ejercicio)
        
        resultados = resultados[:limite]
        ejercicios_formateados = [cls._formatear_ejercicio(ej) for ej in resultados]
        
        return {
            'success': True,
            'count': len(ejercicios_formateados),
            'ejercicios': ejercicios_formateados
        }
    
    @classmethod
    def obtener_todos_los_musculos(cls):
        """Obtiene lista de todos los grupos musculares únicos"""
        cls._load_exercises()
        
        if not cls._cache:
            return []
        
        musculos = set()
        for ejercicio in cls._cache:
            for m in ejercicio.get('primaryMuscles', []):
                musculos.add(m)
            for m in ejercicio.get('secondaryMuscles', []):
                musculos.add(m)
        
        return sorted(list(musculos))


# Funciones de compatibilidad con el código anterior
def buscar_ejercicios(termino, limite=20):
    """Busca ejercicios - función de compatibilidad"""
    return FreeExerciseDB.buscar_ejercicios(termino, limite)

def obtener_ejercicios(limite=20, categoria=None):
    """Obtiene ejercicios - función de compatibilidad"""
    return FreeExerciseDB.obtener_ejercicios_aleatorios(limite)

def obtener_ejercicios_por_categoria(categoria_id, limite=20):
    """Obtiene ejercicios por categoría"""
    # La API de free-exercise-db no tiene categorías como tal
    # Mapeamos IDs a grupos musculares
    mapa_categorias = {
        1: 'chest',
        2: 'legs',
        3: 'back',
        4: 'shoulders',
        5: 'arms',
        6: 'abs',
        7: 'cardio',
    }
    musculo = mapa_categorias.get(categoria_id, '')
    if musculo:
        return FreeExerciseDB.obtener_por_musculo(musculo, limite)
    return FreeExerciseDB.obtener_ejercicios_aleatorios(limite)

def obtener_ejercicio_por_id(ejercicio_id):
    """Obtiene un ejercicio específico por ID"""
    cls = FreeExerciseDB
    cls._load_exercises()
    
    if not cls._cache:
        return None
    
    for ejercicio in cls._cache:
        if ejercicio.get('id') == ejercicio_id:
            return cls._formatear_ejercicio(ejercicio)
    return None

def obtener_categorias():
    """Obtiene las categorías disponibles"""
    return {
        'success': True,
        'categorias': [
            {'id': 1, 'name': 'Pecho'},
            {'id': 2, 'name': 'Espalda'},
            {'id': 3, 'name': 'Piernas'},
            {'id': 4, 'name': 'Hombros'},
            {'id': 5, 'name': 'Brazos'},
            {'id': 6, 'name': 'Abdomen'},
            {'id': 7, 'name': 'Cardio'},
        ]
    }


# Alias para compatibilidad con código existente
class WgerService:
    """Alias para compatibilidad - usa FreeExerciseDB"""
    
    @classmethod
    def buscar_ejercicios(cls, termino, limite=20):
        return FreeExerciseDB.buscar_ejercicios(termino, limite)
    
    @classmethod
    def obtener_ejercicios(cls, limite=20, categoria=None):
        return FreeExerciseDB.obtener_ejercicios_aleatorios(limite)
    
    @classmethod
    def obtener_ejercicios_por_categoria(cls, categoria_id, limite=20):
        return FreeExerciseDB.obtener_ejercicios_por_categoria(categoria_id, limite)
    
    @classmethod
    def obtener_ejercicio_por_id(cls, ejercicio_id):
        return FreeExerciseDB.obtener_ejercicio_por_id(ejercicio_id)
    
    @classmethod
    def obtener_categorias(cls):
        return FreeExerciseDB.obtener_categorias()
