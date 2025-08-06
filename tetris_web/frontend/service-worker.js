const CACHE_NAME = 'tetris-web-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/style.css',
  '/script.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// サービスワーカーのインストール
self.addEventListener('install', function(event) {
  console.log('Service Worker: インストール中...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Service Worker: キャッシュを開きました');
        // 基本的なリソースをプリキャッシュ（オプション）
        return cache.addAll(urlsToCache.slice(0, 4)); // HTMLとCSS、JSのみ
      })
      .catch(function(error) {
        console.log('Service Worker: キャッシュエラー', error);
      })
  );
  
  // 新しいサービスワーカーを即座にアクティブ化
  self.skipWaiting();
});

// サービスワーカーのアクティベーション
self.addEventListener('activate', function(event) {
  console.log('Service Worker: アクティベーション中...');
  
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          // 古いキャッシュを削除
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: 古いキャッシュを削除', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // 新しいサービスワーカーがすべてのクライアントを制御
  self.clients.claim();
});

// フェッチイベントの処理
self.addEventListener('fetch', function(event) {
  // WebSocketリクエストは無視
  if (event.request.url.includes('/ws')) {
    return;
  }
  
  // APIリクエストは常にネットワークから取得
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/high-score') || 
      event.request.url.includes('/submit-score')) {
    event.respondWith(fetch(event.request));
    return;
  }
  
  // その他のリクエストはネットワーク優先、フォールバックでキャッシュ
  event.respondWith(
    fetch(event.request)
      .then(function(response) {
        // レスポンスが有効な場合、キャッシュに保存
        if (response && response.status === 200 && response.type === 'basic') {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(function() {
        // ネットワークエラーの場合、キャッシュから取得
        return caches.match(event.request)
          .then(function(response) {
            if (response) {
              console.log('Service Worker: キャッシュから取得', event.request.url);
              return response;
            }
            // キャッシュにもない場合のフォールバック
            if (event.request.destination === 'document') {
              return caches.match('/index.html');
            }
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