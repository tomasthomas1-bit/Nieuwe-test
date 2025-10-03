import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  Alert,
  StyleSheet,
  TouchableOpacity
} from 'react-native';

export default function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = async () => {
    try {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.text();
      if (response.ok) {
        Alert.alert('Login gelukt', data);
        setIsAuthenticated(true);
      } else {
        Alert.alert('Login mislukt', data);
      }
    } catch (error) {
      Alert.alert('Fout', error.message);
    }
  };

  const handleRegister = async () => {
    try {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.text();
      if (response.ok) {
        Alert.alert('Registratie gelukt', data);
        setIsAuthenticated(true);
      } else {
        Alert.alert('Registratie mislukt', data);
      }
    } catch (error) {
      Alert.alert('Fout', error.message);
    }
  };

  if (isAuthenticated) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Welkom, {email}!</Text>
        <Text style={styles.subtitle}>Je bent nu ingelogd.</Text>
        <Button title="Uitloggen" onPress={() => setIsAuthenticated(false)} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{isLogin ? 'Login' : 'Registreren'}</Text>
      <TextInput
        style={styles.input}
        placeholder="E-mail"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Wachtwoord"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button
        title={isLogin ? 'Inloggen' : 'Registreren'}
        onPress={isLogin ? handleLogin : handleRegister}
      />
      <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
        <Text style={styles.toggleText}>
          {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    padding: 20
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
    textAlign: 'center'
  },
  subtitle: {
    fontSize: 18,
    marginBottom: 20,
    textAlign: 'center',
    color: '#555'
  },
  input: {
    height: 40,
    borderColor: '#999',
    borderWidth: 1,
    marginBottom: 12,
    paddingHorizontal: 10,
    borderRadius: 5
  },
  toggleText: {
    marginTop: 15,
    color: 'blue',
    textAlign: 'center'
  }
});
