import pdfplumber
import pandas as pd
import re
from sqlalchemy import create_engine

# =========================================================
# PDFs
# =========================================================

pdfs = [
    {
    "path": "/workspaces/proyectoBOE/DATOS/TAI_L_GE_154AB89SD658.PDF_2019.pdf",
    "flag": "GENERAL"
    },
    {
    "path": "/workspaces/proyectoBOE/DATOS/TAI_L_CRD_154AB89SD658.PDF_2019.pdf",
    "flag": "CUPO"
    }
]

# =========================================================
# PROVINCIAS
# =========================================================

provincias = [
    "SANTA CRUZ DE TENERIFE",
    "S.C. DE TENERIFE",
    "A CORUÑA",
    "LA CORUÑA",
    "ALAVA",
    "ALBACETE",
    "ALICANTE",
    "ALMERIA",
    "ASTURIAS",
    "AVILA",
    "BADAJOZ",
    "BARCELONA",
    "BIZKAIA",
    "BURGOS",
    "CACERES",
    "CADIZ",
    "CANTABRIA",
    "CASTELLON",
    "CEUTA",
    "CIUDAD REAL",
    "CORDOBA",
    "CUENCA",
    "GIRONA",
    "GRANADA",
    "GUADALAJARA",
    "GIPUZKOA",
    "HUELVA",
    "HUESCA",
    "ILLES BALEARS",
    "JAEN",
    "LA RIOJA",
    "LAS PALMAS",
    "LEON",
    "LLEIDA",
    "LUGO",
    "MADRID",
    "MALAGA",
    "MELILLA",
    "MURCIA",
    "NAVARRA",
    "OURENSE",
    "PALENCIA",
    "PONTEVEDRA",
    "SALAMANCA",
    "SEGOVIA",
    "SEVILLA",
    "SORIA",
    "TARRAGONA",
    "TERUEL",
    "TOLEDO",
    "VALENCIA",
    "VALLADOLID",
    "ZAMORA",
    "ZARAGOZA"
]

# =========================================================
# NORMALIZACIÓN PROVINCIAS
# =========================================================

provincias_alias = {
    "S.C. DE TENERIFE": "SANTA CRUZ DE TENERIFE",
    "LA CORUÑA": "A CORUÑA"
}

# ordenar por longitud descendente
provincias = sorted(provincias, key=len, reverse=True)

# =========================================================
# REGEX NIF
# =========================================================

pattern_nif = r"\*+\s*\d+\s*\*+"

rows = []
debug_rows = []

# =========================================================
# PROCESAR PDFs
# =========================================================

for pdf in pdfs:

    print(f"\nProcesando PDF: {pdf['flag']}")

    with pdfplumber.open(pdf["path"]) as documento:

        for num_pagina, pagina in enumerate(documento.pages, start=1):

            print(f"\n================ PAGINA {num_pagina} ================\n")

            texto = pagina.extract_text()

            if not texto:
                continue

            lineas = texto.split("\n")

            for line in lineas:

                line = line.replace("\xa0", " ")

                line = re.sub(r"\s+", " ", line).strip()

                if not line:
                    continue

                # =================================================
                # DEBUG
                # =================================================

                print("\nRAW LINE:")
                print(repr(line))

                debug_rows.append({
                    "PDF": pdf["flag"],
                    "PAGINA": num_pagina,
                    "RAW": line
                })

                # =================================================
                # DIVIDIR POR NIF
                # =================================================

                partes = re.split(f"({pattern_nif})", line)

                registros = []

                for i in range(1, len(partes), 2):

                    nif = partes[i].strip()

                    texto_registro = ""

                    if i + 1 < len(partes):
                        texto_registro = partes[i + 1].strip()

                    reg = f"{nif} {texto_registro}".strip()

                    registros.append(reg)

                print("\nREGISTROS EXTRAIDOS:")

                for r in registros:
                    print(repr(r))

                # =================================================
                # PARSEAR REGISTROS
                # =================================================

                for reg in registros:

                    print("\n--- PARSEANDO REGISTRO ---")
                    print(repr(reg))

                    reg = re.sub(r"\s+", " ", reg).strip()

                    nif_match = re.match(pattern_nif, reg)

                    if not nif_match:
                        print("SIN NIF")
                        continue

                    nif = nif_match.group()

                    nif = re.sub(r"\s+", "", nif)

                    print(f"NIF: {nif}")

                    resto = reg[len(nif_match.group()):].strip()

                    print(f"RESTO: {resto}")

                    # -------------------------------------------------
                    # DETECTAR PROVINCIA
                    # -------------------------------------------------

                    provincia = None

                    for p in provincias:

                        if resto.endswith(p):

                            provincia = p

                            resto = resto[:-len(p)].strip()

                            break

                    if provincia:
                        provincia = provincias_alias.get(
                            provincia,
                            provincia
                        )

                    print(f"PROVINCIA: {provincia}")
                    print(f"RESTO SIN PROVINCIA: {resto}")

                    if not provincia:
                        print("SIN PROVINCIA")
                        continue

                    # -------------------------------------------------
                    # SEPARAR APELLIDOS / NOMBRE
                    # -------------------------------------------------

                    if "," not in resto:
                        print("SIN COMA")
                        continue

                    partes_nombre = resto.rsplit(",", 1)

                    if len(partes_nombre) != 2:
                        print("SPLIT INVALIDO")
                        continue

                    apellidos = partes_nombre[0].strip()
                    nombre = partes_nombre[1].strip()

                    print(f"APELLIDOS: {apellidos}")
                    print(f"NOMBRE: {nombre}")

                    rows.append({
                        "FLAG": pdf["flag"],
                        "NIF": nif,
                        "APELLIDOS": apellidos,
                        "NOMBRE": nombre,
                        "PROVINCIA": provincia
                    })

                    print(">> REGISTRO INSERTADO")

# =========================================================
# DATAFRAME FINAL
# =========================================================

df_final = pd.DataFrame(rows)

df_final = df_final.drop_duplicates()

print("\nPrimeras filas:")
print(df_final.head())

print(f"\nFilas extraídas: {len(df_final)}")

# =========================================================
# EXPORTAR CSV FINAL
# =========================================================

df_final.to_csv(
    "admitidos.csv",
    index=False,
    encoding="utf-8"
)

print("\nCSV generado: admitidos.csv")

# =========================================================
# EXPORTAR DEBUG CSV
# =========================================================

df_debug = pd.DataFrame(debug_rows)

df_debug.to_csv(
    "pdfplumber_raw.csv",
    index=False,
    encoding="utf-8"
)

print("\nCSV debug generado: pdfplumber_raw.csv")

# =========================================================
# POSTGRESQL
# =========================================================

engine = create_engine(
    "postgresql+psycopg2://admin:admin@localhost:5432/oposiciones"
)

df_final.to_sql(
    "admitidos_prueba",
    engine,
    if_exists="replace",
    index=False,
    method="multi",
    chunksize=1000
)

print("\nTabla 'admitidos_prueba' cargada")