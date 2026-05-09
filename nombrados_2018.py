import requests
from lxml import etree

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String
)

# ==========================================
# DESCARGAR XML
# ==========================================

URL = "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2021-2658"

response = requests.get(URL)
response.raise_for_status()

root = etree.fromstring(response.content)

# ==========================================
# EXTRAER TABLA
# ==========================================

tabla = root.xpath(
    ".//table[contains(@class,'tabla_girada')]"
)[1]

filas = tabla.xpath(".//tr")

datos = []

for fila in filas:

    celdas = fila.xpath("./th | ./td")

    valores = [
        "".join(celda.itertext()).strip()
        for celda in celdas
    ]

    if valores:
        datos.append(valores)

# mostrar cabecera
print("\nCABECERA:")
print(datos[0])

# ==========================================
# CONEXIÓN POSTGRESQL
# ==========================================

engine = create_engine(
    "postgresql+psycopg2://admin:admin@localhost:5432/oposiciones"
)

metadata = MetaData()

# ==========================================
# DEFINIR TABLA
# ==========================================

nombrados = Table(
    "nombrados",
    metadata,

    Column("id", Integer, primary_key=True, autoincrement=True),

    Column("nops", String),
    Column("doc_iden", String),

    Column("apellidos", String),
    Column("nombre", String),

    Column("ministerio", String),
    Column("centro_directivo", String),
    Column("centro_destino", String),

    Column("provincia", String),
    Column("localidad", String),

    Column("puesto_trabajo", String),
    Column("codigo_pt", String),
    Column("nivel_cd", String),
    Column("complemento_especifico", String),
)

# crear tabla si no existe
metadata.create_all(engine)

# ==========================================
# INSERTAR DATOS
# ==========================================

insertadas = 0

with engine.begin() as conn:

    # saltar cabecera
    for fila in datos[1:]:

        # ignorar filas basura
        if len(fila) < 9:
            print("Fila ignorada:", fila)
            continue

        # ignorar índice de abreviaturas
        if "Índice de abreviaturas" in fila[0]:
            continue

        # ==================================
        # NOMBRE
        # ==================================

        nombre_completo = fila[2]

        partes = nombre_completo.split(",")

        apellidos = partes[0].strip()

        nombre = partes[1].strip() if len(partes) > 1 else ""

        # ==================================
        # MINISTERIO / CENTROS
        # ==================================

        bloques = [
            x.strip("- ").strip()
            for x in fila[3].split("\n")
            if x.strip()
        ]

        ministerio = (
            bloques[0]
            if len(bloques) > 0 else ""
        )

        centro_directivo = (
            bloques[1]
            if len(bloques) > 1 else ""
        )

        centro_destino = (
            bloques[2]
            if len(bloques) > 2 else ""
        )

        # ==================================
        # LOCALIDAD / PROVINCIA
        # ==================================

        ubicacion = [
            x.strip("- ").strip(". ").strip()
            for x in fila[4].split("\n")
            if x.strip()
        ]

        localidad = (
            ubicacion[0]
            if len(ubicacion) > 0 else ""
        )

        provincia = (
            ubicacion[1]
            if len(ubicacion) > 1 else ""
        )

        # ==================================
        # INSERT
        # ==================================

        conn.execute(
            nombrados.insert().values(

                nops=fila[0],
                doc_iden=fila[1],

                apellidos=apellidos,
                nombre=nombre,

                ministerio=ministerio,
                centro_directivo=centro_directivo,
                centro_destino=centro_destino,

                provincia=provincia,
                localidad=localidad,

                puesto_trabajo=fila[5],
                codigo_pt=fila[6],
                nivel_cd=fila[7],
                complemento_especifico=fila[8],
            )
        )

        insertadas += 1

print(f"\nDatos insertados correctamente: {insertadas}")