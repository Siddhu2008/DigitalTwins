// Main JS for Auralis

const API_BASE = '';

async function apiCall(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('auralis_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(endpoint, config);
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || 'API Error');
        }
        return result;
    } catch (error) {
        console.error('API Call Failed:', error);
        throw error;
    }
}

function handleLogout() {
    localStorage.removeItem('auralis_token');
    localStorage.removeItem('auralis_user');
    window.location.href = '/auth/login';
}

function checkAuth() {
    const token = localStorage.getItem('auralis_token');
    const path = window.location.pathname;
    if (!token && !path.startsWith('/auth')) {
        window.location.href = '/auth/login';
    } else if (token && path.startsWith('/auth')) {
        window.location.href = '/dashboard/';
    }
}
