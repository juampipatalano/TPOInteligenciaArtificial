# Informe técnico — TP07: agente de lenguaje natural

**Materia:** Inteligencia Artificial · **Comisión:** 578520 · **Turno:** Noche  
**Integrantes:** Altea Portilla, Franco Segesso, Wanda Schafer y Juan Pablo Patalano

## Objetivo y enfoque

El sistema transforma órdenes escritas en castellano en acciones de un robot
Unitree. Distingue seis intenciones: MOVER, GIRAR, DETENERSE, SALUDO,
CONSULTAR_ESTADO y DESCONOCIDO. Una orden puede ejecutarse, rechazarse por
seguridad o quedar sin reconocer. La interacción se realiza mediante consola;
la guía suministrada no exige desarrollar una interfaz gráfica propia.

Se eligió un enfoque híbrido con reglas como primera opción y un clasificador
Naive Bayes opcional como respaldo. Las reglas permiten explicar las decisiones
y cubrir negaciones y expresiones frecuentes. El modelo se entrena con
`dataset.csv` mediante n-gramas de caracteres de 3 a 5 y se consulta cuando las
reglas devuelven DESCONOCIDO. Sólo se acepta una predicción reconocida con
probabilidad de al menos 0,97. Este valor es un umbral de decisión: no demuestra
una confianza calibrada. Si scikit-learn no está disponible, el sistema sigue
funcionando con reglas.

## Pipeline y responsabilidades

1. **ClasificadorIntencion.** Normaliza mayúsculas y tildes, reconoce patrones
   y determina la intención. Dentro de cada paso, prioriza detenerse frente a
   las otras intenciones para interpretar «no avances» como una detención.
2. **ExtractorParametros.** Extrae distancia en metros, ángulo en grados,
   velocidad lineal en m/s, velocidad angular en rad/s y dirección. Admite
   coma decimal y algunos números escritos. Conserva los signos numéricos;
   los valores negativos se consideran inválidos. Para retroceder se utiliza
   una distancia positiva con dirección «atrás».
3. **ValidadorSeguridad.** Comprueba palabras peligrosas, parámetros y batería.
   Se ejecuta siempre, incluso si la intención es DESCONOCIDO. También vuelve
   a validar las órdenes solicitadas por memoria.
4. **Ejecutor.** El componente provisto convierte metros y grados en velocidad
   y tiempo y envía las órdenes al robot. EjecutorHumanoide agrega gestos sin
   modificar el ejecutor base de la cátedra.

AgenteRobot coordina las etapas, conserva un historial en memoria con fecha
UTC y recuerda el último movimiento para pedidos como «otra vez». Las órdenes
compuestas se interpretan por pasos y todos se validan antes de ejecutar; si
alguno es bloqueado no se ejecuta ninguno. Los pasos desconocidos, en cambio,
pueden omitirse: es una limitación documentada, no un bloqueo de seguridad.

## Seguridad y conversión de unidades

El perfil TP07 establece velocidad lineal máxima de 0,20 m/s, velocidad angular
máxima de 0,50 rad/s, duración máxima de 5 segundos por orden y batería mínima
de 25 %. El agente limita además la distancia a 5 metros y el giro a 180°.
Para acciones que implican movimiento, una batería desconocida o inferior al
mínimo impide ejecutar. Detenerse y consultar no dependen de ese umbral.

El validador es independiente porque reconocer una intención no prueba que
su ejecución sea admisible. «Salta desde la mesa» debe bloquearse aunque el
clasificador no sepa ejecutarla. Separar ambos componentes permite reemplazar
reglas por un modelo sin delegar la seguridad en sus predicciones. La API del
robot incorpora además sus propias comprobaciones.

El ejecutor convierte distancia con tiempo = distancia / velocidad y ángulo
con tiempo = radianes / velocidad angular. Por ejemplo, 2 metros a 0,20 m/s
requieren 10 segundos, repartidos en dos órdenes de 5 segundos. La dirección
determina el signo de la velocidad enviada. Los negativos escritos por el
usuario no se utilizan para inferir un sentido automáticamente.

## Evaluación y resultados

Se conservaron sin cambios `evaluar.py` y `casos_prueba.json`. Tanto el agente
con sólo reglas como el híbrido alcanzaron 25/25 resultados finales correctos
(100 %), incluyendo los seis rechazos esperados y los tres casos que el
evaluador identifica específicamente como peligrosos. Siete pruebas
adicionales verificaron las correcciones numéricas, la batería, la repetición,
el bloqueo de órdenes compuestas y la división de movimientos mediante un
robot de prueba que registra llamadas; no se utilizó un robot físico.

El dataset contiene 107 ejemplos. Para el modelo aislado se realizó una
partición estratificada 75/25 con random_state=0: 80 ejemplos de entrenamiento
y 27 de prueba. Se obtuvo accuracy de 63,0 %, precisión macro de 64,2 %,
recall macro de 68,3 % y F1 macro de 65,2 %. Estas métricas evalúan intenciones
en otros textos y no son equivalentes a las decisiones finales del pipeline.
Con los casos actuales no se demostró una mejora del modelo sobre las reglas.

La comparación adicional de parámetros detectó diferencias en los casos 11
y 14. «Despacio» se interpreta como 0,10 m/s, en lugar de 0,20; «rápido» como
0,20 m/s, en lugar de 0,50, respetando el perfil vigente de la guía. El reporte
las muestra sin alterar el material de evaluación. El porcentaje oficial por
sí solo no comprueba parámetros ni desplazamientos físicos.

## Reproducción y alcance

Desde la raíz del repositorio, `python mi_desarrollo/mi_tp07.py --sin-robot`
ejecuta los casos. `python mi_desarrollo/generar_reporte.py` genera la tabla,
la comparación y las evidencias en Markdown, CSV y JSON. Las regresiones se
ejecutan con `python -m unittest discover -s mi_desarrollo -p "test_*.py" -v`.

La validación realizada cubre interpretación, decisiones y llamadas al ejecutor
con un sustituto de prueba. La prueba visual con simulador y la ejecución en
robot físico quedan pendientes. En la instancia física sólo deben utilizarse
los casos previamente validados, según la guía del TP.
