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

tabla = root.xpath(".//table[contains(@class,'tabla_girada')]")[0]

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

# Mostrar cabecera
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

# Crear tabla
metadata.create_all(engine)

# ==========================================
# INSERTAR DATOS
# ==========================================

with engine.begin() as conn:

    # Saltar cabecera
    for fila in datos[1:]:

        if len(fila) != 12:
            print("Fila ignorada:", fila)
            continue

        # ==================================
        # SEPARAR APELLIDOS Y NOMBRE
        # ==================================

        nombre_completo = fila[2]

        partes = nombre_completo.split(",")

        apellidos = partes[0].strip()

        nombre = partes[1].strip() if len(partes) > 1 else ""

        # ==================================
        # INSERT
        # ==================================

        conn.execute(
            nombrados.insert().values(

                nops=fila[0],
                doc_iden=fila[1],

                apellidos=apellidos,
                nombre=nombre,

                ministerio=fila[3],
                centro_directivo=fila[4],
                centro_destino=fila[5],
                provincia=fila[6],
                localidad=fila[7],
                puesto_trabajo=fila[8],
                codigo_pt=fila[9],
                nivel_cd=fila[10],
                complemento_especifico=fila[11],
            )
        )

print("Datos insertados correctamente")