// Service worker: push notifications for meal reminders.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('push', (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = {body: event.data.text()}; }
  event.waitUntil(self.registration.showNotification(data.title || 'Macros', {
    body: data.body || '',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    tag: data.url || 'macros',
    data: {url: data.url || '/'},
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url || '/';
  event.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then((wins) => {
    for (const w of wins) {
      if ('focus' in w) { w.navigate(url); return w.focus(); }
    }
    return self.clients.openWindow(url);
  }));
});
