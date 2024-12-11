# Este proyecto permite la transmisión de video en tiempo real desde un ESP32 con cámara.
# También incluye la funcionalidad de cargar datos a Firebase, simulando el almacenamiento de capturas.
# Funciona configurando un servidor HTTP local para streaming y enviando datos periódicamente.

import network
import esp
import socket
import gc
import camera
import time
import urequests  # Librería para interactuar con Firebase

# Deshabilitar logs y optimizar memoria
esp.osdebug(None)
gc.collect()

# URL de Firebase (actualizar con tu proyecto)
FIREBASE_URL = 'https://<tu-proyecto>.firebaseio.com/streaming.json'

# Inicialización de la cámara
def inicializar_camara():
    """
    Configura la cámara con ajustes específicos para calidad, tamaño y orientación.
    """
    camera.deinit()
    camera.init(0, format=camera.JPEG)
    camera.framesize(camera.FRAME_SVGA)  # Tamaño SVGA para mayor detalle
    camera.flip(1)  # Voltear imagen verticalmente
    camera.mirror(1)  # Reflejar imagen horizontalmente
    camera.quality(15)  # Calidad ajustada
    camera.brightness(-2)  # Ajustar brillo para iluminación baja
    camera.saturation(-1)  # Reducir saturación para colores naturales
    print("Cámara lista para capturas.")

# Conexión a la red WiFi
SSID = 'TROLLS'
PASSWORD = 'm9EqQPk35H'

def conectar_a_wifi():
    """
    Conecta el ESP32 a la red WiFi y devuelve la IP asignada.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Conectando a la red WiFi...")
    while not wlan.isconnected():
        time.sleep(1)
        print("Intentando conexión...")

    ip = wlan.ifconfig()[0]
    print(f"Conexión exitosa. IP asignada: {ip}")
    return ip

# Subida de datos a Firebase
def subir_a_firebase(datos):
    """
    Envía datos simulados o información de capturas a Firebase.
    """
    try:
        print("Enviando datos a Firebase...")
        respuesta = urequests.put(FIREBASE_URL, json=datos)
        print(f"Respuesta de Firebase: {respuesta.status_code}")
        respuesta.close()
    except Exception as error:
        print(f"Error al subir datos: {error}")

# Configuración del servidor de streaming
def iniciar_streaming():
    """
    Configura un servidor HTTP para transmitir video en tiempo real.
    """
    ip = conectar_a_wifi()
    direccion = socket.getaddrinfo(ip, 8080)[0][-1]

    servidor = socket.socket()
    servidor.bind(direccion)
    servidor.listen(3)  # Aceptar hasta 3 conexiones simultáneas
    print(f"Servidor disponible en http://{ip}:8080")

    while True:
        try:
            cliente, direccion_cliente = servidor.accept()
            print(f"Nueva conexión desde: {direccion_cliente}")
            manejar_cliente(cliente)
        except Exception as error:
            print(f"Error manejando cliente: {error}")
        finally:
            cliente.close()

# Manejo de solicitudes de clientes
def manejar_cliente(cliente):
    """
    Envia el streaming de video y simula una carga periódica a Firebase.
    """
    cliente_file = cliente.makefile('rwb', 0)
    while True:
        linea = cliente_file.readline()
        if not linea or linea == b'\r\n':
            break

    cliente.send(b'HTTP/1.1 200 OK\r\n')
    cliente.send(b'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n')

    try:
        while True:
            imagen = camera.capture()
            cliente.send(b'--frame\r\n')
            cliente.send(b'Content-Type: image/jpeg\r\n\r\n')
            cliente.send(imagen)
            cliente.send(b'\r\n')

            datos_firebase = {
                "timestamp": time.time(),
                "info": "Imagen enviada a cliente"
            }
            subir_a_firebase(datos_firebase)

            time.sleep(3)
    except Exception as error:
        print(f"Conexión finalizada: {error}")

# Inicio del programa
if __name__ == "__main__":
    inicializar_camara()
    iniciar_streaming()
