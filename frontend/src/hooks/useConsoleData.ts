import { useState, useEffect } from "react";
import type { LogEntry, AppState } from "../types";

export function useConsoleData() {
  const [state, setState] = useState<AppState>({
    isActive: true,
    logs: [],
    stats: {
      totalCorrections: 0,
      averageLatencyMs: 0,
      wpmHistory: Array(40).fill(0),
    },
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const port = params.get('port') || '5000';
    const token = params.get('token') || '';
    const apiBase = `http://127.0.0.1:${port}/api`;

    // Fetch initial stats
    const fetchStats = async () => {
      try {
        const res = await fetch(`${apiBase}/stats?token=${token}`);
        if (res.ok) {
          const data = await res.json();
          setState(prev => ({
            ...prev,
            stats: {
              ...prev.stats,
              totalCorrections: data.total_corrections || 0,
              averageLatencyMs: data.average_latency || 0,
              modelInfo: data.model_info || { version: 'Unknown', features: 'Unknown', samples: 'Unknown' }
            }
          }));
        }
      } catch (e) {
        console.error("Failed to fetch stats", e);
      }
    };

    fetchStats();
    const statsInterval = setInterval(fetchStats, 2000);

    // Initial Logs
    const fetchLogs = async () => {
      try {
        const res = await fetch(`${apiBase}/activity_log?token=${token}`);
        if (res.ok) {
          const data = await res.json();
          const initialLogs: LogEntry[] = data.map((item: any) => ({
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().getTime(),
            type: item.type.toLowerCase() === 'correction' ? 'correction' : 'info',
            originalText: item.type.toLowerCase() === 'correction' ? item.message.split('->')[0]?.strip() || 'old' : null,
            correctedText: item.message,
            latencyMs: 0
          })).reverse();
          
          setState(prev => ({ ...prev, logs: initialLogs.slice(0, 50) }));
        }
      } catch(e) {}
    };
    fetchLogs();

    // SSE Connection
    const eventSource = new EventSource(`${apiBase}/stream?token=${token}`);
    
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'log' && payload.data) {
          const logData = payload.data;
          const isCorrection = logData.type.toLowerCase() === 'correction';
          
          let originalText = null;
          let correctedText = logData.message;
          let latency = 0;
          
          // Parsing "[latency] old -> new" if present
          if (isCorrection && logData.message.includes('->')) {
             const parts = logData.message.split('->');
             originalText = parts[0].trim();
             correctedText = parts[1].trim();
          }

          const newLog: LogEntry = {
            id: Math.random().toString(36).substring(7),
            timestamp: Date.now(),
            type: isCorrection ? "correction" : "info",
            originalText,
            correctedText,
            latencyMs: latency,
          };

          setState((prev) => {
            const newLogs = [newLog, ...prev.logs].slice(0, 50);
            
            // Generate a fake WPM spike on activity for visual feedback
            // since backend doesn't provide real-time WPM stream yet
            const newWpm = [...prev.stats.wpmHistory.slice(1), isCorrection ? 120 : 60];

            return { 
              ...prev, 
              logs: newLogs,
              stats: {
                ...prev.stats,
                wpmHistory: newWpm
              }
            };
          });
        }
      } catch (err) {
        console.error("SSE Parse Error", err);
      }
    };

    // Decay WPM if idle
    const wpmDecayInterval = setInterval(() => {
      setState(prev => {
        const last = prev.stats.wpmHistory[prev.stats.wpmHistory.length - 1];
        if (last > 10) {
          const newWpm = [...prev.stats.wpmHistory.slice(1), Math.floor(last * 0.8)];
          return { ...prev, stats: { ...prev.stats, wpmHistory: newWpm }};
        }
        return prev;
      });
    }, 500);

    return () => {
      clearInterval(statsInterval);
      clearInterval(wpmDecayInterval);
      eventSource.close();
    };
  }, []);

  return state;
}
