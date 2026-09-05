// Service worker minimo. TODO: agregar cache real de assets estaticos
// y de las ultimas respuestas de la API para soporte offline.

const CACHE_NAME = "mercadito-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Por ahora, pasa directo a la red sin cachear nada.
  // TODO: estrategia cache-first para assets estaticos,
  // network-first para llamadas a la API.
});
