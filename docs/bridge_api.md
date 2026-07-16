# Bridge API & Main Lifecycle

This section acts as the skeleton linking the Python backend to the React frontend. It details how the application boots, secures itself, and streams data in real-time.

## 1. The Boot Sequence (`main.py`)
Layvix is a Hybrid Desktop Application. It does not run as a background service; it manages a Chromium `pywebview` window.

### Secure Dynamic Port Allocation
Because running a fixed-port local server exposes the app to port conflicts and cross-site scripting attacks from the browser, Layvix dynamically allocates a free port and generates a cryptographic token on boot:

```python
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

self.port = find_free_port()
self.token = secrets.token_hex(16)
os.environ["LAYVIX_SECURITY_TOKEN"] = self.token
```
The React frontend is injected with this Token and Port via URL parameters (`?port=...&token=...`) when `webview.create_window` is called.

### Thread Orchestration
`main.py` starts multiple threads:
1. `core.start()`: The global keyboard hook thread.
2. `start_fastapi()`: The FastAPI web server thread.
3. `_run_tray()`: The Windows System Tray icon thread (`pystray`).

## 2. API Routes & Live Streaming (`api.py`)

`FastAPI` serves as the communication bridge. Every endpoint is protected by a dependency that verifies the `token`:
```python
def verify_token(token: str = Query(...)):
    if token != os.environ.get("LAYVIX_SECURITY_TOKEN"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return token
```

### Key Endpoints
- **`GET /api/settings`**: Fetches the `settings.json`.
- **`POST /api/settings/update`**: Updates a specific setting and instantly re-applies it in Python without rebooting. For example, changing `blackbox_mode` triggers `configure_blackbox_mode()` inside `logger.py`.
- **`GET /api/logs/raw`**: Fetches the last 1000 lines of the physical `layvix.log` file for the Black Box Viewer.
- **`DELETE /api/logs`**: Wipes the physical log file.

### Server-Sent Events (SSE)
To push live AI statistics and debug logs to the Developer Console, we use SSE via FastAPI's `StreamingResponse` combined with our custom `EventBus`:

```python
@app.get("/api/stream")
def stream_logs(request: Request, token: str = Depends(verify_token)):
    def event_generator():
        q = event_bus.subscribe("log")
        try:
            while True:
                msg = q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            pass
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```
When the user types, `ai_engine.py` generates a log message. `logger.py` pushes this message to the `EventBus`, which immediately streams it to the React frontend.
