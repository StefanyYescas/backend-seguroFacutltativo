import random

def generar_codigo():
    return str(random.randint(
        100000,
        999999
    ))
