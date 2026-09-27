# -*- coding: utf-8 -*-
"""Backend de la app "Pistas Cristianas": analiza tu voz y genera instrumentales.

Endpoints:
  POST /analizar-tono   (multipart: archivo de audio)  -> tono/registro estimado
  POST /generar-pista   (json: estilo,tono,modo,bpm)   -> zip con MIDI + MP3
  GET  /estilos                                        -> estilos disponibles
"""
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import analizar_audio
import motor

app = FastAPI(title="Pistas Cristianas API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

CARPETA_TRABAJO = os.path.join(tempfile.gettempdir(), "pistas_cristianas_api")
os.makedirs(CARPETA_TRABAJO, exist_ok=True)


class PeticionGenerar(BaseModel):
    estilo: str
    tono: str = "G"
    modo: str = "mayor"
    bpm: int | None = None


@app.get("/estilos")
def listar_estilos():
    return {
        "estilos": list(motor.ESTILOS.keys()),
        "bpm_sugerido": {k: v["bpm_sugerido"] for k, v in motor.ESTILOS.items()},
        "notas_validas": analizar_audio.NOTAS,
        "modos_validos": ["mayor", "menor"],
    }


@app.post("/analizar-tono")
async def analizar_tono(archivo: UploadFile = File(...)):
    id_trabajo = uuid.uuid4().hex[:12]
    ruta_original = os.path.join(CARPETA_TRABAJO, f"{id_trabajo}_orig")
    ruta_wav = os.path.join(CARPETA_TRABAJO, f"{id_trabajo}.wav")

    try:
        with open(ruta_original, "wb") as f:
            shutil.copyfileobj(archivo.file, f)

        resultado_ffmpeg = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", ruta_original,
             "-ar", "16000", "-ac", "1", ruta_wav],
            capture_output=True, text=True,
        )
        if resultado_ffmpeg.returncode != 0 or not os.path.exists(ruta_wav):
            raise HTTPException(400, f"No se pudo leer el audio: {resultado_ffmpeg.stderr[:300]}")

        resultado = analizar_audio.analizar_robusto(ruta_wav)
        if not resultado.get("voz_detectada"):
            raise HTTPException(422, "No se detecto voz/tono en el audio enviado")

        return {
            "tono_estimado": resultado["tonica_estim"],
            "modo_estimado": resultado["modo_estim"],
            "confianza": resultado["confianza"],
            "registro_min_midi": resultado["registro_min_midi"],
            "registro_max_midi": resultado["registro_max_midi"],
            "registro_mediana_midi": resultado["registro_mediana_midi"],
            "duracion_seg": round(resultado["duracion_seg"], 1),
            "nota": "Estimacion automatica: dejar que el usuario la confirme o ajuste medio tono.",
        }
    finally:
        for ruta in (ruta_original, ruta_wav):
            if os.path.exists(ruta):
                os.remove(ruta)


@app.post("/generar-pista")
def generar_pista(peticion: PeticionGenerar):
    if peticion.estilo not in motor.ESTILOS:
        raise HTTPException(400, f"Estilo invalido. Opciones: {list(motor.ESTILOS.keys())}")
    if peticion.modo not in ("mayor", "menor"):
        raise HTTPException(400, "Modo invalido: usa 'mayor' o 'menor'")

    id_trabajo = uuid.uuid4().hex[:12]
    carpeta_salida = os.path.join(CARPETA_TRABAJO, id_trabajo)

    try:
        resultado = motor.generar_paquete(
            estilo=peticion.estilo, tono=peticion.tono, modo=peticion.modo,
            bpm=peticion.bpm, nombre="pista", carpeta_base=carpeta_salida,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    carpeta_pista = resultado["carpeta"]
    for wav in ["pista_para_cantar.wav", "referencia_con_melodia_guia.wav"]:
        ruta_wav = os.path.join(carpeta_pista, wav)
        if os.path.exists(ruta_wav):
            ruta_mp3 = ruta_wav[:-4] + ".mp3"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", ruta_wav,
                 "-codec:a", "libmp3lame", "-qscale:a", "4", ruta_mp3],
                check=True,
            )
            os.remove(ruta_wav)

    ruta_zip = os.path.join(CARPETA_TRABAJO, f"{id_trabajo}.zip")
    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for raiz, _, archivos in os.walk(carpeta_pista):
            for nombre_archivo in archivos:
                ruta_completa = os.path.join(raiz, nombre_archivo)
                zf.write(ruta_completa, arcname=nombre_archivo)

    return FileResponse(
        ruta_zip, media_type="application/zip",
        filename=f"pista_{peticion.estilo}_{peticion.tono}{peticion.modo}.zip",
    )


@app.get("/salud")
def salud():
    return {"ok": True}
