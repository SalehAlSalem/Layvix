import React from 'react';
import '../components/SettingsModal/SettingsModal.css';

interface Props {
  settings: any;
  updateSetting: (k: string, v: any) => void;
  loading: boolean;
  updateInfo?: any;
  installUpdate?: (url: string) => void;
}

export const GeneralView: React.FC<Props> = ({ settings, updateSetting, loading, updateInfo, installUpdate }) => {
  if (loading) return null;
  
  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <h2>General Settings</h2>
        <p className="settings-page-subtitle">Manage core engine behaviors and startup preferences.</p>
      </div>
      <div className="settings-header-separator" />
      
      <div className="settings-content-body">
        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Retroactive Correction</label>
            <p className="settings-description">Automatically correct text that was already typed if the context changes.</p>
          </div>
          <div className="settings-toggle" onClick={() => updateSetting('retroactive_correction', !settings.retroactive_correction)}>
            <div className={`toggle-switch ${settings.retroactive_correction !== false ? 'active' : ''}`}>
              <div className="toggle-thumb" />
            </div>
            <span>{settings.retroactive_correction !== false ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Auto Switch Language</label>
            <p className="settings-description">Detect when you are typing English with an Arabic layout (and vice versa) and automatically switch the system keyboard layout.</p>
          </div>
          <div className="settings-toggle" onClick={() => updateSetting('auto_switch_language', !settings.auto_switch_language)}>
            <div className={`toggle-switch ${settings.auto_switch_language !== false ? 'active' : ''}`}>
              <div className="toggle-thumb" />
            </div>
            <span>{settings.auto_switch_language !== false ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Run on Startup</label>
            <p className="settings-description">Launch Layvix automatically silently in the background when your computer boots.</p>
          </div>
          <div className="settings-toggle" onClick={() => updateSetting('run_on_startup', !settings.run_on_startup)}>
            <div className={`toggle-switch ${settings.run_on_startup ? 'active' : ''}`}>
              <div className="toggle-thumb" />
            </div>
            <span>{settings.run_on_startup ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="settings-group">
          <div className="settings-label-wrapper">
            <label className="settings-label">Software Update</label>
            <p className="settings-description">
              Current version: v{updateInfo?.current_version || '...' }
              {updateInfo?.update_available && (
                <span style={{ color: '#ff4444', marginLeft: '10px', fontWeight: 'bold' }}>
                  v{updateInfo.latest_version} is available!
                </span>
              )}
              {updateInfo?.error && (
                <span style={{ color: '#ffaaaa', marginLeft: '10px' }}>
                  (Check failed)
                </span>
              )}
            </p>
          </div>
          <div>
            {updateInfo?.update_available ? (
              <button 
                className="btn primary" 
                onClick={() => {
                  if (installUpdate && updateInfo.download_url) {
                    installUpdate(updateInfo.download_url);
                  }
                }}
              >
                Install Update
              </button>
            ) : (
              <span style={{ opacity: 0.6 }}>Up to date</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
