import React from 'react';
import './TitleBar.css';

export const TitleBar: React.FC = () => {
  const getApiBase = () => {
    const params = new URLSearchParams(window.location.search);
    const port = params.get('port') || '5000';
    return `http://127.0.0.1:${port}/api`;
  };

  const getToken = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('token') || '';
  };

  const handleMinimize = async () => {
    try {
      await fetch(`${getApiBase()}/window/minimize?token=${getToken()}`, { method: 'POST' });
    } catch (e) {
      console.error('Minimize failed', e);
    }
  };

  const handleClose = async () => {
    try {
      await fetch(`${getApiBase()}/window/hide?token=${getToken()}`, { method: 'POST' });
    } catch (e) {
      console.error('Hide failed', e);
    }
  };

  return (
    <div className="titlebar-container">
      <div className="titlebar-controls">
        <button className="titlebar-btn" onClick={handleMinimize} aria-label="Minimize">
          <svg className="titlebar-icon" viewBox="0 0 12 12">
            <line x1="1" y1="6" x2="11" y2="6" />
          </svg>
        </button>
        <button className="titlebar-btn close" onClick={handleClose} aria-label="Close">
          <svg className="titlebar-icon" viewBox="0 0 12 12">
            <line x1="2" y1="2" x2="10" y2="10" />
            <line x1="2" y1="10" x2="10" y2="2" />
          </svg>
        </button>
      </div>
    </div>
  );
};
