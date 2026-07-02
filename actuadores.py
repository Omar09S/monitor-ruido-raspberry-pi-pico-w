import machine
import config

# Instancias globales de hardware
_pin_buzzer = machine.Pin(config.PIN_BUZZER, machine.Pin.OUT)
_pin_led_verde = machine.Pin(config.PIN_LED_VERDE, machine.Pin.OUT)
_pin_led_amarillo = machine.Pin(config.PIN_LED_AMARILLO, machine.Pin.OUT)
_pin_led_rojo = machine.Pin(config.PIN_LED_ROJO, machine.Pin.OUT)

# Estado del buzzer
_buzzer_activo = False


# FUNCIONES BUZZER 

def encender_buzzer():
    """Enciende el buzzer (GPIO en alto)."""
    _pin_buzzer.value(1)


def apagar_buzzer():
    """Apaga el buzzer (GPIO en bajo)."""
    _pin_buzzer.value(0)


def activar_buzzer_intermitente():
    """Indica que el buzzer debe empezar/seguir pitando intermitente."""
    global _buzzer_activo
    _buzzer_activo = True


def desactivar_buzzer_intermitente():
    """Detiene el patrón intermitente y apaga el buzzer de inmediato."""
    global _buzzer_activo
    _buzzer_activo = False
    apagar_buzzer()


def buzzer_intermitente_activo():
    """Devuelve True si el buzzer debe estar en modo intermitente."""
    return _buzzer_activo


# FUNCIONES SEMÁFORO

def apagar_todos_los_leds():
    """Apaga los tres LEDs del semáforo."""
    _pin_led_verde.value(0)
    _pin_led_amarillo.value(0)
    _pin_led_rojo.value(0)


def mostrar_nivel(nivel):
    """Muestra el nivel de ruido con el semáforo LED."""
    apagar_todos_los_leds()
    if nivel == "Seguro":
        _pin_led_verde.value(1)
    elif nivel == "Moderado":
        _pin_led_amarillo.value(1)
    else:  # "Crítico"
        _pin_led_rojo.value(1)
