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
# INICIO
# ==========================================

print("1 - Inicio")

XML_FILE = "/workspaces/proyectoBOE/DATOS/TAI2019.xml"

print("2 - Leyendo XML local")

with open(XML_FILE, "rb") as f:
    xml_content = f.read()

print("3 - XML leído")

# ==========================================
# PARSEAR XML
# ==========================================

root = etree.fromstring(xml_content)

print("4 - XML parseado")

# ==========================================
# LOCALIZAR TABLAS
# ==========================================

tablas = root.xpath(
    ".//table[contains(@class,'tabla_girada')]"
)

print(f"\nTablas encontradas: {len(tablas)}")

# ==========================================
# EXTRAER DATOS
# ==========================================

datos = []

for i, tabla in enumerate(tablas):

    print(f"\nProcesando tabla {i + 1}")

    filas = tabla.xpath(".//tr")

    for fila in filas:

        celdas = fila.xpath("./th | ./td")

        valores = []

        for celda in celdas:

            lineas = []

            for t in celda.itertext():

                t = t.strip()

                if not t:
                    continue

                # quitar punto final
                t = t.rstrip(".")

                lineas.append(t)

            texto = "\n".join(lineas)

            valores.append(texto)

        if valores:
            datos.append(valores)

print(f"\nFilas extraídas: {len(datos)}")

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

nombrados_prueba = Table(
    "nombrados_prueba",
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

    for fila in datos:

        # ignorar cabecera
        if fila[0] == "NOPS":
            continue

        # ignorar filas inválidas
        if len(fila) != 12:
            print("Fila ignorada:", fila)
            continue

        # ignorar pie de abreviaturas
        if "Índice de abreviaturas" in fila[0]:
            continue

        # ==================================
        # SEPARAR NOMBRE
        # ==================================

        nombre_completo = fila[2]

        partes = nombre_completo.split(",")

        apellidos = (
            partes[0].strip()
            if len(partes) > 0 else ""
        )

        nombre = (
            partes[1].strip()
            if len(partes) > 1 else ""
        )

        # ==================================
        # DEBUG
        # ==================================

        print("\n----------------------")
        print("NOMBRE:", nombre)
        print("APELLIDOS:", apellidos)

        # ==================================
        # INSERT
        # ==================================

        conn.execute(
            nombrados_prueba.insert().values(

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

        insertadas += 1

print(f"\nDatos insertados correctamente: {insertadas}")