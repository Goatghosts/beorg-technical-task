import logging
import time
import json
import threading
import os
from argparse import ArgumentParser

from modules.WebsocketServer import WebsocketServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")


class Server:
    def __init__(self, path: str) -> None:
        self._ws_server = None
        self.path = os.getcwd() if path is None else path
        self.catalog = {}
        self.lock = threading.Event()

    def run(self):
        self.worker = threading.Thread(target=self.check_catalog, daemon=True)
        self.worker.start()
        self._ws_server = WebsocketServer(
            on_open=self.on_open,
            host="0.0.0.0",
            port=8765,
        )
        self.lock.wait()
        self._ws_server.start()

    def check_catalog(self):
        while True:
            catalog = {}
            for root, dirs, files in os.walk(self.path):
                cleaned_root = root.replace(self.path, "")
                for name in dirs:
                    path = os.path.join(cleaned_root, name).replace("\\", "/")
                    full_path = os.path.join(root, name)
                    try:
                        timestamp = os.path.getmtime(full_path)
                    except:
                        timestamp = 0
                    catalog[path] = {
                        "timestamp": timestamp,
                        "type": "Directory",
                        "full_path": full_path,
                    }
                for name in files:
                    path = os.path.join(cleaned_root, name).replace("\\", "/")
                    full_path = os.path.join(root, name)
                    try:
                        timestamp = os.path.getmtime(full_path)
                    except:
                        timestamp = 0
                    catalog[path] = {
                        "timestamp": timestamp,
                        "type": "File",
                        "full_path": full_path,
                    }

            old_catalog = set(self.catalog.keys())
            new_catalog = set(catalog.keys())
            diff = {
                "new": {},
                "deleted": [],
                "updated": {},
            }
            update = False
            for item in new_catalog - old_catalog:
                diff["new"][item] = catalog[item]
                update = True
                logging.info(f"{catalog[item]['type']} created: {item}")
            for item in old_catalog - new_catalog:
                diff["deleted"].append(item)
                update = True
                logging.info(f"{self.catalog[item]['type']} deleted: {item}")
            for item in new_catalog.intersection(old_catalog):
                if self.catalog[item]["timestamp"] < catalog[item]["timestamp"]:
                    diff["updated"][item] = catalog[item]["timestamp"]
                    update = True
                    logging.info(f"{catalog[item]['type']} updated: {item}")
            if update:
                self._ws_server.send_all(json.dumps({"type": "diff", "data": diff}))
                self.catalog = catalog
                self.lock.set()

    def on_open(self):
        return json.dumps({"type": "init", "data": self.catalog})


if __name__ == "__main__":
    argument_parser = ArgumentParser()
    argument_parser.add_argument("-p", "--path")
    args = argument_parser.parse_args()
    if args.path is None or os.path.exists(args.path):
        server = Server(args.path)
        server.run()
        while True:
            time.sleep(1)
    else:
        logging.error("Incorrect path. Shutdown.")
