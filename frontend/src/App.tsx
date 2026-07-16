import { useState } from 'react';
import { useConsoleData } from './hooks/useConsoleData';
import { useSettingsData } from './hooks/useSettingsData';
import { Sidebar } from './components/Sidebar/Sidebar';
import { TitleBar } from './components/TitleBar/TitleBar';
import { DashboardView } from './views/DashboardView';
import { GeneralView } from './views/GeneralView';
import { HotkeysView } from './views/HotkeysView';
import { DictionaryView } from './views/DictionaryView';
import { ExclusionsView } from './views/ExclusionsView';
import { AdvancedView } from './views/AdvancedView';

function App() {
  const { logs, stats } = useConsoleData();
  const settingsData = useSettingsData();
  const [activeView, setActiveView] = useState('dashboard');

  return (
    <div id="app-root">
      <div style={{ gridArea: 'sidebar', borderRight: '1px solid var(--border-subtle)' }}>
        <Sidebar 
          activeView={activeView} 
          setActiveView={setActiveView} 
          appEnabled={settingsData.settings.app_enabled}
          onToggleEngine={() => settingsData.updateSetting('app_enabled', !settingsData.settings.app_enabled)}
          quitApp={settingsData.quitApp}
          hasUpdate={settingsData.updateInfo?.update_available}
        />
      </div>
      <div style={{ gridArea: 'title' }}>
        <TitleBar />
      </div>
      
      <div className="view-container">
        {activeView === 'dashboard' && <DashboardView logs={logs} stats={stats} />}
        {activeView === 'general' && <GeneralView {...settingsData} />}
        {activeView === 'hotkeys' && <HotkeysView {...settingsData} />}
        {activeView === 'dictionary' && <DictionaryView {...settingsData} />}
        {activeView === 'exclusions' && <ExclusionsView {...settingsData} />}
        {activeView === 'advanced' && <AdvancedView {...settingsData} />}
      </div>
    </div>
  );
}

export default App;
