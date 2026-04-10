import asyncio
import json
import threading
from typing import Dict, List, Optional, Any, Callable
import websockets
from websockets.exceptions import ConnectionClosed


class YCYServer:
    def __init__(self, host: str, port: int, external_host: Optional[str] = None,
                 max_strength_a: int = 200, max_strength_b: int = 200):
        self.host = host
        self.port = port
        self.external_host = external_host or f"ws://localhost:{port}"
        self.max_strength_a = max_strength_a
        self.max_strength_b = max_strength_b
        self.server = None
        self.running = False
        self.connections: Dict[str, Any] = {}
        self.lock = threading.Lock()

    async def _handle_connection(self, websocket, path):
        client_id = str(id(websocket))
        print(f"新连接: {client_id}")
        
        try:
            with self.lock:
                self.connections[client_id] = {
                    "websocket": websocket,
                    "strength_a": 0,
                    "strength_b": 0,
                    "limit_a": self.max_strength_a,
                    "limit_b": self.max_strength_b,
                    "bound": False,
                    "client_id": None
                }

            async for message in websocket:
                await self._handle_message(client_id, message)

        except ConnectionClosed:
            print(f"连接关闭: {client_id}")
        except Exception as e:
            print(f"连接错误: {client_id}, {e}")
        finally:
            with self.lock:
                if client_id in self.connections:
                    del self.connections[client_id]

    async def _handle_message(self, client_id: str, message: str):
        try:
            data = json.loads(message)
            conn = self.connections.get(client_id)
            if not conn:
                return

            if data.get("type") == "bind":
                conn["bound"] = True
                conn["client_id"] = data.get("clientId")
                print(f"设备绑定成功: {conn['client_id']}")
                await websocket.send(json.dumps({
                    "type": "bindSuccess",
                    "clientId": conn["client_id"]
                }))

            elif data.get("type") == "strength":
                parts = data.get("data", "").split("+")
                if len(parts) >= 4:
                    try:
                        conn["strength_a"] = int(parts[0])
                        conn["strength_b"] = int(parts[1])
                        conn["limit_a"] = int(parts[2])
                        conn["limit_b"] = int(parts[3])
                    except ValueError:
                        pass

        except Exception as e:
            print(f"处理消息错误: {e}")

    async def send_strength(self, client_id: Optional[str], channel: str, mode: int, value: int):
        with self.lock:
            target_conns = []
            if client_id:
                for cid, conn in self.connections.items():
                    if conn.get("client_id") == client_id:
                        target_conns.append(conn)
            else:
                target_conns = list(self.connections.values())

            for conn in target_conns:
                try:
                    websocket = conn["websocket"]
                    command = f"strength-{channel}+{mode}+{value}"
                    await websocket.send(json.dumps({
                        "type": "control",
                        "data": command
                    }))
                except Exception as e:
                    print(f"发送强度命令失败: {e}")

    async def send_wave(self, client_id: Optional[str], channel: str, wave: List[int]):
        with self.lock:
            target_conns = []
            if client_id:
                for cid, conn in self.connections.items():
                    if conn.get("client_id") == client_id:
                        target_conns.append(conn)
            else:
                target_conns = list(self.connections.values())

            for conn in target_conns:
                try:
                    websocket = conn["websocket"]
                    wave_str = ",".join(map(str, wave))
                    command = f"pulse-{channel}:[{wave_str}]"
                    await websocket.send(json.dumps({
                        "type": "control",
                        "data": command
                    }))
                except Exception as e:
                    print(f"发送波形命令失败: {e}")

    async def clear_queue(self, client_id: Optional[str], channel: str):
        with self.lock:
            target_conns = []
            if client_id:
                for cid, conn in self.connections.items():
                    if conn.get("client_id") == client_id:
                        target_conns.append(conn)
            else:
                target_conns = list(self.connections.values())

            for conn in target_conns:
                try:
                    websocket = conn["websocket"]
                    channel_num = 1 if channel == "A" else 2
                    command = f"clear-{channel_num}"
                    await websocket.send(json.dumps({
                        "type": "control",
                        "data": command
                    }))
                except Exception as e:
                    print(f"清除队列失败: {e}")

    async def stop_output(self, client_id: Optional[str]):
        await self.send_strength(client_id, "A", 0, 0)
        await self.send_strength(client_id, "B", 0, 0)
        await self.clear_queue(client_id, "A")
        await self.clear_queue(client_id, "B")

    def get_status(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        with self.lock:
            if client_id:
                for cid, conn in self.connections.items():
                    if conn.get("client_id") == client_id:
                        return {
                            "connected": True,
                            "bound": conn["bound"],
                            "strength_a": conn["strength_a"],
                            "strength_b": conn["strength_b"],
                            "limit_a": conn["limit_a"],
                            "limit_b": conn["limit_b"]
                        }
                return {"connected": False}
            else:
                return {
                    "connections": len(self.connections),
                    "clients": [
                        {
                            "client_id": conn.get("client_id"),
                            "bound": conn["bound"]
                        }
                        for conn in self.connections.values()
                    ]
                }

    async def start(self):
        if self.running:
            return
        
        self.running = True
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port
        )
        print(f"YCY WebSocket 服务器启动: ws://{self.host}:{self.port}")

    async def stop(self):
        if not self.running:
            return
        
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        print("YCY WebSocket 服务器已停止")

    def get_qrcode_url(self) -> str:
        return self.external_host
