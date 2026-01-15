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


        // Handle 401 Unauthorized - redirect to login (but not if already on login/signup)
        if (response.status === 401) {
            const authEndpoints = ['/auth/login', '/auth/signup'];
            const isAuthEndpoint = authEndpoints.some(ep => endpoint.includes(ep));

            if (!isAuthEndpoint) {
                console.warn('Unauthorized access - redirecting to login');
                localStorage.removeItem('auralis_token');
                localStorage.removeItem('auralis_user');
                window.location.href = '/auth/login';
                throw new Error('Unauthorized - redirecting to login');
            }
        }

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
    const isAuthPage = authPaths.some(p => path === p || path === p + '/');

    if (!token) {
        // If no token and not on an auth page, go to login
        if (!isAuthPage) {
            console.log('No token found - redirecting to login');
            window.location.href = '/auth/login';
        }
        // If on auth page with no token, stay on auth page (don't redirect)
    } else {
        // If token exists and on an auth page, try to validate and redirect to dashboard
        if (isAuthPage) {
            try {
                await apiCall('/auth/session_sync', 'POST');
                // Only redirect if token is valid
                window.location.href = '/dashboard/';
            } catch (err) {
                // If token is invalid/expired, clear it and stay on login
                console.log('Token invalid - clearing and staying on login');
                localStorage.removeItem('auralis_token');
                localStorage.removeItem('auralis_user');
                // Don't redirect - stay on current auth page
            }
        }
        // If token exists and NOT on auth page, allow access (protected pages will handle auth)
    }
}
