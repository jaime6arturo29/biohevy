#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <ArduinoJson.h>

// ================= CONFIGURACIÓN =================
const char* ssid = "TU_RED_WIFI";
const char* password = "TU_PASSWORD";
const char* websockets_server = "ws://192.168.1.XX:8000/ws/emg"; // IP del backend FastAPI

// ================= HARDWARE =================
Adafruit_ADS1115 ads; // Dirección I2C por defecto 0x48
using namespace websockets;
WebsocketsClient client;

// ================= TIMERS Y FLAGS =================
hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
volatile bool sampleReady = false;

// ================= ESTRATEGIA DE BUFFERING =================
// Para no colapsar la red, enviamos bloques de 50 muestras (50ms)
const int BUFFER_SIZE = 50;
int16_t buffer_ch1[BUFFER_SIZE];
int16_t buffer_ch2[BUFFER_SIZE];
volatile int buffer_index = 0;
volatile bool buffer_full = false;

// Interrupción controlada por Hardware Timer (se ejecuta cada 1 ms exacto)
void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  if (!buffer_full) {
    sampleReady = true;
  }
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  Serial.begin(115200);
  
  // 1. Inicialización I2C y ADS1115
  Wire.begin();
  
  // El circuito analógico desplaza la señal a 1.65V (0V a 3.3V)
  // GAIN_ONE permite medir +/- 4.096V (1 bit = 0.125mV), ideal para este rango seguro.
  ads.setGain(GAIN_ONE);
  if (!ads.begin()) {
    Serial.println("Error crítico: ADS1115 no detectado. Revisa las conexiones I2C.");
    while (1); // Detener ejecución
  }
  // Velocidad de muestreo al máximo (860 SPS es el límite del hardware del ADS1115)
  // Nota: Fisiológicamente buscamos 1000 Hz, pero el ADS1115 estándar limitará a ~860 Hz reales.
  ads.setDataRate(RATE_ADS1115_860SPS);
  Serial.println("ADS1115 Inicializado correctamente.");

  // 2. Conexión WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado. IP: " + WiFi.localIP().toString());

  // 3. Conexión WebSocket
  bool connected = client.connect(websockets_server);
  if (connected) {
    Serial.println("Conectado exitosamente al Servidor BioHevy (FastAPI)");
  } else {
    Serial.println("Error: No se pudo conectar al WebSocket.");
  }

  // 4. Configuración del Hardware Timer (1000 Hz)
  // Frecuencia base ESP32 = 80 MHz. Prescaler 80 -> 1 tick = 1 microsegundo
  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  // Alarma cada 1000 ticks (1000 microsegundos = 1 milisegundo)
  timerAlarmWrite(timer, 1000, true);
  timerAlarmEnable(timer);
  Serial.println("Adquisición sEMG Iniciada (1000 Hz)...");
}

void loop() {
  // Mantener viva la conexión WebSocket
  if (client.available()) {
    client.poll();
  }

  // Chequear la bandera de interrupción de forma segura
  bool shouldRead = false;
  portENTER_CRITICAL(&timerMux);
  if (sampleReady) {
    shouldRead = true;
    sampleReady = false;
  }
  portEXIT_CRITICAL(&timerMux);

  // Lectura del ADC
  if (shouldRead && !buffer_full) {
    // Lectura Single-Ended de los Canales 1 (Pecho Alto) y 2 (Pecho Medio)
    // Nota: Esta lectura bloquea por el I2C. Para máxima velocidad se requiere SPI o I2S.
    buffer_ch1[buffer_index] = ads.readADC_SingleEnded(0); // Pin A0
    buffer_ch2[buffer_index] = ads.readADC_SingleEnded(1); // Pin A1
    
    buffer_index++;
    if (buffer_index >= BUFFER_SIZE) {
      buffer_full = true;
    }
  }

  // 5. Transmisión del Buffer en Ráfaga
  if (buffer_full && client.available()) {
    // Empaquetar datos en JSON
    // Se usa DynamicJsonDocument por la cantidad de datos (50 muestras * 2 canales)
    DynamicJsonDocument doc(2048);
    JsonArray ch1 = doc.createNestedArray("ch1");
    JsonArray ch2 = doc.createNestedArray("ch2");

    for (int i = 0; i < BUFFER_SIZE; i++) {
      ch1.add(buffer_ch1[i]);
      ch2.add(buffer_ch2[i]);
    }

    String jsonString;
    serializeJson(doc, jsonString);
    
    // Enviar trama
    client.send(jsonString);

    // Reiniciar ciclo de buffer
    buffer_index = 0;
    buffer_full = false;
  }
}
