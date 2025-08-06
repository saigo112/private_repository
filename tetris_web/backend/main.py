from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import json
import time
import asyncio
from .game import TetrisGame, ActionType

# ゲーム状態の自動更新タスク
async def game_update_task():
    """ゲーム状態を定期的に更新"""
    while True:
        try:
            game = get_game_instance()
            current_time = int(time.time() * 1000)  # ミリ秒
            game.update(current_time)
            
            # 接続中のクライアントに状態を送信
            if connected_clients:
                await broadcast_game_state()
                
        except Exception as e:
            print(f"ゲーム更新エラー: {e}")
        
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

# ゲームインスタンス（シングルトン）
game_instance: Optional[TetrisGame] = None
connected_clients: List[WebSocket] = []

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

def get_game_instance() -> TetrisGame:
    """ゲームインスタンスを取得（なければ作成）"""
    global game_instance
    if game_instance is None:
        game_instance = TetrisGame()
    return game_instance

async def broadcast_game_state():
    """接続中のクライアントにゲーム状態をブロードキャスト"""
    if not connected_clients:
        return
    
    game = get_game_instance()
    game_state = game.get_game_state()
    
    # 接続が切れたクライアントを削除
    disconnected_clients = []
    for client in connected_clients:
        try:
            await client.send_text(json.dumps(game_state))
        except:
            disconnected_clients.append(client)
    
    for client in disconnected_clients:
        connected_clients.remove(client)

# メインページは静的ファイルで配信されるため、このエンドポイントは不要
# @app.get("/", response_class=HTMLResponse)
# async def get_index():
#     """メインページを返す"""
#     with open("/app/frontend/index.html", "r", encoding="utf-8") as f:
#         return HTMLResponse(content=f.read())

@app.post("/start")
async def start_game():
    """新しいゲームを開始"""
    game = get_game_instance()
    game.reset_game()
    
    # WebSocketクライアントに通知
    await broadcast_game_state()
    
    return {"message": "ゲームを開始しました", "game_state": game.get_game_state()}

@app.post("/move")
async def perform_move(action_request: ActionRequest):
    """アクションを実行"""
    game = get_game_instance()
    
    try:
        action = ActionType(action_request.action)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なアクションです")
    
    # アクション実行
    success = game.perform_action(action, x=action_request.x, y=action_request.y)
    
    # WebSocketクライアントに通知
    await broadcast_game_state()
    
    return {
        "success": success,
        "game_state": game.get_game_state()
    }

@app.get("/state", response_model=GameStateResponse)
async def get_game_state():
    """現在のゲーム状態を取得"""
    game = get_game_instance()
    return game.get_game_state()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # 初期状態を送信
        game = get_game_instance()
        await websocket.send_text(json.dumps(game.get_game_state()))
        
        # クライアントからのメッセージを処理
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
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
                
                # 更新された状態を全クライアントに送信
                await broadcast_game_state()
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "無効なJSONです"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

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