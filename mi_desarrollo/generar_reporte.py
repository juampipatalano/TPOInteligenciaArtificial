"""Genera evidencias reproducibles sin modificar el evaluador de la cátedra.

python mi_desarrollo/generar_reporte.py
Opcional: pip install scikit-learn para comparar el modelo en prueba reservada.
"""
import csv
import io
import json
import platform
import subprocess
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from evaluar import cargar_casos, evaluar
from mi_tp07 import AgenteRobot, COMISION, INTEGRANTES, MATERIA, TURNO

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'entrega'


def main():
    DESTINO.mkdir(exist_ok=True)
    reglas = AgenteRobot(usar_modelo=False)
    hibrido = AgenteRobot()
    captura = io.StringIO()
    with redirect_stdout(captura):
        resumen = evaluar(hibrido)
    solo_reglas = evaluar(reglas, mostrar=False)
    # El evaluador oficial compara resultados, no intención ni parámetros.
    # Esta revisión adicional informa diferencias sin cambiar el JSON dado.
    diferencias = []
    aislado = AgenteRobot(usar_modelo=False)
    for caso in cargar_casos():
        respuesta = aislado.procesar(caso['texto'])
        if respuesta['tipo'] != caso['intencion_esperada']:
            diferencias.append({'id': caso['id'], 'campo': 'tipo',
                                'esperado': caso['intencion_esperada'],
                                'obtenido': respuesta['tipo']})
        for clave, valor in caso.get('params_esperados', {}).items():
            if respuesta['parametros'].get(clave) != valor:
                diferencias.append({'id': caso['id'], 'campo': clave,
                                    'esperado': valor,
                                    'obtenido': respuesta['parametros'].get(clave)})

    modelo = {'disponible': hibrido.clasificador.modelo is not None}
    try:
        import sklearn
        from entrenar import cargar_dataset, entrenar, metricas
        from sklearn.model_selection import train_test_split
        textos, etiquetas = cargar_dataset()
        x_tr, x_te, y_tr, y_te = train_test_split(
            textos, etiquetas, test_size=0.25, random_state=0, stratify=etiquetas)
        modelo.update({'sklearn': sklearn.__version__, 'dataset': len(textos),
                       'entrenamiento': len(x_tr), 'prueba': len(x_te),
                       'metricas': metricas(entrenar(x_tr, y_tr), x_te, y_te)})
    except ImportError:
        modelo['nota'] = 'Sin scikit-learn: el pipeline funciona con reglas.'

    try:
        base = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=RAIZ, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        base = 'No disponible'
    datos = {'fecha_utc': datetime.now(timezone.utc).isoformat(),
             'commit_base_al_generar': base,
             'nota_commit': 'Los cambios locales del código también forman parte de esta corrida.',
             'python': platform.python_version(), 'integrantes': INTEGRANTES,
             'comision': COMISION, 'turno': TURNO, 'materia': MATERIA,
             'modo': 'sin robot; no valida movimiento físico ni ventana 3D',
             'hibrido': resumen, 'solo_reglas': solo_reglas,
             'diferencias_con_json': diferencias, 'modelo_aislado': modelo}
    (DESTINO / 'resultados.json').write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (DESTINO / 'resultados.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(resumen['filas'][0]))
        writer.writeheader()
        writer.writerows(resumen['filas'])

    lineas = ['# Reporte de accuracy — TP07', '',
              f'**Materia:** {MATERIA} · **Comisión:** {COMISION} · **Turno:** {TURNO}', '',
              '**Integrantes:** ' + ', '.join(INTEGRANTES), '',
              f"**Fecha UTC:** {datos['fecha_utc']} · **Python:** {datos['python']}", '',
              '**Alcance:** evaluación sin robot; no se comprobó el simulador 3D ni el robot físico.', '',
              '## Resultado oficial', '', '```text', captura.getvalue().strip(), '```', '',
              '## Comparación de enfoques', '',
              '| Enfoque | Evaluación | Resultado |', '|---|---|---|',
              f"| Reglas | 25 casos de cátedra | {solo_reglas['aciertos']}/25 |",
              f"| Híbrido (reglas + modelo si está disponible) | 25 casos de cátedra | {resumen['aciertos']}/25 |"]
    if 'metricas' in modelo:
        m = modelo['metricas']
        lineas += [f"| Naive Bayes aislado | {modelo['prueba']} textos reservados de {modelo['dataset']} ejemplos | Accuracy {m['accuracy']:.1%} |", '',
                   f"Modelo aislado: precisión macro {m['precision']:.1%}, recall macro {m['recall']:.1%}, F1 macro {m['f1']:.1%}.", '',
                   'La partición es estratificada, 75/25 y random_state=0. Es una única partición pequeña; no demuestra desempeño general.', '']
    else:
        lineas += ['', modelo['nota'], '']
    lineas += ['El 100 % del pipeline mide decisiones finales sobre el JSON; las métricas del modelo aislado miden intenciones en otros textos. No son medidas equivalentes.', '',
               '## Revisión adicional de intención y parámetros', '',
               'El evaluador original no se modificó. Se compararon aparte las intenciones y los parámetros enumerados en el JSON.', '',
               '| Caso | Campo | JSON | Agente |', '|---|---|---|---|']
    lineas += [f"| {d['id']} | {d['campo']} | {d['esperado']} | {d['obtenido']} |" for d in diferencias]
    lineas += ['', 'Las diferencias de los casos 11 y 14 se documentan en el informe: se conservó el JSON de la cátedra y se aplicó el perfil de seguridad de 0,20 m/s.', '',
               '## Reproducción', '', '```bash', 'python mi_desarrollo/generar_reporte.py',
               'python -m unittest discover -s mi_desarrollo -p "test_*.py" -v', '```', '',
               'Los tests adicionales y su resultado se registran también en validacion_adicional.txt. Los archivos de reporte se regeneran; el historial del agente sólo vive en memoria durante la sesión.', '']
    (DESTINO / 'reporte_accuracy.md').write_text('\n'.join(lineas), encoding='utf-8')
    print(captura.getvalue())
    print(f'Reportes guardados en {DESTINO}')


if __name__ == '__main__':
    main()
