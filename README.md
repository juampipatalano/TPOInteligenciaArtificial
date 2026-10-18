# TP07 — Inteligencia Artificial

**Comisión 578520 · Turno Noche**  
**Altea Portilla · Franco Segesso · Wanda Schafer · Juan Pablo Patalano**

Agente en castellano para el robot Unitree: clasifica intenciones, extrae
parámetros, valida seguridad y ejecuta órdenes. Funciona por consola; el
simulador proporciona la visualización del robot.

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

Para el simulador seguir [INSTALACION.md](INSTALACION.md), abrir
`INICIAR_SIMULADOR` y luego `EJECUTAR_MI_CODIGO`. El modo interactivo aparece
después de la evaluación. La prueba visual con simulador está pendiente; las
evidencias guardadas corresponden a ejecución sin robot y a un robot de prueba.

`PLAN_TP07.md` es un plan histórico del material del laboratorio; su encabezado
«sin implementar» no describe el estado actual del agente del grupo. Los
requisitos utilizados para esta entrega provienen de `LEEME_ESTUDIANTE.md`.
