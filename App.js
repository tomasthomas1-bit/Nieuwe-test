
/* eslint-disable react-native/no-unused-styles */
// ==== App.js ====
import 'react-native-gesture-handler';
import React, {
  useMemo,
  useState,
  useEffect,
  useCallback,
  useContext,
  createContext,
} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  Platform,
  useColorScheme,
  Image,
  Switch,
} from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import {
  useFonts,
  Montserrat_400Regular,
  Montserrat_600SemiBold,
  Montserrat_700Bold,
} from '@expo-google-fonts/montserrat';
import * as SecureStore from 'expo-secure-store';

/* ================= THEME CONTEXT ================= */
const ThemeContext = createContext(null);
const STORE_KEYS = { MODE: 'pref_theme_mode', PRESET: 'pref_theme_preset' };
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
      bubbleMeBg: '#25D366',
      bubbleMeBorder: 'rgba(0,0,0,0.06)',
      bubbleThemBg: '#F0F2F5',
      bubbleThemBorder: 'rgba(0,0,0,0.06)',
      bubbleMeText: '#0B1A12',
      bubbleThemText: '#111111',
      bubbleMeTime: 'rgba(0,0,0,0.55)',
      bubbleThemTime: '#6E6E73',
      tailThemBorder: 'rgba(0,0,0,0.06)',
    },
    dark: {
      bubbleMeBg: '#005C4B',
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

function useTheming(makeBaseTheme) {
  const osScheme = useColorScheme();
  const [mode, setMode] = useState('system');
  const [preset, setPreset] = useState('ios');

  useEffect(() => {
    (async () => {
      try {
        const m = await SecureStore.getItemAsync(STORE_KEYS.MODE);
        const p = await SecureStore.getItemAsync(STORE_KEYS.PRESET);
        if (m) setMode(m);
        if (p) setPreset(p);
      } catch (e) {
        if (__DEV__) console.debug('Theme prefs not available', e);
      }
    })();
  }, []);

  const effectiveMode =
    mode === 'system'
      ? osScheme === 'dark'
        ? 'dark'
        : 'light'
      : mode === 'dark'
      ? 'dark'
      : 'light';

  const safePreset = PALETTES[preset] ? preset : 'ios';
  const safeMode = effectiveMode === 'dark' ? 'dark' : 'light';

  const baseTheme = useMemo(
    () => makeBaseTheme(safeMode),
    [makeBaseTheme, safeMode]
  );

  const theme = useMemo(() => {
    const chatPalette = PALETTES[safePreset][safeMode];
    return {
      ...baseTheme,
      preset: safePreset,
      chat: {
        ...chatPalette,
        tailMeBorder: chatPalette.bubbleMeBorder,
        tailMeFill: chatPalette.bubbleMeBg,
        tailThemFill: chatPalette.bubbleThemBg,
      },
    };
  }, [baseTheme, safePreset, safeMode]);

  const setUserMode = useCallback(async (m) => {
    setMode(m);
    try {
      await SecureStore.setItemAsync(STORE_KEYS.MODE, m);
    } catch (e) {
      if (__DEV__) console.debug('Persist theme mode failed', e);
    }
  }, []);

  const setUserPreset = useCallback(async (p) => {
    setPreset(p);
    try {
      await SecureStore.setItemAsync(STORE_KEYS.PRESET, p);
    } catch (e) {
      if (__DEV__) console.debug('Persist theme preset failed', e);
    }
  }, []);

  return { theme, mode, setUserMode, preset, setUserPreset };
}

function ThemeProvider({ makeBaseTheme, children }) {
  const value = useTheming(makeBaseTheme);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/* ================= TOKENS ================= */
const TOKENS = {
  light: {
    color: {
      primary: '#007BFF',
      onPrimary: '#FFFFFF',
      secondary: '#32D74B',
      accent: '#FF6B35',
      background: '#F2F2F7',
      surface: '#FFFFFF',
      textPrimary: '#0C0C0D',
      textSecondary: '#6E6E73',
      divider: 'rgba(0,0,0,0.08)',
      overlay: 'rgba(0,0,0,0.6)',
    },
  },
  dark: {
    color: {
      primary: '#007BFF',
      onPrimary: '#FFFFFF',
      secondary: '#32D74B',
      accent: '#FF6B35',
      background: '#1C1C1E',
      surface: '#2A2A2D',
      textPrimary: '#FFFFFF',
      textSecondary: 'rgba(255,255,255,0.72)',
      divider: 'rgba(255,255,255,0.12)',
      overlay: 'rgba(0,0,0,0.6)',
    },
  },
  radius: { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 },
  spacing: { 8: 8, 12: 12, 16: 16, 24: 24, 32: 32 },
  elevation1: { ios: { y: 2, blur: 8, opacity: 0.08 }, android: 2 },
  elevation2: { ios: { y: 6, blur: 24, opacity: 0.10 }, android: 4 },
  navbar: { height: 64, iconSize: 24 },
  chip: { bgAlpha: 0.12 },
};

const shadow = (lvl) =>
  Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOpacity: lvl.ios.opacity,
      shadowRadius: lvl.ios.blur / 2,
      shadowOffset: { width: 0, height: lvl.ios.y },
    },
    android: { elevation: lvl.android },
  });

const makeBaseTheme = (mode) => {
  const c = TOKENS[mode].color;
  const r = TOKENS.radius;
  const s = TOKENS.spacing;
  return {
    mode,
    color: {
      ...c,
      success: '#32D74B',
      danger: '#EF4444',
      warning: '#F59E0B',
      border: c.divider,
      chipBg: 'rgba(50,215,75,0.12)',
    },
    font: {
      headingFamily: 'Montserrat_600SemiBold',
      bodyFamily: 'Montserrat_400Regular',
      bodySemibold: 'Montserrat_600SemiBold',
      bodyBold: 'Montserrat_700Bold',
      size: { xs: 12, sm: 14, md: 16, lg: 18, xl: 24, x2: 32, x3: 40 },
    },
    radius: r,
    space: (px) => px,
    gap: { s: s[8], m: s[16], l: s[24], xl: s[32] },
    shadow1: shadow(TOKENS.elevation1),
    shadow2: shadow(TOKENS.elevation2),
    navbar: TOKENS.navbar,
    gradient: { pulse: { from: c.primary, to: c.secondary } },
  };
};

/* ================= API HOOK ================= */
const BASE_URL = 'https://web-production-ec0bc.up.railway.app';
function useApi() {
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState(null);
  const [profileVersion, setProfileVersion] = useState(0);

  const notifyProfilePhotoChanged = useCallback(() => {
    setProfileVersion((v) => v + 1);
  }, []);

  // Token uit SecureStore lezen bij start
  useEffect(() => {
    (async () => {
      try {
        const stored = await SecureStore.getItemAsync('access_token');
        if (stored) {
          setToken(stored);
          setIsAuthenticated(true);
        }
      } catch (e) {
        console.warn('Token laden mislukt:', e);
      }
    })();
  }, []);

  // Fetch helper met Bearer + 401-afhandeling
  const authFetch = useCallback(
    async (path, options = {}) => {
      const headers = {
        ...(options.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
      if (res.status === 401) {
        try {
          await SecureStore.deleteItemAsync('access_token');
        } catch (e) {
          if (__DEV__) console.debug('SecureStore delete failed', e);
        }
        setToken(null);
        setIsAuthenticated(false);
        setUserId(null);
        Alert.alert('Sessie verlopen', 'Log opnieuw in a.u.b.');
      }
      return res;
    },
    [token]
  );

  // /me ophalen om userId te zetten
  const fetchMe = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authFetch('/me');
      const data = await res.json().catch(() => null);
      if (res.ok && data?.id) setUserId(data.id);
    } catch (e) {
      if (__DEV__) console.debug('fetchMe failed', e);
    }
  }, [token, authFetch]);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  // Inloggen
  const login = useCallback(
    async (username, password) => {
      const body = 'username=' + encodeURIComponent(username) +
                   '&password=' + encodeURIComponent(password);
      const res = await fetch(`${BASE_URL}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      const data = await res.json().catch(() => null);
      if (res.ok && data && data.access_token) {
        setToken(data.access_token);
        setIsAuthenticated(true);
        try { await SecureStore.setItemAsync('access_token', data.access_token); }
        catch (e) { if (__DEV__) console.debug('Persist token failed', e); }
        try { await fetchMe(); } catch (e) { if (__DEV__) console.debug('fetchMe after login failed', e); }
        return { ok: true };
      }
      const errMsg = data && data.detail ? data.detail : 'Login mislukt';
      return { ok: false, error: errMsg };
    },
    [fetchMe]
  );

  // Registreren
  const register = useCallback(async (payload) => {
    const res = await fetch(`${BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { ok: false, error: data?.detail ?? 'Registratie mislukt' };
    }
    return { ok: true, data };
  }, []);

  // Uitloggen
  const logout = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync('access_token');
    } catch (e) {
      if (__DEV__) console.debug('SecureStore delete failed', e);
    }
    setToken(null);
    setIsAuthenticated(false);
    setUserId(null);
  }, []);

  // Profiel helpers
  const getProfile = useCallback(async () => {
    const res = await authFetch('/me');
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(data?.detail ?? `Profiel laden mislukt (status ${res.status})`);
    return data; // { id, username, name, age, bio }
  }, [authFetch]);

  const updateProfile = useCallback(async (partial) => {
    const uid = userId;
    if (!uid) throw new Error('Geen userId beschikbaar');
    const res = await authFetch(`/users/${uid}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(partial),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(data?.detail ?? `Profiel opslaan mislukt (status ${res.status})`);
    return data;
  }, [authFetch, userId]);

  return {
    token, isAuthenticated, userId,
    authFetch, login, register, logout,
    getProfile, updateProfile,
    profileVersion, notifyProfilePhotoChanged,
  };
}

/* ================= REUSABLE: LogoBox ================= */
function LogoBox({ theme, uri, size = 120 }) {
  const styles = StyleSheet.create({
    logoBox: {
      width: size,
      height: size,
      alignSelf: 'center',
      marginBottom: 24,
      backgroundColor: theme.color.surface,
      borderRadius: 0,
      borderWidth: 0,
      borderColor: 'transparent',
      justifyContent: 'center',
      alignItems: 'center',
    },
    logoImage: {
      width: '100%',
      height: '100%',
      resizeMode: 'contain',
      borderRadius: 0,
      backgroundColor: 'transparent',
    },
  });

  return (
    <View style={styles.logoBox}>
      <Image source={{ uri }} style={styles.logoImage} />
    </View>
  );
}

/* ================= SCREENS ================= */
const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

/* ---- AuthScreen ---- */
function AuthScreen({ navigation, api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    username: '',
    name: '',
    age: '',
    bio: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleLogin = useCallback(async () => {
    const { ok, error } = await api.login(form.username, form.password);
    if (ok) {
      Alert.alert('Login gelukt', 'Je bent ingelogd.');
      navigation.reset({ index: 0, routes: [{ name: 'Main' }] });
    } else {
      Alert.alert('Login mislukt', error);
    }
  }, [api, form.username, form.password, navigation]);

  const handleRegister = useCallback(async () => {
    const e = {};
    ['username', 'name', 'age', 'password'].forEach((r) => {
      if (!form[r] || String(form[r]).trim() === '') e[r] = 'Verplicht veld';
    });
    const ageNum = parseInt(form.age, 10);
    if (isNaN(ageNum) || ageNum < 18 || ageNum > 99) e.age = 'Leeftijd moet tussen 18 en 99 zijn';
    if ((form.password ?? '').length < 8) e.password = 'Minimaal 8 karakters';
    setErrors(e);
    if (Object.keys(e).length) return;

    const { ok, error } = await api.register({
      username: form.username,
      name: form.name,
      age: ageNum,
      bio: form.bio,
      password: form.password,
    });
    if (!ok) return Alert.alert('Registratie mislukt', error);
    Alert.alert('Registratie gelukt', 'Account is aangemaakt.');
    await handleLogin();
  }, [api, form, handleLogin]);

  const LOGO_TRANSPARENT = 'https://i.imgur.com/hEpZh82.png';
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.color.surface }}>
      <ScrollView contentContainerStyle={styles.authContainer}>
        <LogoBox theme={theme} uri={LOGO_TRANSPARENT} size={120} />
        <Text style={styles.authTitle}>{isLogin ? 'Inloggen' : 'Registreren'}</Text>

        <TextInput
          style={styles.input}
          placeholder="Gebruikersnaam"
          value={form.username}
          onChangeText={(v) => set('username', v)}
          autoCapitalize="none"
          placeholderTextColor={theme.color.textSecondary}
        />
        {errors.username ? <Text style={styles.error}>{errors.username}</Text> : null}

        {!isLogin ? (
          <>
            <TextInput
              style={styles.input}
              placeholder="Naam"
              value={form.name}
              onChangeText={(v) => set('name', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
            {errors.name ? <Text style={styles.error}>{errors.name}</Text> : null}

            <TextInput
              style={styles.input}
              placeholder="Leeftijd"
              keyboardType="numeric"
              value={form.age}
              onChangeText={(v) => set('age', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
            {errors.age ? <Text style={styles.error}>{errors.age}</Text> : null}

            <TextInput
              style={styles.input}
              placeholder="Bio"
              value={form.bio}
              onChangeText={(v) => set('bio', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
          </>
        ) : null}

        <TextInput
          style={styles.input}
          placeholder="Wachtwoord"
          secureTextEntry
          autoCapitalize="none"
          value={form.password}
          onChangeText={(v) => set('password', v)}
          placeholderTextColor={theme.color.textSecondary}
        />
        {errors.password ? <Text style={styles.error}>{errors.password}</Text> : null}

        <TouchableOpacity onPress={isLogin ? handleLogin : handleRegister} style={styles.primaryBtn}>
          <Text style={styles.primaryBtnText}>{isLogin ? 'Inloggen' : 'Registreren'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setIsLogin(!isLogin)} style={{ marginTop: theme.gap.m }}>
          <Text style={styles.switchText}>
            {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

/* ---- DiscoverScreen ---- */
function DiscoverScreen({ api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [photoIdxById, setPhotoIdxById] = useState({}); // { [userId]: number }

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.authFetch('/suggestions');
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setSuggestions(Array.isArray(data?.suggestions) ? data.suggestions : []);
      if (!data?.suggestions?.length) {
        Alert.alert('Suggesties', 'Geen suggesties gevonden. Maak een tweede testuser en probeer opnieuw.');
      }
    } catch (e) {
      Alert.alert('Fout bij ophalen suggesties', e.message);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const doSwipe = useCallback(async (id, liked) => {
    try {
      setLoading(true);
      const res = await api.authFetch(`/swipe/${id}?liked=${liked ? 'true' : 'false'}`, { method: 'POST' });
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      Alert.alert('Swipe', data?.message ?? (liked ? 'Geliked' : 'Geschipt'));
      await load();
    } catch (e) {
      Alert.alert('Fout bij swipen', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, load]);

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <View style={styles.rowBetween}>
        <Text style={styles.sectionTitle}>Ontdekken</Text>
        <TouchableOpacity onPress={load} style={styles.ghostBtn}>
          <Text style={styles.ghostBtnText}>Vernieuw</Text>
        </TouchableOpacity>
      </View>

      {loading ? <LoaderBar theme={theme} /> : null}

      {(!suggestions || suggestions.length === 0) ? (
        <EmptyState
          theme={theme}
          title="Nog geen suggesties"
          subtitle="Tik op ‘Vernieuw’ om suggesties op te halen."
        />
      ) : (
        <View style={{ gap: theme.gap.m }}>
          {suggestions.map((s) => {
            // Fotolijst
            const photoList = Array.isArray(s.photos) && s.photos.length
              ? s.photos
              : (s.profile_photo_url ? [s.profile_photo_url] : []);
            const activeIdx = photoIdxById[s.id] ?? 0;
            const canBrowse = photoList.length > 1;
            const activeUrl = photoList[Math.min(activeIdx, photoList.length - 1)];

            return (
              <View key={s.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  {/* Header-icoon: profielfoto */}
                  <Avatar theme={theme} size={56} uri={s.profile_photo_url} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.cardTitle}>{s.name} · {s.age}</Text>
                    {s.bio ? <Text style={styles.cardSubtitle} numberOfLines={2}>{s.bio}</Text> : null}
                  </View>
                </View>

                {/* Grote foto: tik om verder te bladeren */}
                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={() => {
                    if (!canBrowse) return;
                    setPhotoIdxById(prev => ({
                      ...prev,
                      [s.id]: (activeIdx + 1) % photoList.length
                    }));
                  }}
                  style={{
                    borderRadius: 16,
                    overflow: 'hidden',
                    borderWidth: 1,
                    borderColor: theme.color.border
                  }}
                >
                  {activeUrl ? (
                    <Image
                      source={{ uri: activeUrl }}
                      style={{ width: '100%', height: 220 }}
                      resizeMode="cover"
                    />
                  ) : (
                    <View style={{
                      width: '100%', height: 220,
                      alignItems: 'center', justifyContent: 'center',
                      backgroundColor: '#F0F2F5'
                    }}>
                      <Ionicons name="image-outline" size={32} color={theme.color.textSecondary} />
                      <Text style={{
                        color: theme.color.textSecondary, marginTop: 6,
                        fontFamily: theme.font.bodyFamily
                      }}>
                        Geen foto
                      </Text>
                    </View>
                  )}
                </TouchableOpacity>

                {/* Acties */}
                <View style={styles.cardActions}>
                  <RoundAction color={theme.color.danger} label="✕" onPress={() => doSwipe(s.id, false)} />
                  <RoundAction color={theme.color.success} label="♥" onPress={() => doSwipe(s.id, true)} />
                </View>

                {/* Dots */}
                {canBrowse ? (
                  <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 6 }}>
                    {photoList.map((_, i) => (
                      <View
                        key={i}
                        style={{
                          width: 6, height: 6, borderRadius: 3,
                          backgroundColor: i === activeIdx ? theme.color.primary : theme.color.border
                        }}
                      />
                    ))}
                  </View>
                ) : null}
              </View>
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}

/* ---- ChatModal ---- */
function ChatModal({ route, navigation, api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const matchUser =
    route && route.params && route.params.matchUser ? route.params.matchUser : null;
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [loading, setLoading] = useState(false);

  const loadChat = useCallback(async () => {
    try {
      setLoading(true);
      const userId = matchUser ? matchUser.id : null;
      const res = await api.authFetch(`/chat/${userId}/messages`);
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setMessages((data && data.chat_history) ? data.chat_history : []);
    } catch (e) {
      Alert.alert('Chat laden', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, matchUser]);

  useEffect(() => { loadChat(); }, [loadChat]);

  const send = useCallback(async () => {
    const text = chatInput.trim();
    if (!text || !matchUser) return;
    if (!api.token) { Alert.alert('Niet ingelogd', 'Log opnieuw in.'); return; }
    try {
      setLoading(true);
      const res = await api.authFetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_id: matchUser.id, message: text }),
      });
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setChatInput('');
      await loadChat();
    } catch (e) {
      Alert.alert('Bericht verzenden', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, chatInput, loadChat, matchUser]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.color.surface }}>
      {loading ? <LoaderBar theme={theme} color={theme.color.accent} /> : null}

      <ScrollView style={styles.chatList} contentContainerStyle={{ padding: theme.gap.m }}>
        {((!messages || messages.length === 0) && !loading) ? (
          <Text style={{ color: theme.color.textSecondary, textAlign: 'center', fontFamily: theme.font.bodyFamily }}>
            Nog geen berichten.
          </Text>
        ) : (
          messages.map((msg, idx) => {
            const isThem = matchUser && msg.sender_id === matchUser.id;
            const bubbleStyle = isThem ? [styles.bubble, styles.bubbleThem] : [styles.bubble, styles.bubbleMe];
            const textStyle = isThem ? [styles.bubbleText, styles.bubbleTextThem] : [styles.bubbleText, styles.bubbleTextMe];
            const timeStyle = isThem ? [styles.bubbleTime, styles.bubbleTimeThem] : [styles.bubbleTime, styles.bubbleTimeMe];
            return (
              <View
                key={(msg.timestamp ? String(msg.timestamp) : 't') + '-' + idx}
                style={bubbleStyle}
              >
                <Text style={textStyle}>{msg.message}</Text>
                <Text style={timeStyle}>{new Date(msg.timestamp).toLocaleString()}</Text>
                {isThem ? (
                  <View style={styles.tailThemContainer} pointerEvents="none">
                    <View style={styles.tailThemBorder} />
                    <View style={styles.tailThemFill} />
                  </View>
                ) : (
                  <View style={styles.tailMeContainer} pointerEvents="none">
                    <View style={styles.tailMeBorder} />
                    <View style={styles.tailMeFill} />
                  </View>
                )}
              </View>
            );
          })
        )}
      </ScrollView>

      <View style={styles.chatInputRow}>
        <TextInput
          style={styles.chatInput}
          placeholder="Typ je bericht…"
          placeholderTextColor={theme.color.textSecondary}
          value={chatInput}
          onChangeText={setChatInput}
        />
        <TouchableOpacity onPress={send} style={styles.sendBtn}>
          <Ionicons name="send" size={18} color="#fff" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ==== Module-scope constants (stabiel, geen deps-ruis) ====
const DAY_LABELS = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
const BLOCKS = Object.freeze([
  { key: 'morning',  label: 'Ochtend',  start: '06:00', end: '12:00' },
  { key: 'afternoon',label: 'Middag',   start: '12:00', end: '18:00' },
  { key: 'evening',  label: 'Avond',    start: '18:00', end: '22:00' },
]);

/* ================= SETTINGS (PROFIEL) ================= */
function SettingsScreen({ api }) {
  const { theme, mode, setUserMode, preset, setUserPreset } = useContext(ThemeContext);
  const styles = useMemo(() => createStyles(theme), [theme]);

  // Herbruikbare Chip
  const Chip = ({ active, label, onPress }) => (
    <TouchableOpacity
      onPress={onPress}
      style={{
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: theme.radius.pill,
        borderWidth: 1,
        borderColor: active ? theme.color.primary : theme.color.border,
        backgroundColor: active ? theme.color.primary : theme.color.surface,
        marginRight: 8,
        marginBottom: 8,
      }}
    >
      <Text
        style={{
          color: active ? theme.color.onPrimary : theme.color.textPrimary,
          fontFamily: theme.font.bodySemibold,
        }}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );

  /* ---- User settings (match_goal, gender, distance, notifications) ---- */
  const USER_ID = api.userId;
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadSettings = useCallback(async () => {
    if (!USER_ID) return;
    try {
      setLoading(true);
      const res = await api.authFetch(`/users/${USER_ID}/settings`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail ?? 'Fout bij ophalen instellingen');
      setSettings(data);
    } catch (e) {
      Alert.alert('Instellingen', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, USER_ID]);

  useEffect(() => {
    if (USER_ID) loadSettings();
  }, [USER_ID, loadSettings]);

  const updateField = (key, value) => setSettings((prev) => ({ ...prev, [key]: value }));

  const saveSettings = useCallback(async () => {
    if (!USER_ID) { Alert.alert('Instellingen', 'Geen userId beschikbaar. Log opnieuw in.'); return; }
    try {
      setLoading(true);
      const res = await api.authFetch(`/users/${USER_ID}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail ?? 'Fout bij opslaan instellingen');
      Alert.alert('Instellingen', 'Instellingen opgeslagen');
    } catch (e) {
      Alert.alert('Instellingen', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, settings, USER_ID]);

  /* ---- Profiel (naam, leeftijd, bio) ---- */
  const [profile, setProfile] = useState({ name: '', age: '', bio: '' });
  const [profileError, setProfileError] = useState(null);
  const [ownId, setOwnId] = useState(null);

  const setProfileField = (k, v) => setProfile((prev) => ({ ...prev, [k]: v }));

  const validateAndBuildProfilePayload = useCallback(() => {
    const errs = {};
    const payload = {};
    const name = (profile.name ?? '').trim();
    const bio = (profile.bio ?? '').trim();
    const ageNum = parseInt(profile.age, 10);
    if (!name) errs.name = 'Naam is verplicht';
    if (!Number.isFinite(ageNum) || ageNum < 18 || ageNum > 99) errs.age = 'Leeftijd 18–99';
    if (Object.keys(errs).length) return { ok: false, errs };
    payload.name = name;
    payload.age = ageNum;
    payload.bio = bio;
    return { ok: true, payload };
  }, [profile]);

  const loadProfile = useCallback(async () => {
    try {
      setProfileError(null);
      const res = await api.authFetch('/me');
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? `Profiel laden mislukt (status ${res.status})`);
      setOwnId(data?.id ?? null);
      setProfile({
        name: data?.name ?? '',
        age: data?.age != null ? String(data.age) : '',
        bio: data?.bio ?? '',
      });
    } catch (e) {
      setProfileError(e.message);
    }
  }, [api]);

  useEffect(() => { loadProfile(); }, [loadProfile]);

  const saveProfile = useCallback(async () => {
    const { ok, errs, payload } = validateAndBuildProfilePayload();
    if (!ok) { setProfileError(Object.values(errs).join('\n')); return; }
    try {
      setProfileError(null);
      const uid = ownId ?? api.userId;
      if (!uid) throw new Error('Geen userId beschikbaar (is /me succesvol?)');
      const res = await api.authFetch(`/users/${uid}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? `Profiel opslaan mislukt (status ${res.status})`);
      Alert.alert('Profiel', 'Profiel opgeslagen');
      await loadProfile();
    } catch (e) {
      setProfileError(e.message);
    }
  }, [api, ownId, validateAndBuildProfilePayload, loadProfile]);

  /* ---- Foto's ---- */
  const [photos, setPhotos] = useState([]); // [{id, photo_url, is_profile_pic}]

  const loadPhotos = useCallback(async () => {
    const uid = api.userId;
    if (!uid) return;
    try {
      const res = await api.authFetch(`/users/${uid}`);
      const data = await res.json().catch(() => null);
      if (res.ok && data?.photos_meta) setPhotos(data.photos_meta);
    } catch (e) {
      if (__DEV__) console.debug('loadPhotos failed', e);
    }
  }, [api]);

  useEffect(() => { loadPhotos(); }, [loadPhotos, api.userId]);

  const setAsProfile = useCallback(async (photoId) => {
    try {
      const res = await api.authFetch(`/photos/${photoId}/set_profile`, { method: 'POST' });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? 'Kon niet instellen als profielfoto');
      Alert.alert('Foto', 'Ingesteld als profielfoto');
      await loadPhotos();
      api.notifyProfilePhotoChanged();
    } catch (e) { Alert.alert('Foto', e.message); }
  }, [api, loadPhotos]);

  const deletePhoto = useCallback(async (photoId) => {
    try {
      const res = await api.authFetch(`/delete_photo/${photoId}`, { method: 'DELETE' });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? 'Verwijderen mislukt');
      await loadPhotos();
    } catch (e) { Alert.alert('Foto', e.message); }
  }, [api, loadPhotos]);

  const addPhotoByUrl = useCallback(async () => {
    if (Platform.OS === 'web' && typeof window !== 'undefined' && typeof window.prompt === 'function') {
      const url = window.prompt('Plak een afbeeldings-URL');
      if (!url) return;
      try {
        const res = await api.authFetch(`/upload_photo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ photo_url: url, is_profile_pic: false }),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) throw new Error(data?.detail ?? 'Upload mislukt');
        await loadPhotos();
      } catch (e) {
        Alert.alert('Foto', e.message);
      }
      return;
    }

    if (Platform.OS === 'ios' && typeof Alert.prompt === 'function') {
      Alert.prompt(
        'Voeg foto via URL',
        'Plak een afbeeldings-URL',
        [
          { text: 'Annuleer', style: 'cancel' },
          {
            text: 'Voeg toe',
            onPress: async (value) => {
              const url = (value || '').trim();
              if (!url) return;
              try {
                const res = await api.authFetch(`/upload_photo`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ photo_url: url, is_profile_pic: false }),
                });
                const data = await res.json().catch(() => null);
                if (!res.ok) throw new Error(data?.detail ?? 'Upload mislukt');
                await loadPhotos();
              } catch (e) {
                Alert.alert('Foto', e.message);
              }
            },
          },
        ],
        'plain-text'
      );
      return;
    }

    Alert.alert('Niet ondersteund', '“Voeg toe via URL” is beschikbaar op web en iOS. Voeg voorlopig foto’s toe via toestel-upload of web.');
  }, [api, loadPhotos]);

  /* ---- Beschikbaarheden ---- */
  const [availabilityGrid, setAvailabilityGrid] = useState(
    Array.from({ length: 7 }, () => ({ morning: false, afternoon: false, evening: false }))
  );

  const toggleAvail = (d, blockKey) => {
    setAvailabilityGrid((prev) => {
      const copy = prev.map((x) => ({ ...x }));
      copy[d][blockKey] = !copy[d][blockKey];
      return copy;
    });
  };

  const loadAvailability = useCallback(async () => {
    const uid = api.userId;
    if (!uid) return;
    try {
      const res = await api.authFetch(`/users/${uid}/availability`);
      const data = await res.json().catch(() => null);
      if (!res.ok) return;
      const grid = Array.from({ length: 7 }, () => ({ morning: false, afternoon: false, evening: false }));
      (data?.availability ?? []).forEach((it) => {
        const { day_of_week, start_time, end_time } = it;
        for (const b of BLOCKS) {
          if (start_time === b.start && end_time === b.end) grid[day_of_week][b.key] = true;
        }
      });
      setAvailabilityGrid(grid);
    } catch (e) {
      if (__DEV__) console.debug('loadAvailability failed', e);
    }
  }, [api, BLOCKS]);

  useEffect(() => { loadAvailability(); }, [loadAvailability, api.userId]);

  const saveAvailability = useCallback(async () => {
    const uid = api.userId;
    if (!uid) return;
    const items = [];
    availabilityGrid.forEach((row, d) => {
      BLOCKS.forEach((b) => { if (row[b.key]) items.push({ day_of_week: d, start_time: b.start, end_time: b.end, timezone: 'Europe/Brussels' }); });
    });
    try {
      const res = await api.authFetch(`/users/${uid}/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? 'Opslaan mislukt');
      Alert.alert('Beschikbaarheden', 'Opgeslagen');
    } catch (e) {
      Alert.alert('Beschikbaarheden', e.message);
    }
  }, [api, availabilityGrid, BLOCKS]);

  /* ---- Uitloggen ---- */
  const handleLogout = useCallback(() => {
    Alert.alert('Uitloggen', 'Weet je zeker dat je wil uitloggen?', [
      { text: 'Annuleer', style: 'cancel' },
      { text: 'Uitloggen', style: 'destructive', onPress: async () => { await api.logout(); } },
    ]);
  }, [api]);

  /* ================= RENDER ================= */
  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      {/* THEMA */}
      <Text style={styles.sectionTitle}>Thema</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: theme.gap.m, flexWrap: 'wrap' }}>
        <Chip label="Systeem" active={mode === 'system'} onPress={() => setUserMode('system')} />
        <Chip label="Licht" active={mode === 'light'} onPress={() => setUserMode('light')} />
        <Chip label="Donker" active={mode === 'dark'} onPress={() => setUserMode('dark')} />
      </View>

      <Text style={styles.sectionTitle}>Chat‑stijl</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' }}>
        <Chip label="iOS" active={preset === 'ios'} onPress={() => setUserPreset('ios')} />
        <Chip label="WhatsApp" active={preset === 'whatsapp'} onPress={() => setUserPreset('whatsapp')} />
      </View>

      <View style={{ marginTop: theme.gap.l }}>
        <Text style={{ color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>
          Je keuzes worden lokaal opgeslagen en blijven behouden bij de volgende app‑start.
        </Text>
      </View>

      {/* PROFIEL (naam, leeftijd, bio) */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>Profiel</Text>
      <View style={[styles.card, { gap: 10 }]}>
        <TextInput
          style={styles.input}
          placeholder="Naam"
          placeholderTextColor={theme.color.textSecondary}
          value={profile.name}
          onChangeText={(v) => setProfileField('name', v)}
        />
        <TextInput
          style={styles.input}
          placeholder="Leeftijd"
          keyboardType="numeric"
          placeholderTextColor={theme.color.textSecondary}
          value={profile.age}
          onChangeText={(v) => setProfileField('age', v)}
        />
        <TextInput
          style={[styles.input, { height: 100, textAlignVertical: 'top' }]}
          placeholder="Bio"
          multiline
          placeholderTextColor={theme.color.textSecondary}
          value={profile.bio}
          onChangeText={(v) => setProfileField('bio', v)}
        />
        {profileError ? (
          <Text style={{ color: theme.color.danger, fontFamily: theme.font.bodyFamily }}>{profileError}</Text>
        ) : null}
        <TouchableOpacity onPress={saveProfile} style={[styles.primaryBtn, { marginTop: theme.gap.s }]}>
          <Text style={styles.primaryBtnText}>Profiel opslaan</Text>
        </TouchableOpacity>
      </View>

      {/* FOTO'S */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>Foto's</Text>
      <View style={[styles.card, { gap: 10 }]}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
          {photos.map((p) => (
            <View key={p.id} style={{ width: 120, alignItems: 'center' }}>
              <Image
                source={{ uri: p.photo_url }}
                style={{ width: 120, height: 120, borderRadius: 12, borderWidth: 1, borderColor: theme.color.border }}
              />
              <Text style={{ marginTop: 6, color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>
                {p.is_profile_pic ? 'Profielfoto' : '—'}
              </Text>
              <View style={{ flexDirection: 'row', gap: 8, marginTop: 6 }}>
                {!p.is_profile_pic && (
                  <SmallChip theme={theme} color={theme.color.primary} label="Als profiel" onPress={() => setAsProfile(p.id)} />
                )}
                <SmallChip theme={theme} color={theme.color.danger} label="Verwijder" onPress={() => deletePhoto(p.id)} />
              </View>
            </View>
          ))}
        </ScrollView>
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <SmallChip theme={theme} color={theme.color.secondary} label="Voeg toe via URL" onPress={addPhotoByUrl} />
        </View>
      </View>

      {/* BESCHIKBAARHEDEN */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>Beschikbaarheden</Text>
      <View style={[styles.card, { gap: 12 }]}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
          {DAY_LABELS.map((dLabel, d) => (
            <View key={d} style={{ alignItems: 'center' }}>
              <Text style={{ marginBottom: 6, color: theme.color.textPrimary, fontFamily: theme.font.bodySemibold }}>{dLabel}</Text>
              {BLOCKS.map((b) => {
                const active = availabilityGrid[d][b.key];
                return (
                  <TouchableOpacity
                    key={b.key}
                    onPress={() => toggleAvail(d, b.key)}
                    style={{
                      marginVertical: 4,
                      paddingHorizontal: 12,
                      paddingVertical: 8,
                      borderRadius: theme.radius.pill,
                      borderWidth: 1,
                      borderColor: active ? theme.color.primary : theme.color.border,
                      backgroundColor: active ? theme.color.primary : theme.color.surface,
                    }}
                  >
                    <Text style={{ color: active ? theme.color.onPrimary : theme.color.textPrimary, fontFamily: theme.font.bodyFamily }}>
                      {b.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          ))}
        </ScrollView>
        <TouchableOpacity onPress={saveAvailability} style={[styles.primaryBtn, { marginTop: theme.gap.s }]}>
          <Text style={styles.primaryBtnText}>Beschikbaarheden opslaan</Text>
        </TouchableOpacity>
      </View>

      {/* PROFIELINSTELLINGEN (match instellingen) */}
      {loading && <LoaderBar theme={theme} color={theme.color.accent} />}
      {!settings ? (
        <ActivityIndicator style={{ margin: 16 }} />
      ) : (
        <>
          <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>Profielinstellingen</Text>
          <Text style={{ marginBottom: 8 }}>Match‑doel</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {['friendship', 'training_partner', 'competition', 'coaching'].map((goal) => (
              <Chip key={goal} label={goal} active={settings.match_goal === goal} onPress={() => updateField('match_goal', goal)} />
            ))}
          </View>

          <Text style={{ marginTop: 16, marginBottom: 8 }}>Voorkeur geslacht</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {['any', 'male', 'female', 'non_binary'].map((gender) => (
              <Chip key={gender} label={gender} active={settings.preferred_gender === gender} onPress={() => updateField('preferred_gender', gender)} />
            ))}
          </View>

          <Text style={{ marginTop: 16 }}>Maximale afstand (km)</Text>
          <TextInput
            style={styles.input}
            keyboardType="numeric"
            value={String(settings.max_distance_km ?? '')}
            onChangeText={(v) => {
              const n = parseInt(v, 10);
              updateField('max_distance_km', Number.isFinite(n) ? n : 0);
            }}
            placeholder="bv. 25"
            placeholderTextColor={theme.color.textSecondary}
          />

          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 16 }}>
            <Text style={{ flex: 1 }}>Pushmeldingen</Text>
            <Switch
              value={!!settings.notifications_enabled}
              onValueChange={(v) => updateField('notifications_enabled', v)}
            />
          </View>

          <TouchableOpacity onPress={saveSettings} style={[styles.primaryBtn, { marginTop: theme.gap.m }]}>
            <Text style={styles.primaryBtnText}>Instellingen opslaan</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Uitloggen */}
      <View style={{ height: theme.gap.l }} />
      <TouchableOpacity onPress={handleLogout} style={[styles.primaryBtn, { backgroundColor: theme.color.danger }]}>
        <Text style={styles.primaryBtnText}>Uitloggen</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

/* ================= NAVIGATION WRAPPER ================= */
function AppContent() {
  const api = useApi();
  const { theme } = useContext(ThemeContext);
  const [fontsLoaded] = useFonts({
    Montserrat_400Regular,
    Montserrat_600SemiBold,
    Montserrat_700Bold,
  });
  if (!fontsLoaded) return null;

  const headerOptions = {
    headerBackground: () => (
      <LinearGradient
        colors={[theme.gradient.pulse.from, theme.gradient.pulse.to]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={{ flex: 1 }}
      />
    ),
    headerTitleStyle: {
      color: theme.color.onPrimary,
      fontFamily: theme.font.headingFamily,
      fontSize: theme.font.size.lg,
    },
    headerTintColor: theme.color.onPrimary,
    headerShadowVisible: false,
    headerStyle: { height: theme.navbar.height },
  };

  const navTheme = {
    ...DefaultTheme,
    colors: { ...DefaultTheme.colors, background: theme.color.surface },
  };

  // Remount navigator wanneer mode/preset veranderen
  return (
    <NavigationContainer theme={navTheme} key={`nav-${api.isAuthenticated}-${theme.mode}-${theme.preset}`}>
      <Stack.Navigator screenOptions={headerOptions} key={`stack-${api.isAuthenticated}-${theme.mode}-${theme.preset}`}>
        {!api.isAuthenticated ? (
          <Stack.Screen name="Auth" options={{ title: 'Aanmelden' }}>
            {(props) => <AuthScreen {...props} api={api} theme={theme} />}
          </Stack.Screen>
        ) : (
          <>
            <Stack.Screen name="Main" options={{ headerShown: false }}>
              {(props) => (
                <MainTabs
                  {...props}
                  api={api}
                  theme={theme}
                />
              )}
            </Stack.Screen>

            <Stack.Screen
              name="Chat"
              options={({ route, navigation }) => {
                const chatName =
                  route && route.params && route.params.matchUser && route.params.matchUser.name
                    ? route.params.matchUser.name
                    : '';
                return {
                  presentation: 'modal',
                  title: 'Chat met ' + chatName,
                  ...headerOptions,
                  headerRight: () => (
                    <TouchableOpacity onPress={() => navigation.goBack()} style={{ paddingHorizontal: 12, paddingVertical: 8 }}>
                      <Text style={{ color: theme.color.onPrimary, fontFamily: theme.font.bodySemibold }}>Sluiten</Text>
                    </TouchableOpacity>
                  ),
                };
              }}
            >
              {(props) => <ChatModal {...props} api={api} theme={theme} />}
            </Stack.Screen>

            {/* Route-screen is GEEN tab, wél bereikbaar vanuit Matches */}
            <Stack.Screen name="Route" options={{ title: 'Route voorstel' }}>
              {(props) => <RouteScreen {...props} theme={theme} />}
            </Stack.Screen>
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

/* ================= TABS ================= */
function MainTabs({ api, theme }) {
  const tabHeader = {
    headerBackground: () => (
      <LinearGradient
        colors={[theme.gradient.pulse.from, theme.gradient.pulse.to]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={{ flex: 1 }}
      />
    ),
    headerTitleStyle: {
      color: theme.color.onPrimary,
      fontFamily: theme.font.headingFamily,
      fontSize: theme.font.size.lg,
    },
    headerTintColor: theme.color.onPrimary,
    headerShadowVisible: false,
    headerStyle: { height: theme.navbar.height },
    tabBarActiveTintColor: theme.color.primary,
    tabBarInactiveTintColor: theme.color.textSecondary,
    tabBarStyle: { backgroundColor: theme.color.surface, borderTopColor: theme.color.border, height: theme.navbar.height },
    tabBarIconStyle: { width: theme.navbar.iconSize, height: theme.navbar.iconSize },
  };

  const [profilePhotoUrl, setProfilePhotoUrl] = useState(null);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        if (!api.userId) return;
        const res = await api.authFetch(`/users/${api.userId}`);
        const data = await res.json().catch(() => null);
        if (res.ok && data?.photos_meta) {
          const p = data.photos_meta.find((x) => x.is_profile_pic);
          if (mounted) setProfilePhotoUrl(p ? p.photo_url : null);
        }
      } catch (e) {
        if (__DEV__) console.debug('profilePhotoUrl load failed', e);
      }
    })();
    return () => { mounted = false; };
  }, [api, api.userId, api.profileVersion]);

  return (
    <Tabs.Navigator
      key={`tabs-${theme.mode}-${theme.preset}`}
      screenOptions={({ route }) => ({
        ...tabHeader,
        tabBarIcon: ({ color, size }) => {
          if (route.name === 'Ontdekken') return <Ionicons name="sparkles-outline" size={size} color={color} />;
          if (route.name === 'Matches') return <Ionicons name="people-outline" size={size} color={color} />;
          if (route.name === 'Profiel') {
            if (profilePhotoUrl) {
              return (
                <Image
                  source={{ uri: profilePhotoUrl }}
                  style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 1, borderColor: theme.color.border }}
                />
              );
            }
            return <Ionicons name="person-circle-outline" size={size} color={color} />;
          }
          return <Ionicons name="ellipse-outline" size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="Ontdekken" options={{ title: 'Ontdekken' }}>
        {(props) => <DiscoverScreen {...props} api={api} theme={theme} />}
      </Tabs.Screen>
      <Tabs.Screen name="Matches" options={{ title: 'Matches' }}>
        {(props) => <MatchesScreen {...props} api={api} theme={theme} />}
      </Tabs.Screen>
      <Tabs.Screen name="Profiel" options={{ title: 'Profiel' }}>
        {(props) => <SettingsScreen {...props} api={api} />}
      </Tabs.Screen>
    </Tabs.Navigator>
  );
}

/* ================= UI HELPERS & STYLES ================= */
function LoaderBar({ theme, color }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8 }}>
      <ActivityIndicator size="small" color={color ?? theme.color.primary} />
      <Text style={{ color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>Bezig…</Text>
    </View>
  );
}

function Avatar({ theme, size = 56, uri }) {
  const radius = size / 2;
  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={{
          width: size,
          height: size,
          borderRadius: radius,
          borderWidth: 1,
          borderColor: theme.color.border,
        }}
      />
    );
  }
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: radius,
        backgroundColor: '#E5E7EB',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: theme.color.border,
      }}
    >
      <Ionicons name="person" size={Math.round(size * 0.6)} color={theme.color.textSecondary} />
    </View>
  );
}

function EmptyState({ theme, title, subtitle }) {
  const styles = createStyles(theme);
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>{title}</Text>
      {subtitle ? <Text style={styles.emptySub}>{subtitle}</Text> : null}
    </View>
  );
}

function RoundAction({ color, label, onPress }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{ width: 54, height: 54, borderRadius: 27, alignItems: 'center', justifyContent: 'center', backgroundColor: color }}
    >
      <Text style={{ color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold' }}>{label}</Text>
    </TouchableOpacity>
  );
}

function SmallChip({ theme, color, label, onPress }) {
  const isPrimary = color === theme.color.primary;
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{
        paddingHorizontal: 10, paddingVertical: 6, borderRadius: theme.radius.pill,
        backgroundColor: isPrimary ? theme.color.primary : theme.color.chipBg,
        borderWidth: 1, borderColor: isPrimary ? theme.color.primary : theme.color.secondary,
      }}
    >
      <Text style={{ color: isPrimary ? theme.color.onPrimary : theme.color.textPrimary, fontFamily: theme.font.bodySemibold }}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const createStyles = (THEME) => StyleSheet.create({
  // Auth
  authContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: THEME.gap.xl,
    gap: THEME.gap.s,
  },
  authTitle: {
    fontSize: THEME.font.size.xl,
    fontFamily: THEME.font.headingFamily,
    textAlign: 'center',
    marginBottom: THEME.gap.l,
    color: THEME.color.textPrimary,
  },
  input: {
    height: 48,
    backgroundColor: THEME.color.surface,
    borderColor: THEME.color.border,
    borderWidth: 1,
    borderRadius: THEME.radius.md,
    paddingHorizontal: 12,
    color: THEME.color.textPrimary,
    fontFamily: THEME.font.bodyFamily,
  },
  error: { color: '#DC2626', marginTop: 4, marginLeft: 4, fontFamily: THEME.font.bodyFamily },
  primaryBtn: {
    marginTop: 4,
    backgroundColor: THEME.color.primary,
    paddingVertical: 12,
    borderRadius: THEME.radius.lg,
    alignItems: 'center',
    ...THEME.shadow1,
  },
  primaryBtnText: { color: THEME.color.onPrimary, fontFamily: THEME.font.bodySemibold, fontSize: THEME.font.size.md },
  switchText: { color: THEME.color.primary, textAlign: 'center', fontFamily: THEME.font.bodySemibold },
  // Tabs content
  tabContent: { padding: THEME.gap.xl, gap: THEME.gap.m },
  sectionTitle: { fontSize: THEME.font.size.lg, fontFamily: THEME.font.headingFamily, color: THEME.color.textPrimary },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  // Buttons
  ghostBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: THEME.radius.pill,
    borderWidth: 1,
    borderColor: THEME.color.border,
    backgroundColor: THEME.color.surface,
  },
  ghostBtnText: { color: THEME.color.textPrimary, fontFamily: THEME.font.bodyFamily },
  // Cards
  card: {
    backgroundColor: THEME.color.surface,
    borderRadius: THEME.radius.xl,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: THEME.color.border,
    padding: 16,
    gap: 12,
    ...THEME.shadow2,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: '#E5E7EB' },
  cardTitle: { fontSize: 17, fontFamily: THEME.font.bodyBold, color: THEME.color.textPrimary },
  cardSubtitle: { color: THEME.color.textSecondary, fontFamily: THEME.font.bodyFamily },
  cardActions: { flexDirection: 'row', justifyContent: 'space-between' },
  // List
  listCard: {
    backgroundColor: THEME.color.surface,
    borderRadius: THEME.radius.xl,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: THEME.color.border,
    ...THEME.shadow1,
  },
  listRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  listRowDivider: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: THEME.color.border },
  avatarSm: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#E5E7EB' },
  listTitle: { fontFamily: THEME.font.bodyBold, color: THEME.color.textPrimary },
  // Route
  routeLine: { color: THEME.color.textPrimary, marginBottom: 6, fontFamily: THEME.font.bodyFamily },
  routeLabel: { fontFamily: THEME.font.bodyBold },
  routeLink: { color: THEME.color.primary, marginTop: 8, fontFamily: THEME.font.bodySemibold },
  // Empty
  empty: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: THEME.color.surface,
    borderRadius: THEME.radius.xl,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: THEME.color.border,
    ...THEME.shadow1,
  },
  emptyTitle: { fontFamily: THEME.font.bodyBold, color: THEME.color.textPrimary, marginBottom: 4 },
  emptySub: { color: THEME.color.textSecondary, fontFamily: THEME.font.bodyFamily },
  // Chat
  chatList: { flex: 1, backgroundColor: THEME.color.surface },
  bubble: {
    position: 'relative',
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginVertical: 6,
    maxWidth: '85%',
    borderRadius: 18,
    ...THEME.shadow1,
  },
  bubbleMe: {
    alignSelf: 'flex-end',
    backgroundColor: THEME.chat.bubbleMeBg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: THEME.chat.bubbleMeBorder,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 6,
  },
  bubbleThem: {
    alignSelf: 'flex-start',
    backgroundColor: THEME.chat.bubbleThemBg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: THEME.chat.bubbleThemBorder,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    borderBottomRightRadius: 18,
    borderBottomLeftRadius: 6,
  },
  bubbleText: { fontSize: 15, lineHeight: 20, fontFamily: THEME.font.bodyFamily },
  bubbleTextMe: { color: THEME.chat.bubbleMeText },
  bubbleTextThem: { color: THEME.chat.bubbleThemText },
  bubbleTime: { fontSize: 11, marginTop: 4, textAlign: 'right', fontFamily: THEME.font.bodyFamily },
  bubbleTimeMe: { color: THEME.chat.bubbleMeTime },
  bubbleTimeThem: { color: THEME.chat.bubbleThemTime },
  tailMeContainer: { position: 'absolute', bottom: -1, right: -5, width: 0, height: 0 },
  tailThemContainer: { position: 'absolute', bottom: -1, left: -5, width: 0, height: 0 },
  tailMeBorder: {
    position: 'absolute',
    bottom: 0, right: 0, width: 0, height: 0,
    borderLeftWidth: 0, borderRightWidth: 0, borderTopWidth: 12,
    borderTopColor: THEME.chat.tailMeBorder,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    transform: [{ rotate: '45deg' }],
  },
  tailMeFill: {
    position: 'absolute',
    bottom: 1, right: 1, width: 0, height: 0,
    borderLeftWidth: 0, borderRightWidth: 0, borderTopWidth: 10,
    borderTopColor: THEME.chat.tailMeFill,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    transform: [{ rotate: '45deg' }],
  },
  tailThemBorder: {
    position: 'absolute',
    bottom: 0, left: 0, width: 0, height: 0,
    borderLeftWidth: 0, borderRightWidth: 0, borderTopWidth: 12,
    borderTopColor: THEME.chat.tailThemBorder,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    transform: [{ rotate: '-45deg' }],
  },
  tailThemFill: {
    position: 'absolute',
    bottom: 1, left: 1, width: 0, height: 0,
    borderLeftWidth: 0, borderRightWidth: 0, borderTopWidth: 10,
    borderTopColor: THEME.chat.tailThemFill,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    transform: [{ rotate: '-45deg' }],
  },
  chatInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: THEME.color.border,
    backgroundColor: THEME.color.surface,
  },
  chatInput: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: THEME.color.border,
    borderRadius: THEME.radius.md,
    paddingHorizontal: 12,
    backgroundColor: THEME.color.surface,
    color: THEME.color.textPrimary,
    fontFamily: THEME.font.bodyFamily,
  },
  sendBtn: {
    backgroundColor: THEME.color.success,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: THEME.radius.md,
  },
});

/* ---- MatchesScreen ---- */
function MatchesScreen({ api, theme, navigation }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.authFetch('/matches');
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? 'Kon matches niet laden');
      setMatches(Array.isArray(data?.matches) ? data.matches : []);
    } catch (e) {
      Alert.alert('Matches', e.message);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { load(); }, [load]);

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <View style={styles.rowBetween}>
        <Text style={styles.sectionTitle}>Matches</Text>
        <TouchableOpacity onPress={load} style={styles.ghostBtn}>
          <Text style={styles.ghostBtnText}>Vernieuw</Text>
        </TouchableOpacity>
      </View>

      {loading ? <LoaderBar theme={theme} /> : null}

      {(!matches || matches.length === 0) ? (
        <EmptyState theme={theme} title="Nog geen matches"
          subtitle="Ga naar Ontdekken en like iemand terug om te matchen." />
      ) : (
        <View style={styles.listCard}>
          {matches.map((m, idx) => (
            <View key={m.id ?? idx}
                  style={[styles.listRow, idx < matches.length-1 && styles.listRowDivider]}>
              {/* avatar */}
              <Avatar theme={theme} size={36} uri={m.photo_url} />
              {/* naam */}
              <Text style={[styles.listTitle, { flex: 1 }]} numberOfLines={1}>
                {m.name ?? 'Onbekend'}
              </Text>
              {/* Route */}
              <TouchableOpacity onPress={() => navigation.navigate('Route', { matchUser: m })}>
                <Ionicons name="map-outline" size={20} color={theme.color.primary} />
              </TouchableOpacity>
              {/* Chat */}
              <TouchableOpacity onPress={() => navigation.navigate('Chat', { matchUser: m })}
                                style={{ marginLeft: 12 }}>
                <Ionicons name="chatbubble-ellipses-outline" size={20} color={theme.color.primary} />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

/* ---- RouteScreen ---- */
function RouteScreen({ route, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const matchUser = route?.params?.matchUser ?? null;

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <Text style={styles.sectionTitle}>Route voorstel</Text>
      <View style={[styles.card, { gap: 8 }]}>
        <Text style={styles.routeLine}>
          <Text style={styles.routeLabel}>Met: </Text>
          {matchUser?.name ?? '—'}
        </Text>
        <Text style={styles.routeLine}>
          Hier komt straks het dynamische routevoorstel (loop/fiets).
        </Text>
        <Text style={styles.routeLine}>
          We kunnen hier later Google/Apple Maps deeplinks tonen.
        </Text>
      </View>
    </ScrollView>
  );
}

/* ================= APP EXPORT ================= */
export default function App() {
  return (
    <ThemeProvider makeBaseTheme={makeBaseTheme}>
      <AppContent />
    </ThemeProvider>
  );
}
