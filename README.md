# OmniGuard CCTV - Sistema de Monitoreo de Video y Video-Vigilancia

**OmniGuard CCTV** es un sistema profesional e integral de video-vigilancia y monitoreo en tiempo real desarrollado en Python y tecnologías web modernas. Permite supervisar múltiples cámaras (webcams USB/integradas, cámaras de red IP mediante RTSP/HTTP, y entornos de prueba simulados), detección inteligente de movimiento con alertas visuales y sonoras, y almacenamiento de instantáneas y clips de video.

---

## 🚀 Características Principales

- 📹 **Matriz Multi-Cámara (CCTV Grid):**
  - Cuadrícula adaptable con selectores de vista rápida: **1x1** (cámara única), **2x2** (4 cámaras), **3x3** (9 cámaras) y ajuste automático.
  - Streaming fluido a 25–30 FPS mediante protocolo multipart MJPEG (compatible con cualquier navegador moderno sin necesidad de plugins ni códecs externos).
  - On-Screen Display (OSD) profesional con marca de agua en tiempo real: Nombre de cámara, fecha y hora exacta, contador de FPS y estado en vivo.
  - Modo pantalla completa para inspección detallada de cualquier canal.

- 🧠 **Detección Inteligente de Movimiento e Intrusión:**
  - Algoritmo de visión artificial basado en sustracción de fondo y análisis de contornos en tiempo real.
  - Dibuja cajas delimitadoras (*bounding boxes*) de alerta roja sobre las zonas con movimiento.
  - Control de sensibilidad individual por cada cámara (1% a 100%).
  - Sistema de prevención de falsos positivos (filtrado por área mínima y tiempo de enfriamiento).

- 🚨 **Centro de Alertas y Notificaciones:**
  - Panel lateral de alertas en vivo con captura instantánea (thumbnail) y registro de hora al milisegundo.
  - **Alarma sonora integrada:** Sintetizador de audio en tiempo real en el navegador (Web Audio API), configurable con botón de silenciado.
  - Borde de alerta pulsante animado en las cámaras donde se detecta actividad.

- 💾 **Grabación Automática y Manual:**
  - **Auto-grabación ante intrusión:** Al detectar movimiento, genera un clip de video de duración configurable (ej. 10 segundos) y una instantánea en alta resolución.
  - **Grabación manual:** Inicia o detiene la grabación de cualquier canal con un solo clic.
  - **Captura general y manual:** Toma fotografías instantáneas de una o todas las cámaras simultáneamente.

- 🎞️ **Galería de Grabaciones y Eventos (Playback):**
  - Buscador y filtros avanzados por cámara, tipo de evento (*Movimiento*, *Instantánea*, *Video*) y fecha.
  - Reproductor de video HTML5 integrado para revisar clips grabados directamente en el navegador.
  - Descarga directa de archivos de video (MP4) y fotografías (JPG).
  - Eliminación segura de eventos y liberación de espacio en disco.

- ⚙️ **Administración y Configuración:**
  - Panel de control para añadir, pausar, editar o eliminar cámaras en caliente sin reiniciar el servidor.
  - Soporte para **Cámaras Web** (índice 0, 1, 2...), **Cámaras IP / RTSP** (`rtsp://admin:pass@ip:port/stream`) y **Cámaras Simuladas** (para pruebas sin hardware físico).

---

## 📁 Estructura del Proyecto

```text
proyecto de sistema de monitoreo de video/
│
├── app.py                  # Servidor Flask principal y API REST
├── run.py                  # Script de inicio rápido con auto-apertura de navegador
├── run.bat                 # Lanzador de 1-clic para Windows
├── requirements.txt        # Dependencias de Python
├── README.md               # Documentación completa del proyecto
│
├── core/                   # Núcleo de Visión y Procesamiento
│   ├── __init__.py
│   ├── camera.py           # Administrador de cámaras, subprocesos y generación sintética
│   ├── detector.py         # Motor de detección de movimiento con OpenCV
│   ├── recorder.py         # Grabador de video (MP4) y capturas instantáneas
│   └── database.py         # Base de datos SQLite (cámaras, eventos, configuraciones)
│
├── static/                 # Recursos Frontend
│   ├── css/
│   │   └── dashboard.css   # Estilos tema oscuro profesional CCTV
│   └── js/
│       ├── dashboard.js    # Lógica de cuadrícula, alertas en vivo y sintetizador de audio
│       └── playback.js     # Reproductor de grabaciones y filtros de galería
│
├── templates/              # Vistas HTML con Jinja2
│   ├── base.html           # Plantilla base con barra de estado y métricas
│   ├── dashboard.html      # Panel principal de vigilancia
│   ├── playback.html       # Galería de eventos y reproductor
│   └── settings.html       # Gestión de cámaras y ajustes de sensibilidad
│
├── recordings/             # Almacenamiento local de medios
│   ├── snapshots/          # Fotografías JPEG de alarmas e instantáneas
│   └── videos/             # Archivos de video MP4
│
└── data/                   # Datos persistentes
    └── surveillance.db     # Base de datos SQLite
```

---

## 🛠️ Requisitos e Instalación

### Requisitos:
- **Python 3.8 o superior** (probado y optimizado en Python 3.12).
- Cualquier navegador web moderno (Chrome, Edge, Firefox, Brave, Safari).

### Instalación de Dependencias:
Abra una terminal o PowerShell en la carpeta del proyecto y ejecute:
```bash
pip install -r requirements.txt
```

---

## 🏃‍♂️ Cómo Iniciar el Sistema

### Opción 1: Con doble clic en Windows
Haga doble clic en el archivo **`run.bat`**. Se iniciará el servidor y se abrirá automáticamente el panel en su navegador.

### Opción 2: Desde la consola / terminal
```bash
python run.py
```

Luego acceda en su navegador a:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🎥 Configurar Cámaras

El sistema viene preconfigurado con 3 cámaras para comenzar a trabajar de inmediato:
1. **Cámara Principal:** Intenta conectarse a la cámara web conectada al equipo (índice `0`). Si no hay cámara física disponible, pasa al modo simulado sin interrumpir la operación.
2. **Cámara de Acceso / Entrada (Simulada):** Genera un flujo de vigilancia con sujetos animados en movimiento para comprobar la detección en tiempo real.
3. **Cámara de Almacén / Perímetro (Simulada):** Entorno de monitoreo perimetral.

### Para añadir una cámara IP / RTSP:
1. Vaya a la pestaña **Configuración**.
2. Presione **"Añadir Nueva Cámara"**.
3. Seleccione **Cámara IP / Flujo RTSP de Red**.
4. Introduzca la URL de su cámara (ejemplo: `rtsp://admin:123456@192.168.1.100:554/h264Preview_01_main`).
5. Ajuste la sensibilidad de detección y guarde.
