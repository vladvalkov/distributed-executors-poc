import os
import subprocess
from subprocess import Popen

import fastapi.cli
import pydantic_settings
import uvicorn
import websockets.sync.server as websockets
from pydantic import Field
from signal import signal, SIGINT
from fastapi import FastAPI

ports = list(range(8765, 8799))


class Settings(pydantic_settings.BaseSettings):
    workers: int


s = Settings()
app = FastAPI()

processes: list[Popen] = []


def kill_all(sig, frame):
    for proc in processes:
        proc.kill()


signal(SIGINT, kill_all)

running_hosts = []

for worker in range(s.workers):
    port = ports[worker]
    print(f"[COORDINATOR]   Starting worker on port {port}")

    env = os.environ.copy()
    env["PORT"] = str(port)
    env["WORKER_ID"] = str(worker)
    proc = subprocess.Popen(["uv", "run", "server.py"], env=env)
    processes.append(proc)
    running_hosts.append(f"ws://localhost:{port}")


@app.get("/workers")
def create_workers():
    return running_hosts


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8760)
