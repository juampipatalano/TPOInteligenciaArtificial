"""Regresiones del agente y del contrato con el ejecutor, sin simulador.

Ejecutar: python -m unittest discover -s mi_desarrollo -p 'test_*.py' -v
"""
import unittest
from types import SimpleNamespace

from ejecutor import Ejecutor
from evaluar import evaluar
from mi_tp07 import AgenteRobot, _perfil_por_defecto


class RobotPrueba:
    def __init__(self, bateria=87):
        self.perfil = _perfil_por_defecto()
        self.bateria = bateria
        self.ordenes = []

    def verificar_estado(self):
        return SimpleNamespace(bateria=self.bateria)

    def avanzar(self, **kw):
        self.ordenes.append(("avanzar", kw))

    def girar(self, **kw):
        self.ordenes.append(("girar", kw))

    def detenerse(self):
        self.ordenes.append(("detenerse", {}))


class PruebasAgente(unittest.TestCase):
    def test_casos_catedra_sin_modelo(self):
        r = evaluar(AgenteRobot(usar_modelo=False), mostrar=False)
        self.assertEqual((r['aciertos'], r['casos']), (25, 25))
        self.assertEqual((r['peligrosos_bloqueados'], r['peligrosos_totales']), (3, 3))

    def test_cantidades_negativas_conservadas_y_bloqueadas(self):
        for texto, clave, numero in [
            ('avanzá -2 metros', 'distancia_m', -2),
            ('avanzá -0,5 metros', 'distancia_m', -0.5),
            ('girá -45 grados', 'angulo_deg', -45),
            ('avanzá a -0.2 m/s', 'velocidad_ms', -0.2),
        ]:
            with self.subTest(texto=texto):
                r = AgenteRobot(usar_modelo=False).procesar(texto)
                self.assertEqual(r['parametros'][clave], numero)
                self.assertTrue(r['bloqueado'])
                self.assertFalse(r['ejecutar'])

    def test_velocidad_angular_se_valida_antes_de_ejecutar(self):
        robot = RobotPrueba()
        agente = AgenteRobot(robot, usar_modelo=False)
        for velocidad in ('2', '-0.5', '0'):
            with self.subTest(velocidad=velocidad):
                r = agente.procesar(f'girá 90 grados a {velocidad} rad/s')
                self.assertTrue(r['bloqueado'])
        self.assertEqual(robot.ordenes, [])
        r = agente.procesar('girá 45 grados a la derecha a 0,5 rad/s')
        self.assertFalse(r['bloqueado'])
        self.assertEqual(r['parametros']['velocidad_giro'], 0.5)
        self.assertEqual(robot.ordenes[0][1]['velocidad'], -0.5)

    def test_peligro_desconocido_y_orden_compuesta_no_se_ejecutan(self):
        robot = RobotPrueba()
        agente = AgenteRobot(robot, usar_modelo=False)
        for texto in ('salta desde la mesa', 'avanzá 1 metro y después empujá la caja'):
            self.assertTrue(agente.procesar(texto)['bloqueado'])
        self.assertEqual(robot.ordenes, [])

    def test_bateria_baja_o_desconocida_bloquea_movimiento_pero_no_freno(self):
        for bateria in (24, None):
            with self.subTest(bateria=bateria):
                robot = RobotPrueba(bateria)
                agente = AgenteRobot(robot, usar_modelo=False)
                self.assertTrue(agente.procesar('avanzá 1 metro')['bloqueado'])
                self.assertTrue(agente.procesar('detente ya')['ejecutar'])
                self.assertEqual(robot.ordenes, [('detenerse', {})])

    def test_dos_metros_se_parten_sin_superar_cinco_segundos(self):
        robot = RobotPrueba()
        Ejecutor(robot, mostrar=False).ejecutar('MOVER', {'distancia_m': 2})
        self.assertEqual(len(robot.ordenes), 2)
        self.assertAlmostEqual(sum(p['tiempo'] * p['velocidad'] for _, p in robot.ordenes), 2)
        self.assertTrue(all(p['tiempo'] <= 5 for _, p in robot.ordenes))

    def test_repeticion_vuelve_a_validar_bateria(self):
        robot = RobotPrueba()
        agente = AgenteRobot(robot, usar_modelo=False)
        agente.procesar('avanzá 1 metro')
        robot.bateria = 24
        self.assertTrue(agente.procesar('hacelo otra vez')['bloqueado'])
        self.assertEqual(len(robot.ordenes), 1)


if __name__ == '__main__':
    unittest.main()
