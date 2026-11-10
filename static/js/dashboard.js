// Dashboard & Live Surveillance Management

let lastAlertId = 0;
let soundEnabled = true;
let audioCtx = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initGridControls();
    initSoundControl();
    initVideoFeeds();
    startPollingStats();
    startPollingAlerts();
});

// Carga asíncrona de video feeds para velocidad ultrarrápida en móviles
function initVideoFeeds() {
    // Permitir que la UI y estilos se pinten primero (50ms)
    setTimeout(() => {
        const feeds = document.querySelectorAll('.camera-feed-img[data-feed]');
        feeds.forEach(img => {
            const feedUrl = img.getAttribute('data-feed');
            if (feedUrl && !img.src.includes('/video_feed/')) {
                img.src = feedUrl;
            }
        });
    }, 60);
}

// Reloj digital en tiempo real
function initClock() {
    const clockEl = document.getElementById('clock-display');
    const update = () => {
        const now = new Date();
        if (clockEl) {
            clockEl.textContent = now.toTimeString().split(' ')[0];
        }
    };
    update();
    setInterval(update, 1000);
}

// Selector de cuadrícula
function initGridControls() {
    const gridBtns = document.querySelectorAll('#grid-controls button');
    const gridEl = document.getElementById('camera-grid');

    gridBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            gridBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const gridClass = btn.getAttribute('data-grid');
            if (gridEl) {
                gridEl.className = `camera-grid ${gridClass}`;
            }
        });
    });

    const snapAllBtn = document.getElementById('btn-snapshot-all');
    if (snapAllBtn) {
        snapAllBtn.addEventListener('click', snapshotAllCameras);
    }
}

// Control de sonido y sintetizador de alarma
function initSoundControl() {
    const soundBtn = document.getElementById('btn-sound-toggle');
    const soundIcon = document.getElementById('sound-icon');
    const soundText = document.getElementById('sound-text');

    if (soundBtn) {
        soundBtn.addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            if (soundEnabled) {
                soundIcon.textContent = '🔊';
                soundText.textContent = 'Alarma Sonora';
                soundBtn.classList.remove('btn-outline');
                soundBtn.classList.add('btn-primary');
                playAlarmTone();
            } else {
                soundIcon.textContent = '🔇';
                soundText.textContent = 'Silenciado';
                soundBtn.classList.remove('btn-primary');
                soundBtn.classList.add('btn-outline');
            }
        });
    }
}

// Generador de tono de alarma sintetizado (Web Audio API)
function playAlarmTone() {
    if (!soundEnabled) return;
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
        osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.25); // A4

        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + 0.26);
    } catch (e) {
        console.warn('Audio API warning:', e);
    }
}

// Polling de estadísticas del sistema (CPU, RAM, Cámaras, Almacenamiento)
function startPollingStats() {
    const updateStats = async () => {
        try {
            const res = await fetch('/api/system_stats');
            if (res.ok) {
                const data = await res.json();
                document.getElementById('stat-cpu').textContent = `${Math.round(data.cpu_usage)}%`;
                document.getElementById('stat-ram').textContent = `${Math.round(data.ram_usage)}%`;
                document.getElementById('stat-cameras').textContent = `${data.active_cameras}/${data.total_cameras} Cams`;
                
                const alertCountEl = document.getElementById('today-alerts-count');
                if (alertCountEl) alertCountEl.textContent = data.today_events;
                
                const storageEl = document.getElementById('storage-used-mb');
                if (storageEl) storageEl.textContent = `${data.recordings_mb} MB`;
            }
        } catch (e) {
            // Error silencioso en polling
        }
    };

    updateStats();
    setInterval(updateStats, 3000);
}

// Polling de alertas de movimiento en tiempo real
function startPollingAlerts() {
    const checkAlerts = async () => {
        try {
            const res = await fetch(`/api/live_alerts?since_id=${lastAlertId}`);
            if (res.ok) {
                const alerts = await res.json();
                if (alerts.length > 0) {
                    alerts.forEach(alert => {
                        if (alert.event_id > lastAlertId) {
                            lastAlertId = alert.event_id;
                            handleNewAlert(alert);
                        }
                    });
                }
            }
        } catch (e) {}
    };

    setInterval(checkAlerts, 1800);
}

// Manejo de una nueva alerta de intrusión
function handleNewAlert(alert) {
    playAlarmTone();

    // Actualizar contador del panel lateral
    const counterEl = document.getElementById('live-alert-counter');
    if (counterEl) {
        counterEl.textContent = parseInt(counterEl.textContent || '0') + 1;
    }

    // Efecto visual en la tarjeta de la cámara
    const card = document.getElementById(`card-${alert.camera_id}`);
    const motionBadge = document.getElementById(`motion-badge-${alert.camera_id}`);
    if (card) {
        card.classList.add('motion-alert');
        if (motionBadge) motionBadge.classList.remove('d-none');

        setTimeout(() => {
            card.classList.remove('motion-alert');
            if (motionBadge) motionBadge.classList.add('d-none');
        }, 4000);
    }

    // Añadir al panel lateral
    const list = document.getElementById('live-alerts-list');
    if (list) {
        const placeholder = list.querySelector('.no-alerts-placeholder');
        if (placeholder) placeholder.remove();

        const item = document.createElement('div');
        item.className = 'alert-item-card';
        item.onclick = () => {
            if (alert.snapshot_path) {
                window.open(alert.snapshot_path, '_blank');
            }
        };

        const imgTag = alert.snapshot_path 
            ? `<img src="${alert.snapshot_path}" class="alert-item-thumb" alt="Alerta">`
            : `<div class="alert-item-thumb"></div>`;

        item.innerHTML = `
            ${imgTag}
            <div class="alert-item-info">
                <span class="alert-cam-name">${alert.camera_name}</span>
                <span class="alert-time">⚠️ Movimiento [${alert.timestamp}]</span>
            </div>
        `;
        list.prepend(item);

        // Mantener máximo 30 elementos en la lista
        while (list.children.length > 30) {
            list.removeChild(list.lastChild);
        }
    }

    showToast(`⚠️ Intrusión detectada en ${alert.camera_name}`, 'alert');
}

// Acciones sobre cámaras individuales
async function triggerSnapshot(cameraId) {
    try {
        const res = await fetch(`/api/cameras/${cameraId}/snapshot`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('📸 Instantánea guardada con éxito', 'success');
        } else {
            showToast('Error al capturar imagen', 'error');
        }
    } catch (e) {
        showToast('Error de conexión', 'error');
    }
}

async function snapshotAllCameras() {
    const cards = document.querySelectorAll('.camera-card[data-cam-id]');
    cards.forEach(card => {
        const camId = card.getAttribute('data-cam-id');
        triggerSnapshot(camId);
    });
}

async function toggleRecording(cameraId) {
    try {
        const btn = document.getElementById(`btn-rec-${cameraId}`);
        const recBadge = document.getElementById(`rec-badge-${cameraId}`);
        
        const res = await fetch(`/api/cameras/${cameraId}/toggle_record`, { method: 'POST' });
        const data = await res.json();
        
        if (data.recording) {
            btn?.classList.add('recording');
            recBadge?.classList.remove('d-none');
            showToast('🔴 Grabación de video iniciada', 'alert');
        } else {
            btn?.classList.remove('recording');
            recBadge?.classList.add('d-none');
            showToast('⏹️ Grabación finalizada y guardada', 'info');
        }
    } catch (e) {
        showToast('Error al alternar grabación', 'error');
    }
}

async function toggleCameraActive(cameraId) {
    try {
        const res = await fetch(`/api/cameras/${cameraId}/toggle_active`, { method: 'POST' });
        const data = await res.json();
        location.reload();
    } catch (e) {
        showToast('Error al cambiar estado de cámara', 'error');
    }
}

// Modal de pantalla completa
function expandCamera(cameraId, cameraName) {
    const modal = document.getElementById('camera-modal');
    const modalImg = document.getElementById('modal-cam-img');
    const modalTitle = document.getElementById('modal-cam-title');

    modalTitle.textContent = `Vigilancia en Vivo: ${cameraName}`;
    modalImg.src = `/video_feed/${cameraId}?t=${Date.now()}`;
    modal.classList.remove('d-none');
}

function closeCameraModal() {
    const modal = document.getElementById('camera-modal');
    const modalImg = document.getElementById('modal-cam-img');
    modalImg.src = '';
    modal.classList.add('d-none');
}

// Recuperación de error en feed de video
function handleFeedError(cameraId) {
    const img = document.getElementById(`feed-img-${cameraId}`);
    if (img) {
        setTimeout(() => {
            img.src = `/video_feed/${cameraId}?retry=${Date.now()}`;
        }, 3000);
    }
}

// Mostrar notificaciones Toast flotantes
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
