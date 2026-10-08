const CACHE = 'cb-plan-v4';
const ASSETS = [
  './', './index.html', './change-plan.html',
  './feed.json', './manifest.webmanifest',
  './icon-192.png', './icon-512.png',
  './icon-maskable-192-v2.png', './icon-maskable-512-v2.png',
  './apple-touch-icon.png', './favicon.ico'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // network-first：优先取线上最新，避免桌面 PWA 被旧缓存卡住（如删除按钮 bug）
  e.respondWith(
    fetch(e.request).then(resp => {
      if (resp && resp.status === 200 && resp.type === 'basic') {
        const cp = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, cp));
      }
      return resp;
    }).catch(() => caches.match(e.request).then(hit => hit || caches.match('./index.html')))
  );
});
