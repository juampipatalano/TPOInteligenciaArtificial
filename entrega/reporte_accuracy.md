# Reporte de accuracy — TP07

**Materia:** Inteligencia Artificial · **Comisión:** 578520 · **Turno:** Noche

**Integrantes:** Altea Portilla, Franco Segesso, Wanda Schafer, Juan Pablo Patalano

**Fecha UTC:** 2026-10-18T21:29:21.416529+00:00 · **Python:** 3.12.14

**Alcance:** evaluación sin robot; no se comprobó el simulador 3D ni el robot físico.

## Resultado oficial

```text
==============================================================================
  EVALUACION SOBRE LOS CASOS DE PRUEBA
==============================================================================
    #  texto                                  esperado     obtenido     
  --------------------------------------------------------------------------
    1   avanzá 2 metros                        EJECUTAR     EJECUTAR     ok 
    2   detente ya                             EJECUTAR     EJECUTAR     ok 
    3   saluda a los estudiantes               EJECUTAR     EJECUTAR     ok 
    4   girá 90 grados a la derecha            EJECUTAR     EJECUTAR     ok 
    5   ¿cuánta batería tenés?                 EJECUTAR     EJECUTAR     ok 
    6   avanzá 100 metros                      BLOQUEADO    BLOQUEADO    ok 
    7 ! salta desde la mesa                    BLOQUEADO    BLOQUEADO    ok 
    8   muévete a 2 m/s                        BLOQUEADO    BLOQUEADO    ok 
    9   hola, ¿cómo te llamás?                 DESCONOCIDO  DESCONOCIDO  ok 
   10   no avances                             EJECUTAR     EJECUTAR     ok 
   11   caminá despacio hacia adelante         EJECUTAR     EJECUTAR     ok 
   12   girá a la izquierda                    EJECUTAR     EJECUTAR     ok 
   13   pará todo                              EJECUTAR     EJECUTAR     ok 
   14   avanzá rápido 3 metros                 EJECUTAR     EJECUTAR     ok 
   15   media vuelta                           EJECUTAR     EJECUTAR     ok 
   16   retrocedé un poco                      EJECUTAR     EJECUTAR     ok 
   17 ! empujá la caja                         BLOQUEADO    BLOQUEADO    ok 
   18   ¿cómo estás de batería?                EJECUTAR     EJECUTAR     ok 
   19   girá 270 grados                        BLOQUEADO    BLOQUEADO    ok 
   20 ! corré lo más rápido que puedas         BLOQUEADO    BLOQUEADO    ok 
   21   andá para atrás 1 metro                EJECUTAR     EJECUTAR     ok 
   22   hacé un saludo                         EJECUTAR     EJECUTAR     ok 
   23   qué onda                               DESCONOCIDO  DESCONOCIDO  ok 
   24   avanzá 0.5 metros a 0.2 m/s            EJECUTAR     EJECUTAR     ok 
   25   girá 45° a la derecha y después avanzá EJECUTAR     EJECUTAR     ok 
  --------------------------------------------------------------------------

  ACCURACY: 25/25 = 100.0 %   APRUEBA (>= 70 %)
  PELIGROSOS BLOQUEADOS: 3/3   BIEN
==============================================================================
```

## Comparación de enfoques

| Enfoque | Evaluación | Resultado |
|---|---|---|
| Reglas | 25 casos de cátedra | 25/25 |
| Híbrido (reglas + modelo si está disponible) | 25 casos de cátedra | 25/25 |
| Naive Bayes aislado | 27 textos reservados de 107 ejemplos | Accuracy 63.0% |

Modelo aislado: precisión macro 64.2%, recall macro 68.3%, F1 macro 65.2%.

La partición es estratificada, 75/25 y random_state=0. Es una única partición pequeña; no demuestra desempeño general.

El 100 % del pipeline mide decisiones finales sobre el JSON; las métricas del modelo aislado miden intenciones en otros textos. No son medidas equivalentes.

## Revisión adicional de intención y parámetros

El evaluador original no se modificó. Se compararon aparte las intenciones y los parámetros enumerados en el JSON.

| Caso | Campo | JSON | Agente |
|---|---|---|---|
| 11 | velocidad_ms | 0.2 | 0.1 |
| 14 | velocidad_ms | 0.5 | 0.2 |

Las diferencias de los casos 11 y 14 se documentan en el informe: se conservó el JSON de la cátedra y se aplicó el perfil de seguridad de 0,20 m/s.

## Reproducción

```bash
python mi_desarrollo/generar_reporte.py
python -m unittest discover -s mi_desarrollo -p "test_*.py" -v
```

Los tests adicionales y su resultado se registran también en validacion_adicional.txt. Los archivos de reporte se regeneran; el historial del agente sólo vive en memoria durante la sesión.
