import websocket
import threading
import logging


class WebsocketClient(threading.Thread):
    def __init__(self, url="0.0.0.0", on_open=None, on_message=None, on_close=None, on_error=None):
        super().__init__()
        self.daemon = True
        self._is_connected = False
        self.on_open_cb = on_open
        self.on_message_cb = on_message
        self.on_close_cb = on_close
        self.on_error_cb = on_error
        logging.info(f"Connect to {url}")
        self._ws = websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

    def run(self):
        self.connect()

    def connect(self):
        self._ws.run_forever(skip_utf8_validation=True)

    def close(self):
        if self._is_connected:
            self._ws.close()

    def send(self, data):
        self._ws.send(data)

    def on_message(self, ws, msg):
        if self.on_message_cb:
            self.on_message_cb(msg)

    def on_error(self, ws, error):
        logging.error("websocket error")
        logging.error(error)
        if self.on_error_cb:
            self.on_error_cb()

    def on_close(self, ws, close_status_code, close_msg):
        logging.info("websocket closed")
        self._is_connected = False
        if self.on_close_cb:
            self.on_close_cb()

    def on_open(self, ws):
        logging.info("websocket connected")
        self._is_connected = True
        if self.on_open_cb:
            self.on_open_cb()

    def is_connected(self):
        return self._is_connected
