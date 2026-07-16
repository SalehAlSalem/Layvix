import React, { useState, useEffect, useRef } from 'react';
import './HotkeyRecorder.css';

interface Props {
  value: string;
  onChange: (hotkey: string) => void;
}

export const HotkeyRecorder: React.FC<Props> = ({ value, onChange }) => {
  const [recording, setRecording] = useState(false);
  const [displayValue, setDisplayValue] = useState(value);
  const [justSaved, setJustSaved] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!recording) {
      setDisplayValue(value);
    }
  }, [value, recording]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!recording) return;
      e.preventDefault();

      // Don't record standalone modifier keys, wait for a non-modifier
      if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
        return;
      }

      const keys: string[] = [];
      if (e.ctrlKey) keys.push('ctrl');
      if (e.altKey) keys.push('alt');
      if (e.shiftKey) keys.push('shift');
      
      let keyName = e.key.toLowerCase();
      // Handle special cases
      if (keyName === ' ') keyName = 'space';
      
      keys.push(keyName);
      
      const hotkeyString = keys.join('+');
      onChange(hotkeyString);
      setRecording(false);
      
      // Trigger subtle green flash transition
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 600);
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setRecording(false);
      }
    };

    if (recording) {
      window.addEventListener('keydown', handleKeyDown);
      window.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousedown', handleClickOutside);
    };
  }, [recording, onChange]);

  const renderKeys = () => {
    if (!displayValue && !recording) return <span className="hotkey-unassigned">Not assigned</span>;
    if (recording) return <span className="hotkey-listening">Listening for input...</span>;

    const parts = displayValue.split('+');
    return (
      <div className={`hotkey-keys-wrapper ${justSaved ? 'saved-flash' : ''}`}>
        {parts.map((part, index) => (
          <React.Fragment key={index}>
            <span className="hotkey-key-pill">{part.charAt(0).toUpperCase() + part.slice(1)}</span>
            {index < parts.length - 1 && <span className="hotkey-key-separator">+</span>}
          </React.Fragment>
        ))}
      </div>
    );
  };

  return (
    <div className="hotkey-recorder-group" ref={containerRef}>
      <div className="hotkey-display">
        {renderKeys()}
      </div>
      <button 
        className="hotkey-edit-btn" 
        onClick={() => setRecording(!recording)}
      >
        {recording ? 'Cancel' : 'Edit'}
      </button>
    </div>
  );
};
