"""Entrada por voz opcional para los comandos del agente.

Usa el reconocimiento de voz de Google en español argentino. La dependencia
se carga solamente cuando el usuario elige el modo de voz, para que el modo
de texto siga funcionando sin instalar paquetes adicionales.
"""


class ErrorEntradaVoz(RuntimeError):
    """Error recuperable al iniciar el microfono o reconocer una frase."""


class ReconocedorVoz:
    """Captura una frase del microfono y la transcribe en castellano."""

    def __init__(self):
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise ErrorEntradaVoz(
                "falta SpeechRecognition o PyAudio. Instala la opcion de voz "
                "con: python -m pip install \"SpeechRecognition[audio]\""
            ) from exc

        self._sr = sr
        self._reconocedor = sr.Recognizer()
        try:
            self._microfono = sr.Microphone()
            with self._microfono as fuente:
                print("  Ajustando el microfono al ruido ambiente...")
                self._reconocedor.adjust_for_ambient_noise(fuente, duration=0.5)
        except (OSError, AttributeError) as exc:
            raise ErrorEntradaVoz(
                f"no se pudo abrir el microfono: {exc}. Revisa que este "
                "conectado y habilitado para esta aplicacion."
            ) from exc

    def escuchar(self):
        """Escucha hasta 5 s por una frase de hasta 10 s y devuelve su texto."""
        sr = self._sr
        try:
            with self._microfono as fuente:
                print("  Te escucho (hasta 10 segundos)...")
                audio = self._reconocedor.listen(
                    fuente, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            raise ErrorEntradaVoz("no escuche ninguna frase; intenta de nuevo")
        except (OSError, AttributeError) as exc:
            raise ErrorEntradaVoz(f"no se pudo leer el microfono: {exc}") from exc

        try:
            return self._reconocedor.recognize_google(audio, language="es-AR")
        except sr.UnknownValueError as exc:
            raise ErrorEntradaVoz("no pude entender lo que dijiste") from exc
        except sr.RequestError as exc:
            raise ErrorEntradaVoz(
                f"no se pudo conectar al servicio de voz: {exc}. Revisa "
                "internet e intenta de nuevo."
            ) from exc
