const API_BASE_URL = 'http://127.0.0.1:5000/api';

function getAuthToken() {
    return localStorage.getItem('token');
}

function setAuthToken(token) {
    if (token) {
        localStorage.setItem('token', token);
    } else {
        localStorage.removeItem('token');
    }
}

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    const token = getAuthToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const fetchOptions = {
        ...options,
        headers,
        credentials: 'include'
    };

    try {
        const response = await fetch(url, fetchOptions);
        let data = {};

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        }

        if (!response.ok) {
            // Auto redirect to login if session expires (401 Unauthorized)
            if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
                setAuthToken(null);
                localStorage.removeItem('user');
                const path = window.location.pathname;
                if (!path.includes('auth.html') && !path.includes('index.html') && path !== '/') {
                    window.location.href = 'auth.html';
                }
            }
            throw new Error(data.message || `Request failed with status ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error(`API Client error during request: ${endpoint}`, error);
        throw error;
    }
}

function showToast(title, message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-title">${title}</span>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;

    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 400);
    });

    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 400);
        }
    }, 5000);
}

const api = {
    get: (endpoint) => apiRequest(endpoint, { method: 'GET' }),
    post: (endpoint, body) => apiRequest(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    delete: (endpoint, body) => apiRequest(endpoint, { method: 'DELETE', body: JSON.stringify(body) }),
    showToast,
    getAuthToken,
    setAuthToken
};
