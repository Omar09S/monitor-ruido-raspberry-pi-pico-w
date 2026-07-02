# Monitor de Ruido (Proyecto N.º 7)

Materiales a usar:
- Raspberry Pi Pico W
- Sensor de temperatura/humedad AM2302 (mismo protocolo que el DHT22)
- Micrófono MAX4466
- Protoboard ZP 830
- Módulo de semáforo LED (verde/amarillo/rojo)
- Módulo buzzer activo

---

## Estructura del código modular

El código está separado en 6 archivos, cada uno con una sola responsabilidad. 

El flujo general es una cadena: el micrófono capta el sonido → el Pico lo lee por su entrada analógica (ADC) → se calcula un nivel de "decibeles" → se clasifica en Seguro/Moderado/Crítico → se enciende el LED correspondiente y suena el buzzer si es Crítico → se envía todo a Ubidots.

| Archivo | Qué hace |
|---|---|
| `config.py` | Guarda TODOS los valores ajustables del proyecto: credenciales Wi-Fi, token de Ubidots, a qué pin va cada componente, los umbrales de ruido y cada cuánto corren las tareas. No tiene lógica: es solo el "panel de ajustes" que leen los demás archivos. |
| `sensores.py` | Lee los dos sensores. Del micrófono (por ADC) saca la amplitud del sonido, la convierte a "decibeles simulados", la corrige según el clima y la clasifica en Seguro/Moderado/Crítico. Del AM2302 saca temperatura y humedad. |
| `actuadores.py` | Controla las salidas físicas: enciende el LED del semáforo que corresponde al nivel actual, y maneja el encendido/apagado del buzzer. |
| `red.py` | Conecta el Pico al Wi-Fi al arrancar y ofrece una forma de revisar/reconectar la red si se cae, sin detener el sistema. |
| `nube.py` | Envía los datos a Ubidots por HTTP (una petición POST en JSON por cada envío). Si falla, avisa por consola pero no detiene el programa. |
| `main.py` | Es el punto de entrada y el "director de orquesta". Arranca el Wi-Fi y luego corre 4 tareas al mismo tiempo con `asyncio`, que se explican abajo. |

### 4 tareas que en paralelo (en `main.py`)

`main.py` usa `asyncio` para hacer 4 cosas a la vez sin que una bloquee a las otras. Las 4 tareas comparten un diccionario `estado` con los últimos valores leídos.

| Tarea | Qué hace | Cada cuánto |
|---|---|---|
| `leer_sensores()` | Lee ruido y clima, calcula y clasifica el nivel, actualiza el semáforo y avisa al buzzer si es Crítico. | 1 s |
| `controlar_buzzer()` | Hace sonar el buzzer de forma intermitente (pitido–pausa) mientras el nivel sea Crítico. | continuo |
| `enviar_a_la_nube()` | Arma el paquete de datos y lo publica en Ubidots. | 5 s |
| `vigilar_wifi()` | Revisa la conexión Wi-Fi y reconecta si se cayó. | 10 s |

> `asyncio` en MicroPython es multitarea **cooperativa** de un solo hilo: cada tarea corre hasta su próximo `await` sin ser interrumpida, y ahí cede el turno a otra. Por eso las 4 tareas comparten el diccionario `estado` sin necesidad de un `lock`: nunca dos tareas lo tocan exactamente a la vez.

---

## PASO 0: Preparar el software antes de tocar el hardware

1. Instalar **Thonny** (thonny.org).
2. Conectar el Pico W a la computadora **botón BOOTSEL** (el botón blanco sobre la placa). Aparecerá como una unidad USB nueva.
3. Descargar el firmware de MicroPython para Pico W desde https://micropython.org/download/RPI_PICO_W/ (el archivo `.uf2` más reciente).
4. Arrastrar ese archivo `.uf2` a la unidad USB que apareció. El Pico se va a reiniciar solo.
5. Abrir Thonny, ir a la esquina inferior derecha y seleccionar el intérprete **"MicroPython (Raspberry Pi Pico)"**. Debería conectarse y mostrar el REPL (la consola interactiva) abajo.

---

## PASO 1: Instalar las librerías que faltan en el Pico

Con el Pico conectado y Thonny abierto, en la consola REPL (abajo en Thonny) escribir línea por línea:

```python
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("SU_WIFI", "SU_PASSWORD")
```

Esperen unos segundos y verifiquen que conectó:

```python
wlan.isconnected()
```

Si responde `True`, instalen las librerías necesarias:

```python
import mip
mip.install('urequests')
```

`urequests` es la librería que permite hacer peticiones HTTP (la que usaremos para mandar datos a Ubidots). 
El módulo `dht` (para leer el AM2302) normalmente ya viene incluido en el firmware; si más adelante da `ImportError: no module named 'dht'`, instalar con `mip.install('dht')`.

---

## PASO 2: Armado físico en la protoboard

Antes de conectar nada, **dejen el Pico W desconectado de la computadora* (sin energía) mientras arman el circuito, para evitar cortocircuitos accidentales mientras mueven cables.

### 2.1 — Coloquen el Pico W en la protoboard

Pónganlo a horcajadas sobre el canal central de la protoboard, de forma que las patas queden divididas a ambos lados (esto es estándar para cualquier microcontrolador tipo DIP).

### 2.2 — Lleven alimentación a los rieles de la protoboard

Con dos cables dupont macho-macho:
- Uno desde el pin **3V3(OUT)** del Pico hasta el **riel rojo (+)** de la protoboard.
- Uno desde cualquier pin **GND** del Pico hasta el **riel azul/negro (−)** de la protoboard.

Todo lo demás se va a alimentar desde estos rieles, no directamente desde el Pico, para mantener todo ordenado.

### 2.3 — Conecten el AM2302 (sensor de temperatura/humedad)

El AM2302 en módulo de 3 pines normalmente viene marcado como `+` (o VCC), `OUT` (o DATA/SDA), y `-` (o GND).

| Pin del AM2302 | Va a |
|---|---|
| `+` / VCC | Riel rojo (+) de la protoboard |
| `OUT` / DATA | **GP15** del Pico |
| `-` / GND | Riel negro (−) de la protoboard |

> Si su AM2302 es el sensor "pelado" de 4 pines (sin placa con
> agujeros de montaje), necesitan agregar una resistencia de 10kΩ
> entre el pin VCC y el pin DATA. Si es el módulo de 3 pines con
> placa verde o azul pequeña, esa resistencia ya viene incluida.

### 2.4 — Conecten el micrófono MAX4466

Tiene 3 pines: VCC, OUT (o AOUT), GND.

| Pin del MAX4466 | Va a |
|---|---|
| VCC | Riel rojo (+) de la protoboard |
| OUT / AOUT | **GP26** del Pico (entrada analógica ADC0) |
| GND | Riel negro (−) de la protoboard |

### 2.5 — Conecten el módulo de semáforo LED

Estos módulos suelen traer 4 pines: GND común + 3 señales (R, Y, G). Si el suyo trae cada LED por separado con su propio VCC/GND/señal, apliquen la misma idea: cada señal a su pin correspondiente y todos los GND al riel negro.

| Pin del módulo | Va a |
|---|---|
| GND (común) | Riel negro (−) de la protoboard |
| Verde (G) | **GP11** del Pico |
| Amarillo (Y) | **GP12** del Pico |
| Rojo (R) | **GP13** del Pico |

### 2.6 — Conecten el módulo buzzer activo

Trae 3 pines: VCC, GND, I/O (o S/SIG).

| Pin del buzzer | Va a |
|---|---|
| VCC | Riel rojo (+) de la protoboard |
| GND | Riel negro (−) de la protoboard |
| I/O / SIG | **GP14** del Pico |

### 2.7 — Revisión antes de energizar

Antes de conectar el USB de nuevo, revisen:
- Que ningún cable de señal (GP11, GP12, GP13, GP14, GP15, GP26) esté tocando por error el riel rojo o el riel negro.
- Que VCC de cada módulo vaya al riel rojo, y GND de cada módulo al riel negro (no al revés).

Recién ahí conecten el cable USB del Pico a la computadora.

---

## PASO 3: Configurar las credenciales en el código

Antes de subir nada, abrir `config.py` y completen estos 4 valores:

```python
WIFI_SSID = "..."          # nombre real de su red Wi-Fi
WIFI_PASSWORD = "..."      # contraseña real de esa red

UBIDOTS_TOKEN = "..."      # el token de cuenta Ubidots
DEVICE_LABEL = "..."       # nombre del dispositivo en Ubidots (sin espacios, minúsculas)
```

No hace falta crear las variables (`ruido`, `temperatura`, etc.) en Ubidots de antemano — se crean solas la primera vez que el Pico manda datos con esos nombres.

---

## PASO 4: Subir los archivos al Pico

En Thonny, con el Pico conectado:

1. Abrir cada archivo (`config.py`, `sensores.py`, `actuadores.py`, `red.py`, `nube.py`, `main.py`) en Thonny.
2. Para cada uno: **Archivo → Guardar como... → Raspberry Pi Pico**, y guardarlo con el mismo nombre exacto (`config.py`, etc.) en la raíz del Pico (no dentro de ninguna carpeta).
3. `main.py` debe llamarse exactamente así, porque el Pico ejecuta automáticamente el archivo `main.py` cada vez que se enciende.

---

## PASO 5: Probar todo por partes (antes de la prueba final completa)

No prueben todo junto de una vez — si algo falla, va a ser difícil saber qué fue. Prueben en este orden, usando la consola REPL de Thonny:

### 5.1 — Probar el Wi-Fi solo
```python
import red
red.conectar_wifi()
```
Debe imprimir la IP del Pico. Si no conecta, revisen `WIFI_SSID` y `WIFI_PASSWORD` en `config.py`.

### 5.2 — Probar el AM2302 solo
```python
import sensores
sensores.leer_temperatura_humedad()
```
Debe devolver algo como `(24.5, 55.0)` (temperatura, humedad). Si devuelve `(None, None)`, revisen que el cable DATA esté en GP15 y que el sensor tenga alimentación.

### 5.3 — Probar el micrófono solo
```python
import sensores
sensores.leer_amplitud()
```
Hagan ruido cerca del micrófono (aplaudan) y vuelvan a correr la línea — el número debería subir notablemente respecto al silencio.

### 5.4 — Probar los LEDs
```python
import actuadores
actuadores.mostrar_nivel("Seguro")    # debe encender el verde
actuadores.mostrar_nivel("Moderado")  # debe encender el amarillo
actuadores.mostrar_nivel("Crítico")   # debe encender el rojo
```

### 5.5 — Probar el buzzer
```python
import actuadores
actuadores.encender_buzzer()
actuadores.apagar_buzzer()
```

### 5.6 — Probar el envío a Ubidots
```python
import red
red.conectar_wifi()
from nube import ClienteNube
nube = ClienteNube()
nube.publicar({"ruido": 10, "temperatura": 22, "humedad": 50})
```
Debe imprimir `"OK enviado a Ubidots"`. Entren a su cuenta de Ubidots y revisen que el dispositivo y las variables aparezcan con ese dato.

### 5.7 — Prueba final: todo junto
Una vez que los pasos anteriores funcionaron por separado, ejecuten `main.py` completo (botón ▶ en Thonny, o reinicien el Pico). Hagan
ruido cerca del micrófono y confirmen que:
- El semáforo cambia de color según el nivel de ruido.
- El buzzer suena de forma intermitente (pitido-pausa-pitido) cuando el nivel llega a "Crítico", y se detiene al bajar el ruido.
- En la consola de Thonny aparecen los mensajes de cada lectura.
- En el dashboard de Ubidots los valores se van actualizando cada pocos segundos.

---

## Errores comunes y qué hacer

| Síntoma | Causa probable |
|---|---|
| `ImportError: no module named 'dht'` | Instalar con `mip.install('dht')` |
| `ImportError: no module named 'urequests'` | Instalar con `mip.install('urequests')` |
| El AM2302 siempre devuelve `(None, None)` | Revisar cable DATA en GP15, o que el módulo tenga su pull-up (ver paso 2.3) |
| El micrófono siempre da valores muy bajos | Revisar que OUT esté en GP26 y que VCC/GND no estén invertidos |
| No conecta a Ubidots | Revisar `UBIDOTS_TOKEN` y que el Wi-Fi sí esté conectado primero |
| El Pico se reinicia solo o se "cuelga" al mandar datos | Problema conocido de `urequests` en algunos Wi-Fi inestables; si pasa muy seguido, avisen para ajustar el intervalo de envío |

---

## Calibración pendiente (si les sobra tiempo)

Los umbrales en `config.py` (`UMBRAL_SEGURO_MAX = 35`, `UMBRAL_MODERADO_MAX = 55`) y la escala (`AMPLITUD_MAX_ESPERADA`, `DB_SIM_MAX`) son valores de partida. Si tienen tiempo antes de la presentación, prueben hablar/aplaudir cerca del micrófono, miren qué valores imprime la consola, y ajusten esos números para que el semáforo reaccione de forma realista en su salón.

## Nota sobre el protocolo del AM2302

El AM2302 (igual que el DHT22) usa un protocolo propietario de un solo cable, que no es I2C, SPI ni UART. La guía del curso pide usar uno de esos tres protocolos; el equipo decidió mantener el AM2302 por limitaciones de tiempo. Esto debe declararse explícitamente en el paper y en la defensa como una limitación conocida.