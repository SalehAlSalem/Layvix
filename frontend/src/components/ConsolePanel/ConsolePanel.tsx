import React, { useState } from "react";
import type { LogEntry } from "../../types";
import "./ConsolePanel.css";

interface ConsolePanelProps {
  logs: LogEntry[];
}

const formatTime = (timestamp: number) => {
  const d = new Date(timestamp);
  return `${d.getHours().toString().padStart(2, "0")}:${d
    .getMinutes()
    .toString()
    .padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`;
};

const renderFormattedText = (text: string) => {
  if (!text) return null;
  
  // Split the text into parts that match our keywords and parts that don't
  const regex = /(ERROR|WARNING|kept|corrected|conf=\d+%)/g;
  const parts = text.split(regex);
  
  return parts.map((part, i) => {
    if (part === 'ERROR') return <span key={i} style={{color: '#E74C3C', fontWeight: 600}}>{part}</span>;
    if (part === 'WARNING') return <span key={i} style={{color: '#F39C12', fontWeight: 600}}>{part}</span>;
    if (part === 'kept' || part === 'corrected') return <span key={i} style={{color: '#00C98F'}}>{part}</span>;
    if (part.startsWith('conf=')) {
      return <span key={i} style={{color: '#4A5568'}}>conf=<span style={{color: '#00C98F'}}>{part.substring(5)}</span></span>;
    }
    return <span key={i}>{part}</span>;
  });
};

export const ConsolePanel: React.FC<ConsolePanelProps> = ({ logs }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyLogs = async () => {
    try {
      const params = new URLSearchParams(window.location.search);
      const port = params.get('port') || '5000';
      const token = params.get('token') || '';
      
      const res = await fetch(`http://127.0.0.1:${port}/api/logs/raw?token=${token}`);
      const data = await res.json();
      
      if (data && data.logs) {
        await navigator.clipboard.writeText(data.logs);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch (e) {
      console.error("Failed to copy logs", e);
    }
  };

  return (
    <div className="console-container" style={{ position: 'relative' }}>
      <button 
        className="copy-logs-btn" 
        onClick={handleCopyLogs}
        title="Copy raw developer logs to clipboard"
      >
        {copied ? (
          <><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!</>
        ) : (
          <><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy Logs</>
        )}
      </button>

      {logs.map((log) => (
        <div key={log.id} className="log-entry">
          <div className="log-time">{formatTime(log.timestamp)}</div>
          
          <div className={`log-content log-type-${log.type}`}>
            {log.type === "info" && (
              <span className="corrected-text">{renderFormattedText(log.correctedText || "")}</span>
            )}
            
            {log.type === "correction" && (
              <>
                <span className="original-text">{log.originalText}</span>
                <span className="arrow">→</span>
                <span className="corrected-text">{log.correctedText}</span>
              </>
            )}
          </div>
          
          {log.latencyMs > 0 && (
            <div className="log-latency">{log.latencyMs.toFixed(1)}ms</div>
          )}
        </div>
      ))}
    </div>
  );
};
