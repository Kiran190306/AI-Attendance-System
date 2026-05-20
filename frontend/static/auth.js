const AUTH_TOKEN_KEY = 'attendance_token';

function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setAuthToken(token) {
    if (token) {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
    }
}

function clearAuthToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
}

function buildAuthHeaders(init = {}) {
    const headers = new Headers(init.headers || {});
    const token = getAuthToken();
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
}

async function authFetch(input, init = {}) {
    const options = { ...init, headers: buildAuthHeaders(init) };
    const response = await fetch(input, options);
    if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return response;
}

function requireAuth() {
    const token = getAuthToken();
    if (!token) {
        window.location.href = '/login';
    }
}

function logout() {
    clearAuthToken();
    window.location.href = '/login';
}

window.authFetch = authFetch;
window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.requireAuth = requireAuth;
window.logout = logout;
