import { supabase } from './supabase';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiFetch(path, options = {}) {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;

    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
        headers.set('Content-Type', 'application/json');
    }
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });
}
