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

    def run(self):
        self._ws_server = WebsocketServer(
            on_open=self.on_open,
            host="0.0.0.0",
            port=8765,
        )
        self._ws_server.start()
        self.job_workers = [
            threading.Thread(target=self.check_catalog, daemon=True),
        ]
        for worker in self.job_workers:
            worker.start()

    def check_catalog(self):
        while True:
            catalog = {}
            for root, dirs, files in os.walk(self.path):
                cleaned_root = root.replace(os.getcwd(), "")
                for name in dirs:
                    path = os.path.join(cleaned_root, name).replace("\\", "/")
                    full_path = os.path.join(root, name)
                    catalog[path] = {
                        "timestamp": os.path.getmtime(full_path),
                        "type": "Directory",
                        "full_path": full_path,
                    }
                for name in files:
                    path = os.path.join(cleaned_root, name).replace("\\", "/")
                    full_path = os.path.join(root, name)
                    catalog[path] = {
                        "timestamp": os.path.getmtime(full_path),
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
                if self.catalog[item]["timestamp"] != catalog[item]["timestamp"]:
                    diff["updated"][item] = catalog[item]["timestamp"]
                    update = True
                    logging.info(f"{catalog[item]['type']} updated: {item}")
            if update:
                self._ws_server.send_all(json.dumps({"type": "diff", "data": diff}))
                self.catalog = catalog

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
