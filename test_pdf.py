from app.services.pdf_services import (
    extraer_datos_nss,
    extraer_datos_vigencia
)



datos_nss = extraer_datos_nss(
    "app/uploads/nss/tarjetaNSS30210215619.pdf"
)

print(datos_nss)



datos_vigencia = extraer_datos_vigencia(
    "app/uploads/constancias/reporteVigenciaDerechos.pdf"
)

print(datos_vigencia)