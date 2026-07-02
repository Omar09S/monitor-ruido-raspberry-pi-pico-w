import network
import time

import config

wlan = network.WLAN(network.STA_IF)


def conectar_wifi(timeout_s=15):
    """
    Conecta al Wi-Fi de forma bloqueante (se usa solo al inicio del
    programa, antes de arrancar el loop de asyncio).
    Devuelve True si logró conectar dentro del timeout, False si no.
    """
    wlan.active(True)
    if wlan.isconnected():
        return True

    print("Conectando a la red Wi-Fi:", config.WIFI_SSID)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    inicio = time.time()
    while not wlan.isconnected():
        if time.time() - inicio > timeout_s:
            print("No se pudo conectar al Wi-Fi (timeout).")
            return False
        time.sleep(1)

    print("Conexión Wi-Fi exitosa.")
    print("IP de la Raspberry Pi Pico W:", wlan.ifconfig()[0])
    return True


def wifi_conectado():
    """Devuelve True/False según el estado actual de la conexión."""
    return wlan.isconnected()
