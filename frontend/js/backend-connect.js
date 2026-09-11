// ============================================================
// backend-connect.js - Gestión de conexión con Raspberry Pi
// ============================================================

const MAX_RETRIES = 5;
const RETRY_DELAY = 3000;
const HEARTBEAT_INTERVAL = 30000;

class BackendConnection {
    constructor() {
        this.connected = false;
        this.retryCount = 0;
        this.eventListeners = new Map();
        this.heartbeatTimer = null;
    }

    async connect() {
        if (this.connected) return;

        try {
            const status = await api.getStatus();
            this.connected = true;
            this.retryCount = 0;
            this.emit('connected', status);
            console.log('[Backend] Conectado:', status.server, status.version);
            return status;
        } catch (error) {
            this.connected = false;
            this.emit('error', error);
            this.scheduleRetry();
            throw error;
        }
    }

    scheduleRetry() {
        if (this.retryCount >= MAX_RETRIES) {
            console.error('[Backend] Máximo de reintentos alcanzado');
            return;
        }
        this.retryCount++;
        console.log(`[Backend] Reintentando (${this.retryCount}/${MAX_RETRIES}) en ${RETRY_DELAY}ms...`);
        setTimeout(() => this.connect(), RETRY_DELAY);
    }

    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const idx = listeners.indexOf(callback);
            if (idx !== -1) listeners.splice(idx, 1);
        }
    }

    emit(event, data) {
        const listeners = this.eventListeners.get(event) || [];
        listeners.forEach(cb => {
            try { cb(data); } catch (e) { console.error('[Backend] Error en listener:', event, e); }
        });
    }

    startHeartbeat(interval = HEARTBEAT_INTERVAL) {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(async () => {
            try {
                await api.getStatus();
                if (!this.connected) {
                    this.connected = true;
                    this.emit('reconnected');
                    console.log('[Backend] Reconexión detectada');
                }
            } catch (error) {
                if (this.connected) {
                    this.connected = false;
                    this.emit('disconnected', error);
                    console.warn('[Backend] Debajo de línea:', error.message);
                }
            }
        }, interval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    destroy() {
        this.stopHeartbeat();
        this.eventListeners.clear();
        this.connected = false;
    }
}

// Se conecta automáticamente y reintenta si la conexión falla.
// El heartbeat detecta desconexiones y emite eventos al UI.
const backend = new BackendConnection();
backend.startHeartbeat();

// ============================================================
// WEBHOOKS (opcional)
// ============================================================

async function configurarWebhooks() {
    try {
        const resp = await fetch(`${API_BASE}/webhooks/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: window.location.origin,
                events: ['adjustment-saved', 'component-updated']
            })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return await resp.json();
    } catch (error) {
        console.warn('[Webhooks] No disponibles:', error.message);
        return null;
    }
}
