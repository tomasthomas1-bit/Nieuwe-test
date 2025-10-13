import 'react-native-gesture-handler';
import React, { useMemo, useState, useEffect, useCallback, useContext } from 'react';
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
// Token persistentie
import * as SecureStore from 'expo-secure-store';
import { ThemeProvider, ThemeContext } from './ThemeContext.js';

/* -------------------- TOKENS -------------------- */
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

/** makeBaseTheme — basis tokens zonder chat-preset (die komt uit ThemeContext) */
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

/* -------------------- API HOOK -------------------- */
const BASE_URL = 'https://web-production-ec0bc.up.railway.app';

// useApi met token-persist + 401-intercept
function useApi() {
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Token bij app-start uit SecureStore laden
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

  const saveToken = useCallback(async (t) => {
    try {
      await SecureStore.setItemAsync('access_token', t);
    } catch (e) {
      console.warn('Token opslaan mislukt:', e);
    }
  }, []);

  const clearToken = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync('access_token');
    } catch (e) {
      // ignore
    }
  }, []);

  const logout = useCallback(() => {
    setIsAuthenticated(false);
    setToken(null);
    clearToken();
  }, [clearToken]);

  // Authenticated fetch met 401-intercept
  const authFetch = useCallback(
    async (path, options = {}) => {
      const headers = {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
      // 401 → sessie verlopen of token ongeldig → user terug naar login
      if (res.status === 401) {
        logout();
        Alert.alert('Sessie verlopen', 'Log opnieuw in a.u.b.');
      }
      return res;
    },
    [token, logout]
  );

  // Inloggen → token opslaan in state + SecureStore
  const login = useCallback(
    async (username, password) => {
      const body =
        'username=' + encodeURIComponent(username) +
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
        await saveToken(data.access_token);
        return { ok: true };
      }
      const errMsg = data && data.detail ? data.detail : 'Login mislukt';
      return { ok: false, error: errMsg };
    },
    [saveToken]
  );

  const register = useCallback(async ({ username, name, age, bio, password }) => {
    const res = await fetch(`${BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, name, age, bio, password }),
    });
    const data = await res.json().catch(() => null);
    if (res.ok) return { ok: true };
    const errMsg = data && data.detail ? data.detail : 'Registratie mislukt';
    return { ok: false, error: errMsg };
  }, []);

  return { token, isAuthenticated, authFetch, login, register, logout };
}

/* -------------------- SCREENS -------------------- */
const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

function AuthScreen({ navigation, api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({ username: '', name: '', age: '', bio: '', password: '' });
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
    if ((form.password || '').length < 8) e.password = 'Minimaal 8 karakters';
    setErrors(e);
    if (Object.keys(e).length) return;

    const { ok, error } = await api.register({
      username: form.username, name: form.name, age: ageNum, bio: form.bio, password: form.password,
    });
    if (!ok) return Alert.alert('Registratie mislukt', error);
    Alert.alert('Registratie gelukt', 'Account is aangemaakt.');
    await handleLogin();
  }, [api, form, handleLogin]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.color.background }}>
      <ScrollView contentContainerStyle={styles.authContainer}>
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

function DiscoverScreen({ api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.authFetch('/suggestions');
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setSuggestions((data && data.suggestions) ? data.suggestions : []);
      const hasNone = !(data && data.suggestions && data.suggestions.length > 0);
      if (hasNone) {
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
      Alert.alert('Swipe', (data && data.message) ? data.message : (liked ? 'Geliked' : 'Geschipt'));
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
        <EmptyState theme={theme} title="Nog geen suggesties" subtitle="Tik op ‘Vernieuw’ om suggesties op te halen." />
      ) : (
        <View style={{ gap: theme.gap.m }}>
          {suggestions.map((s) => (
            <View key={s.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={styles.avatar} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{s.name} · {s.age}</Text>
                  {s.bio ? <Text style={styles.cardSubtitle} numberOfLines={2}>{s.bio}</Text> : null}
                </View>
              </View>
              <View style={styles.cardActions}>
                <RoundAction color={theme.color.danger} label="✕" onPress={() => doSwipe(s.id, false)} />
                <RoundAction color={theme.color.success} label="♥" onPress={() => doSwipe(s.id, true)} />
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function MatchesScreen({ api, theme, navigation, setRouteSuggestion }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.authFetch('/matches');
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setMatches((data && data.matches) ? data.matches : []);
      const hasNone = !(data && data.matches && data.matches.length > 0);
      if (hasNone) {
        Alert.alert('Matches', 'Nog geen matches. Swipe eerst (en laat de andere user terug liken).');
      }
    } catch (e) {
      Alert.alert('Fout bij ophalen matches', e.message);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const openRoute = useCallback(async (matchUserId) => {
    try {
      setLoading(true);
      const res = await api.authFetch(`/suggest_route/${matchUserId}`);
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      setRouteSuggestion(data ? data.route_suggestion : null);
      navigation.navigate('Route');
      const desc = (data && data.route_suggestion && data.route_suggestion.description)
        ? data.route_suggestion.description
        : 'Routevoorstel gehaald.';
      Alert.alert('Route', desc);
    } catch (e) {
      Alert.alert('Routevoorstel', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, navigation, setRouteSuggestion]);

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <View style={styles.rowBetween}>
        <Text style={styles.sectionTitle}>Matches</Text>
        <TouchableOpacity onPress={load} style={styles.ghostBtn}><Text style={styles.ghostBtnText}>Vernieuw</Text></TouchableOpacity>
      </View>

      {loading ? <LoaderBar theme={theme} /> : null}

      {(!matches || matches.length === 0) ? (
        <EmptyState theme={theme} title="Nog geen matches" subtitle="Swipe eerst en laat de andere gebruiker terug liken." />
      ) : (
        <View style={styles.listCard}>
          {matches.map((m, idx) => (
            <View key={m.id} style={[styles.listRow, idx !== matches.length - 1 && styles.listRowDivider]}>
              <View style={styles.avatarSm} />
              <View style={{ flex: 1 }}>
                <Text style={styles.listTitle}>{m.name} · {m.age}</Text>
              </View>
              <SmallChip theme={theme} color={theme.color.primary} label="Route" onPress={() => openRoute(m.id)} />
              <SmallChip theme={theme} color={theme.color.accent} label="Chat" onPress={() => navigation.navigate('Chat', { matchUser: m })} />
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function RouteScreen({ theme, routeSuggestion }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <Text style={styles.sectionTitle}>Route voorstel</Text>
      {!routeSuggestion ? (
        <EmptyState theme={theme} title="Geen route geselecteerd" subtitle="Kies ‘Route’ bij een match om een voorstel te genereren." />
      ) : (
        <View style={styles.card}>
          <Text style={styles.routeLine}><Text style={styles.routeLabel}>Naam:</Text> {routeSuggestion.name}</Text>
          <Text style={styles.routeLine}><Text style={styles.routeLabel}>Afstand (~):</Text> {routeSuggestion.distance_km} km</Text>
          <Text selectable style={styles.routeLink}>{routeSuggestion.map_link}</Text>
        </View>
      )}
    </ScrollView>
  );
}

function ChatModal({ route, navigation, api, theme }) {
  const styles = useMemo(() => createStyles(theme), [theme]);
  const matchUser = route && route.params && route.params.matchUser ? route.params.matchUser : null;
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
        {(!messages || messages.length === 0) && !loading ? (
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

                {/* Staartjes met rand + vulling */}
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

/* -------------------- SETTINGS SCREEN -------------------- */
function SettingsScreen() {
  const { theme, mode, setUserMode, preset, setUserPreset } = useContext(ThemeContext);
  const styles = useMemo(() => createStyles(theme), [theme]);

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

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <Text style={styles.sectionTitle}>Thema</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: theme.gap.m }}>
        <Chip label="Systeem" active={mode === 'system'} onPress={() => setUserMode('system')} />
        <Chip label="Licht"   active={mode === 'light'}  onPress={() => setUserMode('light')} />
        <Chip label="Donker"  active={mode === 'dark'}   onPress={() => setUserMode('dark')} />
      </View>

      <Text style={styles.sectionTitle}>Chat‑stijl</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <Chip label="iOS"       active={preset === 'ios'}       onPress={() => setUserPreset('ios')} />
        <Chip label="WhatsApp"  active={preset === 'whatsapp'}  onPress={() => setUserPreset('whatsapp')} />
      </View>

      <View style={{ marginTop: theme.gap.l }}>
        <Text style={{ color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>
          Je keuzes worden lokaal opgeslagen en blijven behouden bij de volgende app‑start.
        </Text>
      </View>
    </ScrollView>
  );
}

/* -------------------- NAVIGATIE + GRADIENT HEADERS -------------------- */
function AppContent() {
  const api = useApi();
  const { theme } = useContext(ThemeContext); // thema + chat preset uit context
  const [fontsLoaded] = useFonts({
    Montserrat_400Regular,
    Montserrat_600SemiBold,
    Montserrat_700Bold,
  });
  const [routeSuggestion, setRouteSuggestion] = useState(null);

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
    colors: { ...DefaultTheme.colors, background: theme.color.background },
  };

  return (
    <NavigationContainer theme={navTheme}>
      <Stack.Navigator screenOptions={headerOptions}>
        {!api.isAuthenticated ? (
          <Stack.Screen
            name="Auth"
            options={{ title: 'Aanmelden' }}
          >
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
                  routeSuggestion={routeSuggestion}
                  setRouteSuggestion={setRouteSuggestion}
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
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

function MainTabs({ api, theme, routeSuggestion, setRouteSuggestion }) {
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

  return (
    <Tabs.Navigator
      screenOptions={({ route }) => ({
        ...tabHeader,
        tabBarIcon: ({ color, size }) => {
          const icon =
            route.name === 'Ontdekken' ? 'sparkles-outline' :
            route.name === 'Matches'   ? 'people-outline'   :
            route.name === 'Route'     ? 'map-outline'      :
            route.name === 'Instellingen' ? 'settings-outline' :
            'ellipse-outline';
          return <Ionicons name={icon} size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="Ontdekken" options={{ title: 'Ontdekken' }}>
        {(props) => <DiscoverScreen {...props} api={api} theme={theme} />}
      </Tabs.Screen>

      <Tabs.Screen name="Matches" options={{ title: 'Matches' }}>
        {(props) => (
          <MatchesScreen
            {...props}
            api={api}
            theme={theme}
            setRouteSuggestion={setRouteSuggestion}
          />
        )}
      </Tabs.Screen>

      <Tabs.Screen name="Route" options={{ title: 'Route voorstel' }}>
        {(props) => <RouteScreen {...props} theme={theme} routeSuggestion={routeSuggestion} />}
      </Tabs.Screen>

      <Tabs.Screen name="Instellingen" options={{ title: 'Instellingen' }}>
        {(props) => <SettingsScreen {...props} />}
      </Tabs.Screen>
    </Tabs.Navigator>
  );
}

/* -------------------- UI HELPERS & STYLES -------------------- */
function LoaderBar({ theme, color }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8 }}>
      <ActivityIndicator size="small" color={color || theme.color.primary} />
      <Text style={{ color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>Bezig…</Text>
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
    <TouchableOpacity onPress={onPress} style={{ width: 54, height: 54, borderRadius: 27, alignItems: 'center', justifyContent: 'center', backgroundColor: color }}>
      <Text style={{ color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold' }}>{label}</Text>
    </TouchableOpacity>
  );
}

function SmallChip({ theme, color, label, onPress }) {
  const isPrimary = color === theme.color.primary;
  return (
    <TouchableOpacity onPress={onPress}
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
  tabContent: {
    padding: THEME.gap.xl,
    gap: THEME.gap.m,
  },
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

  // Chat — kleuren en staartjes volledig uit THEME.chat.* (preset + mode)
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
  // Jij (rechts)
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
  // De ander (links)
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
  // Tekst & tijd
  bubbleText: { fontSize: 15, lineHeight: 20, fontFamily: THEME.font.bodyFamily },
  bubbleTextMe: { color: THEME.chat.bubbleMeText },
  bubbleTextThem: { color: THEME.chat.bubbleThemText },
  bubbleTime: { fontSize: 11, marginTop: 4, textAlign: 'right', fontFamily: THEME.font.bodyFamily },
  bubbleTimeMe: { color: THEME.chat.bubbleMeTime },
  bubbleTimeThem: { color: THEME.chat.bubbleThemTime },

  // Staartjes containers
  tailMeContainer: { position: 'absolute', bottom: -1, right: -5, width: 0, height: 0 },
  tailThemContainer: { position: 'absolute', bottom: -1, left: -5, width: 0, height: 0 },

  // Outgoing (rechts): borderlaag + invullaag
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

  // Incoming (links): borderlaag + invullaag
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

/* -------------------- APP WRAPPER -------------------- */
export default function App() {
  return (
    <ThemeProvider makeBaseTheme={makeBaseTheme}>
      <AppContent />
    </ThemeProvider>
  );
}
