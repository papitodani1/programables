# Descripción:
# Este programa permite controlar un carrito robótico basado en ESP32 mediante comandos recibidos a través de MQTT y un control remoto infrarrojo.
# Además, se utiliza un sensor ultrasónico para evitar obstáculos y un receptor IR para comandos manuales.
# Los datos, como la distancia a los obstáculos, se envían a un broker MQTT y se simula su almacenamiento en Firebase.

from umqtt.simple import MQTTClient
from machine import Pin, PWM
import machine
import ubinascii
import network
import time
from hcsr04 import HCSR04  # Librería del sensor ultrasónico
import ir_rx  # Librería para manejar el receptor IR
import urequests  # Librería para simular el envío a Firebase

# Configuración de Wi-Fi
SSID = 'ProfesoresTecLeon'          # Reemplaza con tu SSID
PASSWORD = 'T3cNML30n@2024$.'  # Reemplaza con tu contraseña

def connect_wifi():
    """
    Conecta el ESP32 a la red Wi-Fi especificada.
    Lanza una excepción si no logra conectar en un tiempo límite.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a la red...')
        wlan.connect(SSID, PASSWORD)
        timeout = 10  # Segundos
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                raise Exception("No se pudo conectar al Wi-Fi")
            time.sleep(1)
    print('Configuración de red:', wlan.ifconfig())

# Configuración de Firebase
FIREBASE_URL = 'https://papitodani123.firebaseio.com/datos.json'  # Reemplaza con la URL de Firebase

def enviar_a_firebase(datos):
    """
    Simula el envío de datos a Firebase mediante una petición HTTP POST.
    """
    print(f"[DEBUG] Enviando datos a Firebase: {datos}")
    try:
        respuesta = urequests.post(FIREBASE_URL, json=datos)
        print(f"Datos enviados a Firebase: {respuesta.text}")
        respuesta.close()
    except Exception as e:
        print(f"Error al enviar datos a Firebase: {e}")

# Configuración de MQTT
SERVER_MQTT = 'broker.mqttdashboard.com'  # Dirección del broker MQTT
PUERTO = 1883
ID_CLIENTE = ubinascii.hexlify(machine.unique_id()).decode('utf-8')  # ID único para MQTT

# Tópicos para controlar el carrito
TOPICO_ADELANTE = b"adelantepa"
TOPICO_ATRAS = b"atraspa"
TOPICO_DERECHA = b"derechapa"
TOPICO_IZQUIERDA = b"izquierdapa"
TOPICO_ALTO = b"altopapi"
TOPICO_DISTANCIA = b"disdanipapi"

# Configuración del sensor ultrasónico
sensor = HCSR04(trigger_pin=5, echo_pin=18)  # Cambia los pines según tu configuración
DISTANCIA_MINIMA = 20  # Distancia mínima para alerta (en cm)

# Configuración de los motores
class MotorGroup:
    def __init__(self, pin1, pin2):
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin2 = Pin(pin2, Pin.OUT)

    def forward(self):
        """Activa el motor para avanzar."""
        self.pin1.on()
        self.pin2.off()

    def backward(self):
        """Activa el motor para retroceder."""
        self.pin1.off()
        self.pin2.on()

    def stop(self):
        """Detiene el motor."""
        self.pin1.off()
        self.pin2.off()

# Configuración de PWM compartido para ENA y ENB
pwm_speed = PWM(Pin(26), freq=1000)  # GPIO26 configurado como PWM, frecuencia 1 kHz
pwm_speed.duty(512)  # Velocidad inicial: duty cycle al 50% (ajustable entre 0 y 1023)

# Configuración de los motores (izquierdo y derecho)
motores_izquierda = MotorGroup(12, 13)  # Motores del lado izquierdo (Canal A)
motores_derecha = MotorGroup(33, 32)    # Motores del lado derecho (Canal B)

# Diccionario con los códigos IR y las acciones correspondientes
commands = {
    0x18: 'adelante',  # Código para "adelante" en el control remoto
    0x52: 'atras',     # Código para "atrás"
    0x5a: 'derecha',   # Código para "derecha"
    0x8: 'izquierda',  # Código para "izquierda"
    0x1c: 'alto'       # Código para "stop"
}

# Funciones para el movimiento del vehículo
def avanzar():
    """Ejecuta el movimiento hacia adelante."""
    motores_izquierda.forward()
    motores_derecha.forward()

def retroceder():
    """Ejecuta el movimiento hacia atrás."""
    motores_izquierda.backward()
    motores_derecha.backward()

def girar_izquierda():
    """Ejecuta el giro hacia la izquierda."""
    motores_izquierda.stop()
    motores_derecha.forward()

def girar_derecha():
    """Ejecuta el giro hacia la derecha."""
    motores_izquierda.forward()
    motores_derecha.stop()

def parar():
    """Detiene todos los motores."""
    motores_izquierda.stop()
    motores_derecha.stop()

# Ajustar velocidad
def ajustar_velocidad(duty):
    """Ajusta la velocidad del vehículo."""
    pwm_speed.duty(duty)
    print(f"Velocidad ajustada al duty cycle: {duty}")

# Publicar mensaje en el broker MQTT
def publicar_mensaje(client, topico, mensaje):
    """Publica un mensaje en el tópico MQTT especificado."""
    client.publish(topico, mensaje)
    print(f"Mensaje publicado en {topico.decode()}: {mensaje.decode()}")

# Verifica si hay un obstáculo
def verificar_obstaculo():
    """Verifica la presencia de un obstáculo usando el sensor ultrasónico."""
    try:
        distancia = sensor.distance_cm()  # Mide la distancia
        print(f"Distancia medida: {distancia} cm")
        publicar_mensaje(client, TOPICO_DISTANCIA, f"{distancia:.2f} cm".encode('utf-8'))

        # Simular envío a Firebase
        enviar_a_firebase({"distancia": distancia})

        if distancia <= DISTANCIA_MINIMA:
            print("¡Obstáculo detectado, deteniendo el vehículo!")
            parar()
            publicar_mensaje(client, TOPICO_DISTANCIA, b"¡Alerta! Obstáculo cercano")
            return True
        return False
    except OSError as e:
        print(f"Error al leer el sensor ultrasónico: {e}")
        return False

# Callback para manejar mensajes MQTT
def mensaje_recibido(topico, mensaje):
    """Procesa mensajes recibidos en los tópicos MQTT suscritos."""
    print(f"Mensaje recibido en el tópico {topico.decode()}: {mensaje.decode()}")
    if topico == TOPICO_ADELANTE:
        print("Comando: Adelante")
        ejecutar_accion('adelante')
    elif topico == TOPICO_ATRAS:
        print("Comando: Atrás")
        ejecutar_accion('atras')
    elif topico == TOPICO_DERECHA:
        print("Comando: Derecha")
        ejecutar_accion('derecha')
    elif topico == TOPICO_IZQUIERDA:
        print("Comando: Izquierda")
        ejecutar_accion('izquierda')
    elif topico == TOPICO_ALTO:
        print("Comando: Parar")
        ejecutar_accion('alto')
    else:
        print("Tópico no reconocido.")

# Configuración del receptor IR
def ir_callback(data, addr, ctrl):
    """Procesa los códigos recibidos del control remoto IR."""
    if data > 0:
        print(f"Código IR recibido: {hex(data)}")
        accion = commands.get(data, 'desconocido')
        ejecutar_accion(accion)

def ejecutar_accion(accion):
    """Ejecuta una acción según el comando recibido."""
    if verificar_obstaculo():  # Verifica si hay un obstáculo antes de ejecutar la acción
        return  # No ejecuta la acción si hay un obstáculo

    if accion == 'adelante':
        print("Moviendo hacia adelante")
        avanzar()
    elif accion == 'atras':
        print("Moviendo hacia atrás")
        retroceder()
    elif accion == 'derecha':
        print("Girando a la derecha")
        girar_derecha()
    elif accion == 'izquierda':
        print("Girando a la izquierda")
        girar_izquierda()
    elif accion == 'alto':
        print("Parando")
        parar()
    else:
        print(f"Acción desconocida: {accion}")

# Configuración del receptor infrarrojo
ir_pin = Pin(15, Pin.IN)  # Conecta el receptor IR al pin GPIO15
ir = ir_rx.NEC_16(ir_pin, ir_callback)

# Conectar al broker MQTT y manejar comandos
try:
    connect_wifi()
    client = MQTTClient(ID_CLIENTE, SERVER_MQTT, port=PUERTO, keepalive=10000)
    client.set_callback(mensaje_recibido)
    client.connect()
    print("Conectado al broker MQTT")

    # Suscribirse a los tópicos de control
    client.subscribe(TOPICO_ADELANTE)
    client.subscribe(TOPICO_ATRAS)
    client.subscribe(TOPICO_DERECHA)
    client.subscribe(TOPICO_IZQUIERDA)
    client.subscribe(TOPICO_ALTO)
    print("Suscrito a los tópicos de control del carrito.")

    print("Esperando comandos IR y MQTT...")
    while True:
        client.check_msg()  # Escucha mensajes MQTT
        if verificar_obstaculo():
            publicar_mensaje(client, TOPICO_DISTANCIA, b"¡Alerta! Obstáculo cercano")
            parar()
        time.sleep(0.1)

except Exception as e:
    print("Error general:", e)

finally:
    if 'client' in locals():
        client.disconnect()
        print("Desconectado del broker MQTT")
