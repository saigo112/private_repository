class TetrisWebGame {
    constructor() {
        this.gameBoard = document.getElementById('gameBoard');
        this.nextPieceCanvas = document.getElementById('nextPiece');
        this.ctx = this.gameBoard.getContext('2d');
        this.nextCtx = this.nextPieceCanvas.getContext('2d');
        
        this.blockSize = 30;
        this.boardWidth = 10;
        this.boardHeight = 20;
        
        this.gameState = null;
        this.websocket = null;
        this.isConnected = false;
        this.gameStarted = false;
        
        // 連打対策用の変数
        this.lastActionTime = {};
        this.actionCooldown = 100; // ミリ秒
        
        // ゲームオーバー効果音の再生制御
        this.gameOverSoundPlayed = false;
        
        // タッチドラッグ用の変数
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.dragThreshold = 15; // ドラッグ判定の閾値（ピクセル）
        this.lastDragTime = 0;
        this.dragCooldown = 150; // ドラッグ操作のクールダウン（ミリ秒）
        
        // 音声の初期化
        this.sounds = {};
        this.bgm = null;
        this.loadSounds();
        
        this.setupEventListeners();
        this.setupOPScreen();
    }
    
    setupOPScreen() {
        // OP画面の開始ボタンイベント
        const startGameBtn = document.getElementById('startGameBtn');
        if (startGameBtn) {
            startGameBtn.addEventListener('click', () => {
                this.startGameFromOP();
            });
        }
    }

    startGameFromOP() {
        // OP画面を非表示にしてゲーム画面を表示
        const opScreen = document.getElementById('opScreen');
        const gameScreen = document.getElementById('gameScreen');
        
        if (opScreen && gameScreen) {
            opScreen.style.display = 'none';
            gameScreen.classList.remove('hidden');
            
            // ゲームを開始
            this.gameStarted = true;
            this.connectWebSocket();
            
            // WebSocket接続後にゲームを開始
            setTimeout(() => {
                this.startGame();
            }, 1000);
            
            // BGMを開始
            setTimeout(() => {
                this.playBGM();
            }, 2000);
        }
    }

    setupEventListeners() {
        // キーボードイベント
        document.addEventListener('keydown', (e) => {
            if (!this.isConnected || !this.gameStarted) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.sendAction('left');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.sendAction('right');
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.sendAction('down');
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.sendAction('rotate');
                    break;
                case ' ':
                    e.preventDefault();
                    this.sendAction('hard_drop');
                    break;
                case 'b':
                case 'B':
                    e.preventDefault();
                    this.sendAction('spawn_bomb');
                    break;
                case 'p':
                case 'P':
                    e.preventDefault();
                    this.sendAction('pause');
                    break;
                case '+':
                case '=':
                case ';':  // Macの日本語キーボード
                case ':':  // Macの日本語キーボード（Shift+;）
                    e.preventDefault();
                    this.sendAction('speed_up');
                    break;
                case '-':
                case '_':  // Macの日本語キーボード（Shift+-）
                    e.preventDefault();
                    this.sendAction('speed_down');
                    break;
            }
            
            // キーコードベースの判定（Mac対応）
            switch(e.keyCode || e.which) {
                case 187: // = キー
                case 59:  // ; キー
                case 186: // ; キー（一部のMac）
                    e.preventDefault();
                    this.sendAction('speed_up');
                    break;
                case 189: // - キー
                case 173: // - キー（一部のMac）
                    e.preventDefault();
                    this.sendAction('speed_down');
                    break;
            }
            
            // デバッグ用：キー情報をコンソールに出力
            console.log('Key pressed:', e.key, 'KeyCode:', e.keyCode, 'Which:', e.which);
        });
        
        // モバイルコントロールボタン（連打対策付き）
        const mobileButtons = [
            { id: 'leftBtn', action: 'left' },
            { id: 'rightBtn', action: 'right' },
            { id: 'downBtn', action: 'down' },
            { id: 'upBtn', action: 'rotate' },
            { id: 'bombBtn', action: 'spawn_bomb' },
            { id: 'pauseBtn', action: 'pause' }
        ];
        
        mobileButtons.forEach(button => {
            const element = document.getElementById(button.id);
            if (element) {
                element.addEventListener('click', () => {
                    if (this.isConnected) this.sendAction(button.action);
                });
            }
        });
        
        // リスタートボタン
        const restartBtn = document.getElementById('restartBtn');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                this.startGame();
            });
        }
        
        // ゲームボードのタッチドラッグ操作
        this.setupTouchDrag();
        
        // ゲームボードのクリック・タッチイベント（爆弾配置用）
        const handleBoardInteraction = (e) => {
            if (!this.isConnected) return;
            
            const rect = this.gameBoard.getBoundingClientRect();
            let clientX, clientY;
            
            // タッチイベントとマウスイベントの両方に対応
            if (e.touches && e.touches[0]) {
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            } else {
                clientX = e.clientX;
                clientY = e.clientY;
            }
            
            const x = Math.floor((clientX - rect.left) / this.blockSize);
            const y = Math.floor((clientY - rect.top) / this.blockSize);
            
            if (x >= 0 && x < this.boardWidth && y >= 0 && y < this.boardHeight) {
                // クリック/タッチした位置に爆弾を配置
                this.sendAction('place_bomb', x, y);
            }
        };
        
        this.gameBoard.addEventListener('click', handleBoardInteraction);
        this.gameBoard.addEventListener('touchstart', handleBoardInteraction);
    }
    
    loadSounds() {
        // 音声ファイルを読み込み
        try {
            // 効果音の読み込み
            this.sounds.move = new Audio('assets/sounds/move.wav');
            this.sounds.rotate = new Audio('assets/sounds/rotate.wav');
            this.sounds.drop = new Audio('assets/sounds/drop.wav');
            this.sounds.clear = new Audio('assets/sounds/clear.wav');
            this.sounds.bomb = new Audio('assets/sounds/bomb.wav');
            this.sounds.gameover = new Audio('assets/sounds/gameover.wav');
            
            // BGMの読み込み
            this.bgm = new Audio('assets/sounds/tetris_bgm_1.wav');
            this.bgm.loop = true;
            this.bgm.volume = 0.3;
            this.bgm.preload = 'auto';
            
            // BGMの読み込み完了を待つ
            this.bgm.addEventListener('canplaythrough', () => {
                console.log('BGMの読み込みが完了しました');
            });
            
            console.log('音声ファイルの読み込みが完了しました');
        } catch (error) {
            console.error('音声ファイルの読み込みに失敗しました:', error);
        }
    }
    
    playSound(soundName) {
        // 効果音を再生
        if (this.sounds[soundName]) {
            // ゲームオーバー効果音の場合は特別な処理
            if (soundName === 'gameover' && this.gameOverSoundPlayed) {
                return; // 既に再生済みの場合はスキップ
            }
            
            this.sounds[soundName].currentTime = 0;
            this.sounds[soundName].play().catch(e => {
                console.log('効果音の再生に失敗:', e);
            });
        }
    }
    
    playBGM() {
        // BGMを再生
        if (this.bgm) {
            // ユーザーインタラクション後に再生を試行
            const playPromise = this.bgm.play();
            if (playPromise !== undefined) {
                playPromise.catch(e => {
                    console.log('BGMの再生に失敗:', e);
                    // ユーザーインタラクションが必要な場合の処理
                    document.addEventListener('click', () => {
                        this.bgm.play().catch(e => console.log('BGM再生再試行失敗:', e));
                    }, { once: true });
                });
            }
        }
    }
    
    stopBGM() {
        // BGMを停止
        if (this.bgm) {
            this.bgm.pause();
            this.bgm.currentTime = 0;
        }
    }
    
    toggleMute() {
        // ミュートの切り替え
        const muteBtn = document.getElementById('muteBtn');
        if (this.bgm.muted) {
            this.bgm.muted = false;
            muteBtn.textContent = '🔊 ミュート';
        } else {
            this.bgm.muted = true;
            muteBtn.textContent = '🔇 ミュート解除';
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            console.log('WebSocket接続済み');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const gameState = JSON.parse(event.data);
                this.updateGameState(gameState);
            } catch (error) {
                console.error('WebSocketメッセージの解析エラー:', error);
            }
        };
        
        this.websocket.onclose = () => {
            this.isConnected = false;
            console.log('WebSocket接続が切れました');
            // 再接続を試行
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocketエラー:', error);
            console.log('WebSocket接続エラー:', error);
        };
    }
    
    updateConnectionStatus(message, color) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.style.color = color;
        }
    }
    
    sendAction(action, x = null, y = null) {
        if (!this.isConnected) return;
        
        // 連打対策
        const now = Date.now();
        if (this.lastActionTime[action] && (now - this.lastActionTime[action]) < this.actionCooldown) {
            return; // クールダウン中はアクションを無視
        }
        this.lastActionTime[action] = now;
        
        // アクションに応じて効果音を再生
        switch(action) {
            case 'left':
            case 'right':
            case 'down':
                this.playSound('move');
                break;
            case 'rotate':
                this.playSound('rotate');
                break;
            case 'hard_drop':
                this.playSound('drop');
                break;
            case 'spawn_bomb':
                this.playSound('bomb');
                break;
        }
        
        const message = { action };
        if (x !== null && y !== null) {
            message.x = x;
            message.y = y;
        }
        
        this.websocket.send(JSON.stringify(message));
    }
    
    async startGame() {
        try {
            // ゲームオーバー効果音フラグをリセット
            this.gameOverSoundPlayed = false;
            
            const response = await fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateGameState(data.game_state);
                // BGMを開始
                this.playBGM();
            }
        } catch (error) {
            console.error('ゲーム開始エラー:', error);
        }
    }
    
    updateGameState(gameState) {
        // ライン消去エフェクトの処理
        if (gameState.lines_cleared_this_frame > 0) {
            this.playSound('clear');
            this.showLineClearEffect(gameState.lines_cleared_this_frame);
        }
        
        this.gameState = gameState;
        this.render();
        this.updateUI();
    }
    
    render() {
        if (!this.gameState) return;
        
        // ゲームボードの描画
        this.renderBoard();
        
        // 現在のピースの描画
        this.renderCurrentPiece();
        
        // 爆弾の描画
        this.renderBombs();
        
        // 次のピースの描画
        this.renderNextPiece();
    }
    
    renderBoard() {
        // 背景をクリア
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.gameBoard.width, this.gameBoard.height);
        
        // グリッドを描画
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1;
        
        for (let x = 0; x <= this.boardWidth; x++) {
            this.ctx.beginPath();
            this.ctx.moveTo(x * this.blockSize, 0);
            this.ctx.lineTo(x * this.blockSize, this.boardHeight * this.blockSize);
            this.ctx.stroke();
        }
        
        for (let y = 0; y <= this.boardHeight; y++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y * this.blockSize);
            this.ctx.lineTo(this.boardWidth * this.blockSize, y * this.blockSize);
            this.ctx.stroke();
        }
        
        // 配置済みブロックを描画
        for (let y = 0; y < this.boardHeight; y++) {
            for (let x = 0; x < this.boardWidth; x++) {
                const cell = this.gameState.board[y][x];
                if (cell) {
                    this.drawBlock(x, y, cell);
                }
            }
        }
    }
    
    renderCurrentPiece() {
        if (!this.gameState.current_piece) return;
        
        const piece = this.gameState.current_piece;
        const shape = piece.shape;
        
        for (let y = 0; y < shape.length; y++) {
            for (let x = 0; x < shape[y].length; x++) {
                if (shape[y][x]) {
                    if (piece.is_bomb) {
                        this.drawBomb(piece.x + x, piece.y + y);
                    } else {
                        this.drawBlock(piece.x + x, piece.y + y, piece.color);
                    }
                }
            }
        }
    }
    
    renderBombs() {
        if (!this.gameState.bombs) return;
        
        this.gameState.bombs.forEach(bomb => {
            if (bomb.active) {
                this.drawBomb(bomb.x, bomb.y);
            }
        });
    }
    
    renderNextPiece() {
        if (!this.gameState.next_piece) return;
        
        // 背景をクリア
        this.nextCtx.fillStyle = '#000';
        this.nextCtx.fillRect(0, 0, this.nextPieceCanvas.width, this.nextPieceCanvas.height);
        
        const piece = this.gameState.next_piece;
        const shape = piece.shape;
        const blockSize = 20;
        
        // 中央に配置
        const startX = (this.nextPieceCanvas.width - shape[0].length * blockSize) / 2;
        const startY = (this.nextPieceCanvas.height - shape.length * blockSize) / 2;
        
        for (let y = 0; y < shape.length; y++) {
            for (let x = 0; x < shape[y].length; x++) {
                if (shape[y][x]) {
                    if (piece.is_bomb) {
                        // 爆弾ピースの描画
                        const centerX = startX + x * blockSize + blockSize / 2;
                        const centerY = startY + y * blockSize + blockSize / 2;
                        const radius = blockSize / 3;
                        
                        this.nextCtx.fillStyle = '#ff4444';
                        this.nextCtx.beginPath();
                        this.nextCtx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                        this.nextCtx.fill();
                        
                        this.nextCtx.strokeStyle = '#000';
                        this.nextCtx.lineWidth = 2;
                        this.nextCtx.stroke();
                    } else {
                        this.drawBlockOnCanvas(
                            this.nextCtx,
                            startX + x * blockSize,
                            startY + y * blockSize,
                            blockSize,
                            piece.color
                        );
                    }
                }
            }
        }
    }
    
    drawBlock(x, y, color) {
        this.drawBlockOnCanvas(this.ctx, x * this.blockSize, y * this.blockSize, this.blockSize, color);
    }
    
    drawBlockOnCanvas(ctx, x, y, size, color) {
        // メインブロック
        ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
        ctx.fillRect(x, y, size, size);
        
        // ハイライト
        ctx.fillStyle = `rgba(255, 255, 255, 0.3)`;
        ctx.fillRect(x, y, size, size / 4);
        ctx.fillRect(x, y, size / 4, size);
        
        // シャドウ
        ctx.fillStyle = `rgba(0, 0, 0, 0.3)`;
        ctx.fillRect(x + size * 3/4, y, size / 4, size);
        ctx.fillRect(x, y + size * 3/4, size, size / 4);
        
        // ボーダー
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, size, size);
    }
    
    drawBomb(x, y) {
        const centerX = x * this.blockSize + this.blockSize / 2;
        const centerY = y * this.blockSize + this.blockSize / 2;
        const radius = this.blockSize / 2; // サイズを大きくする
        
        // 爆弾の本体（グラデーション効果）
        const gradient = this.ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
        gradient.addColorStop(0, '#ff6666');
        gradient.addColorStop(1, '#cc0000');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // 爆弾のボーダー
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // 爆弾の導火線
        this.ctx.strokeStyle = '#ffaa00';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - radius);
        this.ctx.lineTo(centerX, centerY - radius - 8);
        this.ctx.stroke();
        
        // 火花エフェクト
        this.ctx.strokeStyle = '#ffff00';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 2, centerY - radius - 8);
        this.ctx.lineTo(centerX + 2, centerY - radius - 12);
        this.ctx.stroke();
    }
    
    updateUI() {
        if (!this.gameState) return;
        
        // スコア情報を更新
        document.getElementById('score').textContent = this.gameState.score;
        document.getElementById('level').textContent = this.gameState.level;
        document.getElementById('lines').textContent = this.gameState.lines_cleared;
        document.getElementById('bombs').textContent = this.gameState.bombs_available;
        document.getElementById('speed').textContent = this.gameState.speed_multiplier.toFixed(1) + 'x';
        
        // ゲームオーバー状態を更新
        const gameOverElement = document.getElementById('gameOver');
        if (this.gameState.game_over) {
            gameOverElement.classList.remove('hidden');
            
            // ゲームオーバー効果音を一度だけ再生
            if (!this.gameOverSoundPlayed) {
                this.stopBGM();
                this.playSound('gameover');
                this.gameOverSoundPlayed = true;
                
                // 3秒後にOP画面に戻る
                setTimeout(() => {
                    this.returnToOPScreen();
                }, 3000);
            }
        } else {
            gameOverElement.classList.add('hidden');
            // ゲームが再開されたらフラグをリセット
            this.gameOverSoundPlayed = false;
        }
        
        // ポーズ状態を更新
        const pauseBtn = document.getElementById('pauseBtn');
        if (this.gameState.paused) {
            pauseBtn.textContent = '▶️ 再開';
        } else {
            pauseBtn.textContent = '⏸️ ポーズ';
        }
    }

    setupTouchDrag() {
        // タッチドラッグ操作の設定
        const board = this.gameBoard;
        
        // タッチ開始
        board.addEventListener('touchstart', (e) => {
            if (!this.isConnected || !this.gameStarted) return;
            
            e.preventDefault();
            const touch = e.touches[0];
            this.isDragging = true;
            this.dragStartX = touch.clientX;
            this.dragStartY = touch.clientY;
        }, { passive: false });
        
        // タッチ移動
        board.addEventListener('touchmove', (e) => {
            if (!this.isConnected || !this.gameStarted || !this.isDragging) return;
            
            e.preventDefault();
            const touch = e.touches[0];
            const deltaX = touch.clientX - this.dragStartX;
            const deltaY = touch.clientY - this.dragStartY;
            
            // ドラッグ距離が閾値を超えた場合のみ処理
            if (Math.abs(deltaX) > this.dragThreshold || Math.abs(deltaY) > this.dragThreshold) {
                const now = Date.now();
                if (now - this.lastDragTime > this.dragCooldown) {
                    this.handleDragGesture(deltaX, deltaY);
                    this.lastDragTime = now;
                    this.isDragging = false;
                }
            }
        }, { passive: false });
        
        // タッチ終了時にも処理
        board.addEventListener('touchend', (e) => {
            if (!this.isConnected || !this.gameStarted || !this.isDragging) return;
            
            e.preventDefault();
            const touch = e.changedTouches[0];
            const deltaX = touch.clientX - this.dragStartX;
            const deltaY = touch.clientY - this.dragStartY;
            
            // 短いタップの場合は回転
            if (Math.abs(deltaX) < this.dragThreshold && Math.abs(deltaY) < this.dragThreshold) {
                this.sendAction('rotate');
            }
            
            this.isDragging = false;
        }, { passive: false });
        

        
        // タッチキャンセル
        board.addEventListener('touchcancel', (e) => {
            if (!this.isConnected || !this.gameStarted) return;
            
            e.preventDefault();
            this.isDragging = false;
        }, { passive: false });
    }
    
    handleDragGesture(deltaX, deltaY) {
        // ドラッグ方向に基づいてアクションを実行
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        if (absX > absY) {
            // 水平ドラッグ
            if (deltaX > 0) {
                this.sendAction('right');
            } else {
                this.sendAction('left');
            }
        } else {
            // 垂直ドラッグ
            if (deltaY > 0) {
                this.sendAction('down');
            } else {
                this.sendAction('rotate');
            }
        }
    }

    returnToOPScreen() {
        // ゲーム画面を非表示にしてOP画面を表示
        const opScreen = document.getElementById('opScreen');
        const gameScreen = document.getElementById('gameScreen');
        
        if (opScreen && gameScreen) {
            opScreen.style.display = 'flex';
            gameScreen.classList.add('hidden');
            
            // ゲーム状態をリセット
            this.gameStarted = false;
            this.gameState = null;
            this.isConnected = false;
            this.gameOverSoundPlayed = false;
            
            // WebSocket接続を切断
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            
            // BGMを停止
            this.stopBGM();
        }
    }
    
    showLineClearEffect(linesCleared) {
        // ライン消去エフェクトを表示
        const blockSize = this.gameBoard.width / this.boardWidth;
        
        // 消去されるラインを特定
        const linesToClear = [];
        for (let y = 0; y < this.boardHeight; y++) {
            if (this.gameState.board[y].every(cell => cell !== 0)) {
                linesToClear.push(y);
            }
        }
        
        // エフェクト用のオーバーレイ
        const overlay = document.createElement('canvas');
        overlay.width = this.gameBoard.width;
        overlay.height = this.gameBoard.height;
        overlay.style.position = 'absolute';
        overlay.style.top = this.gameBoard.offsetTop + 'px';
        overlay.style.left = this.gameBoard.offsetLeft + 'px';
        overlay.style.pointerEvents = 'none';
        overlay.style.zIndex = '10';
        
        document.body.appendChild(overlay);
        const overlayCtx = overlay.getContext('2d');
        
        // ライン消去エフェクトの段階
        let stage = 0;
        const totalStages = 6;
        const effectInterval = setInterval(() => {
            overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
            
            switch(stage) {
                case 0: // ラインを白く光らせる
                    linesToClear.forEach(lineY => {
                        overlayCtx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                        overlayCtx.fillRect(0, lineY * blockSize, overlay.width, blockSize);
                    });
                    break;
                    
                case 1: // ラインを黄色く光らせる
                    linesToClear.forEach(lineY => {
                        overlayCtx.fillStyle = 'rgba(255, 255, 0, 0.9)';
                        overlayCtx.fillRect(0, lineY * blockSize, overlay.width, blockSize);
                    });
                    break;
                    
                case 2: // ラインをオレンジに
                    linesToClear.forEach(lineY => {
                        overlayCtx.fillStyle = 'rgba(255, 165, 0, 1.0)';
                        overlayCtx.fillRect(0, lineY * blockSize, overlay.width, blockSize);
                    });
                    break;
                    
                case 3: // ラインを赤く
                    linesToClear.forEach(lineY => {
                        overlayCtx.fillStyle = 'rgba(255, 0, 0, 1.0)';
                        overlayCtx.fillRect(0, lineY * blockSize, overlay.width, blockSize);
                    });
                    break;
                    
                case 4: // 爆発エフェクト（小さな粒子）
                    linesToClear.forEach(lineY => {
                        for (let i = 0; i < 20; i++) {
                            const x = Math.random() * overlay.width;
                            const y = lineY * blockSize + Math.random() * blockSize;
                            const size = Math.random() * 4 + 2;
                            overlayCtx.fillStyle = `rgba(255, ${Math.random() * 255}, 0, 0.8)`;
                            overlayCtx.fillRect(x, y, size, size);
                        }
                    });
                    break;
                    
                case 5: // フェードアウト
                    overlayCtx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                    overlayCtx.fillRect(0, 0, overlay.width, overlay.height);
                    
                    // ライン消去テキスト
                    overlayCtx.fillStyle = 'rgba(255, 0, 0, 0.8)';
                    overlayCtx.font = 'bold 28px Arial';
                    overlayCtx.textAlign = 'center';
                    overlayCtx.fillText(
                        `${linesCleared} LINE${linesCleared > 1 ? 'S' : ''} CLEAR!`, 
                        overlay.width / 2, 
                        overlay.height / 2
                    );
                    break;
            }
            
            stage++;
            if (stage >= totalStages) {
                clearInterval(effectInterval);
                setTimeout(() => {
                    document.body.removeChild(overlay);
                }, 200);
            }
        }, 100);
    }
}

// ゲームの初期化
document.addEventListener('DOMContentLoaded', () => {
    new TetrisWebGame();
}); 