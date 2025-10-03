import React, { useState } from 'react';
import React, { useState } from 'react';
import {
import {
  View,
  View,
  Text,
  Text,
  TextInput,
  TextInput,
  Button,
  Button,
  Alert,
  Alert,
  ScrollView,
  ScrollView,
  StyleSheet,
  StyleSheet,
  TouchableOpacity
  TouchableOpacity
} from 'react-native';
} from 'react-native';


export default function App() {
export default function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
  const [form, setForm] = useState({
    username: '',
    username: '',
    name: '',
    name: '',
    age: '',
    age: '',
    bio: '',
    bio: '',
    sport_type: '',
    sport_type: '',
    avg_distance: '',
    avg_distance: '',
    last_lat: '',
    last_lat: '',
    last_lng: '',
    last_lng: '',
    availability: '',
    availability: '',
    password: ''
    password: ''
  });
  });
const [errors, setErrors] = useState({});
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);


  const handleChange = (key, value) => {
  const handleChange = (key, value) => {
    setForm({ ...form, [key]: value });
    setForm({ ...form, [key]: value });
  };
  };


  const handleLogin = async () => {
  const handleLogin = async () => {
    try {
    try {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/login', {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/login', {
        method: 'POST',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: form.username, password: form.password })
        body: JSON.stringify({ username: form.username, password: form.password })
      });
      });
      const data = await response.text();
      const data = await response.text();
      if (response.ok) {
      if (response.ok) {
        Alert.alert('Login gelukt', data);
        Alert.alert('Login gelukt', data);
        setIsAuthenticated(true);
        setIsAuthenticated(true);
      } else {
      } else {
        Alert.alert('Login mislukt', data);
        Alert.alert('Login mislukt', data);
      }
      }
    } catch (error) {
    } catch (error) {
      Alert.alert('Fout', error.message);
      Alert.alert('Fout', error.message);
    }
    }
  };
  };


  const handleRegister = async () => {
    const newErrors = {};
    const requiredFields = [
    const requiredFields = [
      'username', 'name', 'age', 'sport_type',
      'username', 'name', 'age', 'sport_type',
      'avg_distance', 'last_lat', 'last_lng',
      'avg_distance', 'last_lat', 'last_lng',
      'availability', 'password'
      'availability', 'password'
    ];
    ];
    for (let field of requiredFields) {
    for (let field of requiredFields) {
      if (!form[field] || form[field].toString().trim() === '') {
      if (!form[field] || form[field].toString().trim() === '') {
        newErrors['${field}'] = 'Verplicht veld';
        return;
      }
      }
    }
    }
    if (isNaN(parseInt(form.age)) || parseInt(form.age) < 18 || parseInt(form.age) > 99) {
    if (isNaN(parseInt(form.age)) || parseInt(form.age) < 18 || parseInt(form.age) > 99) {
        newErrors['age'] = 'Leeftijd moet tussen 18 en 99 zijn';
      return;
    }
    }
    if (form.password.length < 8) {
    if (form.password.length < 8) {
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    } else {
      setErrors({});
    }
        newErrors['password'] = 'Minimaal 8 karakters';
      return;
    }
    }


    try {
    try {
      const payload = {
      const payload = {
        username: form.username,
        username: form.username,
        name: form.name,
        name: form.name,
        age: parseInt(form.age),
        age: parseInt(form.age),
        bio: form.bio,
        bio: form.bio,
        sport_type: form.sport_type,
        sport_type: form.sport_type,
        avg_distance: parseFloat(form.avg_distance),
        avg_distance: parseFloat(form.avg_distance),
        last_lat: parseFloat(form.last_lat),
        last_lat: parseFloat(form.last_lat),
        last_lng: parseFloat(form.last_lng),
        last_lng: parseFloat(form.last_lng),
        availability: form.availability,
        availability: form.availability,
        password: form.password
        password: form.password
      };
      };
      const response = await fetch('https://web-production-ec0bc.up.railway.app/register', {
      const response = await fetch('https://web-production-ec0bc.up.railway.app/register', {
        method: 'POST',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
        body: JSON.stringify(payload)
      });
      });
      const data = await response.text();
      const data = await response.text();
      if (response.ok) {
      if (response.ok) {
        Alert.alert('Registratie gelukt', data);
        Alert.alert('Registratie gelukt', data);
        setIsAuthenticated(true);
        setIsAuthenticated(true);
      } else {
      } else {
        Alert.alert('Registratie mislukt', data);
        Alert.alert('Registratie mislukt', data);
      }
      }
    } catch (error) {
    } catch (error) {
      Alert.alert('Fout', error.message);
      Alert.alert('Fout', error.message);
    }
    }
  };
  };


  if (isAuthenticated) {
  if (isAuthenticated) {
    return (
    return (
      <View style={styles.container}>
      <View style={styles.container}>
        <Text style={styles.title}>Welkom, {form.username}!</Text>
        <Text style={styles.title}>Welkom, {form.username}!</Text>
        <Text style={styles.subtitle}>Je bent nu ingelogd.</Text>
        <Text style={styles.subtitle}>Je bent nu ingelogd.</Text>
        <Button title="Uitloggen" onPress={() => setIsAuthenticated(false)} />
        <Button title="Uitloggen" onPress={() => setIsAuthenticated(false)} />
      </View>
      </View>
    );
    );
  }
  }


  return (
  return (
    <ScrollView contentContainerStyle={styles.container}>
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{isLogin ? 'Login' : 'Registreren'}</Text>
      <Text style={styles.title}>{isLogin ? 'Login' : 'Registreren'}</Text>
      <TextInput style={styles.input} placeholder="Gebruikersnaam" value={form.username} onChangeText={v => handleChange('username', v)} />
      <TextInput style={styles.input} placeholder="Gebruikersnaam" value={form.username} onChangeText={v => handleChange('username', v)} />
{errors.username && <Text style={{styles.error}}>{errors.username}</Text>}
      {!isLogin && (
      {!isLogin && (
        <>
        <>
          <TextInput style={styles.input} placeholder="Naam" value={form.name} onChangeText={v => handleChange('name', v)} />
          <TextInput style={styles.input} placeholder="Naam" value={form.name} onChangeText={v => handleChange('name', v)} />
{errors.name && <Text style={{styles.error}}>{errors.name}</Text>}
          <TextInput style={styles.input} placeholder="Leeftijd" value={form.age} onChangeText={v => handleChange('age', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Leeftijd" value={form.age} onChangeText={v => handleChange('age', v)} keyboardType="numeric" />
{errors.age && <Text style={{styles.error}}>{errors.age}</Text>}
          <TextInput style={styles.input} placeholder="Bio" value={form.bio} onChangeText={v => handleChange('bio', v)} />
          <TextInput style={styles.input} placeholder="Bio" value={form.bio} onChangeText={v => handleChange('bio', v)} />
{errors.bio && <Text style={{styles.error}}>{errors.bio}</Text>}
          <TextInput style={styles.input} placeholder="Sporttype" value={form.sport_type} onChangeText={v => handleChange('sport_type', v)} />
          <TextInput style={styles.input} placeholder="Sporttype" value={form.sport_type} onChangeText={v => handleChange('sport_type', v)} />
{errors.sport_type && <Text style={{styles.error}}>{errors.sport_type}</Text>}
          <TextInput style={styles.input} placeholder="Gemiddelde afstand (km)" value={form.avg_distance} onChangeText={v => handleChange('avg_distance', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Gemiddelde afstand (km)" value={form.avg_distance} onChangeText={v => handleChange('avg_distance', v)} keyboardType="numeric" />
{errors.avg_distance && <Text style={{styles.error}}>{errors.avg_distance}</Text>}
          <TextInput style={styles.input} placeholder="Laatste latitude" value={form.last_lat} onChangeText={v => handleChange('last_lat', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Laatste latitude" value={form.last_lat} onChangeText={v => handleChange('last_lat', v)} keyboardType="numeric" />
{errors.last_lat && <Text style={{styles.error}}>{errors.last_lat}</Text>}
          <TextInput style={styles.input} placeholder="Laatste longitude" value={form.last_lng} onChangeText={v => handleChange('last_lng', v)} keyboardType="numeric" />
          <TextInput style={styles.input} placeholder="Laatste longitude" value={form.last_lng} onChangeText={v => handleChange('last_lng', v)} keyboardType="numeric" />
{errors.last_lng && <Text style={{styles.error}}>{errors.last_lng}</Text>}
          <TextInput style={styles.input} placeholder="Beschikbaarheid" value={form.availability} onChangeText={v => handleChange('availability', v)} />
          <TextInput style={styles.input} placeholder="Beschikbaarheid" value={form.availability} onChangeText={v => handleChange('availability', v)} />
{errors.availability && <Text style={{styles.error}}>{errors.availability}</Text>}
        </>
        </>
      )}
      )}
      <TextInput style={styles.input} placeholder="Wachtwoord" value={form.password} onChangeText={v => handleChange('password', v)} secureTextEntry />
      <TextInput style={styles.input} placeholder="Wachtwoord" value={form.password} onChangeText={v => handleChange('password', v)} secureTextEntry />
{errors.password && <Text style={{styles.error}}>{errors.password}</Text>}
      <Button title={isLogin ? 'Inloggen' : 'Registreren'} onPress={isLogin ? handleLogin : handleRegister} />
      <Button title={isLogin ? 'Inloggen' : 'Registreren'} onPress={isLogin ? handleLogin : handleRegister} />
      <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
      <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
        <Text style={styles.toggleText}>
        <Text style={styles.toggleText}>
          {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
          {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
        </Text>
        </Text>
      </TouchableOpacity>
      </TouchableOpacity>
    </ScrollView>
    </ScrollView>
  );
  );
}
}


const styles = StyleSheet.create({
const styles = StyleSheet.create({
  container: {
  container: {
    flexGrow: 1,
    flexGrow: 1,
    backgroundColor: '#fff',
    backgroundColor: '#fff',
    justifyContent: 'center',
    justifyContent: 'center',
    padding: 20
    padding: 20
  },
  },
  title: {
  title: {
    fontSize: 24,
    fontSize: 24,
    marginBottom: 20,
    marginBottom: 20,
    textAlign: 'center'
    textAlign: 'center'
  },
  },
  subtitle: {
  subtitle: {
    fontSize: 18,
    fontSize: 18,
    marginBottom: 20,
    marginBottom: 20,
    textAlign: 'center',
    textAlign: 'center',
    color: '#555'
    color: '#555'
  },
  },
  input: {
  input: {
    height: 40,
    height: 40,
    borderColor: '#999',
    borderColor: '#999',
    borderWidth: 1,
    borderWidth: 1,
    marginBottom: 12,
    marginBottom: 12,
    paddingHorizontal: 10,
    paddingHorizontal: 10,
    borderRadius: 5
    borderRadius: 5
  },
  },
  toggleText: {
error: {
    color: 'red',
    marginBottom: 8,
    marginLeft: 4
  },
  toggleText: {
    marginTop: 15,
    marginTop: 15,
    color: 'blue',
    color: 'blue',
    textAlign: 'center'
    textAlign: 'center'
  }
  }
});
});
