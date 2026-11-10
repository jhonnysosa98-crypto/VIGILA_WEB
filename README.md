# OmniGuard CCTV - Sistema de Monitoreo de Video y Videovigilancia

**OmniGuard CCTV** es un sistema integral de videovigilancia y monitoreo en tiempo real desarrollado en Python y tecnologías web modernas. Permite supervisar múltiples cámaras (webcams USB/integradas, cámaras IP mediante RTSP/HTTP y cámaras simuladas), detectar movimiento, generar alertas y almacenar instantáneas y grabaciones de video.

---

## 🚀 Características principales

### 📹 Matriz multicámara (CCTV Grid)
- Cuadrícula adaptable con vistas 1x1, 2x2, 3x3 y ajuste automático.
- Streaming mediante protocolo multipart MJPEG.
- Información en pantalla (OSD): nombre de cámara, fecha, hora, FPS y estado.
- Modo de pantalla completa.

### 🧠 Detección inteligente de movimiento
- Detección mediante sustracción de fondo y análisis de contornos.
- Cuadros delimitadores para identificar movimiento.
- Sensibilidad configurable por cámara.
- Filtrado de falsos positivos mediante área mínima y tiempo de enfriamiento.

### 🚨 Centro de alertas y notificaciones
- Panel lateral de alertas en tiempo real.
- Capturas instantáneas de eventos.
- Alarmas sonoras mediante Web Audio API.
- Indicadores visuales de actividad en las cámaras.

### 💾 Grabación automática y manual
- Grabación automática ante detección de movimiento.
- Captura de fotografías en alta resolución.
- Grabación manual de cada cámara.
- Captura individual o simultánea de varias cámaras.

### 🎞️ Galería de grabaciones y eventos
- Filtros por cámara, tipo de evento y fecha.
- Reproductor de video HTML5.
- Descarga de videos MP4 e imágenes JPG.
- Administración y eliminación de eventos.

### ⚙️ Administración y configuración
- Agregar, editar, pausar y eliminar cámaras.
- Compatibilidad con webcams USB.
- Compatibilidad con cámaras IP y flujos RTSP/HTTP.
- Cámaras simuladas para realizar pruebas.

---

## 📁 Estructura del proyecto

```text
proyecto de sistema de monitoreo de video/
│
├── app.py
├── run.py
├── run.bat
├── requirements.txt
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── camera.py
│   ├── detector.py
│   ├── recorder.py
│   └── database.py
│
├── static/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       ├── dashboard.js
│       ├── playback.js
│       └── qrcode.min.js
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── playback.html
│   └── settings.html
│
├── recordings/
│   ├── snapshots/
│   └── videos/
│
└── data/
    └── surveillance.db
```

---

## 🛠️ Requisitos e instalación

### Requisitos
- Python 3.8 o superior.
- Navegador web moderno: Chrome, Edge, Firefox, Brave o Safari.
- Webcam o cámara IP (opcional para utilizar cámaras simuladas).

### Instalación de dependencias

Abre CMD o PowerShell dentro de la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

---

## 🏃 Cómo iniciar el sistema

### Opción 1: Desde Windows

Ejecuta mediante doble clic:

```text
run.bat
```

### Opción 2: Desde la terminal

Ejecuta:

```bash
python run.py
```

Luego abre el navegador en:

**http://127.0.0.1:5000**

---

## 🎥 Configuración de cámaras

El sistema incluye una configuración inicial de tres cámaras:

1. **Cámara principal:** intenta conectarse a la webcam del equipo mediante el índice 0. Si no hay cámara disponible, utiliza el modo simulado cuando está configurado para ello.
2. **Cámara de acceso / entrada:** cámara simulada para realizar pruebas de detección.
3. **Cámara de almacén / perímetro:** entorno simulado para pruebas de monitoreo.

### Añadir una cámara IP / RTSP

1. Accede a la pestaña **Configuración**.
2. Selecciona **Añadir nueva cámara**.
3. Elige el tipo **Cámara IP / Flujo RTSP de red**.
4. Introduce la dirección de conexión de tu cámara.
5. Configura los parámetros disponibles y guarda los cambios.

Ejemplo de formato de conexión:

```text
rtsp://usuario:contraseña@192.168.1.100:554/ruta_del_stream
```

**Importante:** No publiques direcciones RTSP reales que contengan usuarios o contraseñas.

---

## 📌 Tecnologías utilizadas

- **Python:** lenguaje principal del backend.
- **Flask:** servidor web y API.
- **OpenCV:** procesamiento de imágenes y detección de movimiento.
- **SQLite:** almacenamiento de información.
- **HTML5:** estructura de las interfaces.
- **CSS3:** diseño y estilos.
- **JavaScript:** interactividad y actualización de información en tiempo real.
- **MJPEG:** transmisión de video en navegadores.

---

## 👨‍💻 Proyecto

**Nombre:** OmniGuard CCTV  
**Repositorio:** VIGILA_WEB  
**Categoría:** Sistema de monitoreo y videovigilancia  
**Desarrollo:** Python y tecnologías web.

