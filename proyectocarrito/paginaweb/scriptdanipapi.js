// Importar módulos de Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.2/firebase-app.js";
import { getDatabase, ref, set } from "https://www.gstatic.com/firebasejs/11.0.2/firebase-database.js";

// =====================
// Configuración de Firebase
// =====================

// Objeto de configuración de Firebase
const firebaseConfig = {
   apiKey: "AIzaSyDjanjjnAa5PAcQfzfgsUfX7D4C9REWlNM",
   authDomain: "papitoprogramables.firebaseapp.com",
   databaseURL: "https://papitoprogramables-default-rtdb.firebaseio.com",
   projectId: "papitoprogramables",
   storageBucket: "papitoprogramables.firebasestorage.app",
   messagingSenderId: "301461174476",
   appId: "1:301461174476:web:9f15de68ca61e1cde12a69"
};

// Inicializar Firebase
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

// =====================
// Funciones de Firebase
// =====================

/**
 * Envía datos a Firebase Realtime Database.
 * @param {string} topico - El tópico/sensor al que se envían los datos.
 * @param {string|number} mensaje - El valor del dato a enviar.
 */
function enviarDatosAFirebase(topico, mensaje) {
    const dbRef = ref(database, `sensores/${topico}`);
    set(dbRef, {
        valor: mensaje,
        timestamp: new Date().toISOString()
    }).then(() => {
        console.log(`Datos enviados a Firebase: ${topico} = ${mensaje}`);
    }).catch((error) => {
        console.error('Error al enviar datos a Firebase:', error);
    });
}

// =====================
// Configuración del broker MQTT
// =====================

const brokerURL = 'ws://broker.mqttdashboard.com:8000/mqtt'; // URL del broker MQTT
const clientId = 'Carrito-' + Math.random().toString(16).substr(2, 8); // ID único para el cliente MQTT

// Crear conexión MQTT
const client = mqtt.connect(brokerURL, {
    clientId: clientId,
    keepalive: 60,
    reconnectPeriod: 1000,
});

// =====================
// Tópicos MQTT Configurados
// =====================

const TOPICO_SENSORES = {
    humedadAmbiente: "humdanipapi",
    temperatura: "tempdanipapi",
    humedadTierra: "humtdanipapi",
    gas: "mq2danipapi",
    distancia: "disdanipapi",
};

const TOPICO_CONTROL = {
    adelante: "adelantepa",
    atras: "atraspa",
    derecha: "derechapa",
    izquierda: "izquierdapa",
    alto: "altopapi",
};

const TOPICO_SERVO = {
    control: "servo/control",
    status: "servo/status",
};

// =====================
// Elementos del DOM
// =====================

// Indicadores de conexión y datos de sensores
const connectionStatus = document.getElementById('connection-status');
const labelHumedad = document.getElementById('labelHumedad');
const labelTemperatura = document.getElementById('labelTemperatura');
const labelHumedadTierra = document.getElementById('labelHumedadTierra');
const labelGas = document.getElementById('labelGas');
const labelDistancia = document.getElementById('labelDistancia');

// Controles del servomotor y reconocimiento de voz
const servoSlider = document.getElementById('servoSlider');
const servoAngleLabel = document.getElementById('servoAngle');
const btnEscuchar = document.getElementById('btnEscuchar');
const estadoVoz = document.getElementById('estadoVoz');

// =====================
// Funciones de Control MQTT
// =====================

/**
 * Publica un comando en un tópico MQTT específico.
 * @param {string} topico - El tópico donde se publicará el comando.
 * @param {string} [mensaje="1"] - El mensaje a enviar (por defecto "1").
 */
function publicarComando(topico, mensaje = "1") {
    client.publish(topico, mensaje, { qos: 0 }, (err) => {
        if (err) {
            console.error(`Error al publicar en el tópico ${topico}:`, err);
        } else {
            console.log(`Comando enviado: "${topico}" con mensaje "${mensaje}"`);
        }
    });
}

// =====================
// Manejo de Eventos de Conexión MQTT
// =====================

// Evento de conexión exitosa al broker MQTT
client.on('connect', () => {
    console.log('Conectado al broker MQTT');
    connectionStatus.textContent = 'Conectado';
    connectionStatus.classList.remove('disconnected');
    connectionStatus.classList.add('connected');

    // Suscribirse a los tópicos de sensores y servomotor
    const subscribeTopics = [...Object.values(TOPICO_SENSORES), TOPICO_SERVO.status];
    client.subscribe(subscribeTopics, (err) => {
        if (err) {
            console.error('Error al suscribirse a los tópicos:', err);
        } else {
            console.log('Suscrito a los tópicos de sensores y servomotor.');
        }
    });
});

// Evento de recepción de mensajes MQTT
client.on('message', (topico, mensaje) => {
    const valor = mensaje.toString();

    switch (topico) {
        case TOPICO_SENSORES.humedadAmbiente:
            labelHumedad.textContent = `${valor} %`;
            enviarDatosAFirebase(TOPICO_SENSORES.humedadAmbiente, valor);
            break;
        case TOPICO_SENSORES.temperatura:
            labelTemperatura.textContent = `${valor} °C`;
            enviarDatosAFirebase(TOPICO_SENSORES.temperatura, valor);
            break;
        case TOPICO_SENSORES.humedadTierra:
            labelHumedadTierra.textContent = `${valor} %`;
            enviarDatosAFirebase(TOPICO_SENSORES.humedadTierra, valor);
            break;
        case TOPICO_SENSORES.gas:
            labelGas.textContent = `${valor} ppm`;
            enviarDatosAFirebase(TOPICO_SENSORES.gas, valor);
            break;
        case TOPICO_SENSORES.distancia:
            labelDistancia.textContent = `${valor} cm`;
            enviarDatosAFirebase(TOPICO_SENSORES.distancia, valor);
            break;
        default:
            console.warn(`Tópico no manejado: ${topico}`);
    }
});

// =====================
// Asignación de Eventos a los Botones de Control
// =====================

// Mapeo de IDs de botones a sus respectivos tópicos MQTT
const botonesControl = {
    btnAdelante: TOPICO_CONTROL.adelante,
    btnAtras: TOPICO_CONTROL.atras,
    btnDerecha: TOPICO_CONTROL.derecha,
    btnIzquierda: TOPICO_CONTROL.izquierda,
    btnDetener: TOPICO_CONTROL.alto,
};

// Asignar eventos de clic a cada botón de control
Object.keys(botonesControl).forEach((btnId) => {
    const boton = document.getElementById(btnId);
    const topico = botonesControl[btnId];
    boton.addEventListener('click', () => publicarComando(topico));
});

// =====================
// Control del Servomotor mediante Slider
// =====================

/**
 * Publica el ángulo del servomotor cuando se cambia el slider.
 */
servoSlider.addEventListener('input', () => {
    const angulo = servoSlider.value;
    servoAngleLabel.textContent = angulo;
    publicarComando(TOPICO_SERVO.control, angulo);
});

// =====================
// Reconocimiento de Voz
// =====================

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    // El navegador no soporta el reconocimiento de voz
    estadoVoz.textContent = "Reconocimiento de voz no soportado en este navegador.";
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES'; // Establecer el idioma a español de España

    /**
     * Inicia el reconocimiento de voz cuando se hace clic en el botón.
     */
    btnEscuchar.addEventListener('click', () => {
        recognition.start();
        estadoVoz.textContent = "Escuchando...";
    });

    /**
     * Maneja el resultado del reconocimiento de voz.
     */
    recognition.onresult = (event) => {
        const comando = event.results[0][0].transcript.toLowerCase();
        console.log(`Comando reconocido: ${comando}`);
        estadoVoz.textContent = `Comando reconocido: ${comando}`;

        // Mapear comandos de voz a acciones de control
        if (comando.includes("adelante")) {
            publicarComando(TOPICO_CONTROL.adelante);
        } else if (comando.includes("atrás") || comando.includes("reversa")) {
            publicarComando(TOPICO_CONTROL.atras);
        } else if (comando.includes("derecha")) {
            publicarComando(TOPICO_CONTROL.derecha);
        } else if (comando.includes("izquierda")) {
            publicarComando(TOPICO_CONTROL.izquierda);
        } else if (comando.includes("alto") || comando.includes("detener")) {
            publicarComando(TOPICO_CONTROL.alto);
        } else {
            estadoVoz.textContent += " - Comando no reconocido.";
            console.warn(`Comando no reconocido: ${comando}`);
        }
    };

    /**
     * Maneja errores en el reconocimiento de voz.
     */
    recognition.onerror = (event) => {
        estadoVoz.textContent = "Error en reconocimiento de voz: " + event.error;
        console.error('Error en reconocimiento de voz:', event.error);
    };

    /**
     * Restablece el estado cuando el reconocimiento de voz termina.
     */
    recognition.onend = () => {
        estadoVoz.textContent = "Estado: Inactivo";
    };
}
