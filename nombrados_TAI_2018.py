from lxml import etree

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    text
)

# ==========================================
# INICIO
# ==========================================

print("1 - Inicio")

XML_FILE = "/workspaces/proyectoBOE/DATOS/TAI2018.xml"

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
# LOCALIZAR TABLA
# ==========================================

tabla = root.xpath(
    ".//table[contains(@class,'tabla_girada')]"
)[0]

print("5 - Tabla localizada")

filas = tabla.xpath(".//tr")

print(f"6 - Filas encontradas: {len(filas)}")

# ==========================================
# EXTRAER DATOS
# ==========================================

datos = []

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

# ==========================================
# MOSTRAR CABECERA
# ==========================================

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

    # vaciar tabla
    conn.execute(
        text("TRUNCATE TABLE nombrados_prueba RESTART IDENTITY")
    )

    for fila in datos[1:]:

        # ignorar filas basura
        if len(fila) < 12:
            print("Fila ignorada:", fila)
            continue

        # ignorar abreviaturas
        if "Índice de abreviaturas" in fila[0]:
            continue

        # ==================================
        # NOMBRE
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
        # CAMPOS DIRECTOS
        # ==================================

        ministerio = fila[3]
        centro_directivo = fila[4]
        centro_destino = fila[5]

        provincia = fila[6]
        localidad = fila[7]

        puesto_trabajo = fila[8]
        codigo_pt = fila[9]
        nivel_cd = fila[10]
        complemento_especifico = fila[11]

        # ==================================
        # DEBUG
        # ==================================

        print("\n---------------------------")
        print("APELLIDOS:", apellidos)
        print("NOMBRE:", nombre)
        print("MINISTERIO:", ministerio)
        print("CENTRO DIRECTIVO:", centro_directivo)
        print("CENTRO DESTINO:", centro_destino)
        print("PROVINCIA:", provincia)
        print("LOCALIDAD:", localidad)

        # ==================================
        # INSERT
        # ==================================

        conn.execute(
            nombrados_prueba.insert().values(

                nops=fila[0],
                doc_iden=fila[1],

                apellidos=apellidos,
                nombre=nombre,

                ministerio=ministerio,
                centro_directivo=centro_directivo,
                centro_destino=centro_destino,

                provincia=provincia,
                localidad=localidad,

                puesto_trabajo=puesto_trabajo,
                codigo_pt=codigo_pt,
                nivel_cd=nivel_cd,
                complemento_especifico=complemento_especifico,
            )
        )

        insertadas += 1

print(f"\nDatos insertados correctamente: {insertadas}")