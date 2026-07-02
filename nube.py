import urequests

import config


class ClienteNube:
    def __init__(self):
        self._url = "https://stem.ubidots.com/api/v1.6/devices/{}".format(
            config.DEVICE_LABEL
        )
        self._headers = {
            "X-Auth-Token": config.UBIDOTS_TOKEN,
            "Content-Type": "application/json",
        }

    def publicar(self, payload):
        """
        Envía un diccionario de variables a Ubidots en una sola petición.
        Ejemplo de payload:
            {"ruido": 42.3, "temperatura": 24.1, "humedad": 55.0,
             "alerta": 1, "nivel_num": 2}

        Devuelve True si el envío fue exitoso, False si falló (sin
        detener el programa).
        """
        print("Enviando a Ubidots:", payload)
        try:
            respuesta = urequests.post(
                self._url, json=payload, headers=self._headers
            )
            respuesta.close()
            print("OK enviado a Ubidots")
            return True
        except Exception as e:
            print("Error al enviar a Ubidots:", e)
            return False
