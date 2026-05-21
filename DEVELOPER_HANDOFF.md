# BioHevy — Guía de Onboarding y Documentación Técnica
## Manual de Traspaso para Desarrolladores

Bienvenido al repositorio central de **BioHevy**, un ecosistema de rendimiento deportivo y análisis biomecánico de alto nivel. Esta guía ha sido diseñada para que cualquier desarrollador se ponga al corriente con la arquitectura, el motor de procesamiento digital de señales (DSP) y el flujo de ejecución en menos de 10 minutos.

---

## 1. Arquitectura General del Sistema

BioHevy está estructurado como una aplicación desacoplada de alto rendimiento que integra hardware telemétrico simulado (ESP32) con analíticas de precisión biomédica.

```mermaid
graph TD
    subgraph Frontend (Next.js 15)
        UI[Dashboard & Graph Engine]
        Clerk[Clerk Auth & OAuth]
        WS_Client[sEMG Web Client]
    end

    subgraph Backend (FastAPI / Python)
        API[FastAPI Router]
        DSP[Biomech Engine / DSP Pipeline]
        DB_ORM[SQLAlchemy / SQLite]
    end

    subgraph Hardware / Telemetría
        ESP32[ESP32 / Sensor sEMG Simulator]
    end

    ESP32 -- Telemetría sEMG --> WS_Client
    WS_Client -- Render Osciloscopio --> UI
    UI -- REST requests --> API
    API -- Consultas/Transacciones --> DB_ORM
    DB_ORM -- SQLite File --> DB[(biohevy.db)]
    DSP -- Métricas de Fatiga (RMS/MNF) --> UI
```

### Stack Tecnológico:
* **Frontend:** Next.js 15 (App Router), Tailwind CSS (Aesthetic Glassmorphism), Clerk (Autenticación y OAuth).
* **Backend:** FastAPI (Python), SQLAlchemy (ORM), SQLite (Base de datos local relacional con Foreign Keys activas).
* **Procesamiento de Señal (DSP):** Algoritmos en Python (`biomech_engine.py`) y simulaciones visuales optimizadas en React Canvas/SVG.

---

## 2. El "Ingrediente Secreto": Motor Biomecánico y DSP

La ventaja competitiva de BioHevy es la detección **predictiva** (no reactiva) de la fatiga muscular a través de electromiografía de superficie (sEMG).

### El Flujo del Procesamiento de Señal:
1. **Adquisición Analógica:** Lectura de microvoltios de la actividad eléctrica del sarcolema muscular (ESP32).
2. **Filtrado Digital (DSP):**
   * **Filtro Notch:** Elimina la interferencia electromagnética de la red eléctrica comercial (50Hz / 60Hz).
   * **Filtro Pasa-Banda:** Limita la señal entre 10Hz y 500Hz, eliminando artefactos de movimiento del cable y ruidos de alta frecuencia.
3. **Cálculo de Amplitud (RMS):** Se calcula la raíz media cuadrática para estimar el reclutamiento de unidades motoras (fuerza y volumen de contracción).
4. **Desplazamiento Espectral (Frecuencia Media - MNF):**
   * El indicador estándar de fatiga biológica en medicina deportiva es el **desplazamiento a la izquierda del espectro de frecuencias** (caída de la frecuencia de disparo).
   * BioHevy calcula y gráfica la **MNF** en tiempo real. Cuando la pendiente cae de forma sostenida (ej. de 120Hz a 65Hz) y el coeficiente de regresión $R^2 \ge 0.90$, el sistema gatilla automáticamente la alerta de **"FATIGA INMINENTE DETECTADA"**.

---

## 3. Estructura del Proyecto

```text
S.M.F/
├── iniciar_proyecto.bat     # Lanzador de un solo clic para entorno local
├── DEVELOPER_HANDOFF.md     # Este documento informativo de bienvenida
├── backend/                 # API FastAPI & Lógica de Datos
│   ├── main.py              # Endpoints REST (Sesiones, Rutinas, Usuarios)
│   ├── models.py            # Modelos Relacionales de SQLAlchemy (SQLite)
│   ├── schemas.py           # Validaciones de Datos con Pydantic
│   ├── database.py          # Configuración del motor y Foreign Keys en SQLite
│   ├── biomech_engine.py    # Algoritmos de Procesamiento de Señales EMG (Notch/RMS)
│   ├── seed.py              # Script para poblar la base de datos local con datos iniciales
│   └── run_tests.py         # Suite de pruebas automatizadas de la API
└── biohevy-web/             # Dashboard Frontend en Next.js
    ├── src/
    │   ├── app/             # Rutas principales y flujo de Clerk Auth
    │   ├── components/      # Interfaz de Usuario (Dashboard.tsx, EMGMonitor, Modales)
    │   └── proxy.ts         # Proxy e integraciones locales
```

---

## 4. Guía de Instalación y Arranque (Paso a Paso)

Para que un nuevo desarrollador corra el proyecto desde cero:

### Requisitos Previos:
* **Node.js** (versión 18 o superior).
* **Python** (versión 3.10 o superior) con `pip`.

### Paso 1: Configurar el Backend
1. Abre una terminal en la carpeta `/backend`.
2. Instala las dependencias necesarias:
   ```bash
   pip install fastapi uvicorn sqlalchemy requests pydantic
   ```
3. Genera y puebla la base de datos SQLite ejecutando el semillero:
   ```bash
   python seed.py
   ```
   *(Esto creará el archivo `biohevy.db` con usuarios, ejercicios reales de biomecánica y rutinas preconfiguradas)*.

### Paso 2: Configurar el Frontend
1. Abre una terminal en la carpeta `/biohevy-web`.
2. Instala los módulos de Node:
   ```bash
   npm install
   ```

### Paso 3: Arrancar el Ecosistema Completo
Para ahorrar tiempo, haz doble clic en el archivo executable **`iniciar_proyecto.bat`** en la carpeta raíz. Este se encargará de levantar los puertos `8000` (Backend) y `3000` (Frontend) y abrir las pestañas de desarrollo en tu navegador al instante.

---

## 5. Tareas recomendadas para profundizar en el código

Si quieres que un nuevo programador entienda a fondo la aplicación rápidamente, sugiérele realizar estos micro-ejercicios prácticos en orden de dificultad:

1. **Nivel Básico (Frontend):** Modificar la tasa de muestreo o el color de renderizado de la señal de la Frecuencia Media (MNF) en el componente `BioHevyEMGMonitor` en `Dashboard.tsx`.
2. **Nivel Intermedio (Fullstack):** Agregar una nueva métrica de rendimiento en el resumen de entrenamiento (ej. "Tiempo bajo tensión") en `models.py` y reflejarla en la pantalla de finalización de entrenamiento en el Frontend.
3. **Nivel Avanzado (DSP/Matemático):** Modificar el algoritmo de cálculo de la regresión lineal en el procesamiento sEMG para incluir un filtro adaptativo que reduzca falsos positivos cuando el atleta realiza movimientos bruscos.

---

## 6. Flujo de Git Recomendado para el Equipo

Para compartir el código de forma profesional:
1. **Crear un repositorio en GitHub:** (ej. `github.com/tu-usuario/biohevy`).
2. **Subir el código ignorando dependencias:** El proyecto ya tiene configurados los archivos `.gitignore` para no subir carpetas pesadas como `node_modules`, archivos `.env` privados o la base de datos local temporal `biohevy.db`.
3. **Comandos rápidos para subir el código:**
   ```bash
   git init
   git add .
   git commit -m "feat: core biomechanical engine setup with custom local launcher"
   # Vincula tu repositorio remoto y sube los cambios:
   git remote add origin https://github.com/tu-usuario/biohevy.git
   git branch -M main
   git push -u origin main
   ```
