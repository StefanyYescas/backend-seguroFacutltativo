class UsuarioModel:

    def __init__(
        self,
        idUsuario,
        nomCompleto,
        numControl,
        correo,
        contrasena,
        rol
    ):

        self.idUsuario = idUsuario
        self.nomCompleto = nomCompleto
        self.numControl = numControl
        self.correo = correo
        self.contrasena = contrasena
        self.rol = rol