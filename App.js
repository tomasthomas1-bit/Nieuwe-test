import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  Alert,
  ScrollView,
  StyleSheet,
  TouchableOpacity
} from 'react-native';

export default function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    username: '',
    name: '',
    age: '',
    bio: '',
    sport_type: '',
    avg_distance: '',
    last_lat: '',
    last_lng: '',
    availability: '',
    password: ''
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleChange = (key, value) => {
    setForm({ ...form, [key]: value });
  };

  const handleLogin = async () => {
    try {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: form.username, password: form.password })
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
    const requiredFields = [
      'username', 'name', 'age', 'sport_type',
      'avg_distance', 'last_lat', 'last_lng',
      'availability', 'password'
    ];
    for (let field of requiredFields) {
      if (!form[field] || form[field].toString().trim() === '') {
        Alert.alert('Fout', `Veld "${field}" is verplicht.`);
        return;
      }
    }
    if (isNaN(parseInt(form.age)) || parseInt(form.age) < 18 || parseInt(form.age) > 99) {
      Alert.alert('Fout', 'Leeftijd moet tussen 18 en 99 zijn.');
      return;
    }
    if (form.password.length < 8) {
      Alert.alert('Fout', 'Wachtwoord moet minimaal 8 karakters lang zijn.');
      return;
    }

    try {
      const payload = {
        username: form.username,
        name: form.name,
        age: parseInt(form.age),
        bio: form.bio,
        sport_type: form.sport_type,
        avg_distance: parseFloat(form.avg_distance),
        last_lat: parseFloat(form.last_lat),
        last_lng: parseFloat(form.last_lng),
        availability: form.availability,
        password: form.password
      };
      const response = await fetch('https://web-production-ec0bc.up.railway.app/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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
        <Text style={styles.title}>Welkom, {form.username}!</Text>
        <Text style={styles.subtitle}>Je bent nu ingelogd.</Text>
        <Button title="Uitloggen" onPress={() => setIsAuthenticated(false)} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{isLogin ? 'Login' : 'Registreren'}</Text>
      <TextInput style={styles.input} placeholder="Gebruikersnaam" value={form.username} onChangeText={v => handleChange('username', v)} />
      {!isLogin && (
        <>
          <TextInput style={styles.input} placeholder="Naam" value={form.name} onChangeText={v => handleChange('name', v)} />
          <TextInput style={styles.input} placeholder="Leeftijd" value={form.age} onChangeText={v => handleChange('age', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Bio" value={form.bio} onChangeText={v => handleChange('bio', v)} />
          <TextInput style={styles.input} placeholder="Sporttype" value={form.sport_type} onChangeText={v => handleChange('sport_type', v)} />
          <TextInput style={styles.input} placeholder="Gemiddelde afstand (km)" value={form.avg_distance} onChangeText={v => handleChange('avg_distance', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Laatste latitude" value={form.last_lat} onChangeText={v => handleChange('last_lat', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Laatste longitude" value={form.last_lng} onChangeText={v => handleChange('last_lng', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Beschikbaarheid" value={form.availability} onChangeText={v => handleChange('availability', v)} />
        </>
      )}
      <TextInput style={styles.input} placeholder="Wachtwoord" value={form.password} onChangeText={v => handleChange('password', v)} secureTextEntry />
      <Button title={isLogin ? 'Inloggen' : 'Registreren'} onPress={isLogin ? handleLogin : handleRegister} />
      <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
        <Text style={styles.toggleText}>
          {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
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
