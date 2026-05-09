import camelot
import pandas as pd
import requests
from lxml import etree
from sqlalchemy import create_engine

pdfs = [
    {
        "path": "/workspaces/proyectoBOE/DATOS/TIC-L-ADM-SA-ALF_GE_154AB89SD658.pdf",
        "flag": "GENERAL"
    },
    {
        "path": "/workspaces/proyectoBOE/DATOS/TIC-L-ADM-SA-ALF_CRD_154AB89SD658.pdf",
        "flag": "CUPO"
    }
]

rows = []

for pdf in pdfs:

    print(f"\nProcesando PDF: {pdf['flag']}")

    tables = camelot.read_pdf(
        pdf["path"],
        pages="all",
        flavor="stream"
    )

    for table in tables:

        df = table.df

        for _, row in df.iterrows():

            row = [str(x).strip() for x in row.tolist()]

            # eliminar filas vacías
            row = [x for x in row if x]

            if not row:
                continue

            line = " ".join(row)

            # saltar cabeceras
            if any(x in line for x in [
                "MINISTERIO",
                "RELACIÓN GENERAL",
                "SISTEMA DE ACCESO",
                "TIC-L-ADM",
                "NIF APELLIDOS",
                "EXAMEN",
                "INSTITUTO NACIONAL"
            ]):
                continue

            # comprobar que empieza por NIF anonimizado
            if not line.startswith("*"):
                continue

            # dividir NIF
            parts = line.split()

            nif = parts[0]

            # reconstruir resto
            resto = " ".join(parts[1:])

            # separar provincia usando lista conocida
            provincias = [
                "A CORUÑA",
                "ALAVA",
                "ALBACETE",
                "ALICANTE",
                "ALMERIA",
                "ASTURIAS",
                "AVILA",
                "BADAJOZ",
                "BARCELONA",
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
                "SANTA CRUZ DE TENERIFE",
                "SEGOVIA",
                "SEVILLA",
                "SORIA",
                "TARRAGONA",
                "TERUEL",
                "TOLEDO",
                "VALENCIA",
                "VALLADOLID",
                "BIZKAIA",
                "ZAMORA",
                "ZARAGOZA"
         ]

            provincia = ""

            for p in provincias:

                if resto.endswith(p):

                    provincia = p

                    resto = resto[:-len(p)].strip()

                    break

            # separar apellidos y nombre
            if "," in resto:

                apellidos, nombre = resto.split(",", 1)

            else:

                apellidos = resto
                nombre = ""

            rows.append({
                "FLAG": pdf["flag"],
                "NIF": nif,
                "APELLIDOS": apellidos.strip(),
                "NOMBRE": nombre.strip(),
                "PROVINCIA": provincia.strip()
            })

df_final = pd.DataFrame(rows)

print(df_final.head())

print(f"\nFilas extraídas: {len(df_final)}")

df_final.to_csv("admitidos.csv", index=False)

print("\nCSV generado: admitidos.csv")


# ----------------------------------------
# conexión PostgreSQL
# ----------------------------------------

engine = create_engine(
    "postgresql+psycopg2://admin:admin@localhost:5432/oposiciones"
)

# =========================================================
# 1. CARGAR CSV DE ADMITIDOS
# =========================================================

df_admitidos = pd.read_csv("admitidos.csv")

print("\nADMITIDOS")
print(df_admitidos.head())

df_admitidos.to_sql(
    "admitidos",
    engine,
    if_exists="append",
    index=False
)

print("\nTabla 'admitidos' cargada")
