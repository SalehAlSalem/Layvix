import React, { useState } from 'react';
import '../components/SettingsModal/SettingsModal.css';

interface Props {
  dictionary: any[];
  addDictWord: (gibberish: string, correct: string) => void;
  removeDictWord: (gibberish: string) => void;
  loading: boolean;
}

export const DictionaryView: React.FC<Props> = ({ dictionary, addDictWord, removeDictWord, loading }) => {
  const [newGibberish, setNewGibberish] = useState('');
  const [newCorrect, setNewCorrect] = useState('');

  if (loading) return null;

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGibberish || !newCorrect) return;
    addDictWord(newGibberish, newCorrect);
    setNewGibberish('');
    setNewCorrect('');
  };
  
  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <h2>Custom Dictionary</h2>
        <p className="settings-page-subtitle">Teach Layvix how to correct your personal typos or specific jargon.</p>
      </div>
      <div className="settings-header-separator" />
      
      <div className="settings-content-body">
        <form className="dict-add-form" onSubmit={handleAdd}>
          <input 
            className="settings-input" 
            style={{flex:1}} 
            placeholder="Wrong word (e.g. teh)" 
            value={newGibberish} 
            onChange={e => setNewGibberish(e.target.value)} 
          />
          <input 
            className="settings-input" 
            style={{flex:1}} 
            placeholder="Correct word (e.g. the)" 
            value={newCorrect} 
            onChange={e => setNewCorrect(e.target.value)} 
          />
          <button type="submit" className="btn-primary">Add</button>
        </form>
        
        <div className="dict-list">
          {dictionary.map((item, i) => (
            <div key={i} className="dict-item">
              <span>{item.gibberish} <span className="dict-word">→</span> {item.correct}</span>
              <button className="dict-remove" onClick={() => removeDictWord(item.gibberish)}>&times;</button>
            </div>
          ))}
          {dictionary.length === 0 && (
            <div className="empty-state">
              <svg viewBox="0 0 24 24" fill="none" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              </svg>
              No custom words added yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
