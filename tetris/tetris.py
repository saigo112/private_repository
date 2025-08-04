import pygame
import random
import sys
import os
import math

# Pygameの初期化
pygame.init()

# 定数
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BLOCK_SIZE = 30
BOARD_X = (SCREEN_WIDTH - BOARD_WIDTH * BLOCK_SIZE) // 2
BOARD_Y = 50  # 上に移動

# 爆弾アイテムの設定
BOMB_LINES_REQUIRED = 10  # 10ライン削除で爆弾獲得

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)
BOMB_RED = (255, 50, 50)
EXPLOSION_ORANGE = (255, 100, 0)

# テトリミノの形状定義（修正版）
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

TETROMINO_COLORS = [CYAN, YELLOW, PURPLE, ORANGE, BLUE, GREEN, RED]

class Bomb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 3
        self.active = True
        self.image = None
    
    def load_image(self, image):
        """爆弾画像を設定"""
        self.image = image
    
    def explode(self, board):
        """爆弾が爆発して周辺のブロックを消去"""
        destroyed_blocks = []
        
        # 爆発範囲（3x3の範囲）
        for dy in range(-self.radius, self.radius + 1):
            for dx in range(-self.radius, self.radius + 1):
                new_x = self.x + dx
                new_y = self.y + dy
                
                # ボード内かチェック
                if (0 <= new_x < BOARD_WIDTH and 
                    0 <= new_y < BOARD_HEIGHT and
                    board[new_y][new_x] != 0):
                    board[new_y][new_x] = 0
                    destroyed_blocks.append((new_x, new_y))
        
        self.active = False
        return destroyed_blocks

class Tetromino:
    def __init__(self, x, y, shape_idx):
        self.x = x
        self.y = y
        self.shape = TETROMINOS[shape_idx]
        self.color = TETROMINO_COLORS[shape_idx]
        self.rotation = 0
    
    def rotate(self, shape):
        # 90度回転（修正版）
        rows = len(shape)
        cols = len(shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = shape[r][c]
        
        return rotated
    
    def get_rotated_shape(self):
        shape = self.shape
        for _ in range(self.rotation):
            shape = self.rotate(shape)
        return shape

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("テトリス")
        self.clock = pygame.time.Clock()
        
        # 音声の初期化
        pygame.mixer.init()
        self.load_sounds()
        
        # 背景画像の読み込み
        self.load_background()
        
        # 日本語フォントの設定
        try:
            # macOS用
            if os.path.exists("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"):
                self.font = pygame.font.Font("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 24)
            # Windows用
            elif os.path.exists("C:/Windows/Fonts/msgothic.ttc"):
                self.font = pygame.font.Font("C:/Windows/Fonts/msgothic.ttc", 24)
            # Linux用
            elif os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                self.font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            else:
                self.font = pygame.font.Font(None, 24)
        except:
            self.font = pygame.font.Font(None, 24)
        
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.bombs = []  # 爆弾のリスト
        self.current_piece = None
        self.next_piece = None  # 次のテトリミノ
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.bombs_available = 0  # 使用可能な爆弾数
        
        self.fall_time = 0
        self.fall_speed = 375  # ミリ秒（4分の3の速度）
        self.base_fall_speed = 375  # 基本落下速度
        self.speed_multiplier = 1.0  # 速度倍率
        
        # BGM再生開始
        self.play_bgm()
        
        self.spawn_new_piece()
    
    def load_sounds(self):
        """音声ファイルを読み込み"""
        try:
            self.move_sound = pygame.mixer.Sound("assets/sounds/move.wav")
            self.rotate_sound = pygame.mixer.Sound("assets/sounds/rotate.wav")
            self.drop_sound = pygame.mixer.Sound("assets/sounds/drop.wav")
            self.clear_sound = pygame.mixer.Sound("assets/sounds/clear.wav")
            self.bomb_sound = pygame.mixer.Sound("assets/sounds/bomb.wav")
            self.gameover_sound = pygame.mixer.Sound("assets/sounds/gameover.wav")
            self.bgm_sound = pygame.mixer.Sound("assets/sounds/tetris_bgm_1.mp3")
        except:
            print("音声ファイルの読み込みに失敗しました")
            self.move_sound = None
            self.rotate_sound = None
            self.drop_sound = None
            self.clear_sound = None
            self.bomb_sound = None
            self.gameover_sound = None
            self.bgm_sound = None
    
    def load_background(self):
        """背景画像と爆弾画像を読み込み"""
        try:
            self.background = pygame.image.load("assets/images/mario_background.png")
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("背景画像の読み込みに失敗しました")
            self.background = None
        
        try:
            self.bomb_image = pygame.image.load("assets/images/bomb.png")
        except:
            print("爆弾画像の読み込みに失敗しました")
            self.bomb_image = None
    
    def play_bgm(self):
        """BGMを再生"""
        if self.bgm_sound:
            self.bgm_sound.play(-1)  # -1でループ再生
    
    def stop_bgm(self):
        """BGMを停止"""
        if self.bgm_sound:
            self.bgm_sound.stop()
    
    def check_stack_height(self):
        """積み上がり具合をチェックして速度を調整"""
        # 最上段から何行目までブロックがあるかをチェック
        top_empty_rows = 0
        for r in range(BOARD_HEIGHT):
            if any(self.board[r]):
                break
            top_empty_rows += 1
        
        # 積み上がり具合（空行が少ないほど積み上がっている）
        stack_ratio = 1.0 - (top_empty_rows / BOARD_HEIGHT)
        
        # 半分以上積み上がったら速度を遅くする
        if stack_ratio > 0.5:
            # 積み上がり具合に応じて速度を調整（最大で1.5倍遅く）
            stack_speed_multiplier = 1.0 + (stack_ratio - 0.5) * 1.0
            self.fall_speed = int(self.base_fall_speed * stack_speed_multiplier / self.speed_multiplier)
        else:
            self.fall_speed = int(self.base_fall_speed / self.speed_multiplier)
    
    def change_speed(self, direction):
        """速度を変更"""
        if direction == "up":
            self.speed_multiplier = min(3.0, self.speed_multiplier + 0.25)
        elif direction == "down":
            self.speed_multiplier = max(0.25, self.speed_multiplier - 0.25)
        
        print(f"速度倍率: {self.speed_multiplier}")  # デバッグ用
        
        # 現在の積み上がり状況に応じて速度を再計算
        self.check_stack_height()
    
    def spawn_new_piece(self):
        # 次のピースがなければ生成
        if self.next_piece is None:
            shape_idx = random.randint(0, len(TETROMINOS) - 1)
            self.next_piece = Tetromino(BOARD_WIDTH // 2 - 1, 0, shape_idx)
        
        # 現在のピースを次のピースに設定
        self.current_piece = self.next_piece
        self.current_piece.x = BOARD_WIDTH // 2 - 1
        self.current_piece.y = 0
        
        # 新しい次のピースを生成
        shape_idx = random.randint(0, len(TETROMINOS) - 1)
        self.next_piece = Tetromino(BOARD_WIDTH // 2 - 1, 0, shape_idx)
        
        # ゲームオーバーチェック
        if not self.is_valid_move(self.current_piece.x, self.current_piece.y, self.current_piece.get_rotated_shape()):
            self.game_over = True
            # ゲームオーバー効果音
            if self.gameover_sound:
                self.gameover_sound.play()
            # BGM停止
            self.stop_bgm()
    
    def is_valid_move(self, x, y, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    new_x = x + c
                    new_y = y + r
                    
                    if (new_x < 0 or new_x >= BOARD_WIDTH or 
                        new_y >= BOARD_HEIGHT or 
                        (new_y >= 0 and self.board[new_y][new_x])):
                        return False
        return True
    
    def place_piece(self):
        shape = self.current_piece.get_rotated_shape()
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    board_y = self.current_piece.y + r
                    board_x = self.current_piece.x + c
                    if board_y >= 0:
                        self.board[board_y][board_x] = self.current_piece.color
        
        self.clear_lines()
        self.spawn_new_piece()
    
    def place_bomb(self, x, y):
        """指定位置に爆弾を配置"""
        print(f"爆弾配置試行: x={x}, y={y}, 使用可能爆弾={self.bombs_available}")
        if self.bombs_available > 0 and 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            bomb = Bomb(x, y)
            if self.bomb_image:
                bomb.load_image(self.bomb_image)
            self.bombs.append(bomb)
            self.bombs_available -= 1
            print(f"爆弾配置成功: 残り爆弾={self.bombs_available}")
            return True
        else:
            print(f"爆弾配置失敗: 条件チェック失敗")
        return False
    
    def explode_bombs(self):
        """爆弾を爆発させる"""
        exploded_bombs = []
        for bomb in self.bombs:
            if bomb.active:
                destroyed_blocks = bomb.explode(self.board)
                if destroyed_blocks:
                    exploded_bombs.append(bomb)
                    if self.bomb_sound:
                        self.bomb_sound.play()
        
        # 爆発した爆弾をリストから削除
        self.bombs = [bomb for bomb in self.bombs if bomb not in exploded_bombs]
    
    def clear_lines(self):
        lines_to_clear = []
        for r in range(BOARD_HEIGHT):
            if all(self.board[r]):
                lines_to_clear.append(r)
        
        for line in lines_to_clear:
            del self.board[line]
            self.board.insert(0, [0 for _ in range(BOARD_WIDTH)])
        
        if lines_to_clear:
            # ライン消去前の爆弾獲得判定
            old_lines = self.lines_cleared
            self.lines_cleared += len(lines_to_clear)
            
            # 10ライン削除で爆弾獲得（ライン消去前後で判定）
            old_bomb_threshold = old_lines // BOMB_LINES_REQUIRED
            new_bomb_threshold = self.lines_cleared // BOMB_LINES_REQUIRED
            if new_bomb_threshold > old_bomb_threshold:
                self.bombs_available += (new_bomb_threshold - old_bomb_threshold)
            
            self.score += len(lines_to_clear) * 100 * self.level
            self.level = self.lines_cleared // 10 + 1
            self.base_fall_speed = max(50, 375 - (self.level - 1) * 37)  # 4分の3の速度調整
            
            # ライン消去効果音
            if self.clear_sound:
                self.clear_sound.play()
    
    def move_piece(self, dx, dy):
        if self.current_piece:
            new_x = self.current_piece.x + dx
            new_y = self.current_piece.y + dy
            
            if self.is_valid_move(new_x, new_y, self.current_piece.get_rotated_shape()):
                self.current_piece.x = new_x
                self.current_piece.y = new_y
                # 移動効果音
                if self.move_sound:
                    self.move_sound.play()
                return True
        return False
    
    def rotate_piece(self):
        if self.current_piece:
            # 回転前の状態を保存
            original_rotation = self.current_piece.rotation
            
            # 回転を試行
            self.current_piece.rotation = (self.current_piece.rotation + 1) % 4
            
            # 壁キック（回転後の位置調整）
            if not self.is_valid_move(self.current_piece.x, self.current_piece.y, self.current_piece.get_rotated_shape()):
                # 左右に移動して回転を試行
                for dx in [-1, 1, -2, 2]:
                    if self.is_valid_move(self.current_piece.x + dx, self.current_piece.y, self.current_piece.get_rotated_shape()):
                        self.current_piece.x += dx
                        return
                
                # 上に移動して回転を試行
                if self.is_valid_move(self.current_piece.x, self.current_piece.y - 1, self.current_piece.get_rotated_shape()):
                    self.current_piece.y -= 1
                    return
                
                # 回転を元に戻す
                self.current_piece.rotation = original_rotation
            else:
                # 回転成功時の効果音
                if self.rotate_sound:
                    self.rotate_sound.play()
    
    def hard_drop(self):
        if self.current_piece:
            while self.move_piece(0, 1):
                pass
            # ハードドロップ効果音
            if self.drop_sound:
                self.drop_sound.play()
            self.place_piece()
    
    def draw_board(self):
        # 背景画像の描画
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # ボードの背景
        pygame.draw.rect(self.screen, GRAY, 
                        (BOARD_X - 2, BOARD_Y - 2, 
                         BOARD_WIDTH * BLOCK_SIZE + 4, 
                         BOARD_HEIGHT * BLOCK_SIZE + 4), 2)
        
        # 配置済みブロックの描画
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                if self.board[r][c]:
                    pygame.draw.rect(self.screen, self.board[r][c],
                                   (BOARD_X + c * BLOCK_SIZE, 
                                    BOARD_Y + r * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(self.screen, BLACK,
                                   (BOARD_X + c * BLOCK_SIZE, 
                                    BOARD_Y + r * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # 爆弾の描画
        for bomb in self.bombs:
            if bomb.active:
                if bomb.image:
                    # 爆弾画像を表示
                    self.screen.blit(bomb.image, 
                                   (BOARD_X + bomb.x * BLOCK_SIZE, 
                                    BOARD_Y + bomb.y * BLOCK_SIZE))
                else:
                    # 画像がない場合は円で表示
                    center_x = BOARD_X + bomb.x * BLOCK_SIZE + BLOCK_SIZE // 2
                    center_y = BOARD_Y + bomb.y * BLOCK_SIZE + BLOCK_SIZE // 2
                    pygame.draw.circle(self.screen, BOMB_RED, (center_x, center_y), 8)
                    pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 8, 2)
        
        # 現在のピースの描画
        if self.current_piece:
            shape = self.current_piece.get_rotated_shape()
            for r, row in enumerate(shape):
                for c, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(self.screen, self.current_piece.color,
                                       (BOARD_X + (self.current_piece.x + c) * BLOCK_SIZE,
                                        BOARD_Y + (self.current_piece.y + r) * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(self.screen, BLACK,
                                       (BOARD_X + (self.current_piece.x + c) * BLOCK_SIZE,
                                        BOARD_Y + (self.current_piece.y + r) * BLOCK_SIZE,
                                        BLOCK_SIZE, BLOCK_SIZE), 1)
    
    def draw_next_piece(self):
        """次のテトリミノを描画"""
        if self.next_piece:
            # 次のピース表示エリア
            next_area_x = 20
            next_area_y = 200
            next_area_width = 120
            next_area_height = 80
            
            # 背景
            pygame.draw.rect(self.screen, GRAY, 
                           (next_area_x - 2, next_area_y - 2, 
                            next_area_width + 4, next_area_height + 4), 2)
            
            # 次のピースの形状を取得
            shape = self.next_piece.shape
            shape_width = len(shape[0])
            shape_height = len(shape)
            
            # 中央に配置
            start_x = next_area_x + (next_area_width - shape_width * 20) // 2
            start_y = next_area_y + (next_area_height - shape_height * 20) // 2
            
            # ピースを描画
            for r, row in enumerate(shape):
                for c, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(self.screen, self.next_piece.color,
                                       (start_x + c * 20, start_y + r * 20, 20, 20))
                        pygame.draw.rect(self.screen, BLACK,
                                       (start_x + c * 20, start_y + r * 20, 20, 20), 1)
    
    def draw_ui(self):
        # 左側のスコア表示
        score_text = self.font.render(f"スコア: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # レベル表示
        level_text = self.font.render(f"レベル: {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, 50))
        
        # ライン数表示
        lines_text = self.font.render(f"ライン: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (20, 80))
        
        # 爆弾情報
        bomb_text = self.font.render(f"使用可能爆弾: {self.bombs_available}", True, WHITE)
        self.screen.blit(bomb_text, (20, 120))
        
        # 配置済み爆弾情報
        placed_bomb_text = self.font.render(f"配置済み爆弾: {len(self.bombs)}", True, WHITE)
        self.screen.blit(placed_bomb_text, (20, 150))
        
        # 速度情報
        speed_text = self.font.render(f"速度: {self.speed_multiplier:.2f}x", True, WHITE)
        self.screen.blit(speed_text, (20, 180))
        
        # 右側の情報表示
        right_x = SCREEN_WIDTH - 250
        # ゲーム情報
        info_text = self.font.render("テトリス", True, WHITE)
        self.screen.blit(info_text, (right_x, 20))
        
        # 操作説明
        controls_text = self.font.render("←→: 移動  ↑: 回転  ↓: 落下  Space: ハードドロップ", True, WHITE)
        self.screen.blit(controls_text, (20, SCREEN_HEIGHT - 90))
        
        # 爆弾配置説明
        bomb_controls_text = self.font.render("B: 爆弾配置  Click: マウスで爆弾配置", True, WHITE)
        self.screen.blit(bomb_controls_text, (20, SCREEN_HEIGHT - 60))
        
        # 速度調節説明
        speed_controls_text = self.font.render("+/-: 速度調節", True, WHITE)
        self.screen.blit(speed_controls_text, (20, SCREEN_HEIGHT - 30))
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("ゲームオーバー", True, WHITE)
        restart_text = self.font.render("Rキーでリスタート", True, WHITE)
        quit_text = self.font.render("Qキーで終了", True, WHITE)
        
        self.screen.blit(game_over_text, 
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                         SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(restart_text, 
                        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                         SCREEN_HEIGHT // 2))
        self.screen.blit(quit_text, 
                        (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 
                         SCREEN_HEIGHT // 2 + 40))
    
    def reset_game(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.bombs = []  # 爆弾リストもリセット
        self.current_piece = None
        self.next_piece = None  # 次のピースもリセット
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.bombs_available = 0  # 使用可能な爆弾数もリセット
        self.fall_time = 0
        self.fall_speed = 375  # 4分の3の速度
        self.base_fall_speed = 375  # 基本落下速度もリセット
        self.speed_multiplier = 1.0  # 速度倍率もリセット
        # BGM再開
        self.play_bgm()
        self.spawn_new_piece()
    
    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # マウスクリックで爆弾配置
                    if event.button == 1:  # 左クリック
                        mouse_x, mouse_y = event.pos
                        # ボード座標に変換
                        board_x = (mouse_x - BOARD_X) // BLOCK_SIZE
                        board_y = (mouse_y - BOARD_Y) // BLOCK_SIZE
                        
                        if (0 <= board_x < BOARD_WIDTH and 0 <= board_y < BOARD_HEIGHT and 
                            self.bombs_available > 0):
                            success = self.place_bomb(board_x, board_y)
                            if success:
                                print(f"マウスクリックで爆弾を配置しました。残り: {self.bombs_available}")
                            else:
                                print("爆弾の配置に失敗しました")
                        elif self.bombs_available <= 0:
                            print("使用可能な爆弾がありません")
                
                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
                        elif event.key == pygame.K_q:
                            running = False
                    else:
                        if event.key == pygame.K_LEFT:
                            self.move_piece(-1, 0)
                        elif event.key == pygame.K_RIGHT:
                            self.move_piece(1, 0)
                        elif event.key == pygame.K_DOWN:
                            self.move_piece(0, 1)
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()
                        elif event.key == pygame.K_b:
                            # 爆弾配置（現在のピースの位置に）
                            if self.current_piece and self.bombs_available > 0:
                                success = self.place_bomb(self.current_piece.x, self.current_piece.y)
                                if success:
                                    print(f"爆弾を配置しました。残り: {self.bombs_available}")
                                else:
                                    print("爆弾の配置に失敗しました")
                            else:
                                print("使用可能な爆弾がありません")
                        elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                            # 速度アップ
                            self.change_speed("up")
                        elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                            # 速度ダウン
                            self.change_speed("down")
            
            if not self.game_over:
                # 自動落下
                if current_time - self.fall_time > self.fall_speed:
                    if not self.move_piece(0, 1):
                        self.place_piece()
                    self.fall_time = current_time
                
                # 積み上がりチェック
                self.check_stack_height()
                
                # 爆弾爆発の処理
                self.explode_bombs()
            
            # 描画
            self.draw_board()
            self.draw_next_piece()  # 次のピースを描画
            self.draw_ui()
            
            if self.game_over:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self.stop_bgm()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run() 