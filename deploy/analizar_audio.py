# -*- coding: utf-8 -*-
"""Analiza un WAV (voz/tarareo) para estimar tono fundamental y tonalidad probable."""
import sys
import numpy as np
from scipy.io import wavfile

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Perfiles de Krumhansl-Kessler (mayor / menor), 12 valores por semitono desde la tonica
PERFIL_MAYOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
PERFIL_MENOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def freq_a_pc_y_midi(freq):
    midi = 69 + 12 * np.log2(freq / 440.0)
    midi_red = int(round(midi))
    return midi_red % 12, midi_red


def detectar_f0_autocorr(frame, sr, f_min=70, f_max=500):
    frame = frame - np.mean(frame)
    energia = np.sum(frame ** 2)
    if energia < 1e-6:
        return None
    ventana = np.hanning(len(frame))
    frame = frame * ventana
    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2:]
    lag_min = int(sr / f_max)
    lag_max = int(sr / f_min)
    if lag_max >= len(corr):
        lag_max = len(corr) - 1
    if lag_min >= lag_max:
        return None
    segmento = corr[lag_min:lag_max]
    if len(segmento) == 0 or corr[0] <= 0:
        return None
    pico_idx = np.argmax(segmento) + lag_min
    claridad = corr[pico_idx] / corr[0]
    if claridad < 0.35:
        return None
    freq = sr / pico_idx
    return freq


def analizar(ruta_wav, tam_frame_ms=40, salto_ms=20):
    sr, datos = wavfile.read(ruta_wav)
    if datos.dtype != np.float32 and datos.dtype != np.float64:
        datos = datos.astype(np.float64) / 32768.0
    if datos.ndim > 1:
        datos = datos.mean(axis=1)

    tam_frame = int(sr * tam_frame_ms / 1000)
    salto = int(sr * salto_ms / 1000)

    f0s = []
    midis = []
    for inicio in range(0, len(datos) - tam_frame, salto):
        frame = datos[inicio:inicio + tam_frame]
        f0 = detectar_f0_autocorr(frame, sr)
        if f0:
            pc, midi = freq_a_pc_y_midi(f0)
            f0s.append(f0)
            midis.append(midi)

    if not midis:
        return {"voz_detectada": False}

    midis = np.array(midis)
    pcs = midis % 12
    histograma = np.bincount(pcs, minlength=12).astype(float)
    histograma_norm = histograma / histograma.sum()

    mejor_score, mejor_tonica, mejor_modo = -1e9, 0, "mayor"
    for tonica in range(12):
        perfil_mayor_rot = np.roll(PERFIL_MAYOR, tonica)
        perfil_menor_rot = np.roll(PERFIL_MENOR, tonica)
        score_mayor = np.corrcoef(histograma_norm, perfil_mayor_rot)[0, 1]
        score_menor = np.corrcoef(histograma_norm, perfil_menor_rot)[0, 1]
        if score_mayor > mejor_score:
            mejor_score, mejor_tonica, mejor_modo = score_mayor, tonica, "mayor"
        if score_menor > mejor_score:
            mejor_score, mejor_tonica, mejor_modo = score_menor, tonica, "menor"

    return {
        "voz_detectada": True,
        "duracion_seg": len(datos) / sr,
        "n_frames_voz": len(midis),
        "midi_min": int(midis.min()),
        "midi_max": int(midis.max()),
        "midi_mediana": float(np.median(midis)),
        "nota_mas_comun": NOTAS[int(np.argmax(histograma))],
        "tonica_estim": NOTAS[mejor_tonica],
        "modo_estim": mejor_modo,
        "confianza": float(mejor_score),
        "histograma_pc": {NOTAS[i]: round(float(histograma_norm[i]), 3) for i in range(12)},
    }


def _extraer_f0_serie(datos, sr, tam_frame_ms=40, salto_ms=20):
    tam_frame = int(sr * tam_frame_ms / 1000)
    salto = int(sr * salto_ms / 1000)
    tiempos, midis = [], []
    for inicio in range(0, len(datos) - tam_frame, salto):
        frame = datos[inicio:inicio + tam_frame]
        f0 = detectar_f0_autocorr(frame, sr)
        if f0:
            _, midi = freq_a_pc_y_midi(f0)
            tiempos.append(inicio / sr)
            midis.append(midi)
    return np.array(tiempos), np.array(midis)


def _estimar_tonalidad(midis):
    pcs = midis.astype(int) % 12
    hist = np.bincount(pcs, minlength=12).astype(float)
    histn = hist / hist.sum()
    mejor_score, mejor_tonica, mejor_modo = -1e9, 0, "mayor"
    for tonica in range(12):
        pm, pn = np.roll(PERFIL_MAYOR, tonica), np.roll(PERFIL_MENOR, tonica)
        sm = np.corrcoef(histn, pm)[0, 1]
        sn = np.corrcoef(histn, pn)[0, 1]
        if sm > mejor_score:
            mejor_score, mejor_tonica, mejor_modo = sm, tonica, "mayor"
        if sn > mejor_score:
            mejor_score, mejor_tonica, mejor_modo = sn, tonica, "menor"
    return NOTAS[mejor_tonica], mejor_modo, float(mejor_score), {NOTAS[i]: round(float(histn[i]), 3) for i in range(12)}


def analizar_robusto(ruta_wav, ventana_seg=2.0, paso_seg=0.5, umbral_std=2.5):
    """Estima tonalidad y registro vocal. Da mas peso a los tramos donde el tono se
    mantiene mas estable (2s con poca variacion), que suelen ser mas fiables para
    fijar una tonalidad que el resto del audio.

    OJO: esto NO distingue canto de habla de forma confiable (se probo y la
    heuristica obvia -fraccion de tramos estables- da resultados inconsistentes:
    en pruebas, una nota de voz hablada salio con mas tramos "estables" que una
    cantada). Por eso el resultado siempre debe tratarse como una ESTIMACION
    editable por el usuario, nunca como un hecho confirmado."""
    sr, datos = wavfile.read(ruta_wav)
    if datos.dtype not in (np.float32, np.float64):
        datos = datos.astype(np.float64) / 32768.0
    if datos.ndim > 1:
        datos = datos.mean(axis=1)

    tiempos, midis = _extraer_f0_serie(datos, sr)
    duracion = len(datos) / sr
    if len(midis) == 0:
        return {"voz_detectada": False, "duracion_seg": duracion}

    seleccion = []
    t = 0.0
    n_ventanas_con_voz, n_ventanas_estables = 0, 0
    while t < duracion:
        mask = (tiempos >= t) & (tiempos < t + ventana_seg)
        sub = midis[mask]
        if len(sub) > 5:
            n_ventanas_con_voz += 1
            if np.std(sub) < umbral_std:
                n_ventanas_estables += 1
                seleccion.extend(sub.tolist())
        t += paso_seg

    fraccion_estable = n_ventanas_estables / n_ventanas_con_voz if n_ventanas_con_voz else 0.0

    base = {
        "voz_detectada": True,
        "duracion_seg": duracion,
        "fraccion_tramos_estables": round(fraccion_estable, 2),
    }

    usar = np.array(seleccion) if len(seleccion) > 20 else midis
    tonica, modo, confianza, histograma = _estimar_tonalidad(usar)
    base.update({
        "tonica_estim": tonica,
        "modo_estim": modo,
        "confianza": round(confianza, 2),
        "registro_min_midi": int(usar.min()),
        "registro_max_midi": int(usar.max()),
        "registro_mediana_midi": float(np.median(usar)),
        "histograma_pc": histograma,
        "n_frames_usados": int(len(usar)),
    })
    return base


if __name__ == "__main__":
    ruta = sys.argv[1]
    r = analizar_robusto(ruta)
    for k, v in r.items():
        print(f"{k}: {v}")
