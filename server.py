import os
import threading
from time import sleep

import pydantic_settings
import websockets.sync.server as websockets
from websockets.sync.server import ServerConnection

from messages import RootMessage, AcknowledgeMessage, ScheduleMessage, ResultMessage, ErrorMessage


class Settings(pydantic_settings.BaseSettings):
    worker_id: int
    port: int


s = Settings()


def process_message(msg: ScheduleMessage, websocket: ServerConnection):
    try:
        result = msg.content ** 2
        sleep(1)
        print(f"[WORKER {s.worker_id}]  {msg.content} -> {result}")
        websocket.send(ResultMessage(id=msg.id, result=str(result)).model_dump_json())
    except Exception as e:
        print(f"[WORKER {s.worker_id}]  Error processing message: {e}")
        websocket.send(ErrorMessage(id=msg.id, error=str(e)).model_dump_json())



def handle(websocket):
    for message in websocket:
        msg = RootMessage.model_validate_json(message)
        print(f"[WORKER {s.worker_id}]  Received message: {msg}")
        # websocket.send(AcknowledgeMessage(id=msg.root.id, status="OK").model_dump_json())

        threading.Thread(target=process_message, args=(msg.root, websocket)).start()


def main():
    print(f"[WORKER {s.worker_id}]      Started worker on port {s.port}")

    with websockets.serve(handle, "localhost", s.port) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
