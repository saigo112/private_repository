const CACHE_NAME = 'tetris-web-v2';
const STATIC_CACHE = 'tetris-static-v2';

// 即座にキャッシュすべき重要なリソース
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/manifest.json'
];

// 遅延キャッシュ（後でキャッシュ）
const SECONDARY_ASSETS = [
  '/script.js',
  '/icon-192.png',
  '/icon-512.png'
];

// サービスワーカーのインストール（高速化）
self.addEventListener('install', function(event) {
  console.log('Service Worker: 高速インストール中...');
  
  event.waitUntil(
    Promise.all([
      // 重要なリソースのみ即座にキャッシュ
      caches.open(STATIC_CACHE).then(cache => {
        return cache.addAll(CORE_ASSETS);
      }),
      // バックグラウンドでセカンダリリソースをキャッシュ
      caches.open(CACHE_NAME).then(cache => {
        return Promise.allSettled(
          SECONDARY_ASSETS.map(url => 
            fetch(url).then(response => response.ok ? cache.put(url, response) : null)
          )
        );
      })
    ]).catch(error => {
      console.log('Service Worker: 軽量キャッシュ完了', error);
    })
  );
  
  // 新しいサービスワーカーを即座にアクティブ化
  self.skipWaiting();
});

// サービスワーカーのアクティベーション（高速化）
self.addEventListener('activate', function(event) {
  console.log('Service Worker: 高速アクティベーション中...');
  
  event.waitUntil(
    Promise.all([
      // 古いキャッシュを非同期で削除
      caches.keys().then(cacheNames => {
        const validCaches = [CACHE_NAME, STATIC_CACHE];
        return Promise.all(
          cacheNames
            .filter(cacheName => !validCaches.includes(cacheName))
            .map(cacheName => {
              console.log('Service Worker: 古いキャッシュを削除', cacheName);
              return caches.delete(cacheName);
            })
        );
      }),
      // 即座にクライアントを制御
      self.clients.claim()
    ])
  );
});

// フェッチイベントの処理（高速化）
self.addEventListener('fetch', function(event) {
  const url = new URL(event.request.url);
  
  // WebSocketリクエストは無視
  if (url.pathname.includes('/ws')) {
    return;
  }
  
  // APIリクエストは常にネットワークから取得（高速化）
  if (url.pathname.includes('/api/') || 
      url.pathname.includes('/high-score') || 
      url.pathname.includes('/submit-score')) {
    event.respondWith(fetch(event.request));
    return;
  }
  
  // 静的リソースはキャッシュ優先（高速表示）
  if (CORE_ASSETS.includes(url.pathname) || SECONDARY_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          // キャッシュがあれば即座に返す
          return cachedResponse;
        }
        
        // キャッシュにない場合のみネットワークから取得
        return fetch(event.request).then(response => {
          if (response && response.status === 200) {
            const responseToCache = response.clone();
            caches.open(STATIC_CACHE).then(cache => {
              cache.put(event.request, responseToCache);
            });
          }
          return response;
        });
      })
    );
    return;
  }
  
  // その他はネットワーク優先
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request).then(response => {
        return response || caches.match('/index.html');
      });
    })
  );
});

// プッシュ通知（将来の拡張用）
self.addEventListener('push', function(event) {
  console.log('Service Worker: プッシュ通知を受信');
  // 将来のプッシュ通知機能用
});

// バックグラウンド同期（将来の拡張用）
self.addEventListener('sync', function(event) {
  console.log('Service Worker: バックグラウンド同期');
  // 将来のオフライン対応用
});