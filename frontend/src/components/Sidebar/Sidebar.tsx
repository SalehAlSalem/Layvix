import React from "react";
import { SidebarLogo } from "../SidebarLogo/SidebarLogo";
import type { AppStatus } from "../SidebarLogo/SidebarLogo";
import "./Sidebar.css";

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  appEnabled: boolean;
  onToggleEngine: () => void;
  quitApp?: () => void;
  hasUpdate?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeView, setActiveView, appEnabled, onToggleEngine, quitApp, hasUpdate }) => {
  const isEnabled = appEnabled !== false;
  
  // Map our simple state to the required AppStatus
  const appStatus: AppStatus = isEnabled ? 'active' : 'paused';
  
  return (
    <nav className="sidebar-container">
      <div className="sidebar-top-group">
        <div 
          className="logo-wrapper"
          onClick={() => setActiveView('dashboard')}
          data-tooltip="Dashboard"
        >
          <SidebarLogo status={appStatus} />
        </div>

        <button 
          className={`power-btn ${isEnabled ? 'engine-active' : 'engine-paused'}`}
          onClick={onToggleEngine}
          data-tooltip={isEnabled ? "Engine Active (Pause)" : "Engine Paused (Resume)"}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
            <line x1="12" y1="2" x2="12" y2="12"></line>
          </svg>
        </button>
      </div>

      <div className="sidebar-separator" />

      <div className="sidebar-nav">
        <button 
          className={`nav-btn ${activeView === 'dashboard' ? 'active' : ''}`} 
          onClick={() => setActiveView('dashboard')}
          data-tooltip="Dashboard"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        </button>

        <button 
          className={`nav-btn ${activeView === 'general' ? 'active' : ''}`} 
          onClick={() => setActiveView('general')}
          data-tooltip="General Settings"
          style={{ position: 'relative' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          {hasUpdate && (
            <span style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              width: '8px',
              height: '8px',
              backgroundColor: '#ff4444',
              borderRadius: '50%',
              boxShadow: '0 0 4px #ff4444'
            }} />
          )}
        </button>

        <button 
          className={`nav-btn ${activeView === 'hotkeys' ? 'active' : ''}`} 
          onClick={() => setActiveView('hotkeys')}
          data-tooltip="Hotkeys"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><line x1="8" y1="10" x2="8" y2="10"></line><line x1="12" y1="10" x2="12" y2="10"></line><line x1="16" y1="10" x2="16" y2="10"></line><line x1="8" y1="14" x2="16" y2="14"></line></svg>
        </button>

        <button 
          className={`nav-btn ${activeView === 'dictionary' ? 'active' : ''}`} 
          onClick={() => setActiveView('dictionary')}
          data-tooltip="Dictionary"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
        </button>

        <button 
          className={`nav-btn ${activeView === 'exclusions' ? 'active' : ''}`} 
          onClick={() => setActiveView('exclusions')}
          data-tooltip="Exclusions"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        </button>
      </div>

      <div className="settings-btn-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button 
          className={`nav-btn ${activeView === 'advanced' ? 'active' : ''}`} 
          onClick={() => setActiveView('advanced')} 
          data-tooltip="Advanced Settings"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
        </button>

        {quitApp && (
          <button 
            className="nav-btn quit-btn" 
            onClick={quitApp} 
            data-tooltip="Quit Layvix completely"
            style={{ color: '#E74C3C' }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        )}
      </div>
    </nav>
  );
};

