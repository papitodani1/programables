import cv2  # OpenCV para procesamiento de imágenes
import urllib.request  # Para manejar solicitudes HTTP
import numpy as np
import time
import logging  # Para el registro de eventos y errores
import os  # Para manejo de archivos locales

# CONFIGURACIÓN DEL PROGRAMA
CAMERA_URL = 'http://192.168.1.191/cam-hi.jpg'  # Dirección IP de la cámara
CLASSES_FILE = 'coco.names'  # Archivo con nombres de clases
CONFIG_PATH = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'  # Configuración del modelo
WEIGHTS_PATH = 'frozen_inference_graph.pb'  # Pesos del modelo
WINDOW_NAME = 'Detección en Tiempo Real'
LOG_FILE = 'deteccion.log'  # Archivo de registro
CAPTURE_DIR = 'captures/'  # Carpeta para guardar capturas

# Configuración de logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Función para cargar clases desde el archivo

def cargar_clases(archivo):
    """Carga nombres de clases desde un archivo de texto."""
    with open(archivo, 'rt') as f:
        return f.read().strip().split('\n')

# Configuración de la red neuronal

def configurar_modelo(config, weights):
    """Configura el modelo de detección con parámetros predeterminados."""
    modelo = cv2.dnn_DetectionModel(weights, config)
    modelo.setInputSize(320, 320)
    modelo.setInputScale(1.0 / 127.5)
    modelo.setInputMean((127.5, 127.5, 127.5))
    modelo.setInputSwapRB(True)
    logging.info("Modelo de detección configurado correctamente.")
    return modelo

# Captura imágenes desde la cámara IP

def capturar_imagen(url):
    """Captura y decodifica una imagen desde una URL."""
    try:
        respuesta = urllib.request.urlopen(url)
        datos = np.array(bytearray(respuesta.read()), dtype=np.uint8)
        imagen = cv2.imdecode(datos, -1)
        return imagen
    except Exception as e:
        logging.error(f"Error al capturar imagen: {e}")
        return None

# Guardar capturas en disco

def guardar_captura(imagen, directorio):
    """Guarda la imagen capturada en el disco con un nombre único."""
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    nombre_archivo = os.path.join(directorio, f"captura_{int(time.time())}.jpg")
    cv2.imwrite(nombre_archivo, imagen)
    logging.info(f"Imagen guardada en {nombre_archivo}")

# Procesamiento de detección

def procesar_deteccion(modelo, imagen, clases):
    """Realiza detección en la imagen y muestra resultados en tiempo real."""
    class_ids, confidences, boxes = modelo.detect(imagen, confThreshold=0.5)
    for class_id, confidence, box in zip(class_ids.flatten(), confidences.flatten(), boxes):
        etiqueta = clases[class_id - 1]
        cv2.rectangle(imagen, box, color=(0, 255, 0), thickness=3)
        cv2.putText(imagen, f"{etiqueta}: {confidence:.2f}", (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        logging.info(f"Detección: {etiqueta} con confianza {confidence:.2f}")
    return imagen

# Función para calcular FPS

def calcular_fps(tiempo_inicial, num_frames):
    """Calcula los cuadros por segundo en función del tiempo y los frames procesados."""
    tiempo_transcurrido = time.time() - tiempo_inicial
    if tiempo_transcurrido > 0:
        fps = num_frames / tiempo_transcurrido
        logging.info(f"FPS: {fps:.2f}")
        return fps
    return 0

# Flujo principal del programa
if __name__ == "__main__":
    clases = cargar_clases(CLASSES_FILE)
    modelo = configurar_modelo(CONFIG_PATH, WEIGHTS_PATH)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    print("Iniciando detección en tiempo real...")
    logging.info("Inicio del programa de detección.")

    tiempo_inicial = time.time()
    num_frames = 0

    while True:
        frame = capturar_imagen(CAMERA_URL)
        if frame is not None:
            frame = procesar_deteccion(modelo, frame, clases)
            guardar_captura(frame, CAPTURE_DIR)
            num_frames += 1
            fps = calcular_fps(tiempo_inicial, num_frames)
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow(WINDOW_NAME, frame)

        # Salir al presionar la tecla ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()
    logging.info("Programa finalizado.")
    print("Programa finalizado.")
