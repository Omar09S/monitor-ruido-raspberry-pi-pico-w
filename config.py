# Wi-Fi
WIFI_SSID = "TU_WIFI"
WIFI_PASSWORD = "TU_PASSWORD"


UBIDOTS_TOKEN = "TU_TOKEN_UBIDOTS"
DEVICE_LABEL = "monitor-ruido-pico"

VAR_RUIDO = "ruido"
# 0 = Seguro, 1 = Moderado, 2 = Crítico (ver sensores.py)
VAR_NIVEL = "nivel_num"   
VAR_TEMPERATURA = "temperatura"
VAR_HUMEDAD = "humedad"
# 0 = normal, 1 = buzzer activo
VAR_ALERTA = "alerta"    

# Pines: entrada de "ruido" (ADC0) 
# Salida analógica del micrófono MAX4466.
PIN_RUIDO_ADC = 26  # ADC0

# Pines: LEDs semáforo (módulo de semáforo LED)
PIN_LED_VERDE = 11
PIN_LED_AMARILLO = 12
PIN_LED_ROJO = 13

# Pines: sensor de temperatura/humedad AM2302
PIN_DHT22 = 15

# Pines: módulo buzzer activo
PIN_BUZZER = 14

# Parámetros de muestreo de ruido
N_MUESTRAS = 200
DELAY_MUESTRA = 0.0005  # 0.5 ms -> ventana total ~100 ms

# Umbrales de "decibeles" simulados

# Deben quedar SIN huecos ni solapamientos entre rangos.
# <= este valor -> Seguro (verde)
UMBRAL_SEGURO_MAX = 35.0      
# entre UMBRAL_SEGURO_MAX y este valor -> Moderado (amarillo)
UMBRAL_MODERADO_MAX = 55.0   
# > UMBRAL_MODERADO_MAX -> Crítico (rojo) + buzzer intermitente

# Escala de amplitud ADC -> dB_sim
AMPLITUD_MAX_ESPERADA = 40000  # amplitud ADC que se mapea a DB_SIM_MAX
DB_SIM_MAX = 90.0

# Factor de corrección por temperatura/humedad
# La velocidad del sonido en el aire varía con la temperatura (y, en ucho menor medida, con la humedad). Se aplica una corrección simple
# fórmula clásica de velocidad del sonido en función de la temperatura
# temperatura: v(T) = 331.3 + 0.606 * T (m/s), usando 20°C (referencia)

TEMP_REFERENCIA_C = 20.0
HUMEDAD_REFERENCIA_PCT = 50.0
FACTOR_CORRECCION_TEMP = 0.05      # % de ajuste de dB_sim por cada °C de diferencia
FACTOR_CORRECCION_HUMEDAD = 0.01   # % de ajuste de dB_sim por cada % de diferencia de humedad

# Patrón intermitente del buzzer en nivel Crítico
BUZZER_ON_MS = 200
BUZZER_OFF_MS = 200

# Intervalos de las tareas asyncio (segundos) 
INTERVALO_LECTURA_SENSORES = 1.0
INTERVALO_ENVIO_NUBE = 5.0
INTERVALO_CHEQUEO_WIFI = 10.0
