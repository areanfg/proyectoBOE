import pdfplumber

pdf_path = "/workspaces/proyectoBOE/DATOS/07TAI_L_01GE_154AB89SD658.pdf"

with pdfplumber.open(pdf_path) as pdf:

    for i, page in enumerate(pdf.pages):

        print(f"\n===== PAGINA {i+1} =====\n")

        text = page.extract_text()

        print(text[:5000])      
        input("Pulsa ENTER para continuar...")
