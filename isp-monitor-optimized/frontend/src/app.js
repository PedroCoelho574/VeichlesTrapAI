// Configurações
const API_BASE_URL = 'http://localhost:8000';
let authToken = localStorage.getItem('authToken');

// Elementos da UI
const cameraGrid = document.getElementById('camera-grid');
const detectionsTable = document.getElementById('detections-table');
const activeCamerasElement = document.getElementById('active-cameras');
const detectedVehiclesElement = document.getElementById('detected-vehicles');
const todayAlertsElement = document.getElementById('today-alerts');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadCameras();
    loadRecentDetections();
    startStatusUpdates();
});

// Funções de Autenticação
async function checkAuth() {
    if (!authToken) {
        window.location.href = '/login';
    }
}

// Carrega câmeras ativas
async function loadCameras() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/cameras`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar câmeras');
        
        const cameras = await response.json();
        renderCameras(cameras);
        activeCamerasElement.textContent = cameras.length;
    } catch (error) {
        console.error('Erro:', error);
    }
}

// Renderiza as câmeras na grade
function renderCameras(cameras) {
    cameraGrid.innerHTML = '';
    
    cameras.forEach(camera => {
        const cameraCard = document.createElement('div');
        cameraCard.className = 'camera-feed bg-gray-800 rounded-lg overflow-hidden relative';
        
        cameraCard.innerHTML = `
            <div class="absolute top-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
                ${camera.location}
            </div>
            <img src="${camera.rtsp_url}" alt="Feed da Câmera" class="w-full h-full object-cover">
            <div class="absolute bottom-2 left-2 flex space-x-2">
                <span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full">Live</span>
                <span class="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">${camera.id}</span>
            </div>
        `;
        
        cameraGrid.appendChild(cameraCard);
    });
}

// Carrega detecções recentes
async function loadRecentDetections() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/detections?limit=5`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Erro ao carregar detecções');
        
        const detections = await response.json();
        renderDetections(detections);
        detectedVehiclesElement.textContent = detections.length;
    } catch (error) {
        console.error('Erro:', error);
    }
}

// Renderiza as detecções na tabela
function renderDetections(detections) {
    detectionsTable.innerHTML = '';
    
    detections.forEach(detection => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${detection.camera_id}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${new Date(detection.timestamp).toLocaleString()}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                    Veículo ISP
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <img src="${detection.image_url}" alt="Detecção" class="h-12 w-auto rounded">
            </td>
        `;
        
        detectionsTable.appendChild(row);
    });
}

// Atualiza status e verifica alertas
function startStatusUpdates() {
    // Verificação de saúde do sistema
    setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                document.getElementById('system-status').textContent = 'Online';
                document.getElementById('system-status').className = 'mt-2 text-3xl font-semibold text-green-500';
            }
        } catch (error) {
            document.getElementById('system-status').textContent = 'Offline';
            document.getElementById('system-status').className = 'mt-2 text-3xl font-semibold text-red-500';
        }
    }, 5000);

    // Conexão SSE para alertas em tempo real
    const eventSource = new EventSource(`${API_BASE_URL}/api/alerts`);

    eventSource.onmessage = (event) => {
        const alert = JSON.parse(event.data);
        if (alert.type === 'TARGET_DETECTED') {
            showAlertNotification(alert);
            playAlertSound();
            updateDetectionCounter();
        }
    };

    eventSource.onerror = () => {
        console.error('Erro na conexão SSE');
        eventSource.close();
        setTimeout(startStatusUpdates, 5000);
    };
}

// Mostra notificação de alerta
function showAlertNotification(alert) {
    const notifications = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-lg';
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-exclamation-triangle mr-2"></i>
            <strong>Alvo detectado!</strong>
        </div>
        <p class="mt-1 text-sm">Câmera ${alert.camera_id} - ${new Date(alert.timestamp).toLocaleTimeString()}</p>
        <p class="mt-1 text-xs">${alert.message}</p>
    `;
    
    notifications.prepend(notification);
    
    // Remove a notificação após 5 segundos
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Toca som de alerta (usando serviço online confiável)
function playAlertSound() {
    try {
        const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-alarm-digital-clock-beep-989.mp3');
        audio.volume = 0.2;  // Volume mais baixo para não assustar
        audio.play().catch(e => console.log('Erro ao reproduzir som:', e));
        
        // Vibração do dispositivo (se suportado)
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
        }
    } catch (e) {
        console.error('Erro no sistema de alerta:', e);
    }
}

// Atualiza contador de alertas
function updateDetectionCounter() {
    const counter = document.getElementById('today-alerts');
    counter.textContent = parseInt(counter.textContent) + 1;
}

// Adiciona nova câmera
async function addCamera() {
    // Implementação da função para adicionar câmera
}

// Logout
function logout() {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
}