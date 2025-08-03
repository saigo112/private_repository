import pygame
import random
import sys

# Pygameの初期化
pygame.init()

# 定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BLOCK_SIZE = 30
BOARD_X = (SCREEN_WIDTH - BOARD_WIDTH * BLOCK_SIZE) // 2
BOARD_Y = 50

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

# テトリミノの形状定義
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

TETROMINO_COLORS = [CYAN, YELLOW, PURPLE, ORANGE, BLUE, GREEN, RED]

class Tetromino:
    def __init__(self, x, y, shape_idx):
        self.x = x
        self.y = y
        self.shape = TETROMINOS[shape_idx]
        self.color = TETROMINO_COLORS[shape_idx]
        self.rotation = 0
    
    def rotate(self):
        # 90度回転
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = self.shape[r][c]
        
        return rotated
    
    def get_rotated_shape(self):
        shape = self.shape
        for _ in range(self.rotation):
            shape = self.rotate()
        return shape

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("テトリス")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        
        self.fall_time = 0
        self.fall_speed = 500  # ミリ秒
        
        self.spawn_new_piece()
    
    def spawn_new_piece(self):
        shape_idx = random.randint(0, len(TETROMINOS) - 1)
        self.current_piece = Tetromino(BOARD_WIDTH // 2 - 1, 0, shape_idx)
        
        # ゲームオーバーチェック
        if not self.is_valid_move(self.current_piece.x, self.current_piece.y, self.current_piece.get_rotated_shape()):
            self.game_over = True
    
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
    
    def clear_lines(self):
        lines_to_clear = []
        for r in range(BOARD_HEIGHT):
            if all(self.board[r]):
                lines_to_clear.append(r)
        
        for line in lines_to_clear:
            del self.board[line]
            self.board.insert(0, [0 for _ in range(BOARD_WIDTH)])
        
        if lines_to_clear:
            self.lines_cleared += len(lines_to_clear)
            self.score += len(lines_to_clear) * 100 * self.level
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(50, 500 - (self.level - 1) * 50)
    
    def move_piece(self, dx, dy):
        if self.current_piece:
            new_x = self.current_piece.x + dx
            new_y = self.current_piece.y + dy
            
            if self.is_valid_move(new_x, new_y, self.current_piece.get_rotated_shape()):
                self.current_piece.x = new_x
                self.current_piece.y = new_y
                return True
        return False
    
    def rotate_piece(self):
        if self.current_piece:
            self.current_piece.rotation = (self.current_piece.rotation + 1) % 4
            if not self.is_valid_move(self.current_piece.x, self.current_piece.y, self.current_piece.get_rotated_shape()):
                self.current_piece.rotation = (self.current_piece.rotation - 1) % 4
    
    def hard_drop(self):
        if self.current_piece:
            while self.move_piece(0, 1):
                pass
            self.place_piece()
    
    def draw_board(self):
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
    
    def draw_ui(self):
        # スコア表示
        score_text = self.font.render(f"スコア: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # レベル表示
        level_text = self.font.render(f"レベル: {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, 60))
        
        # ライン数表示
        lines_text = self.font.render(f"ライン: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (20, 100))
        
        # 操作説明
        controls_text = self.font.render("←→: 移動  ↑: 回転  ↓: 落下  Space: ハードドロップ", True, WHITE)
        self.screen.blit(controls_text, (20, SCREEN_HEIGHT - 40))
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("ゲームオーバー", True, WHITE)
        restart_text = self.font.render("Rキーでリスタート", True, WHITE)
        
        self.screen.blit(game_over_text, 
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                         SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(restart_text, 
                        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                         SCREEN_HEIGHT // 2 + 50))
    
    def reset_game(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_time = 0
        self.fall_speed = 500
        self.spawn_new_piece()
    
    def run(self):
        while True:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
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
            
            if not self.game_over:
                # 自動落下
                if current_time - self.fall_time > self.fall_speed:
                    if not self.move_piece(0, 1):
                        self.place_piece()
                    self.fall_time = current_time
            
            # 描画
            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_ui()
            
            if self.game_over:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = TetrisGame()
    game.run() 