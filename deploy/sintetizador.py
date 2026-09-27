# -*- coding: utf-8 -*-
"""Sintetizador simple (numpy) para escuchar las pistas sin necesidad de FL Studio."""

import wave
import numpy as np

SR = 44100


def freq_de_midi(nota):
    return 440.0 * 2.0 ** ((nota - 69) / 12.0)


def synth_pad(nota, vel, dur_seg, sr=SR):
    freq = freq_de_midi(nota)
    ataque, liberacion = 0.35, 0.6
    n = int((dur_seg + liberacion) * sr)
    t = np.arange(n) / sr
    onda = (0.55 * np.sin(2 * np.pi * freq * t)
            + 0.3 * np.sin(2 * np.pi * freq * 1.004 * t)
            + 0.15 * np.sin(2 * np.pi * freq * 2 * t))
    env = np.ones(n)
    n_atk, n_rel = int(ataque * sr), int(liberacion * sr)
    if n_atk > 0:
        env[:min(n_atk, n)] = np.linspace(0, 1, min(n_atk, n))
    if n_rel > 0:
        env[-n_rel:] *= np.linspace(1, 0, n_rel)
    return onda * env * (vel / 127.0) * 0.22


def synth_piano(nota, vel, dur_seg, sr=SR):
    freq = freq_de_midi(nota)
    cola = 0.3
    n = int((dur_seg + cola) * sr)
    t = np.arange(n) / sr
    onda = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t) + 0.22 * np.sin(2 * np.pi * freq * 3 * t)
    decaimiento = np.exp(-2.2 * t / max(dur_seg, 0.25))
    n_atk = int(0.005 * sr)
    env = np.ones(n)
    if n_atk > 0:
        env[:n_atk] = np.linspace(0, 1, n_atk)
    return onda * env * decaimiento * (vel / 127.0) * 0.20


def synth_bajo(nota, vel, dur_seg, sr=SR):
    freq = freq_de_midi(nota)
    cola = 0.15
    n = int((dur_seg + cola) * sr)
    t = np.arange(n) / sr
    onda = np.sin(2 * np.pi * freq * t) + 0.2 * np.sign(np.sin(2 * np.pi * freq * t))
    decaimiento = np.exp(-1.0 * t / max(dur_seg, 0.3))
    n_atk = int(0.006 * sr)
    env = np.ones(n)
    if n_atk > 0:
        env[:n_atk] = np.linspace(0, 1, n_atk)
    return onda * env * decaimiento * (vel / 127.0) * 0.32


def synth_melodia(nota, vel, dur_seg, sr=SR):
    freq = freq_de_midi(nota)
    liberacion = 0.12
    n = int((dur_seg + liberacion) * sr)
    t = np.arange(n) / sr
    vibrato = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    onda = np.sin(2 * np.pi * freq * vibrato * t) + 0.15 * np.sin(2 * np.pi * freq * 2 * vibrato * t)
    n_atk, n_rel = int(0.04 * sr), int(liberacion * sr)
    env = np.ones(n)
    if n_atk > 0:
        env[:n_atk] = np.linspace(0, 1, n_atk)
    if n_rel > 0:
        env[-n_rel:] *= np.linspace(1, 0, n_rel)
    return onda * env * (vel / 127.0) * 0.28


def synth_bateria(tipo_nota, vel, sr=SR):
    rng = np.random.default_rng((int(tipo_nota) * 1000 + int(vel)) % (2 ** 32))
    amp = vel / 127.0
    if tipo_nota == 36:  # kick
        n = int(0.22 * sr); t = np.arange(n) / sr
        freq = np.linspace(150, 45, n)
        onda = np.sin(2 * np.pi * np.cumsum(freq) / sr)
        return onda * np.exp(-9 * t) * amp * 0.9
    if tipo_nota == 38:  # snare
        n = int(0.18 * sr); t = np.arange(n) / sr
        ruido = rng.uniform(-1, 1, n)
        tono = np.sin(2 * np.pi * 190 * t)
        return (0.7 * ruido + 0.5 * tono) * np.exp(-14 * t) * amp * 0.7
    if tipo_nota == 39:  # clap
        n = int(0.15 * sr); t = np.arange(n) / sr
        ruido = rng.uniform(-1, 1, n)
        pulso = np.zeros(n)
        for despl in (0.0, 0.008, 0.016):
            k = int(despl * sr)
            pulso[k:] += ruido[:n - k] * np.exp(-30 * t[:n - k])
        return pulso * amp * 0.55
    if tipo_nota == 42:  # hihat cerrado
        n = int(0.06 * sr); t = np.arange(n) / sr
        ruido_hp = np.diff(rng.uniform(-1, 1, n), prepend=0)
        return ruido_hp * np.exp(-40 * t) * amp * 0.5
    if tipo_nota == 46:  # hihat abierto
        n = int(0.22 * sr); t = np.arange(n) / sr
        ruido_hp = np.diff(rng.uniform(-1, 1, n), prepend=0)
        return ruido_hp * np.exp(-10 * t) * amp * 0.45
    if tipo_nota == 49:  # crash
        n = int(1.0 * sr); t = np.arange(n) / sr
        ruido_hp = np.diff(rng.uniform(-1, 1, n), prepend=0)
        return ruido_hp * np.exp(-3 * t) * amp * 0.4
    if tipo_nota == 51:  # ride
        n = int(0.4 * sr); t = np.arange(n) / sr
        ruido = rng.uniform(-1, 1, n)
        tono = np.sin(2 * np.pi * 450 * t)
        return (0.5 * ruido + 0.5 * tono) * np.exp(-6 * t) * amp * 0.35
    return np.zeros(1)


GENERADORES = {"pad": synth_pad, "piano": synth_piano, "bajo": synth_bajo, "melodia": synth_melodia}
VOLUMEN_PISTA = {"pad": 1.0, "piano": 1.0, "bajo": 1.05, "melodia": 0.55, "bateria": 0.9}


def renderizar_mezcla(cancion, bpm, incluir_pistas, sr=SR, cola_seg=2.0):
    seg_por_paso = 60.0 / bpm / 4.0
    pasos_max = 0
    for clave in incluir_pistas:
        for ev in cancion["pistas"][clave]:
            pasos_max = max(pasos_max, ev["paso"] + max(ev["dur"], 1))
    duracion_total = pasos_max * seg_por_paso + cola_seg
    n_total = int(duracion_total * sr) + sr
    buffer = np.zeros(n_total)

    for clave in incluir_pistas:
        vol = VOLUMEN_PISTA.get(clave, 1.0)
        for ev in cancion["pistas"][clave]:
            inicio_seg = ev["paso"] * seg_por_paso
            dur_seg = max(ev["dur"], 1) * seg_por_paso
            if clave == "bateria":
                onda = synth_bateria(ev["nota"], ev["vel"], sr=sr)
            else:
                onda = GENERADORES[clave](ev["nota"], ev["vel"], dur_seg, sr=sr)
            i0 = int(inicio_seg * sr)
            i1 = i0 + len(onda)
            if i1 > n_total:
                onda = onda[: n_total - i0]
                i1 = n_total
            if i1 > i0:
                buffer[i0:i1] += onda * vol

    pico = np.max(np.abs(buffer)) if buffer.size else 0.0
    if pico > 0:
        buffer = buffer / pico * 0.9
    return buffer, sr


def guardar_wav(ruta, buffer_mono, sr):
    audio_int16 = np.int16(np.clip(buffer_mono, -1, 1) * 32767)
    estereo = np.column_stack([audio_int16, audio_int16]).flatten()
    with wave.open(ruta, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(estereo.tobytes())
