import asyncio
import websockets
import threading
import logging


class WebsocketServer(threading.Thread):
    def __init__(self, on_open=None, on_message=None, host="0.0.0.0", port=8765):
        super().__init__()
        self.daemon = True
        self.on_open_cb = on_open
        self.on_message_cb = on_message
        self._host = host
        self._port = port
        self.connected = set()
        self._loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self._loop)
        start_server = websockets.serve(
            self.handler, self._host, self._port, ping_interval=120, ping_timeout=120, max_size=None
        )
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def get_loop(self):
        return self._loop

    def register(self, websocket):
        self.connected.add(websocket)
        logging.info("Client registered")

    def unregister(self, websocket):
        self.connected.remove(websocket)
        logging.info("Client unregistered")

    def shutdown(self):
        logging.warning("Shutdown ws server...")
        self._loop.call_soon_threadsafe(self._loop.stop)

    def send_all(self, group: str, message: str):
        websockets.broadcast(self._groups[group], message)

    async def handler(self, websocket, _):
        self.register(websocket)
        try:
            if self.on_open_cb:
                await websocket.send(self.on_open_cb())
            async for msg in websocket:
                if self.on_message_cb:
                    self.on_message_cb(msg)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.unregister(websocket)
