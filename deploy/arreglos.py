# -*- coding: utf-8 -*-
"""Patrones ritmicos y generacion de melodia guia para cada estilo."""

import random
from teoria import construir_escala, pc_a_midi

# --- Notas de bateria GM (canal 10) ---
KICK, SNARE, CHIHAT, OHIHAT, CRASH, CLAP, RIDE = 36, 38, 42, 46, 49, 39, 51

PASOS_POR_COMPAS = 16  # grid de semicorcheas en 4/4


def _ev(paso, nota, vel, dur=1):
    return {"paso": paso, "nota": nota, "vel": vel, "dur": dur}


def patron_bateria(estilo, intensidad):
    """intensidad: 0 (silencio), 1 (suave/verso), 2 (pleno/coro)."""
    if intensidad == 0:
        return []

    if estilo == "corrido":
        base = [
            _ev(0, KICK, 100, 2), _ev(7, KICK, 80, 1), _ev(10, KICK, 90, 2),
            _ev(4, SNARE, 100, 2), _ev(12, SNARE, 100, 2), _ev(14, SNARE, 55, 1),
        ]
        hats = [_ev(p, CHIHAT, 65 if p % 4 == 0 else 50, 1) for p in range(0, 16, 2)]
        if intensidad >= 2:
            hats += [_ev(13, CHIHAT, 65, 1), _ev(14, CHIHAT, 80, 1), _ev(15, CHIHAT, 100, 1)]
            base.append(_ev(0, CRASH, 65, 4))
        return base + hats

    if estilo == "adoracion":
        if intensidad == 1:
            return [
                _ev(0, KICK, 70, 4), _ev(8, KICK, 65, 4),
                _ev(2, CHIHAT, 40, 2), _ev(6, CHIHAT, 38, 2),
                _ev(10, CHIHAT, 40, 2), _ev(14, CHIHAT, 38, 2),
            ]
        return [
            _ev(0, KICK, 80, 4), _ev(8, KICK, 75, 4),
            _ev(4, CLAP, 55, 2), _ev(12, CLAP, 55, 2),
            _ev(0, CHIHAT, 45, 2), _ev(2, CHIHAT, 42, 2), _ev(4, CHIHAT, 45, 2),
            _ev(6, CHIHAT, 42, 2), _ev(8, CHIHAT, 45, 2), _ev(10, CHIHAT, 42, 2),
            _ev(12, CHIHAT, 45, 2), _ev(14, CHIHAT, 42, 2),
        ]

    if estilo == "alabanza":
        if intensidad == 1:
            return [
                _ev(0, KICK, 95, 2), _ev(6, KICK, 85, 2), _ev(8, KICK, 90, 2), _ev(10, KICK, 80, 2),
                _ev(4, SNARE, 90, 2), _ev(12, SNARE, 90, 2),
                _ev(0, CHIHAT, 60, 2), _ev(2, CHIHAT, 55, 2), _ev(4, CHIHAT, 60, 2), _ev(6, CHIHAT, 55, 2),
                _ev(8, CHIHAT, 60, 2), _ev(10, CHIHAT, 55, 2), _ev(12, CHIHAT, 60, 2), _ev(14, CHIHAT, 55, 2),
            ]
        eventos = [
            _ev(0, KICK, 110, 2), _ev(3, KICK, 90, 1), _ev(6, KICK, 95, 2),
            _ev(8, KICK, 105, 2), _ev(11, KICK, 90, 1),
            _ev(4, SNARE, 105, 2), _ev(12, SNARE, 105, 2), _ev(12, CLAP, 90, 2),
        ]
        for p in range(0, 16, 1):
            eventos.append(_ev(p, CHIHAT if p % 2 == 0 else OHIHAT, 70 if p % 4 == 0 else 55, 1))
        return eventos

    # balada
    if intensidad == 1:
        return [
            _ev(0, KICK, 60, 4), _ev(8, KICK, 55, 4),
            _ev(8, SNARE, 45, 4),
            _ev(4, CHIHAT, 35, 2), _ev(12, CHIHAT, 35, 2),
        ]
    return [
        _ev(0, KICK, 85, 4), _ev(8, KICK, 80, 4),
        _ev(4, SNARE, 80, 2), _ev(12, SNARE, 85, 2),
        _ev(0, CHIHAT, 50, 2), _ev(2, CHIHAT, 45, 2), _ev(4, CHIHAT, 50, 2), _ev(6, CHIHAT, 45, 2),
        _ev(8, CHIHAT, 50, 2), _ev(10, CHIHAT, 45, 2), _ev(12, CHIHAT, 50, 2), _ev(14, CHIHAT, 45, 2),
    ]


def patron_bajo(estilo, pcs, octava_base=40):
    if estilo == "corrido":
        raiz = pc_a_midi(pcs[0], 38)
        return [_ev(0, raiz, 105, 6), _ev(8, raiz, 100, 6), _ev(14, raiz, 75, 2)]

    raiz = pc_a_midi(pcs[0], octava_base)
    quinta = pc_a_midi(pcs[2], octava_base)
    if quinta < raiz:
        quinta += 12

    if estilo == "adoracion":
        return [_ev(0, raiz, 75, 8), _ev(8, raiz, 70, 8)]

    if estilo == "alabanza":
        secuencia = [raiz, raiz, quinta, raiz, raiz, raiz, quinta, raiz]
        return [_ev(i * 2, nota, 95 if i % 2 == 0 else 85, 2) for i, nota in enumerate(secuencia)]

    # balada
    return [_ev(0, raiz, 70, 6), _ev(6, quinta - 12 if quinta - 12 >= raiz - 12 else quinta, 55, 2), _ev(8, raiz, 65, 8)]


def patron_piano(estilo, notas_acorde, intensidad):
    if estilo == "corrido":
        eventos = []
        for p in range(0, 16, 2):
            acento = p in (0, 8)
            dur = 2 if acento else 1
            vel = (105 if acento else 80) if intensidad >= 2 else (90 if acento else 65)
            for n in notas_acorde:
                eventos.append(_ev(p, n, vel, dur))
        return eventos

    if estilo == "adoracion":
        base = [_ev(0, n, 55 if intensidad == 1 else 65, 16) for n in notas_acorde]
        return base

    if estilo == "alabanza":
        pasos = [0, 4, 6, 8, 12, 14] if intensidad >= 2 else [0, 4, 8, 12]
        eventos = []
        for p in pasos:
            dur = 2 if p in (6, 14) else 4
            vel = 100 if intensidad >= 2 else 80
            for n in notas_acorde:
                eventos.append(_ev(p, n, vel, dur))
        return eventos

    # balada: arpegio ascendente por compas
    orden = sorted(notas_acorde)
    pasos = [0, 4, 8, 12]
    eventos = []
    for i, p in enumerate(pasos):
        n = orden[i % len(orden)]
        eventos.append(_ev(p, n, 60 if intensidad == 1 else 75, 4))
        eventos.append(_ev(p, n + 12, 40 if intensidad == 1 else 50, 4))
    return eventos


def patron_pad(notas_acorde, velocidad_base):
    return [_ev(0, n, velocidad_base, 16) for n in notas_acorde]


def gancho_coro(tonica_pc, modo, rango=(60, 74)):
    """Motivo melodico FIJO (no aleatorio) para el coro de un corrido: se repite
    identico cada vez que aparece el coro, que es lo que lo hace pegajoso/memorable."""
    escala = construir_escala(tonica_pc, modo)

    def nota(indice_escala):
        pc = escala[indice_escala % 7]
        n = pc_a_midi(pc, 66)
        while n < rango[0]:
            n += 12
        while n > rango[1]:
            n -= 12
        return n

    # (paso, indice_de_escala, duracion_en_pasos) - todo corcheas, ritmo parejo y facil de cantar
    patron_a = [(0, 4, 2), (2, 2, 2), (4, 0, 2), (6, 2, 2), (8, 4, 2), (10, 5, 2), (12, 4, 2), (14, 2, 2)]
    patron_b = [(0, 0, 2), (2, 0, 2), (4, 2, 2), (6, 4, 2), (8, 5, 2), (10, 4, 2), (12, 2, 2), (14, 0, 2)]
    patron_b_final = [(0, 0, 2), (2, 0, 2), (4, 2, 2), (6, 4, 2), (8, 5, 2), (10, 4, 2), (12, 2, 2), (14, 0, 4)]

    orden = ["A", "B", "A", "B", "A", "B", "A", "Bf"]
    mapa = {"A": patron_a, "B": patron_b, "Bf": patron_b_final}

    eventos = []
    for offset, tipo in enumerate(orden):
        for paso, idx, dur in mapa[tipo]:
            eventos.append({"compas_offset": offset, "paso": paso, "nota": nota(idx), "vel": 95, "dur": dur})
    return eventos


# --- Melodia guia ---

def _tono_mas_cercano(pitch_objetivo, opciones):
    return min(opciones, key=lambda n: abs(n - pitch_objetivo))


def generar_melodia_compas(pcs_acorde, escala_pcs, rango, ultima_nota, es_final_frase, rng):
    """Genera eventos de melodia guia para un compas, en semicorcheas (16 pasos)."""
    tonos_acorde = [pc_a_midi(pc, 66) for pc in pcs_acorde]
    tonos_acorde = [n for n in tonos_acorde if rango[0] <= n <= rango[1]]
    tonos_escala = []
    for pc in escala_pcs:
        for octava in (60, 72):
            n = pc_a_midi(pc, octava)
            if rango[0] <= n <= rango[1]:
                tonos_escala.append(n)
    if not tonos_acorde:
        tonos_acorde = [rango[0]]
    if not tonos_escala:
        tonos_escala = tonos_acorde

    celdas_ritmo = [
        [(0, 4), (4, 4), (8, 4), (12, 4)],           # 4 negras
        [(0, 8), (8, 4), (12, 4)],                    # blanca + 2 negras
        [(0, 2), (2, 2), (4, 4), (8, 8)],             # corcheas + blanca
        [(0, 4), (4, 2), (6, 2), (8, 4), (12, 4)],    # sincopada
        [(0, 8), (8, 8)],                             # 2 blancas (frase larga)
    ]
    celda = rng.choice(celdas_ritmo)

    eventos = []
    nota_previa = ultima_nota if ultima_nota is not None else rng.choice(tonos_acorde)
    for idx, (paso, dur) in enumerate(celda):
        es_tiempo_fuerte = paso in (0, 8)
        candidatos = tonos_acorde if es_tiempo_fuerte else tonos_escala
        # favorece movimiento por grados conjuntos desde la nota previa
        cercanos = sorted(candidatos, key=lambda n: abs(n - nota_previa))[:3]
        nota = rng.choice(cercanos) if cercanos else nota_previa

        if es_final_frase and idx == len(celda) - 1:
            nota = _tono_mas_cercano(nota_previa, tonos_acorde)

        eventos.append(_ev(paso, nota, 90, dur))
        nota_previa = nota

    return eventos, nota_previa
