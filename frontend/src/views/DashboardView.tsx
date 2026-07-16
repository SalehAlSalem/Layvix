import React from 'react';
import { ConsolePanel } from '../components/ConsolePanel/ConsolePanel';
import { StatsBar } from '../components/StatsBar/StatsBar';
import { ActivityStrip } from '../components/ActivityStrip/ActivityStrip';

interface DashboardViewProps {
  logs: any[];
  stats: any;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ logs, stats }) => {
  return (
    <div className="dashboard-grid">
      <div style={{ gridArea: 'stats', borderBottom: '1px solid var(--gray-dark)' }}>
        <StatsBar stats={stats} />
      </div>
      <div style={{ gridArea: 'console', overflow: 'hidden' }}>
        <ConsolePanel logs={logs} />
      </div>
      <div style={{ gridArea: 'activity', borderTop: '1px solid var(--gray-dark)' }}>
        <ActivityStrip wpmHistory={stats.wpmHistory} />
      </div>
    </div>
  );
};
