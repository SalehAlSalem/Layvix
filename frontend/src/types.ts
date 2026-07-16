export type LogType = "info" | "correction" | "error";

export interface LogEntry {
  id: string;
  timestamp: number;
  type: LogType;
  originalText: string | null;
  correctedText: string | null;
  latencyMs: number;
}

export interface StatsSnapshot {
  totalCorrections: number;
  averageLatencyMs: number;
  wpmHistory: number[];
  modelInfo?: {
    version: string;
    features: string;
    samples: string;
  };
}

export interface AppState {
  isActive: boolean;
  logs: LogEntry[];
  stats: StatsSnapshot;
}
