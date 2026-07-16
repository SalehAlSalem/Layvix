import React from "react";
import type { StatsSnapshot } from "../../types";
import "./StatsBar.css";

interface StatsBarProps {
  stats: StatsSnapshot;
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats }) => {
  return (
    <div className="stats-container">
      <div className="stat-item">
        <span className="stat-label">Corrections</span>
        <span className="stat-value">{stats.totalCorrections.toLocaleString()}</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Latency</span>
        <span className="stat-value">{stats.averageLatencyMs.toFixed(1)}ms</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Status</span>
        <span className="stat-value status-active">
          <div className="pulse-dot"></div>
          Active
        </span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Model</span>
        <span className="stat-value" style={{ fontSize: '1rem', color: '#8A8A9A' }}>
          {stats.modelInfo ? `v${stats.modelInfo.version} | ${stats.modelInfo.features} feat` : 'v4.0 | 124K feat'}
        </span>
      </div>
    </div>
  );
};
