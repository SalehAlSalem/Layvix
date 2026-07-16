import React from 'react';
import '../components/SettingsModal/SettingsModal.css';
import { HotkeyRecorder } from '../components/HotkeyRecorder/HotkeyRecorder';

interface Props {
  settings: any;
  updateSetting: (k: string, v: any) => void;
  loading: boolean;
}

export const HotkeysView: React.FC<Props> = ({ settings, updateSetting, loading }) => {
  if (loading) return null;
  
  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <h2>Keyboard Shortcuts</h2>
        <p className="settings-page-subtitle">Configure hotkeys to trigger actions instantly from anywhere in the OS.</p>
      </div>
      <div className="settings-header-separator" />
      
      <div className="settings-content-body" style={{ gap: '2rem' }}>
        
        {/* Correction Group */}
        <div>
          <h3 style={{ color: '#F0F0F0', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '1rem', paddingLeft: '4px' }}>
            Correction
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="hotkey-card">
              <div className="hotkey-card-info">
                <label className="settings-label">Undo Hotkey</label>
                <p className="settings-description">Reverts the last correction made by Layvix if you meant to type the gibberish.</p>
              </div>
              <div className="hotkey-card-control">
                <HotkeyRecorder 
                  value={settings.undo_hotkey} 
                  onChange={val => updateSetting('undo_hotkey', val)} 
                />
              </div>
            </div>
            
            <div className="hotkey-card">
              <div className="hotkey-card-info">
                <label className="settings-label">Manual Correction Hotkey</label>
                <p className="settings-description">Forces the AI to re-evaluate the sentence you just typed, even if it didn't trigger automatically.</p>
              </div>
              <div className="hotkey-card-control">
                <HotkeyRecorder 
                  value={settings.manual_hotkey} 
                  onChange={val => updateSetting('manual_hotkey', val)} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Interface Group */}
        <div>
          <h3 style={{ color: '#F0F0F0', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '1rem', paddingLeft: '4px' }}>
            Interface
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="hotkey-card">
              <div className="hotkey-card-info">
                <label className="settings-label">Overlay Hotkey</label>
                <p className="settings-description">Summons the Layvix control panel overlay directly to your screen.</p>
              </div>
              <div className="hotkey-card-control">
                <HotkeyRecorder 
                  value={settings.overlay_hotkey} 
                  onChange={val => updateSetting('overlay_hotkey', val)} 
                />
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
