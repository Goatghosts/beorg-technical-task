import threading
import json
import time
import logging

from modules.WebsocketClient import WebsocketClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")


class Client:
    def __init__(self):
        self.socket = None

    def run(self):
        self.job_workers = [
            threading.Thread(target=self.connection_checker, daemon=True),
        ]
        for worker in self.job_workers:
            worker.start()

    def get_socket(self):
        return WebsocketClient(
            url="ws://localhost:8765",
            on_open=self.on_open_cb,
            on_message=self.on_message_cb,
            on_error=self.on_error_cb,
            on_close=self.on_close_cb,
        )

    def on_open_cb(self):
        logging.info(f"connection opened")

    def on_message_cb(self, msg):
        recived = json.loads(msg)
        print(recived)

    def on_error_cb(self):
        logging.error(f"server send error")
        if self.socket is not None:
            self.socket.close()

    def on_close_cb(self):
        logging.warning(f"connection closed")
        self.socket = None

    def connection_checker(self):
        while True:
            if self.socket is None:
                self.socket = self.get_socket()
                self.socket.start()
            else:
                try:
                    if not self.socket.is_connected():
                        self.socket.close()
                        self.socket = None
                except Exception as e:
                    logging.error(repr(e))
                    logging.error(f"self.socket._is_connected ERROR")
            time.sleep(10)

    def shutdown(self):
        for worker in self.job_workers:
            worker.stop()
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        logging.info("Shutdown client")


if __name__ == "__main__":
    server = Client()
    server.run()
    while True:
        time.sleep(1)
