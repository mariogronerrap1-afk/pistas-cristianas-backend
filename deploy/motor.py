# -*- coding: utf-8 -*-
"""Ensambla la cancion completa (estructura + pistas) y exporta a MIDI."""

import os
import random
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

import teoria
import arreglos
import sintetizador

PASOS_POR_COMPAS = arreglos.PASOS_POR_COMPAS
TICKS_POR_BEAT = 480
TICKS_POR_PASO = TICKS_POR_BEAT // 4  # semicorchea

# Programas GM (0-indexados) por estilo
PROGRAMAS = {
    "adoracion": {"piano": 4, "bajo": 32, "pad": 88, "melodia": 54},
    "alabanza": {"piano": 0, "bajo": 33, "pad": 50, "melodia": 54},
    "balada": {"piano": 0, "bajo": 32, "pad": 88, "melodia": 54},
    # "piano" = guitarra/requinto, "bajo" = bajo tipo 808, "pad" = cuerdas cinematicas
    "corrido": {"piano": 25, "bajo": 38, "pad": 50, "melodia": 54},
}

# Progresion "andaluza" (i - VII - VI - v) tipica de corridos tumbados / belicos
PROGRESIONES_CORRIDO = {
    "intro": [1, 7, 6, 5],
    "verso": [1, 7, 6, 5],
    "coro": [6, 7, 1, 5],
    "puente": [4, 5, 1, 1],
    "outro": [6, 5],
}

CANALES = {"piano": 0, "bajo": 1, "pad": 2, "melodia": 3, "bateria": 9}

ESTILOS = {
    "adoracion": {
        "bpm_sugerido": 70,
        "secciones": [
            {"nombre": "Intro", "compases": 4, "prog": "intro", "bateria": 0, "vel_pad": 45, "melodia": False},
            {"nombre": "Verso 1", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 55, "melodia": True},
            {"nombre": "Coro 1", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 68, "melodia": True},
            {"nombre": "Verso 2", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 55, "melodia": True},
            {"nombre": "Coro 2", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 68, "melodia": True},
            {"nombre": "Puente", "compases": 4, "prog": "puente", "bateria": 1, "vel_pad": 60, "melodia": True},
            {"nombre": "Coro Final", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 78, "melodia": True},
            {"nombre": "Outro", "compases": 4, "prog": "outro", "bateria": 0, "vel_pad": 42, "melodia": False},
        ],
    },
    "alabanza": {
        "bpm_sugerido": 104,
        "secciones": [
            {"nombre": "Intro", "compases": 4, "prog": "intro", "bateria": 1, "vel_pad": 55, "melodia": False},
            {"nombre": "Verso 1", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 60, "melodia": True},
            {"nombre": "Coro 1", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 75, "melodia": True},
            {"nombre": "Verso 2", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 60, "melodia": True},
            {"nombre": "Coro 2", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 75, "melodia": True},
            {"nombre": "Puente", "compases": 4, "prog": "puente", "bateria": 2, "vel_pad": 80, "melodia": True},
            {"nombre": "Coro Final", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 85, "melodia": True},
            {"nombre": "Outro", "compases": 4, "prog": "outro", "bateria": 1, "vel_pad": 60, "melodia": False},
        ],
    },
    "balada": {
        "bpm_sugerido": 76,
        "secciones": [
            {"nombre": "Intro", "compases": 4, "prog": "intro", "bateria": 0, "vel_pad": 40, "melodia": False},
            {"nombre": "Verso 1", "compases": 8, "prog": "verso", "bateria": 0, "vel_pad": 45, "melodia": True},
            {"nombre": "Coro 1", "compases": 8, "prog": "coro", "bateria": 1, "vel_pad": 62, "melodia": True},
            {"nombre": "Verso 2", "compases": 8, "prog": "verso", "bateria": 0, "vel_pad": 45, "melodia": True},
            {"nombre": "Coro 2", "compases": 8, "prog": "coro", "bateria": 1, "vel_pad": 62, "melodia": True},
            {"nombre": "Puente", "compases": 4, "prog": "puente", "bateria": 1, "vel_pad": 65, "melodia": True},
            {"nombre": "Coro Final", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 80, "melodia": True},
            {"nombre": "Outro", "compases": 4, "prog": "outro", "bateria": 0, "vel_pad": 40, "melodia": False},
        ],
    },
    "corrido": {
        "bpm_sugerido": 90,
        "secciones": [
            {"nombre": "Intro", "compases": 4, "prog": "intro", "bateria": 1, "vel_pad": 40, "melodia": False},
            {"nombre": "Verso 1", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 45, "melodia": True},
            {"nombre": "Coro 1", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 60, "melodia": True},
            {"nombre": "Verso 2", "compases": 8, "prog": "verso", "bateria": 1, "vel_pad": 45, "melodia": True},
            {"nombre": "Coro 2", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 60, "melodia": True},
            {"nombre": "Puente", "compases": 4, "prog": "puente", "bateria": 1, "vel_pad": 55, "melodia": True},
            {"nombre": "Coro Final", "compases": 8, "prog": "coro", "bateria": 2, "vel_pad": 70, "melodia": True},
            {"nombre": "Outro", "compases": 4, "prog": "outro", "bateria": 1, "vel_pad": 40, "melodia": False},
        ],
    },
}


def construir_cancion(estilo, tono, modo, semilla=None):
    cfg = ESTILOS[estilo]
    tonica_pc = teoria.nombre_a_pc(tono)
    escala = teoria.construir_escala(tonica_pc, modo)
    rng = random.Random(semilla)

    pistas = {"bateria": [], "bajo": [], "piano": [], "pad": [], "melodia": []}
    estructura = []
    acordes_por_compas = []

    compas_actual = 0
    ultima_nota_melodia = None

    gancho = arreglos.gancho_coro(tonica_pc, modo) if estilo == "corrido" else None

    for sec in cfg["secciones"]:
        if estilo == "corrido":
            grados = PROGRESIONES_CORRIDO[sec["prog"]]
        else:
            grados = teoria.PROGRESIONES[modo][sec["prog"]]
        estructura.append({"nombre": sec["nombre"], "inicio": compas_actual, "compases": sec["compases"]})
        sec_inicio_compas = compas_actual

        es_coro_con_gancho = estilo == "corrido" and sec["nombre"].startswith("Coro") and sec["compases"] == 8
        es_intro_con_adelanto = estilo == "corrido" and sec["nombre"] == "Intro"

        for i in range(sec["compases"]):
            grado = grados[i % len(grados)]
            pcs = teoria.acorde_grado(tonica_pc, modo, grado)
            acordes_por_compas.append((compas_actual, grado, pcs))
            paso_base = compas_actual * PASOS_POR_COMPAS

            for ev in arreglos.patron_bateria(estilo, sec["bateria"]):
                pistas["bateria"].append({**ev, "paso": ev["paso"] + paso_base})

            for ev in arreglos.patron_bajo(estilo, pcs):
                pistas["bajo"].append({**ev, "paso": ev["paso"] + paso_base})

            notas_piano = teoria.notas_acorde_midi(pcs, octava_base=60)
            intensidad_piano = sec["bateria"] if sec["bateria"] > 0 else 1
            for ev in arreglos.patron_piano(estilo, notas_piano, intensidad_piano):
                pistas["piano"].append({**ev, "paso": ev["paso"] + paso_base})

            notas_pad = teoria.notas_acorde_midi(pcs, octava_base=55)
            for ev in arreglos.patron_pad(notas_pad, sec["vel_pad"]):
                pistas["pad"].append({**ev, "paso": ev["paso"] + paso_base})

            if sec["melodia"] and not es_coro_con_gancho:
                es_final_frase = (i % 4 == 3) or (i == sec["compases"] - 1)
                eventos_m, ultima_nota_melodia = arreglos.generar_melodia_compas(
                    pcs, escala, rango=(60, 74), ultima_nota=ultima_nota_melodia,
                    es_final_frase=es_final_frase, rng=rng,
                )
                for ev in eventos_m:
                    pistas["melodia"].append({**ev, "paso": ev["paso"] + paso_base})
            elif not sec["melodia"] and not es_intro_con_adelanto:
                ultima_nota_melodia = None

            compas_actual += 1

        if es_coro_con_gancho:
            for ev in gancho:
                paso = (sec_inicio_compas + ev["compas_offset"]) * PASOS_POR_COMPAS + ev["paso"]
                pistas["melodia"].append({"paso": paso, "nota": ev["nota"], "vel": ev["vel"], "dur": ev["dur"]})
            ultima_nota_melodia = gancho[-1]["nota"]

        if es_intro_con_adelanto:
            # adelanto (teaser) de los primeros 2 compases del gancho, para enganchar desde el inicio
            for ev in gancho[: len([e for e in gancho if e["compas_offset"] < 2])]:
                paso = (sec_inicio_compas + ev["compas_offset"]) * PASOS_POR_COMPAS + ev["paso"]
                pistas["melodia"].append({"paso": paso, "nota": ev["nota"], "vel": 70, "dur": ev["dur"]})
            ultima_nota_melodia = None

    return {
        "pistas": pistas,
        "estructura": estructura,
        "total_compases": compas_actual,
        "escala": escala,
        "acordes_por_compas": acordes_por_compas,
        "tonica_pc": tonica_pc,
    }


def _eventos_a_mensajes(eventos):
    mensajes = []
    for ev in eventos:
        inicio = ev["paso"] * TICKS_POR_PASO
        fin = inicio + max(ev["dur"], 1) * TICKS_POR_PASO
        mensajes.append((inicio, 1, ev["nota"], ev["vel"]))
        mensajes.append((fin, 0, ev["nota"], 0))
    mensajes.sort(key=lambda m: (m[0], m[1]))
    return mensajes


def _track_mido(nombre, eventos, canal, programa, incluir_tempo_bpm=None):
    track = MidiTrack()
    track.append(MetaMessage("track_name", name=nombre, time=0))
    if incluir_tempo_bpm:
        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(incluir_tempo_bpm), time=0))
        track.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    if programa is not None:
        track.append(Message("program_change", program=programa, channel=canal, time=0))
    tiempo_previo = 0
    for tick, tipo, nota, vel in _eventos_a_mensajes(eventos):
        delta = max(tick - tiempo_previo, 0)
        if tipo == 1:
            track.append(Message("note_on", note=nota, velocity=vel, channel=canal, time=delta))
        else:
            track.append(Message("note_off", note=nota, velocity=0, channel=canal, time=delta))
        tiempo_previo = tick
    return track


def exportar_midi_completo(cancion, estilo, bpm, ruta_salida):
    progs = PROGRAMAS[estilo]
    mid = MidiFile(type=1, ticks_per_beat=TICKS_POR_BEAT)

    meta = MidiTrack()
    meta.append(MetaMessage("track_name", name="Tempo", time=0))
    meta.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    meta.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    mid.tracks.append(meta)

    orden = [
        ("Bateria", "bateria", CANALES["bateria"], None),
        ("Bajo", "bajo", CANALES["bajo"], progs["bajo"]),
        ("Piano", "piano", CANALES["piano"], progs["piano"]),
        ("Pad", "pad", CANALES["pad"], progs["pad"]),
        ("Melodia Guia", "melodia", CANALES["melodia"], progs["melodia"]),
    ]
    for nombre, clave, canal, programa in orden:
        mid.tracks.append(_track_mido(nombre, cancion["pistas"][clave], canal, programa))

    mid.save(ruta_salida)


def exportar_midi_individual(cancion, estilo, bpm, clave, ruta_salida):
    progs = PROGRAMAS[estilo]
    canal = CANALES[clave]
    programa = None if clave == "bateria" else progs[clave]
    mid = MidiFile(type=0, ticks_per_beat=TICKS_POR_BEAT)
    mid.tracks.append(_track_mido(clave, cancion["pistas"][clave], canal, programa, incluir_tempo_bpm=bpm))
    mid.save(ruta_salida)


def generar_paquete(estilo, tono, modo, bpm=None, nombre=None, carpeta_base="salida", semilla=42):
    if estilo not in ESTILOS:
        raise ValueError(f"Estilo no reconocido: {estilo}. Opciones: {list(ESTILOS)}")
    if modo not in ("mayor", "menor"):
        raise ValueError("El modo debe ser 'mayor' o 'menor'")

    bpm = bpm or ESTILOS[estilo]["bpm_sugerido"]
    nombre = nombre or f"{estilo}_{tono}{modo}"
    carpeta = os.path.join(carpeta_base, nombre)
    os.makedirs(carpeta, exist_ok=True)

    cancion = construir_cancion(estilo, tono, modo, semilla=semilla)

    ruta_completo = os.path.join(carpeta, "00_cancion_completa.mid")
    exportar_midi_completo(cancion, estilo, bpm, ruta_completo)

    individuales = {}
    for clave, archivo in [
        ("bateria", "01_bateria.mid"), ("bajo", "02_bajo.mid"), ("piano", "03_piano.mid"),
        ("pad", "04_pad.mid"), ("melodia", "05_melodia_guia.mid"),
    ]:
        ruta = os.path.join(carpeta, archivo)
        exportar_midi_individual(cancion, estilo, bpm, clave, ruta)
        individuales[clave] = ruta

    buffer_cantar, sr = sintetizador.renderizar_mezcla(cancion, bpm, ["bateria", "bajo", "piano", "pad"])
    ruta_cantar = os.path.join(carpeta, "pista_para_cantar.wav")
    sintetizador.guardar_wav(ruta_cantar, buffer_cantar, sr)

    buffer_guia, sr = sintetizador.renderizar_mezcla(cancion, bpm, ["bateria", "bajo", "piano", "pad", "melodia"])
    ruta_guia = os.path.join(carpeta, "referencia_con_melodia_guia.wav")
    sintetizador.guardar_wav(ruta_guia, buffer_guia, sr)

    ruta_txt = os.path.join(carpeta, "estructura.txt")
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(f"Pista: {nombre}\n")
        f.write(f"Estilo: {estilo}\n")
        f.write(f"Tonalidad: {tono} {modo}\n")
        f.write(f"Tempo: {bpm} BPM, compás 4/4\n")
        f.write(f"Duración: {cancion['total_compases']} compases\n\n")
        f.write("Estructura:\n")
        for sec in cancion["estructura"]:
            f.write(f"  - {sec['nombre']}: compases {sec['inicio']+1} a {sec['inicio']+sec['compases']}\n")
        f.write("\nAcordes por compas (grado -> notas):\n")
        for compas, grado, pcs in cancion["acordes_por_compas"]:
            notas_str = "-".join(teoria.NOTAS[pc] for pc in pcs)
            f.write(f"  Compas {compas+1:>2}: grado {grado} ({notas_str})\n")
        f.write("\nArchivos:\n")
        f.write("  00_cancion_completa.mid -> las 5 pistas juntas, para importar todo de una vez en FL Studio\n")
        f.write("  01..05_*.mid -> cada instrumento por separado, para arrastrar a un canal ya elegido\n")
        f.write("  pista_para_cantar.wav -> instrumental (bateria+bajo+piano+pad), sin melodia, para cantar encima\n")
        f.write("  referencia_con_melodia_guia.wav -> instrumental + melodia guia mas baja, para aprender la tonada\n")

    return {
        "carpeta": carpeta, "midi_completo": ruta_completo, "midi_individuales": individuales,
        "wav_para_cantar": ruta_cantar, "wav_referencia": ruta_guia, "estructura_txt": ruta_txt,
        "bpm": bpm, "tono": tono, "modo": modo, "cancion": cancion,
    }
