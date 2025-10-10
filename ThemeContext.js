// ThemeContext.js (of bovenaan in App.js plaatsen)
import React, { createContext, useMemo, useEffect, useState, useCallback } from 'react';
import * as SecureStore from 'expo-secure-store';
import { useColorScheme } from 'react-native';

export const ThemeContext = createContext(null);

const STORE_KEYS = {
  MODE: 'pref_theme_mode',        // 'system' | 'light' | 'dark'
  PRESET: 'pref_theme_preset',    // 'ios' | 'whatsapp'
};

// Kleurenpaletten per preset+mode
const PALETTES = {
  ios: {
    light: {
      bubbleMeBg: '#0A84FF',
      bubbleMeBorder: 'rgba(255,255,255,0.35)',
      bubbleThemBg: '#E5E5EA',
      bubbleThemBorder: 'rgba(0,0,0,0.06)',
      bubbleMeText: '#FFFFFF',
      bubbleThemText: '#111111',
      bubbleMeTime: 'rgba(255,255,255,0.85)',
      bubbleThemTime: '#6E6E73',
      tailThemBorder: 'rgba(0,0,0,0.06)',
    },
    dark: {
      bubbleMeBg: '#0A84FF',
      bubbleMeBorder: 'rgba(255,255,255,0.35)',
      bubbleThemBg: '#2C2C2E',
      bubbleThemBorder: 'rgba(255,255,255,0.10)',
      bubbleMeText: '#FFFFFF',
      bubbleThemText: '#FFFFFF',
      bubbleMeTime: 'rgba(255,255,255,0.85)',
      bubbleThemTime: 'rgba(255,255,255,0.75)',
      tailThemBorder: 'rgba(255,255,255,0.10)',
    },
  },
  whatsapp: {
    light: {
      bubbleMeBg: '#25D366',           // WA green
      bubbleMeBorder: 'rgba(0,0,0,0.06)',
      bubbleThemBg: '#F0F2F5',         // WA list bg-ish
      bubbleThemBorder: 'rgba(0,0,0,0.06)',
      bubbleMeText: '#0B1A12',
      bubbleThemText: '#111111',
      bubbleMeTime: 'rgba(0,0,0,0.55)',
      bubbleThemTime: '#6E6E73',
      tailThemBorder: 'rgba(0,0,0,0.06)',
    },
    dark: {
      bubbleMeBg: '#005C4B',           // WA dark outgoing
      bubbleMeBorder: 'rgba(255,255,255,0.08)',
      bubbleThemBg: '#202C33',
      bubbleThemBorder: 'rgba(255,255,255,0.06)',
      bubbleMeText: '#E7F5EF',
      bubbleThemText: '#E8EDEF',
      bubbleMeTime: 'rgba(231,245,239,0.75)',
      bubbleThemTime: 'rgba(232,237,239,0.70)',
      tailThemBorder: 'rgba(255,255,255,0.06)',
    },
  },
};

// makeTheme dat je bestaande tokens uitbreidt met chat-preset kleuren
export function useTheming(makeBaseTheme) {
  const osScheme = useColorScheme(); // 'dark'|'light'|null
  const [mode, setMode] = useState('system');      // 'system' | 'light' | 'dark'
  const [preset, setPreset] = useState('ios');     // 'ios' | 'whatsapp'

  // bij start voorkeuren laden
  useEffect(() => {
    (async () => {
      const m = await SecureStore.getItemAsync(STORE_KEYS.MODE);
      const p = await SecureStore.getItemAsync(STORE_KEYS.PRESET);
      if (m) setMode(m);
      if (p) setPreset(p);
    })();
  }, []);

  const effectiveMode = mode === 'system' ? (osScheme === 'dark' ? 'dark' : 'light') : mode;
  const baseTheme = useMemo(() => makeBaseTheme(effectiveMode), [effectiveMode, makeBaseTheme]);

  const chatPalette = PALETTES[preset][effectiveMode];
  const theme = useMemo(() => ({
    ...baseTheme,
    preset,
    chat: {
      ...chatPalette,
      // staartjes (mogen meeschalen met palette)
      tailMeBorder: chatPalette.bubbleMeBorder,
      tailMeFill: chatPalette.bubbleMeBg,
      tailThemFill: chatPalette.bubbleThemBg,
    }
  }), [baseTheme, preset, chatPalette]);

  const setUserMode = useCallback(async (m) => {
    setMode(m);
    await SecureStore.setItemAsync(STORE_KEYS.MODE, m);
  }, []);
  const setUserPreset = useCallback(async (p) => {
    setPreset(p);
    await SecureStore.setItemAsync(STORE_KEYS.PRESET, p);
  }, []);

  return { theme, mode, setUserMode, preset, setUserPreset };
}

export function ThemeProvider({ makeBaseTheme, children }) {
  const value = useTheming(makeBaseTheme);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
