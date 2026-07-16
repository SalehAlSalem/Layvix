# Frontend UI Architecture (React & Vite)

The UI for Layvix v4.0.0 is entirely decoupled from the Python engine. It is built as a Single Page Application (SPA) using React, Vite, and TailwindCSS. It runs inside a Chromium-based `pywebview` window.

## 1. The Design System (Glassmorphism)
The app targets "Power Users" and developers, abandoning the traditional clean-but-empty minimalist approach in favor of a **Dense Data Layout**. 
- No scrolling on the main dashboard.
- Real-time data visualization.
- Glassmorphism UI using absolute positioning and SVG glows.
- Custom scrollbars (`custom-scrollbar`) to maintain the sleek dark theme.

## 2. State Management (`Zustand`)
We use `Zustand` (`store/useAppStore.ts`) to manage global state. The store is the single source of truth for the UI and mirrors the Python backend's state.

```typescript
interface AppState {
  settings: Record<string, any>;
  stats: Record<string, any>;
  logs: LogEntry[];
  updateSettings: (newSettings: Record<string, any>) => void;
  addLog: (log: LogEntry) => void;
}
```

When a user modifies a setting (e.g., changes a hotkey), the component updates the Zustand store instantly for immediate UI feedback, and concurrently sends a `POST` request to `/api/settings/update` to persist the change to disk.

## 3. Real-Time Telemetry (Server-Sent Events)
The Python engine generates thousands of logs (AI decisions, Latency, Hooks). Polling the server every second would be inefficient. Instead, we use `Server-Sent Events` (SSE) in `utils/apiClient.ts`:

```typescript
export const connectSSE = (onMessage: (data: any) => void) => {
  const source = new EventSource(`http://127.0.0.1:${port}/api/stream?token=${token}`);
  source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
};
```
This guarantees an instant, one-way stream of diagnostic data directly into the Developer Console without hanging the UI thread.

## 4. The Raw Logs Viewer (Black Box)
Inside the Developer Console (`DeveloperView.tsx`), we implemented a "Raw Logs Viewer".
To prevent React from crashing when rendering the massive `layvix.log` file:
1. The backend (`/api/logs/raw`) caps the output to the last 1,000 lines.
2. The frontend uses `React.useMemo` (or efficient `.map` rendering) to parse the text.
3. It applies **Semantic Syntax Highlighting** using Regex on the client-side to colorize `[ERROR]` (Red), `[WARNING]` (Amber), and dim the timestamps for readability.
