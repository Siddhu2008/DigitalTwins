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

async function handleLogout() {
    try {
        await fetch('/auth/logout', { method: 'POST' });
    } catch (e) { }
    localStorage.removeItem('auralis_token');
    localStorage.removeItem('auralis_user');
    window.location.href = '/auth/login';
}

async function checkAuth() {
    const token = localStorage.getItem('auralis_token');
    const path = window.location.pathname;

    // Auth routes that should redirect to dashboard if token exists
    const authPaths = ['/auth/login', '/auth/signup', '/auth/loading', '/auth/'];

    if (!token) {
        // If no token and not on an auth page, go to loading (which leads to login)
        if (!path.startsWith('/auth')) {
            window.location.href = '/auth/loading';
        }
    } else {
        // If token exists and on an auth page, try to restore session and go to dashboard
        if (authPaths.some(p => path === p || path === p + '/')) {
            try {
                await apiCall('/auth/session_sync', 'POST');
                window.location.href = '/dashboard/';
            } catch (err) {
                // If token is invalid/expired, clear it
                localStorage.removeItem('auralis_token');
                localStorage.removeItem('auralis_user');
                if (path !== '/auth/login') window.location.href = '/auth/login';
            }
        }
    }
}
