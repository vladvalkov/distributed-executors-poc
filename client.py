import os
import queue
import sys
import threading
import time

import httpx
import pykka
from pydantic import RootModel, BaseModel
from pykka import ActorRef, ActorProxy
from websockets.sync.client import connect, ClientConnection
from concurrent.futures import Future

from messages import ScheduleMessage, AcknowledgeMessage, ResultMessage, ErrorMessage, RootMessage, ReplyMessage


class WorkerConnection(pykka.ThreadingActor):
    def __init__(self, host: str, scheduler: ActorProxy['Scheduler']):
        super().__init__()
        self.websocket = connect(host)
        self.scheduler = scheduler

    def close(self):
        self.websocket.close()

    def on_start(self) -> None:
        threading.Thread(target=self.listen, args=(self.websocket, self.scheduler)).start()

    def submit(self, message: ScheduleMessage):
        self.websocket.send(message.model_dump_json())

    @classmethod
    def listen(cls, websocket: ClientConnection, scheduler: ActorProxy['Scheduler']):
        for msg in websocket:
            msg = ReplyMessage.model_validate_json(msg)
            match msg.root:
                case AcknowledgeMessage(id=_, status=_):
                    print(f"[WORKER CLIENT] Acknowledged message {msg.root.id}")
                case ResultMessage(id=_, result=_):
                    print(f"[WORKER CLIENT] Received result for {msg.root.id}")
                    scheduler.put_result(msg.root)
                case ErrorMessage(id=_, error=_):
                    print(f"[WORKER CLIENT] Received error for {msg.root.id}")
                    scheduler.put_result(msg.root)
                case _:
                    raise ValueError(f"Invalid message: {msg.root}")

class Running:
    def __init__(self, worker: ActorProxy[WorkerConnection], message: ScheduleMessage, future: Future[ResultMessage]):
        self.worker = worker
        self.message = message
        self.future = future
        self.t0 = time.time()

    worker: ActorProxy[WorkerConnection]
    message: ScheduleMessage
    future: Future[ResultMessage]
    t0: float


class Scheduler(pykka.ThreadingActor):
    def __init__(self, connections: list[str]):
        super().__init__()
        self.workers = queue.Queue(maxsize=len(connections))
        for host in connections:
            self.workers.put(WorkerConnection.start(host, self).proxy())

    def close(self):
        while not self.workers.empty():
            worker = self.workers.get()
            worker.close()

    id: int = 0
    running: dict[int, Running] = {}
    workers: queue.Queue[ActorProxy[WorkerConnection]]

    def submit(self, message: ScheduleMessage):
        self.id += 1
        message.id = self.id
        print(f"[SCHEDULER]     Submitting message {message.id}")
        worker = self.workers.get()
        worker.submit(message)
        future = Future()
        self.running[self.id] = Running(worker=worker, message=message, future=future)
        return future

    def put_result(self, message: ResultMessage | ErrorMessage):
        print(f"[SCHEDULER]     Received reply for message {message.id}: {message}; processing: {time.time() - self.running[message.id].t0}")
        task = self.running[message.id]
        self.workers.put(task.worker)
        self.running.pop(message.id)
        task.future.set_result(message)


def main():
    response = httpx.get("http://localhost:8760/workers")
    hosts = response.json()

    messages = range(1, 100)

    scheduler = Scheduler.start(hosts).proxy()
    futures = []
    for message in messages:
        future = scheduler.submit(ScheduleMessage(id=0, content=message)).get()
        futures.append(future)

    for future in futures:
        print(future.result())

    scheduler.close()
    pykka.ActorRegistry.stop_all()
    print("[CLIENT] Done!")


if __name__ == "__main__":
    main()
