import pdfplumber
import pandas as pd
import re
from sqlalchemy import create_engine

# =========================================================
# PDFs
# =========================================================

pdfs = [
    {
        "path": "/workspaces/proyectoBOE/DATOS/07TAI_L_01GE_154AB89SD658.pdf",
        "flag": "GENERAL"
    },
    {
        "path": "/workspaces/proyectoBOE/DATOS/07TAI_L_02CRD_154AB89SD658.pdf",
        "flag": "CUPO"
    }
]

# =========================================================
# REGEX NIF
# =========================================================

pattern_nif = r"\*+\d+\*+"

# =========================================================
# RESULTADOS
# =========================================================

rows = []
debug_rows = []

# =========================================================
# PROCESAR PDFs
# =========================================================

for pdf in pdfs:

    print(f"\nProcesando PDF: {pdf['flag']}")

    with pdfplumber.open(pdf["path"]) as documento:

        for num_pagina, pagina in enumerate(documento.pages, start=1):

            print(f"\n========= PAGINA {num_pagina} =========\n")

            texto = pagina.extract_text()

            if not texto:
                continue

            lineas = texto.split("\n")

            for line in lineas:

                # =================================================
                # LIMPIEZA
                # =================================================

                line = line.replace("\xa0", " ")
                line = re.sub(r"\s+", " ", line).strip()

                if not line:
                    continue

                # =================================================
                # DEBUG
                # =================================================

                print("\nRAW:")
                print(line)

                debug_rows.append({
                    "PDF": pdf["flag"],
                    "PAGINA": num_pagina,
                    "RAW": line
                })

                # =================================================
                # SALTAR CABECERAS
                # =================================================

                if any(x in line.upper() for x in [
                    "NIF APELLIDOS",
                    "PRUEBAS SELECTIVAS",
                    "RELACIÓN GENERAL",
                    "SISTEMA DE ACCESO",
                    "INSTITUTO NACIONAL",
                    "COMISIÓN PERMANENTE",
                    "MINISTERIO",
                    "FUNCIÓN PÚBLICA",
                    "Nº REGISTROS",
                    "PÁGINA"
                ]):
                    continue

                # =================================================
                # DEBE CONTENER NIF
                # =================================================

                if "***" not in line:
                    continue

                # =================================================
                # EXTRAER REGISTROS POR NIF
                # =================================================

                matches = list(re.finditer(pattern_nif, line))

                if not matches:
                    continue

                for i in range(len(matches)):

                    start = matches[i].start()

                    if i + 1 < len(matches):
                        end = matches[i + 1].start()
                    else:
                        end = len(line)

                    reg = line[start:end].strip()

                    print("\nREGISTRO:")
                    print(reg)

                    # =================================================
                    # EXTRAER NIF
                    # =================================================

                    nif_match = re.match(pattern_nif, reg)

                    if not nif_match:
                        continue

                    nif = nif_match.group()

                    # =================================================
                    # RESTO
                    # =================================================

                    resto = reg[len(nif):].strip()

                    # =================================================
                    # ELIMINAR L FINAL
                    # =================================================

                    resto = re.sub(r"\s+L\s*$", "", resto).strip()

                    print(f"RESTO: {resto}")

                    # =================================================
                    # SEPARAR APELLIDOS / NOMBRE
                    # =================================================

                    if "," not in resto:
                        print("NO COMA")
                        continue

                    partes = resto.rsplit(",", 1)

                    if len(partes) != 2:
                        continue

                    apellidos = partes[0].strip()
                    nombre = partes[1].strip()

                    # =================================================
                    # LIMPIEZA FINAL
                    # =================================================

                    apellidos = re.sub(r",\s*$", "", apellidos)
                    nombre = re.sub(r",\s*$", "", nombre)

                    # =================================================
                    # INSERTAR
                    # =================================================

                    rows.append({
                        "FLAG": pdf["flag"],
                        "NIF": nif,
                        "APELLIDOS": apellidos,
                        "NOMBRE": nombre,
                        "PROVINCIA": None
                    })

                    print("INSERTADO")

# =========================================================
# DATAFRAME FINAL
# =========================================================

df_final = pd.DataFrame(rows)

df_final = df_final.drop_duplicates()

print("\n================ RESULTADO ================\n")

print(df_final.head())

print(f"\nTOTAL FILAS: {len(df_final)}")

# =========================================================
# EXPORTAR CSV
# =========================================================

df_final.to_csv(
    "admitidos.csv",
    index=False,
    encoding="utf-8"
)

print("\nCSV generado: admitidos.csv")

# =========================================================
# EXPORTAR DEBUG
# =========================================================

df_debug = pd.DataFrame(debug_rows)

df_debug.to_csv(
    "debug_raw.csv",
    index=False,
    encoding="utf-8"
)

print("\nCSV debug generado: debug_raw.csv")

# =========================================================
# POSTGRESQL
# =========================================================

engine = create_engine(
    "postgresql+psycopg2://admin:admin@localhost:5432/oposiciones"
)

# =========================================================
# CARGAR TABLA
# =========================================================

df_final.to_sql(
    "admitidos_prueba",
    engine,
    if_exists="replace",
    index=False,
    method="multi",
    chunksize=1000
)

print("\nTabla admitidos_prueba cargada")