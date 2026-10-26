# TP07 — Inteligencia Artificial

**Comisión 578520 · Turno Noche**  
**Altea Portilla · Franco Segesso · Wanda Schafer · Juan Pablo Patalano**

Agente en castellano para el robot Unitree: clasifica intenciones, extrae
parámetros, valida seguridad y ejecuta órdenes. Incluye una interfaz de
escritorio para escribir comandos o cambiar al micrófono. El simulador
proporciona la visualización del robot.

## Ejecutar sin robot

```bash
python mi_desarrollo/mi_tp07.py --sin-robot
```

No requiere dependencias externas para el enfoque de reglas. Para activar
la extensión Naive Bayes y reproducir su comparación, instalar scikit-learn:

```bash
python -m pip install scikit-learn
python mi_desarrollo/entrenar.py
```

## Evidencias y documentación

- [Informe técnico](entrega/informe_tecnico.md).
- [Análisis de fallos y limitaciones](entrega/analisis_fallos.md).
- [Reporte de accuracy y diferencias de parámetros](entrega/reporte_accuracy.md).
- [Resultados CSV](entrega/resultados.csv) y [JSON](entrega/resultados.json).
- [Registro de pruebas adicionales](entrega/validacion_adicional.txt).

Para regenerar los reportes y ejecutar las regresiones:

```bash
python mi_desarrollo/generar_reporte.py
python -m unittest discover -s mi_desarrollo -p "test_*.py" -v
```

Resultados registrados: 25/25 decisiones correctas con reglas y con el
híbrido; 3/3 peligrosos bloqueados; 7 tests adicionales correctos. El modelo
aislado obtuvo 63,0 % de accuracy en 27 frases reservadas de 107 ejemplos.
El evaluador oficial no comprueba intención ni parámetros: el reporte informa
por separado las diferencias de los casos 11 y 14. La versión de Python y
scikit-learn usada para medir se encuentra en `entrega/resultados.json`.

## Entrega y uso con simulador

Entregar la carpeta `mi_desarrollo` con sus dependencias locales, el dataset y
los documentos de `entrega`. `tp07_schafer_wanda.py` es una entrada con apellido
que importa la implementación compartida; **no es un archivo independiente**.
No se cambiaron los lanzadores ni los archivos de evaluación originales.

Para probarlo, seguir [INSTALACION.md](INSTALACION.md), abrir
`INICIAR_SIMULADOR` y luego `EJECUTAR_MI_CODIGO`. La interfaz se abre después
de la evaluación.

Para usar el micrófono, instalar una vez:

```bash
python -m pip install "SpeechRecognition[audio]"
```

La interfaz abre en modo texto. Usá los botones **Texto** y **Voz** para
cambiar de modo; en modo voz, presioná **Escuchar comando** para dictar una
orden. El reconocimiento en español argentino envía el audio al servicio de
Google y requiere conexión a internet. También podés iniciar directamente en
modo voz con `python mi_desarrollo/mi_tp07.py --voz`.

El panel **Comandos disponibles** muestra ejemplos por categoría. Al pulsar
uno se carga en el campo de texto para editarlo; se ejecuta al presionar
**Enviar** o Enter. Los gestos que no admite el robot conectado aparecen
deshabilitados.

Con el **G1 del simulador** también podés decir "bailá", "festejá" o
"hacé una pose de fisicoculturista". Son gestos cortos de brazos que no
desplazan la base. No están habilitados en el Go2 ni en un robot físico.

`PLAN_TP07.md` es un plan histórico del material del laboratorio; su encabezado
«sin implementar» no describe el estado actual del agente del grupo. Los
requisitos utilizados para esta entrega provienen de `LEEME_ESTUDIANTE.md`.
