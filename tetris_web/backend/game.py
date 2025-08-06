import random
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# 定数
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BOMB_LINES_REQUIRED = 10  # 10ライン削除で爆弾獲得

# 色の定義（RGB値）
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

# テトリミノの形状定義
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

class ActionType(Enum):
    LEFT = "left"
    RIGHT = "right"
    DOWN = "down"
    ROTATE = "rotate"
    HARD_DROP = "hard_drop"
    PLACE_BOMB = "place_bomb"
    SPAWN_BOMB = "spawn_bomb"
    PAUSE = "pause"
    SPEED_UP = "speed_up"
    SPEED_DOWN = "speed_down"

@dataclass
class Bomb:
    x: int
    y: int
    radius: int = 3
    active: bool = True

    def explode(self, board: List[List[int]]) -> List[Tuple[int, int]]:
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

@dataclass
class Tetromino:
    x: int
    y: int
    shape_idx: int
    rotation: int = 0

    @property
    def shape(self) -> List[List[int]]:
        if self.shape_idx == -1:  # 爆弾ピース
            return [[1]]  # 1x1の爆弾
        return TETROMINOS[self.shape_idx]

    @property
    def color(self) -> Tuple[int, int, int]:
        if self.shape_idx == -1:  # 爆弾ピース
            return BOMB_RED
        return TETROMINO_COLORS[self.shape_idx]
    
    @property
    def is_bomb(self) -> bool:
        return self.shape_idx == -1

    def rotate(self, shape: List[List[int]]) -> List[List[int]]:
        """90度回転"""
        rows = len(shape)
        cols = len(shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = shape[r][c]
        
        return rotated

    def get_rotated_shape(self) -> List[List[int]]:
        shape = self.shape
        for _ in range(self.rotation):
            shape = self.rotate(shape)
        return shape

class TetrisGame:
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.bombs: List[Bomb] = []
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.bombs_available = 0
        
        self.fall_time = 0
        self.fall_speed = 300  # ミリ秒
        self.base_fall_speed = 300
        self.speed_multiplier = 1.0
        self.paused = False
        self.lines_cleared_this_frame = 0  # ライン消去エフェクト用
        
        # 接地時の移動・回転可能時間
        self.lock_delay = 200  # 0.2秒
        self.lock_time = 0
        self.is_locked = False
        
        # ライン消去エフェクトの遅延
        self.line_clear_delay = 250  # 0.25秒
        self.line_clear_time = 0
        self.pending_line_clear = False
        self.pending_lines = 0
        
        self.spawn_new_piece()

    def spawn_new_piece(self):
        """新しいテトリミノを生成"""
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

    def is_valid_move(self, x: int, y: int, shape: List[List[int]]) -> bool:
        """移動が有効かチェック"""
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
        """現在のピースをボードに配置"""
        if not self.current_piece:
            return
        
        # 爆弾ピースの場合、配置と同時に爆発
        if self.current_piece.is_bomb:
            shape = self.current_piece.get_rotated_shape()
            for r, row in enumerate(shape):
                for c, cell in enumerate(row):
                    if cell:
                        board_y = self.current_piece.y + r
                        board_x = self.current_piece.x + c
                        if board_y >= 0:
                            # 爆弾を配置して即座に爆発
                            bomb = Bomb(board_x, board_y)
                            bomb.explode(self.board)
        else:
            # 通常のピース
            shape = self.current_piece.get_rotated_shape()
            for r, row in enumerate(shape):
                for c, cell in enumerate(row):
                    if cell:
                        board_y = self.current_piece.y + r
                        board_x = self.current_piece.x + c
                        if board_y >= 0:
                            self.board[board_y][board_x] = self.current_piece.color
        
        # ライン消去を遅延実行
        lines_cleared = self.clear_lines()
        if lines_cleared > 0:
            self.pending_line_clear = True
            self.pending_lines = lines_cleared
            self.line_clear_time = 0
        else:
            self.spawn_new_piece()
        
        # ライン消去エフェクト用のフラグ
        if lines_cleared > 0:
            self.lines_cleared_this_frame = lines_cleared

    def place_bomb(self, x: int, y: int) -> bool:
        """指定位置に爆弾を配置"""
        if self.bombs_available > 0 and 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            bomb = Bomb(x, y)
            self.bombs.append(bomb)
            self.bombs_available -= 1
            return True
        return False
    
    def spawn_bomb_piece(self) -> bool:
        """爆弾ピースを生成（次のピースを爆弾に変更）"""
        if self.bombs_available > 0:
            # 次のピースを爆弾ピースに変更
            self.next_piece = Tetromino(BOARD_WIDTH // 2 - 1, 0, -1)  # -1は爆弾ピースを示す
            self.bombs_available -= 1
            return True
        return False

    def explode_bombs(self):
        """爆弾を爆発させる"""
        exploded_bombs = []
        for bomb in self.bombs:
            if bomb.active:
                destroyed_blocks = bomb.explode(self.board)
                if destroyed_blocks:
                    exploded_bombs.append(bomb)
        
        # 爆発した爆弾をリストから削除
        self.bombs = [bomb for bomb in self.bombs if bomb not in exploded_bombs]

    def clear_lines(self):
        """ライン消去処理"""
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
            
            # 10ライン削除で爆弾獲得
            old_bomb_threshold = old_lines // BOMB_LINES_REQUIRED
            new_bomb_threshold = self.lines_cleared // BOMB_LINES_REQUIRED
            if new_bomb_threshold > old_bomb_threshold:
                self.bombs_available += (new_bomb_threshold - old_bomb_threshold)
            
            self.score += len(lines_to_clear) * 100 * self.level
            self.level = self.lines_cleared // 10 + 1
            self.base_fall_speed = max(50, 375 - (self.level - 1) * 37)
            
            # 消去されたライン数を返す
            return len(lines_to_clear)
        return 0

    def move_piece(self, dx: int, dy: int) -> bool:
        """ピースを移動"""
        if not self.current_piece or self.pending_line_clear:
            return False
        
        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        
        if self.is_valid_move(new_x, new_y, self.current_piece.get_rotated_shape()):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            return True
        return False

    def rotate_piece(self) -> bool:
        """ピースを回転"""
        if not self.current_piece or self.pending_line_clear:
            return False
            
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
                    return True
            
            # 上に移動して回転を試行
            if self.is_valid_move(self.current_piece.x, self.current_piece.y - 1, self.current_piece.get_rotated_shape()):
                self.current_piece.y -= 1
                return True
            
            # 回転を元に戻す
            self.current_piece.rotation = original_rotation
            return False
        return True

    def hard_drop(self):
        """ハードドロップ"""
        if not self.current_piece:
            return
            
        while self.move_piece(0, 1):
            pass
        self.place_piece()

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
        
        # 速度が極端に遅くならないように制限
        self.fall_speed = max(50, self.fall_speed)

    def change_speed(self, direction: str):
        """速度を変更"""
        if direction == "up":
            self.speed_multiplier = min(3.0, self.speed_multiplier + 0.25)
        elif direction == "down":
            self.speed_multiplier = max(0.25, self.speed_multiplier - 0.25)
        
        # 現在の積み上がり状況に応じて速度を再計算
        self.check_stack_height()

    def update(self, current_time: int):
        """ゲーム状態を更新"""
        if self.game_over or self.paused:
            return

        # ライン消去の遅延処理
        if self.pending_line_clear:
            self.line_clear_time += 16  # 約60FPS
            if self.line_clear_time >= self.line_clear_delay:
                self.pending_line_clear = False
                self.lines_cleared_this_frame = self.pending_lines
                # ライン消去後に新しいピースを生成
                self.spawn_new_piece()
                # ゲームオーバーチェック
                if self.game_over:
                    return
                return

        # 自動落下
        if current_time - self.fall_time > self.fall_speed:
            if not self.move_piece(0, 1):
                # ピースが接地した場合
                if not self.is_locked:
                    self.is_locked = True
                    self.lock_time = current_time
                else:
                    # ロック時間が経過したら配置
                    if current_time - self.lock_time >= self.lock_delay:
                        self.place_piece()
                        self.is_locked = False
            else:
                # 移動できた場合はロック状態をリセット
                self.is_locked = False
            self.fall_time = current_time
        
        # 積み上がりチェック
        self.check_stack_height()
        
        # 爆弾爆発の処理
        self.explode_bombs()
        
        # ライン消去エフェクトフラグをリセット（遅延処理中はリセットしない）
        if not self.pending_line_clear:
            self.lines_cleared_this_frame = 0

    def perform_action(self, action: ActionType, **kwargs) -> bool:
        """アクションを実行"""
        if self.game_over:
            return False

        if action == ActionType.LEFT:
            return self.move_piece(-1, 0)
        elif action == ActionType.RIGHT:
            return self.move_piece(1, 0)
        elif action == ActionType.DOWN:
            # ↓ボタンで高速落下（複数マス落下）
            moved = False
            for _ in range(3):  # 最大3マス落下
                if self.move_piece(0, 1):
                    moved = True
                else:
                    # 接地した場合、ロック遅延を短縮
                    if self.is_locked:
                        self.lock_delay = 50  # 即座に配置
                    break
            return moved
        elif action == ActionType.ROTATE:
            return self.rotate_piece()
        elif action == ActionType.HARD_DROP:
            self.hard_drop()
            return True
        elif action == ActionType.PLACE_BOMB:
            x = kwargs.get('x', 0)
            y = kwargs.get('y', 0)
            return self.place_bomb(x, y)
        elif action == ActionType.SPAWN_BOMB:
            return self.spawn_bomb_piece()
        elif action == ActionType.PAUSE:
            self.paused = not self.paused
            return True
        elif action == ActionType.SPEED_UP:
            self.change_speed("up")
            return True
        elif action == ActionType.SPEED_DOWN:
            self.change_speed("down")
            return True
        
        return False

    def reset_game(self):
        """ゲームをリセット"""
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.bombs = []
        self.current_piece = None
        self.next_piece = None
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.bombs_available = 0
        self.fall_time = 0
        self.fall_speed = 375
        self.base_fall_speed = 375
        self.speed_multiplier = 1.0
        self.paused = False
        self.lines_cleared_this_frame = 0
        
        # リセット時に新しい変数も初期化
        self.lock_delay = 200
        self.lock_time = 0
        self.is_locked = False
        self.line_clear_delay = 250
        self.line_clear_time = 0
        self.pending_line_clear = False
        self.pending_lines = 0
        
        self.spawn_new_piece()

    def get_game_state(self) -> Dict[str, Any]:
        """ゲーム状態を取得"""
        return {
            "board": self.board,
            "current_piece": {
                "x": self.current_piece.x,
                "y": self.current_piece.y,
                "shape": self.current_piece.get_rotated_shape(),
                "color": self.current_piece.color,
                "is_bomb": self.current_piece.is_bomb
            } if self.current_piece else None,
            "next_piece": {
                "shape": self.next_piece.shape,
                "color": self.next_piece.color,
                "is_bomb": self.next_piece.is_bomb
            } if self.next_piece else None,
            "bombs": [{"x": bomb.x, "y": bomb.y, "active": bomb.active} for bomb in self.bombs],
            "game_over": self.game_over,
            "paused": self.paused,
            "score": self.score,
            "level": self.level,
            "lines_cleared": self.lines_cleared,
            "bombs_available": self.bombs_available,
            "speed_multiplier": self.speed_multiplier,
            "lines_cleared_this_frame": self.lines_cleared_this_frame
        } 