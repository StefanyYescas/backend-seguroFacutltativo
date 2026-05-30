import pdfplumber
import re



# =========================
# EXTRAER DATOS NSS
# =========================

def extraer_datos_nss(ruta_pdf):

    texto = ""

    with pdfplumber.open(ruta_pdf) as pdf:

        for pagina in pdf.pages:

            texto += pagina.extract_text()



    print(texto)



    # NSS
    patron_nss = r"\b\d{11}\b"

    resultado_nss = re.search(
        patron_nss,
        texto
    )



    # CURP
    patron_curp = r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b"

    resultado_curp = re.search(
        patron_curp,
        texto
    )



    return {

        "nss": resultado_nss.group() if resultado_nss else "No encontrado",

        "curp": resultado_curp.group() if resultado_curp else "No encontrado"
    }



# =========================
# EXTRAER DATOS VIGENCIA
# =========================

def extraer_datos_vigencia(ruta_pdf):

    texto = ""

    with pdfplumber.open(ruta_pdf) as pdf:

        for pagina in pdf.pages:

            texto += pagina.extract_text()



    print(texto)



    # =========================
    # CLINICA
    # =========================

    patron_clinica = r"UMF\s+\d+.*"

    resultado_clinica = re.search(
        patron_clinica,
        texto
    )



    # =========================
    # VIGENCIA
    # =========================

    patron_vigencia = r"Vigente:\s*(\d{2}/\d{2}/\d{4})"

    resultado_vigencia = re.search(
        patron_vigencia,
        texto
    )



    return {

        "clinica": resultado_clinica.group() if resultado_clinica else "No encontrada",

        "vigencia": resultado_vigencia.group(1) if resultado_vigencia else "No encontrada"
    }