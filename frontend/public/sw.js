// Aureon Portality - Service Worker
const CACHE_NAME = 'aureon-portality-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json'
];

// Install: Cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('🌀 Aureon SW: Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch: Network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // API calls: Network only (don't cache dynamic data)
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/webhook/')) {
        event.respondWith(fetch(request));
        return;
    }

    // Static assets: Cache-first, fallback to network
    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) {
                return cached;
            }
            return fetch(request).then((response) => {
                // Cache successful responses
                if (response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, clone);
                    });
                }
                return response;
            });
        }).catch(() => {
            // Offline fallback
            if (request.destination === 'document') {
                return caches.match('/');
            }
        })
    );
});

// Background sync for offline messages (future feature)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-messages') {
        console.log('🌀 Aureon SW: Syncing offline messages');
        // TODO: Implement offline message queue
    }
});

// Push notifications (future feature)
self.addEventListener('push', (event) => {
    const data = event.data?.json() || { title: 'Auréon', body: 'Nueva notificación' };

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/icons/icon-192.png',
            badge: '/icons/badge-72.png',
            tag: 'aureon-notification',
            vibrate: [200, 100, 200]
        })
    );
});
