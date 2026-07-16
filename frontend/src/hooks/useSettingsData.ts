import { useState, useEffect } from "react";

export function useSettingsData() {
  const [settings, setSettings] = useState<any>({});
  const [dictionary, setDictionary] = useState<any[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
      const [setRes, dictRes, excRes, updateRes] = await Promise.all([
        fetch(`${getApiBase()}/settings?token=${getToken()}`),
        fetch(`${getApiBase()}/dictionary?token=${getToken()}`),
        fetch(`${getApiBase()}/exclusions?token=${getToken()}`),
        fetch(`${getApiBase()}/update/check?token=${getToken()}`)
      ]);
      setSettings(await setRes.json());
      setDictionary(await dictRes.json());
      setExclusions(await excRes.json());
      try { setUpdateInfo(await updateRes.json()); } catch(e) {}
      setLoading(false);
    } catch (err) {
      console.error("Failed to load settings data", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const updateSetting = async (key: string, value: any) => {
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

  const addDictWord = async (gibberish: string, correct: string) => {
    if (!gibberish || !correct) return;
    try {
      const res = await fetch(`${getApiBase()}/dictionary/add?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gibberish, correct })
      });
      setDictionary(await res.json());
    } catch (err) { console.error(err); }
  };

  const removeDictWord = async (gibberish: string) => {
    try {
      const res = await fetch(`${getApiBase()}/dictionary/remove?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gibberish })
      });
      setDictionary(await res.json());
    } catch (err) { console.error(err); }
  };

  const addExclusion = async (appName: string) => {
    if (!appName) return;
    try {
      const res = await fetch(`${getApiBase()}/exclusions/add?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name: appName })
      });
      setExclusions(await res.json());
    } catch (err) { console.error(err); }
  };

  const removeExclusion = async (appName: string) => {
    try {
      const res = await fetch(`${getApiBase()}/exclusions/remove?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name: appName })
      });
      setExclusions(await res.json());
    } catch (err) { console.error(err); }
  };

  const quitApp = async () => {
    try {
      await fetch(`${getApiBase()}/quit?token=${getToken()}`, { method: 'POST' });
    } catch (e) { console.error(e); }
  };

  const installUpdate = async (downloadUrl: string) => {
    try {
      await fetch(`${getApiBase()}/update/install?token=${getToken()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ download_url: downloadUrl })
      });
    } catch (err) { console.error("Update failed to trigger", err); }
  };

  return {
    loading,
    settings,
    dictionary,
    exclusions,
    updateSetting,
    addDictWord,
    removeDictWord,
    addExclusion,
    removeExclusion,
    quitApp,
    updateInfo,
    installUpdate
  };
}
