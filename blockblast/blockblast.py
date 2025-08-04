import pygame
import random
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

# Pygame初期化
pygame.init()
pygame.mixer.init()

# ゲーム定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BOARD_SIZE = 8
CELL_SIZE = 50
BOARD_OFFSET_X = 250
BOARD_OFFSET_Y = 50
BLOCK_PREVIEW_SIZE = 35
BLOCK_PREVIEW_OFFSET_Y = 450

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# ブロックの色リスト
BLOCK_COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, CYAN]

class SparkleEffect:
    """キラキラエフェクトクラス"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = []
        self.lifetime = 60  # フレーム数
        self.current_frame = 0
        
        # パーティクルを生成
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'x': x,
                'y': y,
                'color': random.choice([(255, 255, 0), (255, 255, 255), (255, 215, 0), (255, 255, 224)]),
                'size': random.randint(2, 4)
            })
    
    def update(self):
        """エフェクトを更新"""
        self.current_frame += 1
        
        for particle in self.particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['dy'] += 0.1  # 重力効果
        
        return self.current_frame < self.lifetime
    
    def draw(self, screen):
        """エフェクトを描画"""
        alpha = max(0, 255 - (self.current_frame * 255 // self.lifetime))
        
        for particle in self.particles:
            # パーティクルの透明度を調整
            particle_alpha = max(0, alpha - random.randint(0, 50))
            if particle_alpha > 0:
                # キラキラ効果を描画
                pygame.draw.circle(screen, particle['color'], 
                                 (int(particle['x']), int(particle['y'])), particle['size'])
                
                # 十字のキラキラ効果
                size = particle['size']
                x, y = int(particle['x']), int(particle['y'])
                pygame.draw.line(screen, particle['color'], (x-size, y), (x+size, y), 1)
                pygame.draw.line(screen, particle['color'], (x, y-size), (x, y+size), 1)

class AssetGenerator:
    """ゲーム素材（画像・音声）を生成するクラス"""
    
    def __init__(self):
        self.assets_dir = "assets"
        self.images_dir = os.path.join(self.assets_dir, "images")
        self.sounds_dir = os.path.join(self.assets_dir, "sounds")
        self.create_directories()
    
    def create_directories(self):
        """必要なディレクトリを作成"""
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.sounds_dir, exist_ok=True)
    
    def generate_block_image(self, color, size=CELL_SIZE):
        """ブロック画像を生成"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # メインの色で塗りつぶし
        draw.rectangle([0, 0, size-1, size-1], fill=color)
        
        # ハイライト効果
        highlight_color = tuple(min(255, c + 50) for c in color)
        draw.rectangle([2, 2, size//3, size//3], fill=highlight_color)
        
        # 影効果
        shadow_color = tuple(max(0, c - 50) for c in color)
        draw.rectangle([size-6, size-6, size-2, size-2], fill=shadow_color)
        
        # 境界線
        draw.rectangle([0, 0, size-1, size-1], outline=BLACK, width=1)
        
        return img
    
    def generate_board_background(self):
        """盤面背景画像を生成"""
        board_width = BOARD_SIZE * CELL_SIZE
        board_height = BOARD_SIZE * CELL_SIZE
        
        img = Image.new('RGBA', (board_width, board_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # レトロゲーム風の背景色（マリオ風）
        draw.rectangle([0, 0, board_width-1, board_height-1], fill=(135, 206, 235))  # 空色
        
        # グリッド線（より太く、レトロ風）
        for i in range(BOARD_SIZE + 1):
            x = i * CELL_SIZE
            draw.line([(x, 0), (x, board_height)], fill=(100, 100, 100), width=3)
            draw.line([(0, x), (board_width, x)], fill=(100, 100, 100), width=3)
        
        # 盤面の外枠を強調
        draw.rectangle([0, 0, board_width-1, board_height-1], outline=(50, 50, 50), width=5)
        
        return img
    
    def generate_score_panel(self):
        """スコア表示用パネル画像を生成"""
        width, height = 150, 100
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # パネル背景
        draw.rectangle([0, 0, width-1, height-1], fill=(50, 50, 50, 200))
        draw.rectangle([0, 0, width-1, height-1], outline=WHITE, width=2)
        
        return img
    
    def generate_sound(self, frequency, duration, volume=0.3):
        """簡単な効果音を生成"""
        sample_rate = 44100
        samples = int(duration * sample_rate)
        
        # サイン波を生成
        wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration, samples))
        
        # フェードアウト効果
        fade_samples = int(0.1 * sample_rate)
        if fade_samples < samples:
            wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # 音量調整
        wave = (wave * volume * 32767).astype(np.int16)
        
        return wave
    
    def save_sound(self, wave, filename):
        """音声ファイルを保存"""
        import wave as wave_module
        
        filepath = os.path.join(self.sounds_dir, filename)
        with wave_module.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(wave.tobytes())
        
        return filepath
    
    def generate_all_assets(self):
        """すべての素材を生成"""
        assets = {}
        
        # ブロック画像を生成
        for i, color in enumerate(BLOCK_COLORS):
            img = self.generate_block_image(color)
            filename = f"block_{i}.png"
            filepath = os.path.join(self.images_dir, filename)
            img.save(filepath)
            assets[f"block_{i}"] = pygame.image.load(filepath)
        
        # 盤面背景を生成
        board_img = self.generate_board_background()
        board_filepath = os.path.join(self.images_dir, "board_background.png")
        board_img.save(board_filepath)
        assets["board_background"] = pygame.image.load(board_filepath)
        
        # スコアパネルを生成
        panel_img = self.generate_score_panel()
        panel_filepath = os.path.join(self.images_dir, "score_panel.png")
        panel_img.save(panel_filepath)
        assets["score_panel"] = pygame.image.load(panel_filepath)
        
        # 効果音を生成
        # ブロック配置音
        place_sound = self.generate_sound(800, 0.1)
        place_filepath = self.save_sound(place_sound, "place.wav")
        assets["place_sound"] = pygame.mixer.Sound(place_filepath)
        
        # ライン消去音
        clear_sound = self.generate_sound(1200, 0.2)
        clear_filepath = self.save_sound(clear_sound, "clear.wav")
        assets["clear_sound"] = pygame.mixer.Sound(clear_filepath)
        
        # ゲームオーバー音
        gameover_sound = self.generate_sound(400, 0.5)
        gameover_filepath = self.save_sound(gameover_sound, "gameover.wav")
        assets["gameover_sound"] = pygame.mixer.Sound(gameover_filepath)
        
        return assets

class Block:
    """ブロッククラス - ブロックの形状と色を管理"""
    
    def __init__(self, shape, color):
        self.shape = shape  # 2次元配列でブロックの形状を表現
        self.color = color
        self.width = len(shape[0])
        self.height = len(shape)
    
    def draw(self, screen, x, y, cell_size, assets):
        """ブロックを描画"""
        for row in range(self.height):
            for col in range(self.width):
                if self.shape[row][col]:
                    block_x = x + col * cell_size
                    block_y = y + row * cell_size
                    
                    # 色に対応するブロック画像を使用
                    color_index = BLOCK_COLORS.index(self.color)
                    block_img = assets[f"block_{color_index}"]
                    screen.blit(block_img, (block_x, block_y))

class BlockGenerator:
    """ブロック生成クラス - ランダムなブロックを生成"""
    
    def __init__(self):
        self.block_shapes = [
            # 1x1 ブロック
            [[1]],
            
            # 2x1 ブロック
            [[1, 1]],
            
            # 1x2 ブロック
            [[1], [1]],
            
            # 2x2 ブロック
            [[1, 1],
             [1, 1]],
            
            # L字ブロック
            [[1, 0],
             [1, 1]],
            
            # T字ブロック
            [[1, 1, 1],
             [0, 1, 0]],
            
            # 3x1 ブロック
            [[1, 1, 1]],
            
            # 1x3 ブロック
            [[1], [1], [1]],
        ]
    
    def generate_block(self):
        """ランダムなブロックを生成"""
        shape = random.choice(self.block_shapes)
        color = random.choice(BLOCK_COLORS)
        return Block(shape, color)
    
    def generate_next_blocks(self, count=3):
        """次のブロックセットを生成"""
        return [self.generate_block() for _ in range(count)]

class Board:
    """盤面クラス - ゲーム盤の管理"""
    
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.score = 0
    
    def is_valid_placement(self, block, x, y):
        """ブロックの配置が有効かチェック"""
        # ブロックが盤面内に完全に収まるかチェック
        if (x < 0 or y < 0 or 
            x + block.width > BOARD_SIZE or 
            y + block.height > BOARD_SIZE):
            return False
        
        for row in range(block.height):
            for col in range(block.width):
                if block.shape[row][col]:
                    board_x = x + col
                    board_y = y + row
                    
                    # 既存ブロックとの重複チェック
                    if self.grid[board_y][board_x] is not None:
                        return False
        
        return True
    
    def place_block(self, block, x, y):
        """ブロックを盤面に配置"""
        if not self.is_valid_placement(block, x, y):
            return False
        
        for row in range(block.height):
            for col in range(block.width):
                if block.shape[row][col]:
                    board_x = x + col
                    board_y = y + row
                    self.grid[board_y][board_x] = block.color
        
        return True
    
    def clear_lines(self):
        """完成したラインを消去してスコアを加算"""
        lines_cleared = 0
        
        # 行のチェック
        for row in range(BOARD_SIZE):
            if all(cell is not None for cell in self.grid[row]):
                # 行を消去
                self.grid[row] = [None] * BOARD_SIZE
                lines_cleared += 1
        
        # 列のチェック
        for col in range(BOARD_SIZE):
            if all(self.grid[row][col] is not None for row in range(BOARD_SIZE)):
                # 列を消去
                for row in range(BOARD_SIZE):
                    self.grid[row][col] = None
                lines_cleared += 1
        
        # スコア加算
        if lines_cleared > 0:
            self.score += lines_cleared * 100
        
        return lines_cleared
    
    def is_game_over(self, available_blocks):
        """ゲームオーバー判定"""
        for block in available_blocks:
            for y in range(BOARD_SIZE):
                for x in range(BOARD_SIZE):
                    if self.is_valid_placement(block, x, y):
                        return False
        return True
    
    def draw(self, screen, assets):
        """盤面を描画"""
        # 背景を描画
        screen.blit(assets["board_background"], (BOARD_OFFSET_X, BOARD_OFFSET_Y))
        
        # 盤面の外枠を追加で描画（より目立つように）
        pygame.draw.rect(screen, (50, 50, 50), 
                        (BOARD_OFFSET_X - 3, BOARD_OFFSET_Y - 3, 
                         BOARD_SIZE * CELL_SIZE + 6, BOARD_SIZE * CELL_SIZE + 6), 6)
        
        # 配置済みブロックを描画
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.grid[row][col] is not None:
                    x = BOARD_OFFSET_X + col * CELL_SIZE
                    y = BOARD_OFFSET_Y + row * CELL_SIZE
                    
                    color_index = BLOCK_COLORS.index(self.grid[row][col])
                    block_img = assets[f"block_{color_index}"]
                    screen.blit(block_img, (x, y))

class Score:
    """スコア管理クラス"""
    
    def __init__(self):
        self.score = 0
        self.high_score = self.load_high_score()
        self.font = self.get_japanese_font(36)
        self.small_font = self.get_japanese_font(24)
    
    def get_japanese_font(self, size):
        """日本語フォントを取得"""
        # システムフォントを試す
        system_fonts = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",  # macOS
            "C:/Windows/Fonts/msgothic.ttc",  # Windows
            "C:/Windows/Fonts/msmincho.ttc",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
        ]
        
        for font_path in system_fonts:
            try:
                return pygame.font.Font(font_path, size)
            except:
                continue
        
        # デフォルトフォントを使用
        return pygame.font.Font(None, size)
    
    def load_high_score(self):
        """ハイスコアを読み込み"""
        try:
            with open("high_score.txt", "r") as f:
                return int(f.read().strip())
        except:
            return 0
    
    def save_high_score(self):
        """ハイスコアを保存"""
        try:
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            pass
    
    def add_score(self, points):
        """スコアを加算"""
        self.score += points
        # ハイスコア更新チェック
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
    
    def reset_score(self):
        """スコアをリセット"""
        self.score = 0
    
    def draw(self, screen, assets):
        """スコアを描画"""
        # スコアパネルを描画
        screen.blit(assets["score_panel"], (20, 20))
        
        # スコアテキスト
        score_text = self.font.render(f"スコア: {self.score}", True, WHITE)
        screen.blit(score_text, (30, 40))
        
        # ハイスコアテキスト
        high_score_text = self.small_font.render(f"ハイスコア: {self.high_score}", True, WHITE)
        screen.blit(high_score_text, (30, 70))

class Game:
    """メインゲームクラス"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ブロックブラスト")
        self.clock = pygame.time.Clock()
        
        # 素材を生成
        self.asset_generator = AssetGenerator()
        self.assets = self.asset_generator.generate_all_assets()
        
        # ゲームオブジェクトを初期化
        self.board = Board()
        self.block_generator = BlockGenerator()
        self.score = Score()
        
        # ゲーム状態
        self.next_blocks = self.block_generator.generate_next_blocks()
        self.selected_block = None
        self.dragging = False
        self.drag_pos = (0, 0)
        self.game_over = False
        
        # エフェクト管理
        self.sparkle_effects = []
        
        # BGM再生
        pygame.mixer.music.load("assets/sounds/ブロックブラスト用.wav")
        pygame.mixer.music.play(-1)
    
    def get_japanese_font(self, size):
        """日本語フォントを取得"""
        # システムフォントを試す
        system_fonts = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",  # macOS
            "C:/Windows/Fonts/msgothic.ttc",  # Windows
            "C:/Windows/Fonts/msmincho.ttc",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
        ]
        
        for font_path in system_fonts:
            try:
                return pygame.font.Font(font_path, size)
            except:
                continue
        
        # デフォルトフォントを使用
        return pygame.font.Font(None, size)
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart_game()
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    self.handle_mouse_down(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左クリック
                    self.handle_mouse_up(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.drag_pos = event.pos
            
            elif event.type == pygame.KEYDOWN:
                pass  # 回転機能を無効化
        
        return True
    
    def handle_mouse_down(self, pos):
        """マウスダウン処理"""
        # 次のブロックエリアをチェック
        for i, block in enumerate(self.next_blocks):
            block_x = 20 + i * 120
            block_y = BLOCK_PREVIEW_OFFSET_Y
            block_rect = pygame.Rect(block_x, block_y, 100, 100)  # エリアを大きくする
            
            if block_rect.collidepoint(pos):
                self.selected_block = block
                self.dragging = True
                self.drag_pos = pos
                break
    
    def handle_mouse_up(self, pos):
        """マウスアップ処理"""
        if self.dragging and self.selected_block:
            # 盤面上の位置を計算（ブロックの中心を考慮）
            board_x = (pos[0] - BOARD_OFFSET_X) // CELL_SIZE
            board_y = (pos[1] - BOARD_OFFSET_Y) // CELL_SIZE
            
            # ブロックの左上角を基準にした位置に調整
            board_x -= self.selected_block.width // 2
            board_y -= self.selected_block.height // 2
            
            # ブロックを配置
            if self.board.place_block(self.selected_block, board_x, board_y):
                # 配置成功
                self.assets["place_sound"].play()
                
                # ライン消去チェック
                lines_cleared = self.board.clear_lines()
                if lines_cleared > 0:
                    self.assets["clear_sound"].play()
                    self.score.add_score(lines_cleared * 100)
                    
                    # キラキラエフェクトを追加
                    self.add_sparkle_effects()
                
                # 使用したブロックを削除し、新しいブロックを追加
                if self.selected_block in self.next_blocks:
                    self.next_blocks.remove(self.selected_block)
                    if len(self.next_blocks) == 0:
                        self.next_blocks = self.block_generator.generate_next_blocks()
                
                # ゲームオーバーチェック
                if self.board.is_game_over(self.next_blocks):
                    self.game_over = True
                    self.assets["gameover_sound"].play()
                    pygame.mixer.music.stop()
            
            self.dragging = False
            self.selected_block = None
    
    def restart_game(self):
        """ゲームをリスタート"""
        self.board = Board()
        self.score.reset_score()  # スコアをリセット
        self.next_blocks = self.block_generator.generate_next_blocks()
        self.selected_block = None
        self.dragging = False
        self.game_over = False
        self.sparkle_effects = []  # エフェクトをクリア
        pygame.mixer.music.play(-1)
    
    def draw(self):
        """画面描画"""
        # レトロゲーム風の背景（マリオ風）
        self.screen.fill((135, 206, 235))  # 空色の背景
        
        # マリオ風の雲を描画
        self.draw_clouds()
        
        # マリオ風の地面を描画
        self.draw_ground()
        
        # 盤面を描画
        self.board.draw(self.screen, self.assets)
        
        # 次のブロックを描画
        self.draw_next_blocks()
        
        # スコアを描画
        self.score.draw(self.screen, self.assets)
        
        # ドラッグ中のブロックを描画
        if self.dragging and self.selected_block:
            x = self.drag_pos[0] - (self.selected_block.width * CELL_SIZE) // 2
            y = self.drag_pos[1] - (self.selected_block.height * CELL_SIZE) // 2
            self.selected_block.draw(self.screen, x, y, CELL_SIZE, self.assets)
            
            # 配置可能位置のプレビューを表示
            board_x = (self.drag_pos[0] - BOARD_OFFSET_X) // CELL_SIZE
            board_y = (self.drag_pos[1] - BOARD_OFFSET_Y) // CELL_SIZE
            board_x -= self.selected_block.width // 2
            board_y -= self.selected_block.height // 2
            
            # 配置可能かチェック
            if self.board.is_valid_placement(self.selected_block, board_x, board_y):
                # 配置可能な場合は緑色の枠を表示
                preview_x = BOARD_OFFSET_X + board_x * CELL_SIZE
                preview_y = BOARD_OFFSET_Y + board_y * CELL_SIZE
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (preview_x, preview_y, 
                                self.selected_block.width * CELL_SIZE, 
                                self.selected_block.height * CELL_SIZE), 3)
            else:
                # 配置不可能な場合は赤色の枠を表示
                preview_x = BOARD_OFFSET_X + board_x * CELL_SIZE
                preview_y = BOARD_OFFSET_Y + board_y * CELL_SIZE
                pygame.draw.rect(self.screen, (255, 0, 0), 
                               (preview_x, preview_y, 
                                self.selected_block.width * CELL_SIZE, 
                                self.selected_block.height * CELL_SIZE), 3)
        
        # エフェクトを更新・描画
        self.update_sparkle_effects()
        
        # ゲームオーバー表示
        if self.game_over:
            self.draw_game_over()
        
        # 操作説明
        self.draw_instructions()
        
        pygame.display.flip()
    
    def draw_next_blocks(self):
        """次のブロックを描画"""
        font = self.get_japanese_font(20)  # フォントサイズを小さく
        
        title = font.render("次のブロック:", True, WHITE)
        self.screen.blit(title, (20, BLOCK_PREVIEW_OFFSET_Y - 25))
        
        for i, block in enumerate(self.next_blocks):
            block_x = 20 + i * 120
            block_y = BLOCK_PREVIEW_OFFSET_Y
            
            # 選択中のブロックを強調表示
            if block == self.selected_block:
                pygame.draw.rect(self.screen, (100, 100, 255), 
                               (block_x, block_y, 100, 100))
                pygame.draw.rect(self.screen, (255, 255, 0), 
                               (block_x, block_y, 100, 100), 3)
            else:
                # ブロックエリアの背景（サイズを統一）
                pygame.draw.rect(self.screen, (50, 50, 50), 
                               (block_x, block_y, 100, 100))
                pygame.draw.rect(self.screen, WHITE, 
                               (block_x, block_y, 100, 100), 2)
            
            # ブロックを描画（中央配置）
            center_x = block_x + 50 - (block.width * BLOCK_PREVIEW_SIZE) // 2
            center_y = block_y + 50 - (block.height * BLOCK_PREVIEW_SIZE) // 2
            block.draw(self.screen, center_x, center_y, BLOCK_PREVIEW_SIZE, self.assets)
    
    def draw_game_over(self):
        """ゲームオーバー画面を描画"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 日本語フォントを取得
        game_over_font = self.get_japanese_font(72)
        score_font = self.get_japanese_font(48)
        restart_font = self.get_japanese_font(36)
        
        # ゲームオーバーテキスト
        game_over_text = game_over_font.render("ゲームオーバー", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        # スコア表示
        score_text = score_font.render(f"最終スコア: {self.score.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
        self.screen.blit(score_text, score_rect)
        
        # リスタート指示
        restart_text = restart_font.render("Rキーでリスタート", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(restart_text, restart_rect)
        
        # ハイスコア表示
        high_score_text = score_font.render(f"ハイスコア: {self.score.high_score}", True, (255, 255, 0))
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
        self.screen.blit(high_score_text, high_score_rect)
    
    def add_sparkle_effects(self):
        """キラキラエフェクトを追加"""
        # 消去されたブロックの位置にエフェクトを追加
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board.grid[row][col] is None:  # 空のマス
                    x = BOARD_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
                    y = BOARD_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
                    self.sparkle_effects.append(SparkleEffect(x, y))
    
    def update_sparkle_effects(self):
        """キラキラエフェクトを更新・描画"""
        # エフェクトを更新
        self.sparkle_effects = [effect for effect in self.sparkle_effects if effect.update()]
        
        # エフェクトを描画
        for effect in self.sparkle_effects:
            effect.draw(self.screen)
    
    def draw_clouds(self):
        """マリオ風の雲を描画"""
        cloud_color = (255, 255, 255)
        
        # 雲1
        pygame.draw.ellipse(self.screen, cloud_color, (50, 80, 60, 30))
        pygame.draw.ellipse(self.screen, cloud_color, (80, 80, 50, 25))
        pygame.draw.ellipse(self.screen, cloud_color, (110, 80, 40, 20))
        
        # 雲2
        pygame.draw.ellipse(self.screen, cloud_color, (600, 120, 70, 35))
        pygame.draw.ellipse(self.screen, cloud_color, (640, 120, 55, 30))
        pygame.draw.ellipse(self.screen, cloud_color, (670, 120, 45, 25))
        
        # 雲3
        pygame.draw.ellipse(self.screen, cloud_color, (300, 60, 50, 25))
        pygame.draw.ellipse(self.screen, cloud_color, (330, 60, 40, 20))
    
    def draw_ground(self):
        """マリオ風の地面を描画"""
        # 地面の色（緑）
        ground_color = (34, 139, 34)
        
        # 地面を描画
        pygame.draw.rect(self.screen, ground_color, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        
        # 地面の装飾（草）
        grass_color = (50, 205, 50)
        for i in range(0, SCREEN_WIDTH, 30):
            pygame.draw.rect(self.screen, grass_color, (i, SCREEN_HEIGHT - 100, 20, 10))
    
    def draw_instructions(self):
        """操作説明を描画"""
        font = self.get_japanese_font(14)  # フォントサイズをさらに小さく
        
        instructions = [
            "操作方法:",
            "・マウスでブロックをドラッグ",
            "・縦横のラインが完成すると消去",
            "・ブロックが置けなくなったら",
            "  ゲームオーバー"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, WHITE)
            self.screen.blit(text, (20, 120 + i * 16))  # 位置と行間を調整
    
    def run(self):
        """メインゲームループ"""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

def main():
    """メイン関数"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
