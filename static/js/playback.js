// Playback & Event Gallery Management

document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
});

async function loadEvents() {
    const gallery = document.getElementById('events-gallery');
    const cameraId = document.getElementById('filter-camera').value;
    const eventType = document.getElementById('filter-type').value;
    const limit = document.getElementById('filter-limit').value;

    gallery.innerHTML = '<div class="loading-spinner">Cargando eventos...</div>';

    try {
        let url = `/api/events?limit=${limit}`;
        if (cameraId) url += `&camera_id=${encodeURIComponent(cameraId)}`;
        if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;

        const res = await fetch(url);
        const events = await res.json();

        if (events.length === 0) {
            gallery.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 60px 20px;">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                    <h3 style="margin-top: 12px;">No se encontraron grabaciones</h3>
                    <p class="text-muted">No existen eventos que coincidan con los filtros seleccionados.</p>
                </div>
            `;
            return;
        }

        gallery.innerHTML = '';
        events.forEach(evt => {
            const card = createEventCard(evt);
            gallery.appendChild(card);
        });

    } catch (e) {
        gallery.innerHTML = '<div class="text-danger text-center">Error al cargar registros.</div>';
    }
}

function createEventCard(evt) {
    const card = document.createElement('div');
    card.className = 'event-gallery-card';
    card.id = `event-card-${evt.id}`;

    let badgeClass = 'badge-warning';
    let typeName = 'Movimiento';
    let isVideo = !!evt.video_path;

    if (evt.event_type === 'snapshot') {
        badgeClass = 'badge-info';
        typeName = 'Captura Manual';
    } else if (evt.event_type === 'recording' || isVideo) {
        badgeClass = 'badge-secondary';
        typeName = 'Video';
    }

    const mediaSrc = evt.snapshot_path || '/static/img/video_placeholder.png';
    const targetMedia = evt.video_path || evt.snapshot_path;

    card.innerHTML = `
        <div class="event-thumb-wrapper" onclick="openMediaModal('${targetMedia}', '${isVideo ? 'video' : 'image'}', '${evt.camera_name}', '${evt.timestamp}')">
            <img src="${mediaSrc}" class="event-thumb-img" alt="${evt.camera_name}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 60%22><rect fill=%22%23222%22 width=%22100%22 height=%2260%22/><text fill=%22%23888%22 x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2210%22>SIN VISTA</text></svg>'">
            <span class="badge ${badgeClass} event-badge-overlay">${typeName}</span>
            ${isVideo ? '<div class="play-icon-overlay"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg></div>' : ''}
        </div>
        <div class="event-info-box">
            <strong>${evt.camera_name}</strong>
            <span class="text-muted text-xs">${evt.timestamp}</span>
            <p class="text-xs text-muted" style="margin-top: 2px;">${evt.details || ''}</p>
            <div class="event-card-actions">
                <button class="btn btn-xs btn-outline" onclick="openMediaModal('${targetMedia}', '${isVideo ? 'video' : 'image'}', '${evt.camera_name}', '${evt.timestamp}')">
                    ${isVideo ? 'Reproducir' : 'Ver Foto'}
                </button>
                <button class="btn btn-xs btn-danger" onclick="deleteEvent(${evt.id})">Eliminar</button>
            </div>
        </div>
    `;

    return card;
}

function openMediaModal(mediaUrl, type, cameraName, timestamp) {
    const modal = document.getElementById('media-modal');
    const container = document.getElementById('media-container');
    const title = document.getElementById('media-modal-title');
    const ts = document.getElementById('media-modal-timestamp');
    const dlBtn = document.getElementById('btn-download-media');

    title.textContent = `${cameraName} - ${type === 'video' ? 'Clip de Grabación' : 'Instantánea'}`;
    ts.textContent = timestamp;
    dlBtn.href = mediaUrl;

    if (type === 'video') {
        container.innerHTML = `
            <video controls autoplay class="modal-stream-img" style="max-height: 70vh; width: 100%;">
                <source src="${mediaUrl}" type="video/mp4">
                Su navegador no soporta reproducción de video HTML5.
            </video>
        `;
    } else {
        container.innerHTML = `
            <img src="${mediaUrl}" class="modal-stream-img" alt="Foto">
        `;
    }

    modal.classList.remove('d-none');
}

function closeMediaModal() {
    const modal = document.getElementById('media-modal');
    const container = document.getElementById('media-container');
    container.innerHTML = '';
    modal.classList.add('d-none');
}

async function deleteEvent(eventId) {
    if (!confirm("¿Desea eliminar este registro y su archivo del disco?")) return;

    try {
        const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
        if (res.ok) {
            document.getElementById(`event-card-${eventId}`)?.remove();
        }
    } catch (e) {
        alert("Error al eliminar el evento");
    }
}
