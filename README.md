# POC
Simple POC of a distributed job execution.

# WIP
- [x] Simple algorithm of non-persistent task distribution
- [ ] Improved error handling (Mostly errors related to broken connection / dead workers)
- [ ] Bundling and passing function to workers
- [ ] Metrics and observability

## How to run
You will need `uv` installed.
```bash
# Install dependencies
uv sync

# Start the server
# This starts five workers on ports 8765-8769
# At the moment, the workers square the passed number and sleep for 1 second before returning the result
WORKERS=5 uv run coordinator.py

# Start the client
# This sends 100 tasks to the workers
uv run client.py
```
