class SolicitudSeguroModel:

    def __init__(
        self,
        idSolicitud=None,
        fechaSolicitud=None,
        fechaEntrega=None,
        estado="pendiente",
        observacion=None,
        rutaConstancia=None,
        rutaNss=None,
        idUsuario=None
    ):

        self.idSolicitud = idSolicitud
        self.fechaSolicitud = fechaSolicitud
        self.fechaEntrega = fechaEntrega
        self.estado = estado
        self.observacion = observacion
        self.rutaConstancia = rutaConstancia
        self.rutaNss = rutaNss
        self.idUsuario = idUsuario