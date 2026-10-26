"""Los dos robots reales: donde esta su modelo oficial y como se anima cada uno.

Usamos los modelos OFICIALES de Unitree (repo unitreerobotics/unitree_mujoco),
no una figura inventada: el alumno tiene que ver el robot que despues va a usar.

El movimiento es CINEMATICO: escribimos la pose y llamamos mj_forward, sin
correr fisica. Es a proposito:

  - El G1 es un humanoide y SE CAE SOLO sin un controlador de locomocion. El
    simulador oficial no trae ese controlador (vive en la PC interna del robot
    y Unitree no lo publica). Con fisica real, el robot se desploma antes de
    que el alumno pueda probar nada.
  - Un TP de programacion evalua el algoritmo, no la marcha. Si el robot se
    tropieza, el alumno recibe roja por algo que no es suyo.

La animacion de las patas es COSMETICA: el robot se desliza. Sirve para que se
vea que camina, no para simular como camina.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

# Donde buscar los modelos oficiales, en orden.
UBICACIONES = [
    # Primero los que vienen DENTRO del paquete: es lo que tiene un profesor
    # que bajo su carpeta y nada mas. Antes iba primero ~/unitree_libs, asi que
    # en la maquina de Teo se usaban esos y los del paquete no se probaban nunca.
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "unitree_mujoco", "unitree_robots"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "unitree_robots"),
    os.path.expanduser("~/unitree_libs/unitree_mujoco/unitree_robots"),
    os.path.expanduser("~/unitree_mujoco/unitree_robots"),
    os.path.join(os.getcwd(), "unitree_mujoco", "unitree_robots"),
]


ESCENA_LIMPIA = """<mujoco model="{modelo} - escena limpia UADE">
  <!-- Generado por el laboratorio UADE. NO es un archivo oficial de Unitree.
       La escena oficial del Go2 trae 8 cajas de obstaculo, incluida una
       escalera, y dos vigas que cruzan justo por donde se dibuja la grilla del
       TP03: el robot parecia atravesar paredes. Esta escena tiene el mismo
       robot y el mismo piso, sin esos obstaculos.
       Se regenera solo si se borra. No modifica ningun archivo oficial. -->
  <include file="{incluye}"/>

  <statistic center="0 0 0.1" extent="1.2"/>

  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.35 0.35 0.35" specular="0 0 0"/>
    <rgba haze="0.15 0.25 0.35 1"/>
    <global azimuth="-130" elevation="-20"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0"
             width="512" height="3072"/>
    <texture type="2d" name="groundplane_uade" builtin="checker" mark="edge"
             rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" markrgb="0.8 0.8 0.8"
             width="300" height="300"/>
    <material name="groundplane_uade" texture="groundplane_uade" texuniform="true"
              texrepeat="5 5" reflectance="0.2"/>
  </asset>

  <worldbody>
    <light pos="0 0 1.5" dir="0 0 -1" directional="true"/>
    <geom name="floor" size="0 0 0.05" type="plane" material="groundplane_uade"/>
  </worldbody>
</mujoco>
"""


def _generar_escena_limpia(destino: str, incluye: str) -> str:
    """Escribe la escena sin obstaculos al lado del modelo oficial."""
    contenido = ESCENA_LIMPIA.format(
        modelo=os.path.splitext(incluye)[0], incluye=incluye)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(contenido)
    return destino


@dataclass
class Robot:
    clave: str
    nombre: str
    tipo: str
    escena: str          # ruta relativa dentro de unitree_robots/
    altura: float        # altura de la base al estar de pie, en metros
    incluye: str = ""    # si esta, generamos una escena limpia que lo incluya
    pose_de_pie: dict = field(default_factory=dict)   # indice art -> radianes
    # Indices (dentro de qpos, contando desde la primera articulacion) que se
    # animan al caminar: (indice, amplitud, desfase)
    marcha: list = field(default_factory=list)
    saludo: dict = field(default_factory=dict)
    pose_sentado: dict = field(default_factory=dict)
    # Gestos extra: nombre -> (pose base {indice: rad},
    #                          oscilacion [(indice, amplitud, hz, desfase)])
    gestos: dict = field(default_factory=dict)
    # Rutinas con keyframes: nombre -> (duracion, [(segundo, pose), ...]).
    rutinas: dict = field(default_factory=dict)

    def aplicar_gesto(self, accion: str, art, t: float) -> bool:
        """Aplica una pose o interpola una rutina de articulaciones."""
        rutina = self.rutinas.get(accion)
        if rutina is not None:
            duracion, cuadros = rutina
            t = max(0.0, min(float(t), duracion))
            anterior_t, anterior = cuadros[0]
            siguiente_t, siguiente = cuadros[-1]
            for (ta, a), (tb, b) in zip(cuadros, cuadros[1:]):
                if t <= tb:
                    anterior_t, anterior = ta, a
                    siguiente_t, siguiente = tb, b
                    break
            tramo = max(1e-9, siguiente_t - anterior_t)
            u = max(0.0, min(1.0, (t - anterior_t) / tramo))
            # Ease-in/ease-out: los brazos arrancan y frenan con suavidad.
            u = u * u * (3.0 - 2.0 * u)
            for idx in anterior.keys() | siguiente.keys():
                desde = anterior.get(idx, 0.0)
                hasta = siguiente.get(idx, desde)
                if idx < len(art):
                    art[idx] = desde + (hasta - desde) * u
            return True

        gesto = self.gestos.get(accion)
        if gesto is None:
            return False
        base, oscilacion = gesto
        for idx, valor in base.items():
            if idx < len(art):
                art[idx] = valor
        for idx, amplitud, hz, desfase in oscilacion:
            if idx < len(art):
                art[idx] += amplitud * math.sin(2 * math.pi * hz * t + desfase)
        return True

    def ruta_escena(self) -> str | None:
        for base in UBICACIONES:
            ruta = os.path.join(base, self.escena)
            if os.path.exists(ruta):
                return ruta
            # Escena limpia: la generamos al lado del modelo oficial si falta.
            if self.incluye:
                modelo = os.path.join(base, os.path.dirname(self.escena),
                                      self.incluye)
                if os.path.exists(modelo):
                    return _generar_escena_limpia(ruta, self.incluye)
        return None


# --- G1: humanoide de 29 grados de libertad -----------------------------
# Indices relativos (qpos real = 7 + indice)
G1_L_HIP_P, G1_L_KNEE = 0, 3
G1_R_HIP_P, G1_R_KNEE = 6, 9
G1_L_SHOULDER_P, G1_L_ELBOW = 15, 18
G1_R_SHOULDER_P, G1_R_ELBOW = 22, 25
G1_L_SHOULDER_R, G1_L_WRIST_R = 16, 19
G1_R_SHOULDER_R, G1_R_WRIST_R = 23, 26
G1_L_SHOULDER_Y, G1_R_SHOULDER_Y = 17, 24


def _brazos_g1(hombro_p=0.20, hombro_r=0.0, codo=-0.30,
               muneca=0.0, hombro_y=0.0) -> dict[int, float]:
    """Pose simetrica de brazos, con signos espejados en los ejes laterales."""
    return {
        G1_L_SHOULDER_P: hombro_p, G1_R_SHOULDER_P: hombro_p,
        G1_L_SHOULDER_R: hombro_r, G1_R_SHOULDER_R: -hombro_r,
        G1_L_SHOULDER_Y: hombro_y, G1_R_SHOULDER_Y: -hombro_y,
        G1_L_ELBOW: codo, G1_R_ELBOW: codo,
        G1_L_WRIST_R: muneca, G1_R_WRIST_R: -muneca,
    }


def _brazos_g1_asimetricos(izq, der) -> dict[int, float]:
    """Combina dos poses para keyframes de brazos alternados."""
    pose = _brazos_g1()
    pose.update({G1_L_SHOULDER_P: izq[0], G1_L_SHOULDER_R: izq[1],
                 G1_L_ELBOW: izq[2], G1_L_WRIST_R: izq[3],
                 G1_R_SHOULDER_P: der[0], G1_R_SHOULDER_R: der[1],
                 G1_R_ELBOW: der[2], G1_R_WRIST_R: der[3]})
    return pose

G1 = Robot(
    clave="g1",
    nombre="Unitree G1",
    tipo="humanoide",
    escena="g1/scene_29dof.xml",   # scene.xml tiene ~100 obstaculos del terrain_tool
    altura=0.793,
    pose_de_pie={
        G1_L_SHOULDER_P: 0.20, G1_R_SHOULDER_P: 0.20,
        G1_L_ELBOW: -0.30, G1_R_ELBOW: -0.30,
    },
    marcha=[
        (G1_L_HIP_P, 0.40, 0.0),
        (G1_R_HIP_P, 0.40, math.pi),
        (G1_L_KNEE, 0.45, 1.1),
        (G1_R_KNEE, 0.45, 1.1 + math.pi),
        (G1_L_SHOULDER_P, 0.30, math.pi),
        (G1_R_SHOULDER_P, 0.30, 0.0),
    ],
    saludo={G1_R_SHOULDER_P: -2.4, G1_R_ELBOW: -1.0},
    # Agachado (FSM Sit / Damp). No es un desplome: es una postura.
    pose_sentado={G1_L_HIP_P: -1.2, G1_R_HIP_P: -1.2,
                  G1_L_KNEE: 1.8, G1_R_KNEE: 1.8},
    gestos={
        # El "67" (six seven): antebrazos al frente, palmas arriba, y las
        # manos suben y bajan alternadas, como una balanza.
        "seis_siete": (
            {G1_L_SHOULDER_P: -0.1, G1_R_SHOULDER_P: -0.1,
             G1_L_SHOULDER_R: 0.15, G1_R_SHOULDER_R: -0.15,
             G1_L_ELBOW: 0.0, G1_R_ELBOW: 0.0,
             G1_L_WRIST_R: -1.5, G1_R_WRIST_R: 1.5},
            [(G1_L_ELBOW, 0.45, 2.2, 0.0),
             (G1_R_ELBOW, 0.45, 2.2, math.pi)],
        ),
        # Brazo derecho extendido al frente.
        "dar_la_mano": (
            {G1_R_SHOULDER_P: -0.8, G1_R_SHOULDER_R: -0.1, G1_R_ELBOW: 0.6},
            [],
        ),
    },
    rutinas={
        # Baile de brazos tipo "brazos arriba": alterna lados y termina abierto.
        "baile": (4.8, [
            (0.0, _brazos_g1()),
            (0.4, _brazos_g1(-0.15, 0.65, 1.0)),
            (0.9, _brazos_g1_asimetricos(
                (-2.15, 0.20, -0.35, 0.0), (-0.15, -0.65, 1.0, 0.0))),
            (1.45, _brazos_g1_asimetricos(
                (-0.15, 0.65, 1.0, 0.0), (-2.15, -0.20, -0.35, 0.0))),
            (2.0, _brazos_g1(-2.15, 0.20, -0.35)),
            (2.55, _brazos_g1_asimetricos(
                (-2.15, 0.20, -0.35, 0.0), (-0.15, -0.65, 1.0, 0.0))),
            (3.1, _brazos_g1_asimetricos(
                (-0.15, 0.65, 1.0, 0.0), (-2.15, -0.20, -0.35, 0.0))),
            (3.7, _brazos_g1(-1.8, 0.35, 0.1)),
            (4.25, _brazos_g1()),
            (4.8, _brazos_g1()),
        ]),
        # Festejo: sube ambos brazos en V y hace tres bombeos alternados.
        "festejo": (4.8, [
            (0.0, _brazos_g1()),
            (0.55, _brazos_g1(-2.25, 0.22, -0.35)),
            (1.0, _brazos_g1_asimetricos(
                (-0.75, 0.72, 1.25, 0.0), (-2.25, -0.22, -0.35, 0.0))),
            (1.45, _brazos_g1(-2.25, 0.22, -0.35)),
            (1.9, _brazos_g1_asimetricos(
                (-2.25, 0.22, -0.35, 0.0), (-0.75, -0.72, 1.25, 0.0))),
            (2.35, _brazos_g1(-2.25, 0.22, -0.35)),
            (2.8, _brazos_g1_asimetricos(
                (-0.75, 0.72, 1.25, 0.0), (-2.25, -0.22, -0.35, 0.0))),
            (3.25, _brazos_g1(-2.25, 0.22, -0.35)),
            (4.0, _brazos_g1(-2.25, 0.22, -0.35)),
            (4.8, _brazos_g1()),
        ]),
        # Doble biceps: abduce los hombros y gira cada brazo sobre su eje
        # (shoulder_yaw) para que el codo pliegue en el plano frontal.
        # El cero del codo del MJCF ya forma aproximadamente un angulo recto:
        # no corresponde al brazo estirado. -0.55 inclina las manos hacia la cabeza.
        "pose_fisicoculturista": (12.0, [
            (0.0, _brazos_g1()),
            (0.65, _brazos_g1(0.0, math.pi / 2, math.pi / 2)),
            (1.30, _brazos_g1(0.0, math.pi / 2, -0.55, -0.60,
                                hombro_y=math.pi / 2)),
            (12.0, _brazos_g1(0.0, math.pi / 2, -0.55, -0.60,
                                hombro_y=math.pi / 2)),
        ]),
    },
)

# --- Go2: cuadrupedo de 12 grados de libertad ---------------------------
GO2_FL_T, GO2_FL_C = 1, 2
GO2_FR_T, GO2_FR_C = 4, 5
GO2_RL_T, GO2_RL_C = 7, 8
GO2_RR_T, GO2_RR_C = 10, 11

# Pose de perro parado. Sin esto el modelo aparece con las patas estiradas.
_GO2_MUSLO, _GO2_PANTORRILLA = 0.80, -1.55

GO2 = Robot(
    clave="go2",
    nombre="Unitree Go2",
    tipo="cuadrupedo",
    # La escena oficial del Go2 trae una escalera y vigas que cruzan la grilla.
    # Usamos una escena limpia que se genera sola. La del G1 ya viene limpia.
    escena="go2/scene_uade.xml",
    incluye="go2.xml",
    altura=0.33,
    pose_de_pie={
        GO2_FL_T: _GO2_MUSLO, GO2_FR_T: _GO2_MUSLO,
        GO2_RL_T: _GO2_MUSLO, GO2_RR_T: _GO2_MUSLO,
        GO2_FL_C: _GO2_PANTORRILLA, GO2_FR_C: _GO2_PANTORRILLA,
        GO2_RL_C: _GO2_PANTORRILLA, GO2_RR_C: _GO2_PANTORRILLA,
    },
    # Trote: las diagonales van juntas (FL con RR, FR con RL).
    marcha=[
        (GO2_FL_T, 0.28, 0.0), (GO2_RR_T, 0.28, 0.0),
        (GO2_FR_T, 0.28, math.pi), (GO2_RL_T, 0.28, math.pi),
        (GO2_FL_C, 0.22, 0.0), (GO2_RR_C, 0.22, 0.0),
        (GO2_FR_C, 0.22, math.pi), (GO2_RL_C, 0.22, math.pi),
    ],
    # El perro "saluda" levantando la pata delantera izquierda.
    saludo={GO2_FL_T: -0.6, GO2_FL_C: -0.9},
    pose_sentado={GO2_FL_T: 1.3, GO2_FR_T: 1.3, GO2_RL_T: 1.3, GO2_RR_T: 1.3,
                  GO2_FL_C: -2.4, GO2_FR_C: -2.4, GO2_RL_C: -2.4, GO2_RR_C: -2.4},
)

# Largo x ancho aproximados de pie, en metros. Medidos sobre el modelo oficial.
# Sirven para avisar cuando el robot no entra en la celda de la grilla del TP03.
HUELLA = {"g1": (0.32, 0.32), "go2": (0.62, 0.28)}

ROBOTS = {"g1": G1, "go2": GO2}


def entra_en_celda(clave: str, tamano_celda: float) -> tuple[bool, float]:
    """Devuelve si el robot entra en una celda y cuanto mide su lado mayor."""
    largo, ancho = HUELLA.get(clave, (0.4, 0.4))
    mayor = max(largo, ancho)
    return mayor <= tamano_celda, mayor


def obtener(clave: str) -> Robot:
    c = clave.lower().strip()
    if c not in ROBOTS:
        raise ValueError(f"Robot desconocido: '{clave}'. Validos: g1, go2.")
    return ROBOTS[c]


def faltan_modelos() -> str:
    """Mensaje de ayuda si no encuentra los modelos oficiales."""
    return (
        "No encuentro los modelos oficiales de Unitree.\n\n"
        "Se descargan una sola vez con:\n"
        "    git clone https://github.com/unitreerobotics/unitree_mujoco\n\n"
        "Dejalos en alguna de estas carpetas:\n"
        + "\n".join(f"    {u}" for u in UBICACIONES)
    )
