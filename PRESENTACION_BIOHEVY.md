# BioHevy — Diapositivas de Presentación Técnica
## Sistema Biomecánico de Fatiga Muscular y sEMG en Tiempo Real

---

<!-- slide -->
## Diapositiva 1: Portada
### **BioHevy — Monitoreo sEMG y Análisis Biomecánico Predictivo**
* **Subtítulo:** Llevando el entrenamiento de fuerza del registro manual a la precisión médica.
* **Presentadores:** [Tus Nombres]
* **Enfoque:** Integración de hardware IoT telemétrico (ESP32 + ADS1115), procesamiento digital de señales (DSP) en tiempo real, base de datos relacional y experiencia de usuario premium (Glassmorphic UX).

---

<!-- slide -->
## Diapositiva 2: El Problema
### **El Vacío en el Entrenamiento de Fuerza Actual**
* **Falta de objetividad:** Los atletas registran series, peso y repeticiones (método mecánico manual), pero no tienen datos del estado biológico interno de su músculo.
* **El riesgo del sobreentrenamiento:** Trabajar al fallo mecánico sin medir la fatiga neurológica e inminente incrementa exponencialmente el riesgo de desgarros y lesiones articulares.
* **El obstáculo de la conectividad:** Muchas aplicaciones en la nube fallan dentro de sótanos o zonas de gimnasio con mala señal de internet.

---

<!-- slide -->
## Diapositiva 3: Nuestra Propuesta de Valor
### **¿Qué es BioHevy?**
* **Monitoreo sEMG no invasivo:** Captura y procesamiento de las corrientes eléctricas del músculo en plena serie de ejercicio.
* **Predicción Científica de Fatiga:** Algoritmo que detecta el colapso inminente del músculo antes de que ocurra el fallo mecánico, permitiendo entrenar con máxima intensidad y seguridad.
* **Flujo Relacional Seguro y Local:** Base de datos relacional robusta en local con sincronización ágil, diseñada para resistir entornos con conectividad nula o intermitente.

---

<!-- slide -->
## Diapositiva 4: Arquitectura General del Sistema
### **Ecosistema Integrado de Tres Capas**
* **Capa 1: Telemetría de Hardware (ESP32 + ADS1115)**
  * Captura señales analógicas de sEMG a 1000 Hz exactos controlados por hardware timers.
* **Capa 2: Procesamiento y Backend Engine (FastAPI + SQLite)**
  * Recepción de señales mediante WebSockets de alta velocidad.
  * API REST para persistencia y analíticas históricas de volumen.
* **Capa 3: Interfaz del Atleta (Next.js 15 + Tailwind CSS)**
  * Dashboard de alto rendimiento, osciloscopios vectoriales de precisión y modal personalizado de confirmación de eliminación con integridad en cascada.

---

<!-- slide -->
## Diapositiva 5: Adquisición de Señal sEMG
### **Precisión de Entrada de Hardware**
* **Sensor sEMG Analógico:** Captura las despolarizaciones de las membranas musculares mediante electrodos de superficie colocados sobre el vientre muscular.
* **Conversor ADS1115 de 16 Bits:** 
  * ¿Por qué externo? Los ADC internos de los microcontroladores estándar (como el ESP32) son altamente ruidosos y no lineales. El ADS1115 ofrece lectura I2C ultra limpia de alta resolución.
* **Hardware Timer a 1000 Hz:**
  * Una interrupción crítica de hardware en el ESP32 gatilla una lectura exacta cada 1 milisegundo (1000 muestras por segundo), cumpliendo con el Teorema de Nyquist para señales musculares.

---

<!-- slide -->
## Diapositiva 6: Procesamiento Digital de Señales (DSP)
### **Filtrado del Ruido al Análisis**
* **Filtro Notch Digital:**
  * Atenúa específicamente la banda de 50Hz / 60Hz para eliminar el ruido eléctrico ambiental que radian los cables de luz y paredes del gimnasio.
* **Filtro Pasa-Banda (Bandpass):**
  * Limita la señal entre 10Hz y 500Hz para remover artefactos causados por el movimiento de los cables y ruidos de alta frecuencia.
* **Cálculo de Amplitud RMS (Root Mean Square):**
  * Calcula la raíz media cuadrática en tiempo real para cuantificar el nivel total de reclutamiento de fibras musculares durante la contracción.

---

<!-- slide -->
## Diapositiva 7: El Algoritmo de Detección de Fatiga
### **Desplazamiento Espectral de Frecuencia Media (MNF)**
* **La Fisiología de la Fatiga:** A medida que el músculo se agota debido al ácido láctico y fatiga neurológica, la velocidad de conducción de las fibras disminuye.
* **El Desplazamiento Espectral:** La frecuencia de la señal sEMG se desplaza hacia la izquierda (frecuencias más bajas).
* **El Análisis Real-Time:** 
  * BioHevy calcula continuamente la **Frecuencia Media (MNF)** (medida en Hz, bajando de 120Hz a 65Hz en fatiga extrema).
  * Al correlacionar esta caída espectral con el ajuste de regresión lineal ($R^2 \ge 0.90$), el sistema gatilla el indicador visual rojo de **"FATIGA INMINENTE DETECTADA"** antes del colapso físico.

---

<!-- slide -->
## Diapositiva 8: Panel de Precisión y Calidad Biomédica
### **Métricas de Nivel de Laboratorio en Pantalla**
* **Calidad de Señal (SNR - Relación Señal-Ruido):** 
  * Calcula en decibelios (dB) la relación señal útil/ruido de fondo. SNR > 25 dB garantiza una captura impecable del sensor.
* **Precisión del Modelo (Coeficiente de Determinación $R^2$):**
  * Valida matemáticamente que la pendiente de fatiga calculada corresponde con los modelos biológicos estándar.
* **Confianza de Estimación:**
  * Porcentaje dinámico en tiempo real que asegura la fiabilidad médica de la alarma de seguridad antes de cada repetición.

---

<!-- slide -->
## Diapositiva 9: El Software & Experiencia Premium (UX)
### **Estética Futurista y Control de Flujo Seguro**
* **Diseño Glassmorphism Premium:**
  * Fondo ultra oscuro con paneles translúcidos difuminados, tipografías deportivas de alta visibilidad y osciloscopios delgados e interactivos.
* **Control de Integridad Referencial:**
  * Modificación del backend en FastAPI para limpiar las llaves foráneas (`ON DELETE SET NULL`) al borrar rutinas.
  * **Modal personalizado de eliminación:** Evita bloqueos del navegador mediante una hermosa advertencia roja translúcida para confirmar borrados de forma segura.

---

## Diapositiva 10: Banco de Preguntas y Respuestas de Defensa (Q&A)
### **Preparación para Preguntas Difíciles del Jurado**

#### **P1: ¿Por qué usaron un ADC externo ADS1115 en vez del ADC interno del ESP32?**
* **Respuesta Técnica:** El ADC interno del ESP32 tiene un diseño altamente no lineal (especialmente en los extremos de voltaje cerca de 0V y 3.3V) y sufre de una gran cantidad de ruido electromagnético proveniente de las antenas integradas de WiFi y Bluetooth. Para un análisis médico/biomecánico de sEMG, requerimos la resolución de 16 bits y el Amplificador de Ganancia Programable (PGA) del ADS1115 para obtener una lectura limpia y precisa.

#### **P2: ¿Cómo evitan que la conexión WiFi o WebSocket sature la red con 1000 muestras por segundo?**
* **Respuesta Técnica:** Implementamos una **estrategia de buffering (almacenamiento temporal)** en el firmware del ESP32. En lugar de transmitir trama por trama en cada muestra (lo que generaría un overhead inmenso en la red), el microcontrolador acumula un buffer de 50 muestras y las envía en una sola ráfaga empaquetada en formato JSON 20 veces por segundo. Esto reduce drásticamente el tráfico y garantiza una fluidez absoluta en el renderizado del osciloscopio en el navegador.

#### **P3: ¿Qué pasaría si la base de datos pierde conexión o si queremos borrar una rutina histórica?**
* **Respuesta Técnica:** Diseñamos el Backend bajo principios ACID. Al borrar una rutina, aplicamos una pre-consulta que pone en `NULL` la relación `routine_id` en las sesiones de entrenamiento históricas antes de proceder con el borrado. Esto mantiene intactos los récords de volumen del usuario sin violar las restricciones de llaves foráneas de SQLite, evitando la caída del sistema (`IntegrityError 500`).

#### **P4: ¿Cómo se diferencia su indicador de Fatiga RMS del indicador MNF (Frecuencia Media)?**
* **Respuesta Técnica:** El RMS mide la **amplitud** de la señal (qué tanta fuerza o contracción está haciendo el músculo). La MNF mide la **frecuencia** (la velocidad a la que disparan las fibras). Durante una serie al fallo, el RMS suele subir (porque el cuerpo recluta más fibras para compensar el cansancio), pero la MNF cae (porque las fibras se fatigan químicamente por la acidez muscular). Monitorear ambos nos da una lectura de precisión sobre el reclutamiento motor frente a la fatiga neurológica.
