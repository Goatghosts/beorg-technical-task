import threading
import json
import time
import logging

from modules.WebsocketClient import WebsocketClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")


class Client:
    def __init__(self):
        self.socket = None
        self.catalog = None
        self.worker = None

    def run(self):
        self.worker = threading.Thread(target=self.connection_checker, daemon=True)
        self.worker.start()

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

    def get_strftime(self, timestamp: int) -> str:
        return time.strftime("%D %H:%M:%S", time.localtime(timestamp))

    def processing_init(self, data):
        self.catalog = data
        for key, value in self.catalog.items():
            item_type = value["type"].lower()
            update_time = self.get_strftime(value["timestamp"])
            logging.info(f"New {item_type}: {key}, updated at {update_time}")
        return None

    def processing_diff(self, data):
        for key, value in data["new"].items():
            item_type = value["type"].lower()
            update_time = self.get_strftime(value["timestamp"])
            logging.info(f"Create {item_type}: {key}, created at {update_time}")
            self.catalog[key] = value
        for key in data["deleted"]:
            try:
                item_type = self.catalog[key]["type"].lower()
                logging.info(f"Delete {item_type}: {key}")
                del self.catalog[key]
            except KeyError:
                logging.error(f"Delete error. This item does not exist in the directory: {key}")
        for key, value in data["updated"].items():
            try:
                item_type = self.catalog[key]["type"].lower()
                update_time = self.get_strftime(value)
                logging.info(f"Update {item_type}: {key}, updated at {update_time}")
                self.catalog[key]["timestamp"] = value
            except KeyError:
                logging.error(f"Update error. This item does not exist in the directory: {key}")
        return None

    def on_message_cb(self, msg):
        recived = json.loads(msg)
        if recived["type"] == "init":
            self.processing_init(recived["data"])
        elif recived["type"] == "diff":
            self.processing_diff(recived["data"])

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


if __name__ == "__main__":
    server = Client()
    server.run()
    while True:
        time.sleep(1)
