# Descripción:
# Este programa utiliza un ESP32 para recopilar datos de sensores ambientales, mostrar los datos en una pantalla TFT y enviarlos a un broker MQTT y Firebase.
# Los sensores utilizados son:
#   - DHT11: mide temperatura y humedad.
#   - MQ2: mide concentración de gas.
#   - Sensor de humedad de suelo: mide la humedad del suelo.
# Además, incluye un buzzer que se activa cuando la concentración de gas excede un límite predefinido.
# Los datos se publican en tópicos MQTT para integrarse con aplicaciones IoT y también se almacenan en Firebase.

from umqtt.simple import MQTTClient
import machine
import ubinascii
import network
import time
from machine import SPI, Pin, ADC
from st7735 import TFT
from sysfont import sysfont
import dht
import urequests  # Librería para realizar peticiones HTTP

# Configuración de Wi-Fi
SSID = 'Red Deco'          # Reemplaza con tu SSID
PASSWORD = 'Angeldaniel1*'  # Reemplaza con tu contraseña

def connect_wifi():
    """
    Conecta el ESP32 a la red Wi-Fi especificada.
    Lanza una excepción si no logra conectar en un tiempo límite.
    """
    print("[DEBUG] Intentando conectar al Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a la red...')
        wlan.connect(SSID, PASSWORD)
        timeout = 10  # Tiempo límite en segundos
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                raise Exception("No se pudo conectar al Wi-Fi")
            time.sleep(1)
    print('[DEBUG] Configuración de red:', wlan.ifconfig())

# Configuración de Firebase
FIREBASE_URL = 'https://<perritodani>.firebaseio.com/sensores.json'  # Reemplaza con tu URL de Firebase

def enviar_a_firebase(datos):
    """
    Envía los datos a Firebase utilizando una petición HTTP POST.
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
TOPICO_HUMEDAD = b"humdanipapi"               # Tópico para la humedad
TOPICO_TEMPERATURA = b"tempdanipapi"         # Tópico para la temperatura
TOPICO_MQ2 = b"mq2danipapi"                   # Tópico para el MQ2
TOPICO_HUMEDAD_TIERRA = b"humtdanipapi" # Tópico para la humedad en tierra

# Configuración de la pantalla TFT
# Pines del TFT
tft_CS = 5
tft_RESET = 4
tft_A0 = 2

# Configurar SPI
spi = SPI(2, baudrate=20000000, polarity=0, phase=0, miso=None)

# Inicializar la pantalla TFT ST7735
tft = TFT(spi, tft_A0, tft_RESET, tft_CS)
tft.initr()
tft.rgb(True)

# Dimensiones de la pantalla
tft_ancho = 128
tft_alto = 160

# Configuración de sensores
# Sensor DHT11 (temperatura y humedad)
dht_sensor = dht.DHT11(Pin(21))  # Cambia este pin según tu conexión del DHT11

# Sensor MQ2 (concentración de gas)
mq2_pin = 34  # GPIO34 es un pin ADC en ESP32
mq2 = ADC(Pin(mq2_pin))
mq2.atten(ADC.ATTN_11DB)  # Configurar la atenuación para un rango completo
mq2.width(ADC.WIDTH_12BIT) # Resolución de 12 bits

# Sensor de humedad en la tierra
humedad_tierra_pin = 32  # GPIO32 es un pin ADC en ESP32
humedad_tierra = ADC(Pin(humedad_tierra_pin))
humedad_tierra.atten(ADC.ATTN_11DB)  # Configurar la atenuación para un rango completo
humedad_tierra.width(ADC.WIDTH_12BIT) # Resolución de 12 bits

# Buzzer activo
buzzer_pin = 15  # GPIO15
buzzer = Pin(buzzer_pin, Pin.OUT)
buzzer.value(0)   # Inicialmente desactivado

# Definición de colores personalizados en formato RGB565
ORANGE = 0xFD20   # Definición manual de ORANGE
PURPLE = 0xF81F   # Definición manual de PURPLE

# Funciones auxiliares
def mostrar_texto(x, y, texto, color=TFT.WHITE, tamaño=1):
    """Muestra texto en la pantalla TFT."""
    print(f"[DEBUG] Mostrando texto en pantalla: '{texto}' en ({x}, {y})")
    tft.text((x, y), texto, color, sysfont, tamaño)

def publicar_mensaje(client, topico, mensaje):
    """Publica un mensaje en el tópico especificado del broker MQTT."""
    print(f"[DEBUG] Publicando mensaje en MQTT {topico.decode()}: {mensaje.decode()}")
    client.publish(topico, mensaje)

def convertir_mq2(valor_adc):
    """Convierte el valor analógico del MQ2 a una estimación de concentración en ppm."""
    ppm = (valor_adc / 4095) * 1000  # Ejemplo: Mapea 0-4095 a 0-1000 ppm
    print(f"[DEBUG] Valor ADC MQ2: {valor_adc}, Concentración calculada: {ppm} ppm")
    return ppm

def convertir_humedad_tierra(valor_adc):
    """Convierte el valor analógico del sensor de humedad de tierra a porcentaje."""
    humedad = (valor_adc / 4095) * 100  # Mapea 0-4095 a 0-100%
    print(f"[DEBUG] Valor ADC Humedad Tierra: {valor_adc}, Porcentaje calculado: {humedad}%")
    return humedad

# Ejecución principal
try:
    # Conectar al Wi-Fi
    connect_wifi()

    # Crear una conexión MQTT
    client = MQTTClient(ID_CLIENTE, SERVER_MQTT, port=PUERTO, keepalive=10000)
    client.connect()
    print("[DEBUG] Conectado al broker MQTT")

    while True:
        try:
            print("[DEBUG] Leyendo datos de sensores...")
            # Leer datos del sensor DHT11
            dht_sensor.measure()
            temperatura = dht_sensor.temperature()
            humedad = dht_sensor.humidity()
            print(f"[DEBUG] DHT11 - Temperatura: {temperatura}°C, Humedad: {humedad}%")

            # Leer datos del sensor MQ2
            valor_mq2_adc = mq2.read()
            concentración_mq2 = convertir_mq2(valor_mq2_adc)

            # Leer datos del sensor de humedad en tierra
            valor_humedad_tierra_adc = humedad_tierra.read()
            humedad_tierra_percent = convertir_humedad_tierra(valor_humedad_tierra_adc)

            # Publicar datos al broker MQTT
            publicar_mensaje(client, TOPICO_TEMPERATURA, f"{temperatura} °C".encode('utf-8'))
            publicar_mensaje(client, TOPICO_HUMEDAD, f"{humedad} %".encode('utf-8'))
            publicar_mensaje(client, TOPICO_MQ2, f"{concentración_mq2:.2f} ppm".encode('utf-8'))
            publicar_mensaje(client, TOPICO_HUMEDAD_TIERRA, f"{humedad_tierra_percent:.2f} %".encode('utf-8'))

            # Enviar datos a Firebase
            datos = {
                "temperatura": temperatura,
                "humedad": humedad,
                "concentracion_gas": concentración_mq2,
                "humedad_tierra": humedad_tierra_percent
            }
            enviar_a_firebase(datos)

            # Limpiar la pantalla
            print("[DEBUG] Limpiando pantalla TFT")
            tft.fill(TFT.BLACK)

            # Mostrar datos en pantalla TFT
            mostrar_texto(10, 10, f"Temp: {temperatura} C", TFT.CYAN, 1.5)
            mostrar_texto(10, 40, f"Humedad: {humedad} %", TFT.GREEN, 1.5)
            mostrar_texto(10, 70, f"MQ2: {concentración_mq2:.2f} ppm", ORANGE, 1.5)
            mostrar_texto(10, 100, f"Humedad Tierra: {humedad_tierra_percent:.2f} %", PURPLE, 1.5)

            # Activar buzzer si la concentración de gas es alta
            if concentración_mq2 > 100:
                print("[DEBUG] Concentración de gas alta, activando buzzer")
                buzzer.value(1)
                mostrar_texto(10, 130, "¡Alerta! Gas alto", TFT.RED, 1.5)
            else:
                print("[DEBUG] Concentración de gas normal, desactivando buzzer")
                buzzer.value(0)
                mostrar_texto(10, 130, "              ", TFT.BLACK, 1.5)  # Limpiar la línea

            # Pausa de 1 segundo
            time.sleep(1)

        except Exception as e:
            print(f"Error en el bucle: {e}")
            tft.fill(TFT.BLACK)
            mostrar_texto(10, 10, "Error!", TFT.RED, 2)
            mostrar_texto(10, 40, str(e), TFT.RED, 1)
            time.sleep(2)

except Exception as e:
    print("Error general:", e)

finally:
    # Desconectar el cliente MQTT
    if 'client' in locals():
        print("[DEBUG] Desconectando del broker MQTT")
        client.disconnect()
        print("Desconectado del broker MQTT")

