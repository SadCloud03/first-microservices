import logging
import json
import requests

# handler para los logs de la libreria loggings
class HTTPLogHandler(logging.Handler):
    def __init__(self, url, service_id, token, timeout=0.3): # Añadimos token
        super().__init__() # como hereda de la clase logging.headler entonces copiar los atributos
        self.url = url #guardar el url
        self.service_id = service_id #guardar el id del servicio
        self.token = token # Guardamos el token
        self.timeout = timeout # poner el timeout a las operaciones

    # metodo de emicion de logs
    def emit(self, record):
        try:
            formatted_data = json.loads(self.format(record))
            payload = {
                "service_id": int(self.service_id), # este es el formato por el cual llega a la base de datos
                "level": formatted_data.get("level"),
                "message": formatted_data.get("message"),
                "extra": {
                    "timestamp" : formatted_data.get("timestamp"), # enviar el timestamp tambien en el log por cualquier cosa
                    "details" : formatted_data.get("extra")}
            }

            # AÑADIMOS EL HEADER DE AUTHORIZATION
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            # se envia todo el log al path de @app.post("/logs")
            requests.post(
                self.url, 
                json=payload, 
                headers=headers, # <--- IMPORTANTE : enviar el token del respectivo servicio 
                timeout=self.timeout
            )
        except Exception:
            pass

        #la chispa evento 