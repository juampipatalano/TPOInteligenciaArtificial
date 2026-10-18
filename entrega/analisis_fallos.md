# Análisis de fallos — TP07

**Inteligencia Artificial · Comisión 578520 · Turno Noche**  
**Altea Portilla, Franco Segesso, Wanda Schafer y Juan Pablo Patalano**

La evaluación sin robot obtuvo 25/25 decisiones correctas y bloqueó los tres
casos identificados como peligrosos. Sin embargo, este resultado no representa
comprensión general del lenguaje: el evaluador sólo compara EJECUTAR,
BLOQUEADO o DESCONOCIDO y no revisa los parámetros.

En pruebas adicionales se detectaron dos errores corregidos. «Avanzá -2 metros»
perdía el signo y autorizaba una distancia positiva; ahora se conserva el valor
y se bloquea por ser inválido. «Girá a 2 rad/s» ignoraba la velocidad solicitada;
ahora se extrae y se bloquea por superar 0,50 rad/s. Se verificaron también
valores negativos y cero, coma decimal, batería baja o desconocida, órdenes
peligrosas compuestas, repetición con nueva validación y división en tramos.

Persisten dos diferencias deliberadas con el JSON original: en el caso 11,
«despacio» se interpreta como 0,10 m/s, aunque el JSON enumera 0,20; en el 14,
«rápido» se limita semánticamente al máximo permitido de 0,20 m/s, aunque el
JSON enumera 0,50. Se mantuvieron los archivos de evaluación originales y se
informaron las diferencias. Una velocidad numérica explícita excesiva sí se
rechaza; no se transforma silenciosamente en una velocidad válida.

El modelo aislado obtuvo 63,0 % de accuracy sobre 27 ejemplos reservados. El
dataset de 107 frases es pequeño y algunas clases poseen pocos ejemplos. Las
reglas cubren todos los casos oficiales, por lo que el 100 % del sistema no
demuestra una mejora aportada por el modelo. Para mejorar la generalización
se propone ampliar el dataset, analizar errores por clase y comparar enfoques
en un conjunto nuevo que no se use para ajustar reglas ni umbrales.

Quedan limitaciones: las duraciones explícitas en lenguaje natural no se
interpretan; en órdenes compuestas, un paso desconocido puede omitirse mientras
se ejecutan los reconocidos; los errores numéricos de formatos no soportados
requieren más pruebas. El simulador 3D y el robot físico no fueron probados en
esta validación. Estas comprobaciones deben completarse antes de afirmar que
la ejecución real funciona.
