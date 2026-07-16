import React from 'react';
import '../components/SettingsModal/SettingsModal.css';

interface Props {
  settings: any;
  updateSetting: (k: string, v: any) => void;
  quitApp: () => void;
  loading: boolean;
}

export const AdvancedView: React.FC<Props> = ({ settings, updateSetting, loading }) => {
  if (loading) return null;
  
  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <h2>Advanced</h2>
        <p className="settings-page-subtitle">Developer tools and diagnostic settings.</p>
      </div>
      <div className="settings-header-separator" />
      
      <div className="settings-content-body">
        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Black Box Mode (Developer Logs)</label>
            <p className="settings-description">Enables verbose system logging inside the Black Box console and writes diagnostic events to layvix.log. Keep this off to save resources unless you are troubleshooting.</p>
          </div>
          <div className="settings-toggle" onClick={() => updateSetting('blackbox_mode', !settings.blackbox_mode)}>
            <div className={`toggle-switch ${settings.blackbox_mode ? 'active' : ''}`}>
              <div className="toggle-thumb" />
            </div>
            <span>{settings.blackbox_mode ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Export Diagnostic Archive</label>
            <p className="settings-description">Download a ZIP file containing your logs, learned words, and performance stats to send to the developer.</p>
          </div>
          <button 
            className="add-exclusion-btn"
            style={{ minWidth: '120px' }}
            onClick={() => {
              const params = new URLSearchParams(window.location.search);
              const port = params.get('port') || '5000';
              const token = params.get('token') || '';
              window.open(`http://127.0.0.1:${port}/api/logs/export?token=${token}`, '_blank');
            }}
          >
            Export ZIP
          </button>
        </div>
      </div>
    </div>
  );
};
