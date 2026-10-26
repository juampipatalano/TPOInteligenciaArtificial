"""Regresion geometrica de la doble biceps sobre el modelo MJCF real.

Requiere MuJoCo (la misma dependencia que usa el simulador). Se omite si no
esta instalado; el resto de las pruebas del agente no lo necesita.
"""

import sys
import unittest
from pathlib import Path

_ENTORNO = Path(__file__).resolve().parent.parent / "entorno"
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

try:
    import mujoco
    import numpy as np
except ImportError:
    mujoco = None

from sim.arrancar import cargar_modelo
from sim.robots import G1


@unittest.skipIf(mujoco is None, "MuJoCo no esta instalado")
class PruebasDobleBiceps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modelo = cargar_modelo(mujoco, G1.ruta_escena())

    def _pose(self, tiempo):
        datos = mujoco.MjData(self.modelo)
        datos.qpos[2] = G1.altura
        datos.qpos[3] = 1.0
        articulaciones = datos.qpos[7:]
        for indice, valor in G1.pose_de_pie.items():
            articulaciones[indice] = valor
        self.assertTrue(G1.aplicar_gesto(
            "pose_fisicoculturista", articulaciones, tiempo))
        mujoco.mj_forward(self.modelo, datos)
        return datos

    def test_codos_abiertos_a_altura_de_hombros_y_manos_arriba(self):
        datos = self._pose(2.0)
        for lado, signo in (("left", 1), ("right", -1)):
            with self.subTest(lado=lado):
                hombro = datos.body(f"{lado}_shoulder_roll_link").xpos
                codo = datos.body(f"{lado}_elbow_link").xpos
                muneca = datos.body(f"{lado}_wrist_yaw_link").xpos
                # Brazos superiores abiertos, casi horizontales.
                self.assertGreater(signo * (codo[1] - hombro[1]), 0.16)
                self.assertLess(abs(codo[2] - hombro[2]), 0.05)
                # Antebrazos hacia arriba y adentro, en el plano frontal.
                self.assertGreater(muneca[2] - codo[2], 0.13)
                self.assertGreater(signo * (codo[1] - muneca[1]), 0.045)
                self.assertLess(abs(muneca[0] - codo[0]), 0.04)
        izquierda = datos.body("left_wrist_yaw_link").xpos
        derecha = datos.body("right_wrist_yaw_link").xpos
        np.testing.assert_allclose(izquierda, derecha * [1, -1, 1], atol=0.001)

    def test_toda_la_transicion_respeta_limites_y_mantiene_la_base(self):
        for tiempo in np.linspace(0.0, 12.0, 121):
            datos = self._pose(tiempo)
            np.testing.assert_allclose(datos.qpos[7:22], 0.0)
            for articulacion in range(self.modelo.njnt):
                if not self.modelo.jnt_limited[articulacion]:
                    continue
                valor = datos.qpos[self.modelo.jnt_qposadr[articulacion]]
                minimo, maximo = self.modelo.jnt_range[articulacion]
                with self.subTest(tiempo=tiempo, articulacion=articulacion):
                    self.assertGreaterEqual(valor, minimo - 1e-6)
                    self.assertLessEqual(valor, maximo + 1e-6)

    def test_la_pose_final_se_sostiene(self):
        inicio = self._pose(1.30).qpos.copy()
        final = self._pose(11.9).qpos
        np.testing.assert_allclose(inicio, final, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
