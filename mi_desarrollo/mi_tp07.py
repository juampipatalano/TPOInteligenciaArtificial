# =====================================================================
#  TP07 - Inteligencia Artificial
#  Agente que interpreta comandos en lenguaje natural
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Integrantes: Altea Portilla, Franco Segesso, Wanda Schafer,
#               Juan Pablo Patalano
#  Comision: 578520 - Turno Noche - Inteligencia Artificial
#
#  Que hace este agente, ademas de lo minimo:
#    - Nivel 1: reglas con `re` (siempre activas, son el respaldo).
#    - Nivel 2: Naive Bayes entrenado con dataset.csv. Solo se consulta
#      cuando las reglas no entienden, y solo si esta muy seguro.
#    - Memoria: "hacelo otra vez", "como antes pero mas despacio".
#    - Ordenes compuestas: "gira 45 grados y despues avanza 1 metro".
#    - Humanoide G1: saludo, mano, 67, baile, festejo y pose muscular.
#    - Bateria: si hay robot, no se mueve con menos del minimo.
# =====================================================================

import re
import unicodedata
from datetime import datetime, timezone

from robot import Robot

from ejecutor import Ejecutor
from evaluar import evaluar

INTEGRANTES = ("Altea Portilla", "Franco Segesso", "Wanda Schafer",
               "Juan Pablo Patalano")
ALUMNO = "; ".join(INTEGRANTES)
COMISION = "578520"
TURNO = "Noche"
MATERIA = "Inteligencia Artificial"


# =====================================================================
#  UTILIDAD COMPARTIDA - normalizar el texto
# =====================================================================
def normalizar(texto):
    """Minusculas, sin tildes, sin signos. "¿Cuánta batería?" -> "cuanta bateria".

    Las comas decimales ("0,5") se pasan a punto; las demas comas se van.
    Los simbolos de grado y la barra de "m/s" se conservan.
    """
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)
    t = re.sub(r"[¿?¡!,;:\"'()]", " ", t)
    t = re.sub(r"\.(?!\d)", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# El meme del "67": lo usan el clasificador y el extractor.
# "avanza 67 metros" es una distancia, no el gesto: por eso el lookahead.
GESTO_67 = (r"\b(?:67|6 7|seis siete|sesenta y siete|six seven)\b"
            r"(?!\s*(?:metros?|mts?|m\b|cm|centimetros?|grados?|°|º|km))")


# Conectores que separan una orden compuesta en pasos.
_VERBOS_INICIO = (r"gir|avanz|avanc|camin|salud|bail|festej|celebr|flex|"
                  r"mov|muev|retroced|and|par|fren|deten|rot|dobl|volv|da|hac")
_SEPARADOR = re.compile(
    r"\s*\b(?:y\s+)?(?:despues|luego|entonces)\b\s*"
    rf"|\s+y\s+(?=(?:{_VERBOS_INICIO}))")


def partir_en_pasos(texto_normalizado):
    """ "gira 45 grados y despues avanza" -> ["gira 45 grados", "avanza"]."""
    pasos = [p.strip() for p in _SEPARADOR.split(texto_normalizado)]
    return [p for p in pasos if p] or [texto_normalizado]


# =====================================================================
#  ETAPA 1 - CLASIFICADOR DE INTENCION
# =====================================================================
class ClasificadorIntencion:
    """Decide QUE quiere el usuario, sin mirar los numeros todavia."""

    TIPOS = ("MOVER", "GIRAR", "DETENERSE", "SALUDO", "GESTO",
             "CONSULTAR_ESTADO", "DESCONOCIDO")

    # Las reglas se prueban en este orden. Frenar va primero: "no avances"
    # contiene "avanc", y es justamente lo contrario de moverse.
    REGLAS_FRENAR = (
        r"\bno (?:te )?(?:avances|avance|muevas|mueva|camines|sigas|gires|"
        r"gire|andes|vayas)\b",
        r"\b(?:deten\w*|frena\w*|frene|quiet[oa]s?|stop|alto|basta|parate|"
        r"pare|emergencia|cortala|quedate)\b",
        r"\bdeja(?:r)? de\b",
        # "para" es ambiguo: "para todo" frena, "anda para atras" no.
        r"^para\b(?!\s+(?:atras|adelante|la|el|los|las|aca|alla|el costado))",
        r"\bpara (?:todo|ya|ahi|ahora|ahi mismo)\b",
    )
    REGLAS_ESTADO = (
        r"\b(?:bateria|carga|estado|posicion|ubicacion|reporte|telemetria)\b",
        r"\bcomo (?:estas|andas|te encontras|va)\b(?!.*\bllam)",
        r"\bdonde (?:estas|te encontras)\b",
    )
    REGLAS_SALUDO = (
        r"\bsalud\w*",
        r"\b(?:hace|hacele|haceles|deci|decile|deciles)\s+(?:hola|chau)\b",
        r"\b(?:da|dame|dar|dame|dale)\s+(?:la|una)\s+mano\b",
        r"\b(?:chau|adios|bienvenid\w*)\b",
        # El gesto del "67" (six seven).
        GESTO_67,
        # "hola" solo, sin pregunta atras: "hola, como te llamas?" NO es
        # una orden de saludar, es una charla fuera de dominio.
        r"^(?:hola|buenas|buen dia|buenas tardes|buenas noches)"
        r"(?: (?:robot|a todos|a todas|chicos|clase|g1))?$",
    )
    REGLAS_GESTO = (
        r"\b(?:bail\w*|bailecito|danza)\b",
        r"\b(?:festej\w*|celebr\w*)\b",
        r"\b(?:pose|fisicocultur\w*|culturist\w*|muscul\w*|biceps)\b",
        r"\bflexiona los brazos\b",
    )
    REGLAS_GIRAR = (
        r"\b(?:gir\w*|rot\w*|volte\w*|vuelta|dobl\w*)\b",
    )
    REGLAS_MOVER = (
        r"\b(?:avanz\w*|avanc\w*|mov\w*|muev\w*|camin\w*|anda|andate|"
        r"adelante|retroced\w*|atras|desplaz\w*|veni|acercate|alejate|"
        r"segui|sigue|recorre\w*)\b",
    )

    # Umbral para aceptar lo que dice el modelo cuando las reglas no saben.
    # Es alto a proposito: con ~100 ejemplos el Naive Bayes es muy
    # confiado aun cuando se equivoca ("hace silencio" -> SALUDO al 96 %).
    UMBRAL_MODELO = 0.97

    def __init__(self, usar_modelo=True):
        self.modelo = None
        self.ultima_confianza = 0.0

        # NIVEL 2: el modelo entrenado con dataset.csv. Si no hay
        # scikit-learn o no hay dataset, se sigue solo con reglas.
        if usar_modelo:
            try:
                from entrenar import entrenar_desde_csv
                self.modelo = entrenar_desde_csv()
            except Exception:                                # noqa: BLE001
                self.modelo = None

    @staticmethod
    def _primera(reglas, texto):
        """Posicion del primer match de cualquiera de las reglas, o None."""
        pos = [m.start() for r in reglas for m in [re.search(r, texto)] if m]
        return min(pos) if pos else None

    def clasificar_por_reglas(self, texto):
        t = normalizar(texto)
        if self._primera(self.REGLAS_FRENAR, t) is not None:
            return "DETENERSE", 0.95
        if self._primera(self.REGLAS_ESTADO, t) is not None:
            return "CONSULTAR_ESTADO", 0.9
        if self._primera(self.REGLAS_GESTO, t) is not None:
            return "GESTO", 0.95
        if self._primera(self.REGLAS_SALUDO, t) is not None:
            return "SALUDO", 0.9

        # MOVER y GIRAR pueden aparecer juntos: gana el que aparece primero.
        girar = self._primera(self.REGLAS_GIRAR, t)
        mover = self._primera(self.REGLAS_MOVER, t)
        if girar is not None and (mover is None or girar <= mover):
            return "GIRAR", 0.9
        if mover is not None:
            return "MOVER", 0.9
        return "DESCONOCIDO", 0.0

    def clasificar(self, texto):
        """Devuelve una de las intenciones de TIPOS.

        Reglas primero, porque son explicables y no alucinan. Si las reglas
        no reconocen nada, se le pregunta al modelo entrenado, que generaliza
        mejor a redacciones nuevas ("dale para adelante"). Solo se acepta si
        esta muy seguro: ante la duda, DESCONOCIDO.
        """
        tipo, confianza = self.clasificar_por_reglas(texto)

        if tipo == "DESCONOCIDO" and self.modelo is not None:
            probas = self.modelo.predict_proba([texto])[0]
            i = probas.argmax()
            candidato = self.modelo.classes_[i]
            if candidato != "DESCONOCIDO" and probas[i] >= self.UMBRAL_MODELO:
                tipo, confianza = candidato, float(probas[i])

        self.ultima_confianza = confianza
        return tipo


# =====================================================================
#  ETAPA 2 - EXTRACTOR DE PARAMETROS
# =====================================================================
_NUMEROS_ESCRITOS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "medio": 0.5, "media": 0.5, "cien": 100,
}
_NUM = (r"(?<![\w.])([+-]?\d+(?:\.\d+)?|"
        + "|".join(sorted(_NUMEROS_ESCRITOS, key=len, reverse=True)) + r")")


def _a_numero(palabra):
    if palabra in _NUMEROS_ESCRITOS:
        return float(_NUMEROS_ESCRITOS[palabra])
    return float(palabra)


class ExtractorParametros:
    """Saca los numeros del texto. Sigue en unidades humanas."""

    VELOCIDAD_LENTA = 0.10     # m/s para "despacio"
    DISTANCIA_CORTA = 0.30     # m para "un poco"

    def __init__(self, velocidad_max=0.20):
        # "rapido" significa la maxima que permite la materia, no mas.
        self.velocidad_max = velocidad_max

    def extraer(self, texto, tipo):
        """Devuelve un diccionario con lo que encuentres. Todo es opcional.

            {"distancia_m": 2.0}                  de "2 metros"
            {"angulo_deg": 90}                    de "90 grados" o "90°"
            {"velocidad_ms": 0.2}                 de "a 0.2 m/s"
            {"direccion": "derecha"}              de "a la derecha"
            {"direccion": "atras"}                de "retrocede"
            {"gesto": "mano"}                     de "dame la mano"
        """
        t = normalizar(texto)
        p = {}

        # Se separa antes de las velocidades lineales para conservar la unidad.
        m = re.search(_NUM + r"\s*(?:rad/s|rads|radianes? por segundo)", t)
        if m:
            p["velocidad_giro"] = _a_numero(m.group(1))
            t = t[:m.start()] + " " + t[m.end():]

        # --- velocidad: primero, y se borra, para que "2 m/s" no se lea
        #     despues como "2 m" de distancia.
        m = re.search(_NUM + r"\s*(?:m/s|mps|metros? por segundo)", t)
        if m:
            p["velocidad_ms"] = _a_numero(m.group(1))
            t = t[:m.start()] + " " + t[m.end():]
        m = re.search(_NUM + r"\s*(?:km/h|kmh|kilometros? por hora)", t)
        if m:
            p["velocidad_ms"] = round(_a_numero(m.group(1)) / 3.6, 3)
            t = t[:m.start()] + " " + t[m.end():]

        if "velocidad_ms" not in p:
            if re.search(r"\b(?:despac\w*|lent\w*|tranqui\w*|suave\w*)\b", t):
                p["velocidad_ms"] = self.VELOCIDAD_LENTA
            elif re.search(r"\b(?:rapid\w*|velo\w*|ligero|apurad\w*)\b", t):
                p["velocidad_ms"] = self.velocidad_max

        # --- distancia
        m = re.search(_NUM + r"\s*(centimetros?|cm)\b", t)
        if m:
            p["distancia_m"] = _a_numero(m.group(1)) / 100.0
        else:
            m = re.search(_NUM + r"\s*(?:metros?|mts?|m)\b", t)
            if m:
                p["distancia_m"] = _a_numero(m.group(1))
                if re.search(r"\bmetros? y medio\b", t[m.start():]):
                    p["distancia_m"] += 0.5
            elif re.search(r"\b(?:un poco|un poquito|un toque|apenas)\b", t):
                p["distancia_m"] = self.DISTANCIA_CORTA

        # --- angulo
        m = re.search(_NUM + r"\s*(?:°|º|grados?)", t)
        if m:
            p["angulo_deg"] = _a_numero(m.group(1))
        elif re.search(r"\bmedia vuelta\b", t):
            p["angulo_deg"] = 180
        elif re.search(r"\bcuarto de vuelta\b", t):
            p["angulo_deg"] = 90
        elif re.search(r"\bvuelta (?:entera|completa)\b|\buna vuelta\b|\bgira en el lugar\b", t):
            p["angulo_deg"] = 360

        # --- direccion
        if re.search(r"\bderech\w*\b", t):
            p["direccion"] = "derecha"
        elif re.search(r"\bizquierd\w*\b", t):
            p["direccion"] = "izquierda"
        elif re.search(r"\b(?:retroced\w*|atras|reversa)\b", t):
            p["direccion"] = "atras"

        # --- gesto del humanoide
        if tipo == "SALUDO" and re.search(r"\bmano\b", t):
            p["gesto"] = "mano"
        if tipo == "SALUDO" and re.search(GESTO_67, t):
            p["gesto"] = "67"
        if tipo == "GESTO":
            if re.search(r"\b(?:bail\w*|bailecito|danza)\b", t):
                p["gesto"] = "baile"
            elif re.search(r"\b(?:festej\w*|celebr\w*)\b", t):
                p["gesto"] = "festejo"
            elif re.search(
                    r"\b(?:pose|fisicocultur\w*|culturist\w*|muscul\w*|"
                    r"biceps)\b|\bflexiona los brazos\b", t):
                p["gesto"] = "pose_fisicoculturista"

        # Los enteros quedan enteros: 90 y no 90.0, es mas legible.
        for k in ("angulo_deg",):
            if k in p and float(p[k]).is_integer():
                p[k] = int(p[k])
        return p


# =====================================================================
#  ETAPA 3 - VALIDADOR DE SEGURIDAD
# =====================================================================
class ValidadorSeguridad:
    """La ultima barrera antes del robot.

    Este es el corazon del TP. Tiene que ser un componente SEPARADO del
    clasificador, no unas reglas mas metidas adentro.

    El motivo: tu clasificador se va a equivocar. Todos se equivocan. Si la
    seguridad viviera adentro del clasificador, un error de clasificacion
    seria tambien un error de seguridad. Separandolos, un error de
    clasificacion sigue siendo bloqueado.
    """

    # Palabras que describen acciones que el robot no debe intentar nunca.
    PALABRAS_PELIGROSAS = ("salta", "salto", "corre", "corré", "sprint",
                           "empuja", "empujá", "golpea", "rompe", "tira",
                           "cae", "fuerza")

    # Lo mismo, como patrones sobre el texto normalizado (sin tildes). Cubre
    # las conjugaciones: "saltá", "saltar", "corras", "empujala", "tirate".
    PATRONES_PELIGROSOS = (
        r"\bsalt\w*",
        r"\bcorr(?:e|er|a|as|an|es|en|iendo|ete|ite)\b",
        r"\bsprint\w*",
        r"\bempuj\w*",
        r"\bgolpe\w*",
        r"\bromp\w*",
        r"\btir(?:a|ar|ate|alo|ala|en|es)\b",
        r"\bca(?:e|er|ete|igas|erte)\b",
        r"\b(?:fuerz\w*|forz\w*)",
        r"\bpate\w*",
        r"\b(?:trep\w*|escal(?:a|ar|es)\b)",
        r"\b(?:lanz\w*|arroj\w*|atropell\w*|choc\w*)",
        r"\b(?:pegale|pegales|pega a|lastim\w*|ataca\w*)\b",
        r"\bsub\w*\b.*\b(?:mesa|silla|escritorio|escalera|baranda)\b",
        r"\b(?:desde|de) la (?:mesa|silla|escalera|ventana)\b",
    )

    # En un aula no tiene sentido ir mas lejos que esto de una sola vez.
    DISTANCIA_MAX_M = 5.0
    ANGULO_MAX_DEG = 180
    TIPOS_QUE_MUEVEN = ("MOVER", "GIRAR", "SALUDO", "GESTO")

    def __init__(self, perfil, leer_bateria=None):
        # perfil trae los limites de tu materia:
        #   perfil.velocidad_max          m/s
        #   perfil.velocidad_angular_max  rad/s
        #   perfil.duracion_max           segundos por orden
        #   perfil.bateria_min            porcentaje
        self.perfil = perfil
        # Funcion que devuelve la bateria en %. None = sin robot (modo
        # --sin-robot), y entonces la bateria no se puede revisar.
        self.leer_bateria = leer_bateria

    def palabra_peligrosa(self, texto):
        t = normalizar(texto)
        for patron in self.PATRONES_PELIGROSOS:
            m = re.search(patron, t)
            if m:
                return m.group(0)
        return None

    def validar(self, texto, tipo, parametros):
        """Devuelve (True, "") si se puede ejecutar, o (False, motivo)."""
        p = parametros or {}

        # 1. Palabras peligrosas en el TEXTO ORIGINAL, entienda o no el
        #    clasificador. Esto va primero y no tiene excepciones.
        peligro = self.palabra_peligrosa(texto)
        if peligro:
            return False, f"palabra peligrosa: '{peligro}'"

        # 2. Velocidad lineal.
        v = p.get("velocidad_ms")
        if v is not None:
            if v <= 0:
                return False, f"velocidad invalida ({v} m/s)"
            if v > self.perfil.velocidad_max + 1e-9:
                return False, (f"velocidad {v:g} m/s > maximo "
                               f"{self.perfil.velocidad_max:g} m/s")

        # 3. Velocidad de giro.
        w = p.get("velocidad_giro")
        if w is not None and w <= 0:
            return False, f"velocidad de giro invalida ({w} rad/s)"
        if w is not None and abs(w) > self.perfil.velocidad_angular_max + 1e-9:
            return False, (f"velocidad de giro {w:g} rad/s > maximo "
                           f"{self.perfil.velocidad_angular_max:g} rad/s")

        # 4. Distancia razonable para un aula.
        d = p.get("distancia_m")
        if d is not None:
            if d <= 0:
                return False, f"distancia invalida ({d} m)"
            if d > self.DISTANCIA_MAX_M:
                return False, (f"distancia {d:g} m > maximo "
                               f"{self.DISTANCIA_MAX_M:g} m en el aula")

        # 5. Angulo.
        a = p.get("angulo_deg")
        if a is not None:
            if a <= 0:
                return False, f"angulo invalido ({a} grados)"
            if a > self.ANGULO_MAX_DEG:
                return False, (f"angulo {a:g} grados > maximo "
                               f"{self.ANGULO_MAX_DEG} grados")

        # 6. Bateria. Solo para lo que mueve el robot: frenar y consultar
        #    tienen que andar SIEMPRE, sobre todo con poca bateria.
        if tipo in self.TIPOS_QUE_MUEVEN and self.leer_bateria is not None:
            try:
                bateria = self.leer_bateria()
            except Exception:                                # noqa: BLE001
                bateria = None
            if bateria is None:
                # Fail-closed: bateria desconocida no es bateria segura.
                return False, "bateria desconocida: no se mueve"
            if bateria < self.perfil.bateria_min:
                return False, (f"bateria {bateria}% < minimo "
                               f"{self.perfil.bateria_min}%")

        return True, ""


# =====================================================================
#  EJECUTOR DEL HUMANOIDE - extiende el que viene dado, sin tocarlo
# =====================================================================
class EjecutorHumanoide(Ejecutor):
    """Agrega los gestos del G1 al ejecutor de la catedra.

    "dame la mano" -> ShakeHand. Si el robot no tiene manos (Go2), saluda.
    Las nuevas rutinas GESTO son solo para el G1 del simulador.
    """

    def ejecutar(self, tipo, parametros):
        parametros = parametros or {}
        if tipo == "SALUDO" and parametros.get("gesto") == "mano":
            try:
                self.robot.dar_la_mano()
                return "dio la mano"
            except NotImplementedError:
                pass   # el Go2 no tiene manos: cae al saludo normal
        if tipo == "SALUDO" and parametros.get("gesto") == "67":
            try:
                self.robot.hacer_67()
                return "hizo el 67"
            except NotImplementedError:
                pass
        if tipo == "GESTO":
            rutina = {
                "baile": self.robot.hacer_baile,
                "festejo": self.robot.festejar,
                "pose_fisicoculturista": self.robot.posar_fisicoculturista,
            }.get(parametros.get("gesto"))
            if rutina is None:
                return "no reconoci ese gesto"
            try:
                rutina()
                return {
                    "baile": "baile iniciado",
                    "festejo": "festejo iniciado",
                    "pose_fisicoculturista": "pose de doble biceps activa",
                }[parametros["gesto"]]
            except NotImplementedError as exc:
                return str(exc)
        if tipo == "CONSULTAR_ESTADO":
            e = self.robot.verificar_estado()
            return f"estado: {e}  bateria={e.bateria}%"
        return super().ejecutar(tipo, parametros)


# =====================================================================
#  EL AGENTE - une las tres etapas y llama al ejecutor
# =====================================================================
_REPETIR = re.compile(r"\b(?:otra vez|de nuevo|nuevamente|repeti\w*|repetilo|"
                      r"lo mismo|como antes|hacelo de vuelta)\b")


class AgenteRobot:
    def __init__(self, robot=None, usar_modelo=True):
        self.robot = robot
        perfil = robot.perfil if robot else _perfil_por_defecto()
        self.clasificador = ClasificadorIntencion(usar_modelo=usar_modelo)
        self.extractor = ExtractorParametros(velocidad_max=perfil.velocidad_max)
        self.validador = ValidadorSeguridad(
            perfil,
            leer_bateria=(lambda: robot.verificar_estado().bateria) if robot else None)
        self.ejecutor = EjecutorHumanoide(robot) if robot else None
        self.historial = []
        self.ultimo_ejecutado = None     # (tipo, parametros) para la memoria

    # ---------- interpretacion ----------
    def _interpretar(self, paso):
        """Un paso de texto -> (tipo, parametros, confianza).

        Si pide repetir, se reusa la ultima orden ejecutada, y lo nuevo
        que diga ("pero mas despacio") pisa lo anterior.
        """
        if _REPETIR.search(paso) and self.ultimo_ejecutado is not None:
            tipo, anteriores = self.ultimo_ejecutado
            nuevos = self.extractor.extraer(paso, tipo)
            return tipo, {**anteriores, **nuevos}, 0.8

        tipo = self.clasificador.clasificar(paso)
        confianza = self.clasificador.ultima_confianza
        parametros = self.extractor.extraer(paso, tipo)
        return tipo, parametros, confianza

    def procesar(self, texto):
        """El pipeline completo. ESTA ES LA FUNCION QUE SE TE EVALUA.

        clasificar -> extraer -> validar -> ejecutar, para cada paso de la
        orden. El validador corre SIEMPRE, aunque el tipo sea DESCONOCIDO, y
        si UN paso no pasa no se ejecuta NINGUNO: no se hace media orden.
        """
        pasos = partir_en_pasos(normalizar(texto))
        interpretados = [self._interpretar(p) for p in pasos]

        tipo, parametros, confianza = interpretados[0]
        respuesta = {
            "tipo": tipo,
            "parametros": parametros,
            "ejecutar": False,
            "bloqueado": False,
            "confianza": round(confianza, 2),
            "texto_original": texto,
            "mensaje": "",
        }
        if len(interpretados) > 1:
            respuesta["pasos"] = [{"tipo": t, "parametros": p}
                                  for t, p, _ in interpretados]

        # --- validar: el texto completo y cada paso. Sin excepciones.
        for t, p, _ in interpretados:
            ok, motivo = self.validador.validar(texto, t, p)
            if not ok:
                respuesta["bloqueado"] = True
                respuesta["mensaje"] = f"BLOQUEADO: {motivo}"
                self._registrar(respuesta)
                return respuesta

        # --- lo que se entiende se ejecuta; lo que no, no.
        ejecutables = [(t, p) for t, p, _ in interpretados if t != "DESCONOCIDO"]
        if not ejecutables:
            respuesta["mensaje"] = "no entendi la orden (fuera de dominio)"
            self._registrar(respuesta)
            return respuesta

        respuesta["ejecutar"] = True
        if self.ejecutor is None:
            respuesta["mensaje"] = "valido (sin robot: no se ejecuta)"
        else:
            resultados = [self.ejecutor.ejecutar(t, p) for t, p in ejecutables]
            respuesta["mensaje"] = " | ".join(resultados)

        # La memoria solo guarda movimientos: "otra vez" despues de frenar
        # no tiene que volver a frenar sino repetir lo ultimo que hizo.
        for t, p in ejecutables:
            if t in ("MOVER", "GIRAR", "SALUDO", "GESTO"):
                self.ultimo_ejecutado = (t, dict(p))
        self._registrar(respuesta)
        return respuesta

    def _registrar(self, respuesta):
        respuesta["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        self.historial.append(respuesta)


def _perfil_por_defecto():
    """Permite evaluar el agente sin abrir el simulador."""
    import sys
    from pathlib import Path
    entorno = Path(__file__).resolve().parent.parent / "entorno"
    if str(entorno) not in sys.path:
        sys.path.insert(0, str(entorno))
    from sim.safety import perfil
    return perfil("tp07")


# =====================================================================
#  PROGRAMA PRINCIPAL - no hace falta que lo toques
# =====================================================================
def main():
    import sys

    # Modo sin robot: solo evalua los 25 casos. Sirve para trabajar el
    # clasificador sin tener el simulador abierto.
    sin_robot = "--sin-robot" in sys.argv
    modo_voz = "--voz" in sys.argv

    robot = None
    if not sin_robot:
        robot = Robot()
        robot.conectar()

    try:
        agente = AgenteRobot(robot)
        print(f"\n  {MATERIA} - Comision {COMISION} - Turno {TURNO}")
        print(f"  Integrantes: {ALUMNO}")
        evaluar(agente)

        if robot is not None:
            from interfaz import InterfazComandos

            InterfazComandos(agente, robot, modo_voz=modo_voz).iniciar()
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    main()
