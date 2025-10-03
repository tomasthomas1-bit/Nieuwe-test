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
const [errors, setErrors] = useState({});
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
      const data = await response.text();
      if (response.ok) {
        Alert.alert('Login gelukt', data);
        setIsAuthenticated(true);
      } else {
        Alert.alert('Login mislukt', data);
      }
    } catch (error) {
      Alert.alert('Fout', error.message);
  const handleRegister = async () => {
    const newErrors = {};
    const requiredFields = [
      'username', 'name', 'age', 'sport_type',
      'avg_distance', 'last_lat', 'last_lng',
      'availability', 'password'
    ];
    for (let field of requiredFields) {
    if (!form[field] || form[field].toString().trim() === '') {
        newErrors[field] = 'Verplicht veld';
    }
}
    if (isNaN(parseInt(form.age)) || parseInt(form.age) < 18 || parseInt(form.age) > 99) {
        newErrors['age'] = 'Leeftijd moet tussen 18 en 99 zijn';
    if (form.password.length < 8) {
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setErrors({});
        newErrors['password'] = 'Minimaal 8 karakters';
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
      const response = await fetch('https://web-production-ec0bc.up.railway.app/register', {
        body: JSON.stringify(payload)
        Alert.alert('Registratie gelukt', data);
        Alert.alert('Registratie mislukt', data);
  if (isAuthenticated) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Welkom, {form.username}!</Text>
        <Text style={styles.subtitle}>Je bent nu ingelogd.</Text>
        <Button title="Uitloggen" onPress={() => setIsAuthenticated(false)} />
      </View>
    );
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{isLogin ? 'Login' : 'Registreren'}</Text>
      <TextInput style={styles.input} placeholder="Gebruikersnaam" value={form.username} onChangeText={v => handleChange('username', v)} />
{errors.username && <Text style={{styles.error}}>{errors.username}</Text>}
      {!isLogin && (
        <>
          <TextInput style={styles.input} placeholder="Naam" value={form.name} onChangeText={v => handleChange('name', v)} />
{errors.name && <Text style={{styles.error}}>{errors.name}</Text>}
          <TextInput style={styles.input} placeholder="Leeftijd" value={form.age} onChangeText={v => handleChange('age', v)} keyboardType="numeric" />
{errors.age && <Text style={{styles.error}}>{errors.age}</Text>}
          <TextInput style={styles.input} placeholder="Bio" value={form.bio} onChangeText={v => handleChange('bio', v)} />
{errors.bio && <Text style={{styles.error}}>{errors.bio}</Text>}
          <TextInput style={styles.input} placeholder="Sporttype" value={form.sport_type} onChangeText={v => handleChange('sport_type', v)} />
{errors.sport_type && <Text style={{styles.error}}>{errors.sport_type}</Text>}
          <TextInput style={styles.input} placeholder="Gemiddelde afstand (km)" value={form.avg_distance} onChangeText={v => handleChange('avg_distance', v)} keyboardType="numeric" />
{errors.avg_distance && <Text style={{styles.error}}>{errors.avg_distance}</Text>}
          <TextInput style={styles.input} placeholder="Laatste latitude" value={form.last_lat} onChangeText={v => handleChange('last_lat', v)} keyboardType="numeric" />
{errors.last_lat && <Text style={{styles.error}}>{errors.last_lat}</Text>}
          <TextInput style={styles.input} placeholder="Laatste longitude" value={form.last_lng} onChangeText={v => handleChange('last_lng', v)} keyboardType="numeric" />
{errors.last_lng && <Text style={{styles.error}}>{errors.last_lng}</Text>}
          <TextInput style={styles.input} placeholder="Beschikbaarheid" value={form.availability} onChangeText={v => handleChange('availability', v)} />
{errors.availability && <Text style={{styles.error}}>{errors.availability}</Text>}
        </>
      )}
      <TextInput style={styles.input} placeholder="Wachtwoord" value={form.password} onChangeText={v => handleChange('password', v)} secureTextEntry />
{errors.password && <Text style={{styles.error}}>{errors.password}</Text>}
      <Button title={isLogin ? 'Inloggen' : 'Registreren'} onPress={isLogin ? handleLogin : handleRegister} />
      <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
        <Text style={styles.toggleText}>
          {isLogin ? 'Nog geen account? Registreer hier.' : 'Heb je al een account? Log in.'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
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
  subtitle: {
    fontSize: 18,
    textAlign: 'center',
    color: '#555'
  input: {
    height: 40,
    borderColor: '#999',
    borderWidth: 1,
    marginBottom: 12,
    paddingHorizontal: 10,
    borderRadius: 5
  toggleText: {
error: {
    color: 'red',
    marginBottom: 8,
    marginLeft: 4
    marginTop: 15,
    color: 'blue',