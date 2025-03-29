// Sistema de Reconhecimento de Veículos ISP - Versão Atualizada
const API_BASE_URL = 'http://localhost:5000/api';
const authToken = localStorage.getItem('authToken');

// Elementos da UI
const loginModal = document.getElementById('login-modal');
const cameraContainer = document.getElementById('camera-container');
const uploadForm = document.getElementById('upload-form');

// Inicialização
document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
    if (!await checkAuth()) {
        showLoginModal();
        return;
    }
    
    loadCameras();
    setupEventListeners();
}

async function checkAuth() {
    if (!authToken) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        return response.ok;
    } catch (error) {
        console.error('Falha na verificação:', error);
        return false;
    }
}

async function loadCameras() {
    try {
        const response = await fetch(`${API_BASE_URL}/cameras`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const cameras = await response.json();
            renderCameras(cameras);
        }
    } catch (error) {
        console.error('Erro ao carregar câmeras:', error);
    }
}

function renderCameras(cameras) {
    cameraContainer.innerHTML = cameras.map(cam => `
        <div class="camera-card">
            <h3>${cam.camera_id}</h3>
            <div class="camera-feed">
                <!-- Implementar visualização da câmera -->
            </div>
        </div>
    `).join('');
}

// Implementar outras funções conforme necessário