import React, { useState, useEffect } from 'react';
import './SettingsModal.css';

interface SettingsModalProps {
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<any>({});
  const [dictionary, setDictionary] = useState<any[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const [newGibberish, setNewGibberish] = useState('');
  const [newCorrect, setNewCorrect] = useState('');
  const [newExclusion, setNewExclusion] = useState('');

  const getApiBase = () => {
    const params = new URLSearchParams(window.location.search);
    const port = params.get('port') || '5000';
    return `http://127.0.0.1:${port}/api`;
  };

  const getToken = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('token') || '';
  };

  const fetchData = async () => {
    try {
      const [setRes, dictRes, excRes] = await Promise.all([
        fetch(`${getApiBase()}/settings?token=${getToken()}`),
        fetch(`${getApiBase()}/dictionary?token=${getToken()}`),
        fetch(`${getApiBase()}/exclusions?token=${getToken()}`)
      ]);
      setSettings(await setRes.json());
      setDictionary(await dictRes.json());
      setExclusions(await excRes.json());
      setLoading(false);
    } catch (err) {
      console.error("Failed to load settings data", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpdate = async (key: string, value: any) => {
    setSettings((prev: any) => ({ ...prev, [key]: value }));
    try {
      await fetch(`${getApiBase()}/settings/update?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
      });
    } catch (err) {
      console.error("Update failed", err);
    }
  };

  const handleAddDict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGibberish || !newCorrect) return;
    try {
      const res = await fetch(`${getApiBase()}/dictionary/add?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gibberish: newGibberish, correct: newCorrect })
      });
      setDictionary(await res.json());
      setNewGibberish('');
      setNewCorrect('');
    } catch (err) { console.error(err); }
  };

  const handleRemoveDict = async (gibberish: string) => {
    try {
      const res = await fetch(`${getApiBase()}/dictionary/remove?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gibberish })
      });
      setDictionary(await res.json());
    } catch (err) { console.error(err); }
  };

  const handleAddExclusion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newExclusion) return;
    try {
      const res = await fetch(`${getApiBase()}/exclusions/add?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name: newExclusion })
      });
      setExclusions(await res.json());
      setNewExclusion('');
    } catch (err) { console.error(err); }
  };

  const handleRemoveExclusion = async (app_name: string) => {
    try {
      const res = await fetch(`${getApiBase()}/exclusions/remove?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name })
      });
      setExclusions(await res.json());
    } catch (err) { console.error(err); }
  };

  const handleQuit = async () => {
    try {
      await fetch(`${getApiBase()}/quit?token=${getToken()}`, { method: 'POST' });
    } catch (e) { console.error(e); }
  };

  if (loading) return null;

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-sidebar">
          <div className="settings-sidebar-header">Control Center</div>
          <div className={`settings-tab ${activeTab === 'general' ? 'active' : ''}`} onClick={() => setActiveTab('general')}>عام (General)</div>
          <div className={`settings-tab ${activeTab === 'hotkeys' ? 'active' : ''}`} onClick={() => setActiveTab('hotkeys')}>الاختصارات (Hotkeys)</div>
          <div className={`settings-tab ${activeTab === 'dictionary' ? 'active' : ''}`} onClick={() => setActiveTab('dictionary')}>القاموس (Dictionary)</div>
          <div className={`settings-tab ${activeTab === 'exclusions' ? 'active' : ''}`} onClick={() => setActiveTab('exclusions')}>الاستثناءات (Exclusions)</div>
          <div className={`settings-tab ${activeTab === 'advanced' ? 'active' : ''}`} onClick={() => setActiveTab('advanced')}>متقدم (Advanced)</div>
        </div>
        
        <div className="settings-content-wrapper">
          <div className="settings-content-header">
            <button className="settings-close" onClick={onClose}>&times;</button>
          </div>
          <div className="settings-content-body">
            
            {activeTab === 'general' && (
              <>
                <div className="settings-group">
                  <label className="settings-label">Engine Status</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('app_enabled', !settings.app_enabled)}>
                    <div className={`toggle-switch ${settings.app_enabled !== false ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.app_enabled !== false ? 'Active' : 'Paused'}</span>
                  </div>
                </div>

                <div className="settings-group">
                  <label className="settings-label">Retroactive Correction</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('retroactive_correction', !settings.retroactive_correction)}>
                    <div className={`toggle-switch ${settings.retroactive_correction !== false ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.retroactive_correction !== false ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>

                <div className="settings-group">
                  <label className="settings-label">Auto Switch Language</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('auto_switch_language', !settings.auto_switch_language)}>
                    <div className={`toggle-switch ${settings.auto_switch_language !== false ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.auto_switch_language !== false ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>

                <div className="settings-group">
                  <label className="settings-label">Run on Startup</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('run_on_startup', !settings.run_on_startup)}>
                    <div className={`toggle-switch ${settings.run_on_startup ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.run_on_startup ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'hotkeys' && (
              <>
                <div className="settings-group">
                  <label className="settings-label">Undo Hotkey</label>
                  <input 
                    className="settings-input" 
                    value={settings.undo_hotkey || ''} 
                    onChange={e => handleUpdate('undo_hotkey', e.target.value)}
                  />
                </div>
                <div className="settings-group">
                  <label className="settings-label">Manual Correction Hotkey</label>
                  <input 
                    className="settings-input" 
                    value={settings.manual_hotkey || ''} 
                    onChange={e => handleUpdate('manual_hotkey', e.target.value)}
                  />
                </div>
                <div className="settings-group">
                  <label className="settings-label">Overlay Hotkey</label>
                  <input 
                    className="settings-input" 
                    value={settings.overlay_hotkey || ''} 
                    onChange={e => handleUpdate('overlay_hotkey', e.target.value)}
                  />
                </div>
              </>
            )}

            {activeTab === 'dictionary' && (
              <>
                <form className="dict-add-form" onSubmit={handleAddDict}>
                  <input className="settings-input" style={{flex:1}} placeholder="Wrong word (e.g. teh)" value={newGibberish} onChange={e => setNewGibberish(e.target.value)} />
                  <input className="settings-input" style={{flex:1}} placeholder="Correct word (e.g. the)" value={newCorrect} onChange={e => setNewCorrect(e.target.value)} />
                  <button type="submit" className="btn-primary">Add</button>
                </form>
                <div className="dict-list">
                  {dictionary.map((item, i) => (
                    <div key={i} className="dict-item">
                      <span>{item.gibberish} <span className="dict-word">→</span> {item.correct}</span>
                      <button className="dict-remove" onClick={() => handleRemoveDict(item.gibberish)}>&times;</button>
                    </div>
                  ))}
                  {dictionary.length === 0 && <div style={{color:'var(--gray-light)'}}>No custom words added yet.</div>}
                </div>
              </>
            )}

            {activeTab === 'exclusions' && (
              <>
                <form className="dict-add-form" onSubmit={handleAddExclusion}>
                  <input className="settings-input" style={{flex:1}} placeholder="App Name (e.g. code.exe)" value={newExclusion} onChange={e => setNewExclusion(e.target.value)} />
                  <button type="submit" className="btn-primary">Add</button>
                </form>
                <div className="dict-list">
                  {exclusions.map((app, i) => (
                    <div key={i} className="dict-item">
                      <span>{app}</span>
                      <button className="dict-remove" onClick={() => handleRemoveExclusion(app)}>&times;</button>
                    </div>
                  ))}
                  {exclusions.length === 0 && <div style={{color:'var(--gray-light)'}}>No excluded apps.</div>}
                </div>
              </>
            )}

            {activeTab === 'advanced' && (
              <>
                <div className="settings-group">
                  <label className="settings-label">Show Floating Bubble</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('show_floating_bubble', !settings.show_floating_bubble)}>
                    <div className={`toggle-switch ${settings.show_floating_bubble !== false ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.show_floating_bubble !== false ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>

                <div className="settings-group">
                  <label className="settings-label">Black Box Mode (Debug Logs)</label>
                  <div className="settings-toggle" onClick={() => handleUpdate('blackbox_mode', !settings.blackbox_mode)}>
                    <div className={`toggle-switch ${settings.blackbox_mode ? 'active' : ''}`}>
                      <div className="toggle-thumb" />
                    </div>
                    <span>{settings.blackbox_mode ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>

                <div className="settings-group danger-zone">
                  <label className="settings-label" style={{color: '#ff4444'}}>Danger Zone</label>
                  <p style={{color: 'var(--gray-light)', fontSize: '0.9rem', marginBottom: '1rem'}}>
                    Quitting the application will stop all automatic corrections and background monitoring.
                  </p>
                  <button className="danger-btn" onClick={handleQuit}>Quit Layvix</button>
                </div>
              </>
            )}

          </div>
        </div>
      </div>
    </div>
  );
};
