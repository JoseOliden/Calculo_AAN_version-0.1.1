import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import io
import json
from datetime import datetime
from scipy.optimize import root
import sympy as sp
import matplotlib.pyplot as plt
import tempfile
import base64
# ------------------ RPT ---------------------------------
def limpiar(valor):
    if isinstance(valor, str):
        # 1. quitar solo un espacio inicial si existe
        if valor.startswith(" "):
            valor = valor[1:]
        # 2. quitar espacios al final completamente
        valor = valor.rstrip()
    return valor


def procesar_RPT(rpt_file):
    if rpt_file is None:
        return None

    # 1. Leer directo desde uploader sin guardarlo
    contenido = rpt_file.read().decode("utf-8", errors="ignore")

    # 2. Convertir a pandas como una fila por línea
    lineas = contenido.splitlines()
    df = pd.DataFrame(lineas, columns=["linea"])

    # 3. Eliminar primeras 19 filas
    df = df.iloc[19:].reset_index(drop=True)

    # 4. Crear columna auxiliar sin espacios
    df["sin_espacios"] = df["linea"].str.lstrip()

    # 5. Filtrar patrones a eliminar
    patrones_excluir = ("Peak", "M =", "m =", "F =", "Error")
    df = df[~df["sin_espacios"].str.startswith(patrones_excluir)]

    # 6. Eliminar líneas que empiezan con exactamente 3 espacios
    df = df[~df["linea"].str.startswith("   ")]

    # 7. Eliminar líneas vacías o solo con espacios
    df = df[~df["linea"].str.strip().eq("")]

    # 8. Eliminar columna auxiliar
    df = df.drop(columns=["sin_espacios"])

    # 9. Reiniciar índices
    df = df.reset_index(drop=True)

    # 10. Quitar 1 espacio inicial (si hay) y todos los finales
    df = df.applymap(limpiar)

    # 11. Separar columnas
    df_tab = df["linea"].str.split(r"\s+", expand=True)

    # 12. Asignar nombres de columnas
    df_tab.columns = [
        "Tipo", "Peak No.", "ROI Start", "ROI End", "Peak Centroid",
        "Energy (keV)", "Net Peak Area", "Net Peak Uncert",
        "Continuum Counts", "Tentative Nuclide"
    ]

    st.success("Archivo procesado correctamente 🚀")
    
    return df_tab

# ------------------ kos ---------------------------------

def extraer_DATE_MEAS_TIM(kos_file):
    if kos_file is None:
        return None

    # Leer sin consumir el buffer
    contenido = kos_file.getvalue().decode("utf-8", errors="ignore")
    lineas = contenido.splitlines()

    fecha = hora = tiempo_real = tiempo_vivo = None

    for linea in lineas:
        linea = linea.strip()

        # ----------------- DATE_MEA -----------------
        if linea.startswith("$DATE_MEA"):
            partes = linea.split()
            # $DATE_MEA YYYY-MM-DD HH:MM:SS
            if len(partes) >= 3:
                fecha = partes[1]
                hora = partes[2]

        # ----------------- MEAS_TIM -----------------
        if linea.startswith("$MEAS_TIM"):
            partes = linea.split()
            # $MEAS_TIM TR TL
            if len(partes) >= 3:
                tiempo_real = partes[1]
                tiempo_vivo = partes[2]

    return fecha, hora, tiempo_real, tiempo_vivo

