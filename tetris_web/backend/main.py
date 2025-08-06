from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import json
import time
import asyncio
from game import TetrisGame, ActionType

# ゲーム状態の自動更新タスク
async def game_update_task():
    """各クライアントのゲーム状態を定期的に更新"""
    while True:
        try:
            current_time = int(time.time() * 1000)  # ミリ秒
            
            # 各クライアントのゲームを更新
            disconnected_clients = []
            for websocket, game in client_games.items():
                try:
                    game.update(current_time)
                    # 更新された状態をそのクライアントに送信
                    await websocket.send_text(json.dumps(game.get_game_state()))
                except Exception as e:
                    print(f"クライアント {websocket} のゲーム更新エラー: {e}")
                    disconnected_clients.append(websocket)
            
            # 切断されたクライアントを削除
            for websocket in disconnected_clients:
                if websocket in client_games:
                    del client_games[websocket]
                
        except Exception as e:
            print(f"ゲーム更新タスクエラー: {e}")
        
        await asyncio.sleep(0.1)  # 100ms間隔で更新

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    asyncio.create_task(game_update_task())
    yield
    # 終了時の処理（必要に応じて）

app = FastAPI(title="テトリスWebゲーム", version="1.0.0", lifespan=lifespan)

# 静的ファイルの配信（APIエンドポイントの後にマウント）

# クライアントごとのゲームインスタンス管理
client_games: Dict[WebSocket, TetrisGame] = {}

# Pydanticモデル
class ActionRequest(BaseModel):
    action: str
    x: Optional[int] = None
    y: Optional[int] = None

class GameStateResponse(BaseModel):
    board: List[List[int]]
    current_piece: Optional[Dict[str, Any]]
    next_piece: Optional[Dict[str, Any]]
    bombs: List[Dict[str, Any]]
    game_over: bool
    paused: bool
    score: int
    level: int
    lines_cleared: int
    bombs_available: int
    speed_multiplier: float
    lines_cleared_this_frame: int

def get_or_create_game(websocket: WebSocket) -> TetrisGame:
    """WebSocket接続に対応するゲームインスタンスを取得または作成"""
    if websocket not in client_games:
        client_games[websocket] = TetrisGame()
    return client_games[websocket]

def remove_client_game(websocket: WebSocket):
    """WebSocket接続に対応するゲームインスタンスを削除"""
    if websocket in client_games:
        del client_games[websocket]

# メインページは静的ファイルで配信されるため、このエンドポイントは不要
# @app.get("/", response_class=HTMLResponse)
# async def get_index():
#     """メインページを返す"""
#     with open("/app/frontend/index.html", "r", encoding="utf-8") as f:
#         return HTMLResponse(content=f.read())

@app.post("/start")
async def start_game():
    """新しいゲームを開始（WebSocket経由で実行されるため、このエンドポイントは非推奨）"""
    return {"message": "WebSocket接続経由でゲームを開始してください"}

@app.post("/move")
async def perform_move(action_request: ActionRequest):
    """アクションを実行（WebSocket経由で実行されるため、このエンドポイントは非推奨）"""
    return {"message": "WebSocket接続経由でアクションを実行してください"}

@app.get("/state", response_model=GameStateResponse)
async def get_game_state():
    """現在のゲーム状態を取得（WebSocket経由で実行されるため、このエンドポイントは非推奨）"""
    return {"message": "WebSocket接続経由でゲーム状態を取得してください"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント"""
    await websocket.accept()
    
    try:
        # このクライアント用のゲームインスタンスを作成
        game = get_or_create_game(websocket)
        
        # 初期状態を送信
        await websocket.send_text(json.dumps(game.get_game_state()))
        
        # クライアントからのメッセージを処理
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                # このクライアントのゲームインスタンスを取得
                game = get_or_create_game(websocket)
                
                if action == "start":
                    game.reset_game()
                elif action in ["left", "right", "down", "rotate", "hard_drop"]:
                    action_type = ActionType(action)
                    game.perform_action(action_type)
                elif action == "place_bomb":
                    x = message.get("x", 0)
                    y = message.get("y", 0)
                    game.perform_action(ActionType.PLACE_BOMB, x=x, y=y)
                elif action == "spawn_bomb":
                    game.perform_action(ActionType.SPAWN_BOMB)
                elif action == "pause":
                    game.perform_action(ActionType.PAUSE)
                elif action == "speed_up":
                    game.perform_action(ActionType.SPEED_UP)
                elif action == "speed_down":
                    game.perform_action(ActionType.SPEED_DOWN)
                
                # 更新された状態をこのクライアントにのみ送信
                await websocket.send_text(json.dumps(game.get_game_state()))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "無効なJSONです"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
                
    except WebSocketDisconnect:
        # クライアント切断時にゲームインスタンスを削除
        remove_client_game(websocket)

# 静的ファイルの配信（APIエンドポイントの後にマウント）
import os
app.mount(
    "/",
    StaticFiles(directory="/app/frontend", html=True),
    name="static"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 