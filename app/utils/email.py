import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def enviar_correo(destinatario, asunto, mensaje, ruta_archivo=None):
    print("📨 ENTRÓ A enviar_correo")

    #  AQUÍ VAN LOS PRINTS IMPORTANTES
    print("📨 ENVIANDO A:", destinatario)
    print("📨 ASUNTO:", asunto)

    remitente = "stefanyyescas17@gmail.com"
    password = "enztfgjhwclymkwo"

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = asunto

    msg.attach(MIMEText(mensaje, "plain"))

    #  Adjuntar archivo si existe
    if ruta_archivo and os.path.exists(ruta_archivo):
        print(" Adjuntando archivo:", ruta_archivo)  # 👈 útil también

        with open(ruta_archivo, "rb") as archivo:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(archivo.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(ruta_archivo)}"
        )

        msg.attach(part)

    try:
        print("📡 Conectando a SMTP...")  # 👈 otro punto clave

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("🔐 Iniciando sesión...")
        server.login(remitente, password)

        print("📤 Enviando correo...")
        server.sendmail(remitente, destinatario, msg.as_string())

        server.quit()

        print("✅ CORREO ENVIADO")
        return True

    except Exception as e:
        print("❌ Error correo:", e)
        return False