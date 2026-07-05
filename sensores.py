import machine
import time
import dht

import config

# Instancias globales de hardware
_adc_ruido = machine.ADC(machine.Pin(config.PIN_RUIDO_ADC))
_sensor_dht = dht.DHT22(machine.Pin(config.PIN_DHT22))


# FUNCIONES RUIDO

def leer_amplitud():
    """
    Toma N_MUESTRAS lecturas en una ventana corta, descarta los valores
    más extremos (probable ruido eléctrico del ADC) y devuelve la
    amplitud pico a pico (max - min) del conjunto ya filtrado.
    En el micrófono real, esto representa el nivel de ruido captado.
    """
    muestras = []
    for _ in range(config.N_MUESTRAS):
        muestras.append(_adc_ruido.read_u16())
        time.sleep(config.DELAY_MUESTRA)

    return _amplitud_filtrada(muestras)


def _amplitud_filtrada(muestras):
    """
    Descarta un porcentaje de las lecturas más altas y más bajas
    (recorte por percentil, config.PORCENTAJE_RECORTE_ADC) antes de
    calcular la amplitud pico a pico.

    Justificación: el ruido eléctrico del ADC tiende a aparecer como
    lecturas puntuales muy alejadas del resto (1-2 muestras aisladas),
    mientras que la señal de audio real varía de forma más continua
    entre muestras consecutivas dentro de la ventana de ~100 ms.
    Recortar los extremos antes de tomar max/min reduce la
    sensibilidad a esos picos aislados sin filtrar la dinámica real
    del sonido (a diferencia de un promedio, que sí aplanaría picos
    genuinos).
    """
    n = len(muestras)
    ordenadas = sorted(muestras)

    n_recorte = int(n * config.PORCENTAJE_RECORTE_ADC)
    # Evita recortar todo el arreglo si N_MUESTRAS fuera muy pequeño.
    if n_recorte * 2 >= n:
        n_recorte = 0

    if n_recorte > 0:
        ordenadas = ordenadas[n_recorte:n - n_recorte]

    return ordenadas[-1] - ordenadas[0]


def leer_nivel_simulado():
    """
    Devuelve una lectura ADC instantánea (0-65535).
    """
    return _adc_ruido.read_u16()


def amplitud_a_db_sim(amplitud):
    """
    Convierte una amplitud ADC (0-65535) a una magnitud en
    "decibeles simulados" (dB_sim), usando un mapeo lineal simple.
    No son decibeles físicos reales: es una escala de conveniencia
    para comparar contra referencias como los límites de la OMS.
    """
    amplitud = min(amplitud, config.AMPLITUD_MAX_ESPERADA)
    return (amplitud / config.AMPLITUD_MAX_ESPERADA) * config.DB_SIM_MAX


def corregir_por_clima(db_sim, temperatura, humedad):
    """
    Aplica un factor de corrección a la lectura de dB_sim según la
    diferencia de temperatura y humedad respecto a una condición de
    referencia (config.TEMP_REFERENCIA_C / HUMEDAD_REFERENCIA_PCT).

    Justificación física simplificada: la velocidad del sonido en el
    aire aumenta con la temperatura (v(T) = 331.3 + 0.606*T m/s), lo
    que afecta cómo se propaga el sonido; la humedad tiene un efecto
    menor pero también documentado. Esta función traduce esas
    diferencias en un pequeño porcentaje de ajuste.

    Si temperatura o humedad no están disponibles, se devuelve el
    valor sin corregir.
    """
    if temperatura is None or humedad is None:
        return db_sim

    delta_temp = temperatura - config.TEMP_REFERENCIA_C
    delta_humedad = humedad - config.HUMEDAD_REFERENCIA_PCT

    ajuste_pct = (
        delta_temp * config.FACTOR_CORRECCION_TEMP
        + delta_humedad * config.FACTOR_CORRECCION_HUMEDAD
    )

    return db_sim * (1 + ajuste_pct / 100)


def clasificar(db_sim):
    """
    Clasifica la magnitud en dB_sim en 'Seguro', 'Moderado' o
    'Crítico'.
    """
    if db_sim <= config.UMBRAL_SEGURO_MAX:
        return "Seguro"
    elif db_sim <= config.UMBRAL_MODERADO_MAX:
        return "Moderado"
    else:
        return "Crítico"


def nivel_a_numero(nivel):
    """
    Convierte el nivel de texto a un código numérico
    """
    return {"Seguro": 0, "Moderado": 1, "Crítico": 2}.get(nivel, 0)


# FUNCIONES CLIMA 

def leer_temperatura_humedad():
    """
    Lee temperatura (°C) y humedad (%) del DHT22. Devuelve una tupla
    (temperatura, humedad) o (None, None) si la lectura falla.
    El DHT22 es sensible a leerse con demasiada frecuencia (mínimo ~2
    segundos entre lecturas), por eso se maneja el error con try/except
    en vez de detener el sistema.
    """
    try:
        _sensor_dht.measure()
        return _sensor_dht.temperature(), _sensor_dht.humidity()
    except OSError as e:
        print("Error leyendo DHT22:", e)
        return None, None