import asyncio

import config
import red
import nube
import sensores
import actuadores


# Estado compartido entre tareas
estado = {
    "db_sim": 0.0,
    "nivel_ruido": "Seguro",
    "temperatura": None,
    "humedad": None,
}

# Instancia del cliente de nube
cliente_nube = nube.ClienteNube()


async def leer_sensores():
    """
    - lee la entrada de ruido y el DHT22 periódicamente, 
    - calcula los dB_sim corregidos por temperatura/humedad
    - clasifica el nivel
    - actualiza el semáforo LED. NO controla el buzzer directamente.
    """
    contador_dht = 0
    while True:
        # Entrada de "ruido" (MAX4466 ) 
        amplitud = sensores.leer_amplitud()

        if amplitud < 50:
            nivel_adc = sensores.leer_nivel_simulado()
        else:
            nivel_adc = amplitud

        db_sim_crudo = sensores.amplitud_a_db_sim(nivel_adc)
        db_sim = sensores.corregir_por_clima(
            db_sim_crudo, estado["temperatura"], estado["humedad"]
        )
        nivel = sensores.clasificar(db_sim)

        estado["db_sim"] = db_sim
        estado["nivel_ruido"] = nivel

        actuadores.mostrar_nivel(nivel)

        # Activa o desactiva el patrón intermitente del buzzer según el nivel
        # El parpadeo en sí lo ejecuta controlar_buzzer().
        if nivel == "Crítico":
            actuadores.activar_buzzer_intermitente()
        else:
            actuadores.desactivar_buzzer_intermitente()

        print("Nivel:", nivel, "| dB_sim:", round(db_sim, 1))

        # Sensor ambiental (cada ~5 ciclos, porque el DHT22 no debe leerse con demasiada frecuencia) ---
        contador_dht += 1
        if contador_dht >= 5:
            contador_dht = 0
            temperatura, humedad = sensores.leer_temperatura_humedad()
            if temperatura is not None:
                estado["temperatura"] = temperatura
                estado["humedad"] = humedad
                print("Temperatura:", temperatura, "C | Humedad:", humedad, "%")

        await asyncio.sleep(config.INTERVALO_LECTURA_SENSORES)


async def controlar_buzzer():
    """
    Mientras buzzer_intermitente_activo() sea True:
    - alterna encendido/apagado según BUZZER_ON_MS / BUZZER_OFF_MS 
    - Esta tarea corre en paralelo a leer_sensores() y no bloquea su ejecución.
    """
    while True:
        if actuadores.buzzer_intermitente_activo():
            actuadores.encender_buzzer()
            await asyncio.sleep_ms(config.BUZZER_ON_MS)
            # Vuelve a chequear: si en ese instante el nivel ya bajó se deteiene
            if actuadores.buzzer_intermitente_activo():
                actuadores.apagar_buzzer()
                await asyncio.sleep_ms(config.BUZZER_OFF_MS)
        else:
            # Nada que hacer; se revisa de nuevo poco después.
            await asyncio.sleep_ms(100)


async def enviar_a_la_nube():
    """
    arma un único payload con todas las variables y lo publica a Ubidots por HTTP cada INTERVALO_ENVIO_NUBE segundos.
    """
    while True:
        payload = {
            config.VAR_RUIDO: round(estado["db_sim"], 1),
            config.VAR_NIVEL: sensores.nivel_a_numero(estado["nivel_ruido"]),
            config.VAR_ALERTA: 1 if estado["nivel_ruido"] == "Crítico" else 0,
        }

        if estado["temperatura"] is not None:
            payload[config.VAR_TEMPERATURA] = estado["temperatura"]
            payload[config.VAR_HUMEDAD] = estado["humedad"]

        cliente_nube.publicar(payload)

        await asyncio.sleep(config.INTERVALO_ENVIO_NUBE)


async def vigilar_wifi():
    """
    revisa periódicamente si el Wi-Fi sigue conectado.
    Si se cayó, intenta reconectar sin detener las otras tareas.
    """
    while True:
        if not red.wifi_conectado():
            print("Wi-Fi desconectado, reintentando...")
            red.conectar_wifi()
        await asyncio.sleep(config.INTERVALO_CHEQUEO_WIFI)


async def main():
    print(">> Iniciando el sistema <<")

    conectado = red.conectar_wifi()
    if not conectado:
        print("Aviso: continuará reintentando en segundo plano.")

    tarea_sensores = asyncio.create_task(leer_sensores())
    tarea_buzzer = asyncio.create_task(controlar_buzzer())
    tarea_nube = asyncio.create_task(enviar_a_la_nube())
    tarea_wifi = asyncio.create_task(vigilar_wifi())

    await asyncio.gather(tarea_sensores, tarea_buzzer, tarea_nube, tarea_wifi)


asyncio.run(main())
