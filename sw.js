const CACHE_NAME = 'sport-tv-cache-v1';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json'
];

// Installazione
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Attivazione e pulizia vecchie cache
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch (Network first per data.json, Cache first per il resto)
self.addEventListener('fetch', event => {
  if (event.request.url.includes('data.json')) {
    // Per i dati JSON vai sempre in rete
    event.respondWith(fetch(event.request));
  } else {
    // Per il resto (HTML, manifest) prova la cache, poi la rete
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          if (response) {
            return response;
          }
          return fetch(event.request);
        }
      )
    );
  }
});