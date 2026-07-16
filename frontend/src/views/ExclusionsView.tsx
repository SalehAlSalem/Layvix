import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/apiClient';

interface AppItem {
  name: string;
  exe: string;
  path: string;
  icon?: string;
}

interface Props {
  exclusions: string[];
  addExclusion: (app: string) => void;
  removeExclusion: (app: string) => void;
  loading: boolean;
}

export const ExclusionsView: React.FC<Props> = ({ exclusions, addExclusion, removeExclusion, loading }) => {
  const [installedApps, setInstalledApps] = useState<AppItem[]>([]);
  const [fetchingApps, setFetchingApps] = useState(false);
  const [isPicking, setIsPicking] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchApps = async () => {
    setFetchingApps(true);
    try {
      const data = await apiClient('/api/installed_apps');
      if (data && data.apps) {
        setInstalledApps(data.apps);
      }
    } catch (e) {
      console.error("Failed to fetch installed apps:", e);
    } finally {
      setFetchingApps(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, []);

  if (loading) return null;

  const startPicker = async () => {
    try {
      await apiClient('/api/exclusions/picker/start', { method: 'POST' });
      setIsPicking(true);

      const pollInterval = setInterval(async () => {
        try {
          const res = await apiClient('/api/exclusions/picker/status');
          if (!res.active) {
            clearInterval(pollInterval);
            setIsPicking(false);
            if (res.result && res.result !== 'unknown') {
              addExclusion(res.result);
            }
          }
        } catch (e) {
          console.error("Polling picker failed", e);
          clearInterval(pollInterval);
          setIsPicking(false);
        }
      }, 500);
    } catch (e) {
      console.error("Failed to start picker", e);
    }
  };

  const isExcluded = (exe: string) => exclusions.map(e => e.toLowerCase()).includes(exe.toLowerCase());

  const toggleApp = (app: AppItem) => {
    if (isExcluded(app.exe)) {
      removeExclusion(app.exe.toLowerCase());
    } else {
      addExclusion(app.exe.toLowerCase());
    }
  };

  const filteredApps = installedApps.filter(app => 
    app.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    app.exe.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group into Excluded and Available
  const excludedApps = filteredApps.filter(app => isExcluded(app.exe));
  const availableApps = filteredApps.filter(app => !isExcluded(app.exe));

  // Sort available apps by name
  excludedApps.sort((a, b) => a.name.localeCompare(b.name));
  availableApps.sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '32px', overflow: 'hidden' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>App Exclusions</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Select applications where Layvix should pause its tracking and correcting.</p>
      </div>
      
      {/* Magic Target */}
      <div style={{ 
        marginBottom: '24px', 
        background: 'rgba(255,255,255,0.03)', 
        padding: '20px', 
        borderRadius: '12px', 
        border: isPicking ? '1px solid var(--accent-success)' : '1px solid var(--border-subtle)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        backdropFilter: 'blur(10px)'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🎯</span> Magic Target
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>Click the button, then click on any window on your screen to exclude it instantly.</p>
        </div>
        <button 
          onClick={startPicker} 
          disabled={isPicking}
          style={{
            background: isPicking ? 'transparent' : '#ffffff',
            color: isPicking ? 'var(--accent-success)' : '#000000',
            border: isPicking ? '1px solid var(--accent-success)' : 'none',
            padding: '10px 20px',
            borderRadius: '24px',
            cursor: isPicking ? 'wait' : 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s ease',
          }}
        >
          {isPicking ? 'Click any window...' : 'Pick Window'}
        </button>
      </div>

      {/* Apps Browser */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }}>🔍</span>
            <input 
              type="text" 
              placeholder="Search installed apps..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 10px 10px 36px',
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: 'white',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>
          {fetchingApps && <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Scanning...</span>}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px', alignContent: 'start' }}>
          
          {/* Excluded Apps First */}
          {excludedApps.map(app => (
            <div key={app.path} style={{ 
              display: 'flex', alignItems: 'center', padding: '12px', 
              background: 'rgba(239, 68, 68, 0.1)', 
              border: '1px solid rgba(239, 68, 68, 0.3)', 
              borderRadius: '8px', transition: 'all 0.2s',
              cursor: 'pointer'
            }} onClick={() => toggleApp(app)}>
              {app.icon ? (
                <img src={app.icon} alt={app.name} style={{ width: '32px', height: '32px', marginRight: '12px', borderRadius: '4px' }} />
              ) : (
                <div style={{ width: '32px', height: '32px', marginRight: '12px', background: 'var(--border-subtle)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>EXE</div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: '500', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{app.name}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{app.exe}</div>
              </div>
              <div style={{ width: '20px', height: '20px', borderRadius: '4px', background: 'var(--accent-danger)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </div>
            </div>
          ))}

          {/* Available Apps */}
          {availableApps.map(app => (
            <div key={app.path} style={{ 
              display: 'flex', alignItems: 'center', padding: '12px', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-subtle)', 
              borderRadius: '8px', transition: 'all 0.2s',
              cursor: 'pointer'
            }} onClick={() => toggleApp(app)}
               onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
               onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
            >
              {app.icon ? (
                <img src={app.icon} alt={app.name} style={{ width: '32px', height: '32px', marginRight: '12px', borderRadius: '4px' }} />
              ) : (
                <div style={{ width: '32px', height: '32px', marginRight: '12px', background: 'var(--border-subtle)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>EXE</div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: '500', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{app.name}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{app.exe}</div>
              </div>
              <div style={{ width: '20px', height: '20px', borderRadius: '4px', border: '2px solid var(--text-secondary)', opacity: 0.5 }}>
              </div>
            </div>
          ))}

          {!fetchingApps && filteredApps.length === 0 && (
            <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No apps found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

