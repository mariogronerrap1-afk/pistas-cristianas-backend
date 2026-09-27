# -*- coding: utf-8 -*-
"""Teoria musical basica: escalas, acordes y progresiones para musica cristiana."""

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

INTERVALOS_MAYOR = [0, 2, 4, 5, 7, 9, 11]   # escala mayor (jonico)
INTERVALOS_MENOR = [0, 2, 3, 5, 7, 8, 10]   # escala menor natural (eolico)

# Triadas diatonicas por grado (mayor: I ii iii IV V vi vii°)
CALIDAD_TRIADA_MAYOR = ["mayor", "menor", "menor", "mayor", "mayor", "menor", "dis"]
# Triadas diatonicas por grado (menor natural: i ii° III iv v VI VII)
CALIDAD_TRIADA_MENOR = ["menor", "dis", "mayor", "menor", "menor", "mayor", "mayor"]


def nombre_a_pc(nombre):
    """Convierte 'C', 'D#', 'Bb', etc. a clase de altura 0-11."""
    equivalencias = {
        "DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#",
    }
    n = nombre.strip().upper()
    if n in equivalencias:
        n = equivalencias[n]
    if n not in NOTAS:
        raise ValueError(f"Nota no reconocida: {nombre}")
    return NOTAS.index(n)


def construir_escala(tonica_pc, modo="mayor"):
    intervalos = INTERVALOS_MAYOR if modo == "mayor" else INTERVALOS_MENOR
    return [(tonica_pc + i) % 12 for i in intervalos]


def acorde_grado(tonica_pc, modo, grado):
    """grado: 1..7 (numero romano). Devuelve lista de pitch-classes de la triada."""
    escala = construir_escala(tonica_pc, modo)
    i = grado - 1
    raiz = escala[i % 7]
    tercera = escala[(i + 2) % 7]
    quinta = escala[(i + 4) % 7]
    return [raiz, tercera, quinta]


def pc_a_midi(pc, octava_base=60):
    """Ubica una clase de altura en la octava mas cercana a octava_base."""
    candidato = pc + 12 * (octava_base // 12)
    mejor = min(
        [candidato - 12, candidato, candidato + 12],
        key=lambda n: abs(n - octava_base),
    )
    return mejor


def notas_acorde_midi(pcs, octava_base=48, con_septima=False, escala=None, grado=None):
    """Devuelve las notas MIDI de un acorde (voces cerradas) en la octava dada."""
    notas = [pc_a_midi(pc, octava_base) for pc in pcs]
    notas = sorted(notas)
    # asegura que esten dentro de una octava razonable (voicing cerrado)
    while notas[-1] - notas[0] > 12:
        notas[-1] -= 12
        notas.sort()
    return notas


# Progresiones tipicas de musica cristiana contemporanea, en numeros de grado (1-7)
PROGRESIONES = {
    "mayor": {
        "verso": [1, 5, 6, 4],       # I - V - vi - IV
        "coro": [6, 4, 1, 5],        # vi - IV - I - V  (mas anhelante/anthem)
        "puente": [4, 1, 5, 6],      # IV - I - V - vi
        "intro": [1, 5, 6, 4],
        "outro": [4, 1],
    },
    "menor": {
        "verso": [1, 6, 3, 7],       # i - VI - III - VII
        "coro": [6, 3, 7, 1],        # VI - III - VII - i (relativo mayor -> resolucion)
        "puente": [4, 5, 1, 1],      # iv - v - i - i
        "intro": [1, 6, 3, 7],
        "outro": [4, 1],
    },
}
