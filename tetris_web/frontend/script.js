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
        
        this.setupEventListeners();
        this.connectWebSocket();
        this.startGame();
    }
    
    setupEventListeners() {
        // キーボードイベント
        document.addEventListener('keydown', (e) => {
            if (!this.isConnected) return;
            
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
                    this.sendAction('place_bomb');
                    break;
            }
        });
        
        // モバイルコントロールボタン
        document.getElementById('leftBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('left');
        });
        
        document.getElementById('rightBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('right');
        });
        
        document.getElementById('downBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('down');
        });
        
        document.getElementById('rotateBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('rotate');
        });
        
        document.getElementById('hardDropBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('hard_drop');
        });
        
        document.getElementById('bombBtn').addEventListener('click', () => {
            if (this.isConnected) this.sendAction('place_bomb');
        });
        
        // リスタートボタン
        document.getElementById('restartBtn').addEventListener('click', () => {
            this.startGame();
        });
        
        // ゲームボードのクリックイベント（爆弾配置用）
        this.gameBoard.addEventListener('click', (e) => {
            if (!this.isConnected) return;
            
            const rect = this.gameBoard.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.blockSize);
            const y = Math.floor((e.clientY - rect.top) / this.blockSize);
            
            if (x >= 0 && x < this.boardWidth && y >= 0 && y < this.boardHeight) {
                this.sendAction('place_bomb', x, y);
            }
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus('接続済み', 'green');
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
            this.updateConnectionStatus('接続が切れました', 'red');
            // 再接続を試行
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocketエラー:', error);
            this.updateConnectionStatus('接続エラー', 'red');
        };
    }
    
    updateConnectionStatus(message, color) {
        const statusElement = document.getElementById('connectionStatus');
        statusElement.textContent = message;
        statusElement.style.color = color;
    }
    
    sendAction(action, x = null, y = null) {
        if (!this.isConnected) return;
        
        const message = { action };
        if (x !== null && y !== null) {
            message.x = x;
            message.y = y;
        }
        
        this.websocket.send(JSON.stringify(message));
    }
    
    async startGame() {
        try {
            const response = await fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateGameState(data.game_state);
            }
        } catch (error) {
            console.error('ゲーム開始エラー:', error);
        }
    }
    
    updateGameState(gameState) {
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
                    this.drawBlock(piece.x + x, piece.y + y, piece.color);
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
        const radius = 8;
        
        // 爆弾の本体
        this.ctx.fillStyle = '#ff4444';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // 爆弾のボーダー
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // 爆弾の導火線
        this.ctx.strokeStyle = '#ffaa00';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - radius);
        this.ctx.lineTo(centerX, centerY - radius - 5);
        this.ctx.stroke();
    }
    
    updateUI() {
        if (!this.gameState) return;
        
        // スコア情報を更新
        document.getElementById('score').textContent = this.gameState.score;
        document.getElementById('level').textContent = this.gameState.level;
        document.getElementById('lines').textContent = this.gameState.lines_cleared;
        document.getElementById('bombs').textContent = this.gameState.bombs_available;
        
        // ゲームオーバー状態を更新
        const gameOverElement = document.getElementById('gameOver');
        if (this.gameState.game_over) {
            gameOverElement.classList.remove('hidden');
        } else {
            gameOverElement.classList.add('hidden');
        }
    }
}

// ゲームの初期化
document.addEventListener('DOMContentLoaded', () => {
    new TetrisWebGame();
}); 