
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
  useRef,
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

/* ================= TRANSLATIONS ================= */
const translations = {
  nl: {
    login: 'Inloggen', register: 'Registreren', username: 'Gebruikersnaam', password: 'Wachtwoord',
    name: 'Naam', age: 'Leeftijd', bio: 'Bio', email: 'E-mail', verifyEmail: 'E-mail verifiëren',
    discover: 'Ontdekken', matches: 'Matches', chat: 'Chat', profile: 'Profiel',
    settings: 'Instellingen', logout: 'Uitloggen', save: 'Opslaan', cancel: 'Annuleren',
    workouts: 'Workouts', distance: 'Afstand', hours: 'Uren', kmAway: 'km verderop',
    like: 'Like', dislike: 'Dislike', noMoreProfiles: 'Geen profielen meer om te tonen',
    itsAMatch: 'It\'s a Match!', sendMessage: 'Stuur bericht', keepSwiping: 'Doorgaan met swipen',
    typeMessage: 'Typ een bericht...', send: 'Verstuur', noMessages: 'Nog geen berichten',
    matchGoal: 'Match-doel', preferredGender: 'Voorkeur geslacht', maxDistance: 'Maximale afstand (km)',
    minAge: 'Minimum leeftijd', maxAge: 'Maximum leeftijd', notifications: 'Pushmeldingen',
    saveSettings: 'Instellingen opslaan', settingsSaved: 'Instellingen opgeslagen!', saveProfile: 'Profiel opslaan', photos: 'Foto\'s',
    uploadPhoto: 'Upload foto', setAsProfile: 'Als profielfoto', deletePhoto: 'Verwijder',
    availability: 'Beschikbaarheid', saveAvailability: 'Beschikbaarheden opslaan',
    availabilities: 'Beschikbaarheden', availabilitySaved: 'Opgeslagen',
    addViaUrl: 'Voeg toe via URL', notSupported: 'Niet ondersteund',
    addViaUrlMessage: '"Voeg toe via URL" is beschikbaar op web en iOS. Voeg voorlopig foto\'s toe via toestel-upload of web.',
    monday: 'Ma', tuesday: 'Di', wednesday: 'Wo', thursday: 'Do', friday: 'Vr', saturday: 'Za', sunday: 'Zo',
    morning: 'Ochtend', afternoon: 'Middag', evening: 'Avond',
    friendship: 'vriendschap', training_partner: 'trainingspartner', competition: 'competitie',
    coaching: 'coaching', any: 'elk', male: 'man', female: 'vrouw', non_binary: 'non-binair',
    profileSettings: 'Profielinstellingen', language: 'Taal / Language',
    ageRange18to99: 'Leeftijd moet tussen 18 en 99 zijn', nameRequired: 'Naam is verplicht',
    allFieldsRequired: 'Alle velden zijn verplicht', passwordMin6: 'Wachtwoord min 8 tekens',
    findYourFit: 'Vind je sportmaatje.',
    verificationSent: 'Een verificatiemail is verzonden. Controleer je inbox en klik op de link om je account te activeren.',
    enterVerificationCode: 'Voer de verificatiecode in uit je e-mail',
    code: 'Code', verify: 'Verifiëren', resendCode: 'Code opnieuw versturen',
    sessionExpired: 'Sessie verlopen', sessionExpiredMessage: 'Log opnieuw in a.u.b.',
    logoutConfirm: 'Weet je zeker dat je wil uitloggen?',
    profilePhoto: 'Profielfoto',
    theme: 'Thema', system: 'Systeem', light: 'Licht', dark: 'Donker',
    chatStyle: 'Chat-stijl',
    preferencesStored: 'Je keuzes worden lokaal opgeslagen en blijven behouden bij de volgende app-start.',
    ageExample: 'bv. 25',
    loginFailed: 'Login mislukt', registrationFailed: 'Registratie mislukt',
    profileLoadFailed: 'Profiel laden mislukt', profileSaveFailed: 'Profiel opslaan mislukt',
    noUserIdAvailable: 'Geen userId beschikbaar',
  },
  en: {
    login: 'Login', register: 'Register', username: 'Username', password: 'Password',
    name: 'Name', age: 'Age', bio: 'Bio', email: 'Email', verifyEmail: 'Verify Email',
    discover: 'Discover', matches: 'Matches', chat: 'Chat', profile: 'Profile',
    settings: 'Settings', logout: 'Logout', save: 'Save', cancel: 'Cancel',
    workouts: 'Workouts', distance: 'Distance', hours: 'Hours', kmAway: 'km away',
    like: 'Like', dislike: 'Dislike', noMoreProfiles: 'No more profiles to show',
    itsAMatch: 'It\'s a Match!', sendMessage: 'Send Message', keepSwiping: 'Keep Swiping',
    typeMessage: 'Type a message...', send: 'Send', noMessages: 'No messages yet',
    matchGoal: 'Match goal', preferredGender: 'Preferred gender', maxDistance: 'Max distance (km)',
    minAge: 'Minimum age', maxAge: 'Maximum age', notifications: 'Push notifications',
    saveSettings: 'Save Settings', settingsSaved: 'Settings saved!', saveProfile: 'Save Profile', photos: 'Photos',
    uploadPhoto: 'Upload photo', setAsProfile: 'Set as profile', deletePhoto: 'Delete',
    availability: 'Availability', saveAvailability: 'Save Availability',
    availabilities: 'Availabilities', availabilitySaved: 'Saved',
    addViaUrl: 'Add via URL', notSupported: 'Not supported',
    addViaUrlMessage: '"Add via URL" is available on web and iOS. For now, add photos via device upload or web.',
    monday: 'Mo', tuesday: 'Tu', wednesday: 'We', thursday: 'Th', friday: 'Fr', saturday: 'Sa', sunday: 'Su',
    morning: 'Morning', afternoon: 'Afternoon', evening: 'Evening',
    friendship: 'friendship', training_partner: 'training partner', competition: 'competition',
    coaching: 'coaching', any: 'any', male: 'male', female: 'female', non_binary: 'non-binary',
    profileSettings: 'Profile Settings', language: 'Language / Taal',
    ageRange18to99: 'Age must be between 18 and 99', nameRequired: 'Name is required',
    allFieldsRequired: 'All fields are required', passwordMin6: 'Password min 8 chars',
    findYourFit: 'Find your fit.',
    verificationSent: 'A verification email has been sent. Check your inbox and click the link to activate your account.',
    enterVerificationCode: 'Enter the verification code from your email',
    code: 'Code', verify: 'Verify', resendCode: 'Resend Code',
    sessionExpired: 'Session expired', sessionExpiredMessage: 'Please log in again.',
    logoutConfirm: 'Are you sure you want to log out?',
    profilePhoto: 'Profile photo',
    theme: 'Theme', system: 'System', light: 'Light', dark: 'Dark',
    chatStyle: 'Chat style',
    preferencesStored: 'Your choices are stored locally and will be retained on next app start.',
    ageExample: 'e.g. 25',
    loginFailed: 'Login failed', registrationFailed: 'Registration failed',
    profileLoadFailed: 'Failed to load profile', profileSaveFailed: 'Failed to save profile',
    noUserIdAvailable: 'No user ID available',
  },
  fr: {
    login: 'Connexion', register: 'S\'inscrire', username: 'Nom d\'utilisateur', password: 'Mot de passe',
    name: 'Nom', age: 'Âge', bio: 'Bio', email: 'Email', verifyEmail: 'Vérifier l\'email',
    discover: 'Découvrir', matches: 'Matchs', chat: 'Chat', profile: 'Profil',
    settings: 'Paramètres', logout: 'Déconnexion', save: 'Enregistrer', cancel: 'Annuler',
    workouts: 'Entraînements', distance: 'Distance', hours: 'Heures', kmAway: 'km',
    like: 'J\'aime', dislike: 'Je n\'aime pas', noMoreProfiles: 'Plus de profils à afficher',
    itsAMatch: 'C\'est un Match!', sendMessage: 'Envoyer un message', keepSwiping: 'Continuer',
    typeMessage: 'Tapez un message...', send: 'Envoyer', noMessages: 'Pas encore de messages',
    matchGoal: 'Objectif de match', preferredGender: 'Genre préféré', maxDistance: 'Distance max (km)',
    minAge: 'Âge minimum', maxAge: 'Âge maximum', notifications: 'Notifications push',
    saveSettings: 'Enregistrer', settingsSaved: 'Paramètres enregistrés!', saveProfile: 'Enregistrer le profil', photos: 'Photos',
    uploadPhoto: 'Télécharger photo', setAsProfile: 'Définir comme profil', deletePhoto: 'Supprimer',
    availability: 'Disponibilité', saveAvailability: 'Enregistrer',
    availabilities: 'Disponibilités', availabilitySaved: 'Enregistré',
    addViaUrl: 'Ajouter via URL', notSupported: 'Non supporté',
    addViaUrlMessage: '"Ajouter via URL" est disponible sur web et iOS. Pour l\'instant, ajoutez des photos via le téléchargement depuis l\'appareil ou le web.',
    monday: 'Lu', tuesday: 'Ma', wednesday: 'Me', thursday: 'Je', friday: 'Ve', saturday: 'Sa', sunday: 'Di',
    morning: 'Matin', afternoon: 'Après-midi', evening: 'Soir',
    friendship: 'amitié', training_partner: 'partenaire d\'entraînement', competition: 'compétition',
    coaching: 'coaching', any: 'tout', male: 'homme', female: 'femme', non_binary: 'non-binaire',
    profileSettings: 'Paramètres du profil', language: 'Langue / Language',
    ageRange18to99: 'L\'âge doit être entre 18 et 99', nameRequired: 'Le nom est requis',
    allFieldsRequired: 'Tous les champs sont requis', passwordMin6: 'Mot de passe min 8 caractères',
    findYourFit: 'Trouvez votre partenaire.',
    verificationSent: 'Un email de vérification a été envoyé. Vérifiez votre boîte de réception.',
    enterVerificationCode: 'Entrez le code de vérification de votre email',
    code: 'Code', verify: 'Vérifier', resendCode: 'Renvoyer le code',
    sessionExpired: 'Session expirée', sessionExpiredMessage: 'Veuillez vous reconnecter.',
    logoutConfirm: 'Voulez-vous vraiment vous déconnecter?',
    profilePhoto: 'Photo de profil',
    theme: 'Thème', system: 'Système', light: 'Clair', dark: 'Sombre',
    chatStyle: 'Style de chat',
    preferencesStored: 'Vos choix sont stockés localement et seront conservés au prochain démarrage.',
    ageExample: 'ex. 25',
    loginFailed: 'Connexion échouée', registrationFailed: 'Inscription échouée',
    profileLoadFailed: 'Échec du chargement du profil', profileSaveFailed: 'Échec de l\'enregistrement du profil',
    noUserIdAvailable: 'Aucun ID utilisateur disponible',
  },
  de: {
    login: 'Anmelden', register: 'Registrieren', username: 'Benutzername', password: 'Passwort',
    name: 'Name', age: 'Alter', bio: 'Bio', email: 'E-Mail', verifyEmail: 'E-Mail verifizieren',
    discover: 'Entdecken', matches: 'Matches', chat: 'Chat', profile: 'Profil',
    settings: 'Einstellungen', logout: 'Abmelden', save: 'Speichern', cancel: 'Abbrechen',
    workouts: 'Workouts', distance: 'Entfernung', hours: 'Stunden', kmAway: 'km entfernt',
    like: 'Gefällt mir', dislike: 'Gefällt nicht', noMoreProfiles: 'Keine Profile mehr',
    itsAMatch: 'Es ist ein Match!', sendMessage: 'Nachricht senden', keepSwiping: 'Weiter swipen',
    typeMessage: 'Nachricht eingeben...', send: 'Senden', noMessages: 'Noch keine Nachrichten',
    matchGoal: 'Match-Ziel', preferredGender: 'Bevorzugtes Geschlecht', maxDistance: 'Max. Entfernung (km)',
    minAge: 'Mindestalter', maxAge: 'Höchstalter', notifications: 'Push-Benachrichtigungen',
    saveSettings: 'Einstellungen speichern', settingsSaved: 'Einstellungen gespeichert!', saveProfile: 'Profil speichern', photos: 'Fotos',
    uploadPhoto: 'Foto hochladen', setAsProfile: 'Als Profil', deletePhoto: 'Löschen',
    availability: 'Verfügbarkeit', saveAvailability: 'Verfügbarkeit speichern',
    availabilities: 'Verfügbarkeiten', availabilitySaved: 'Gespeichert',
    addViaUrl: 'Per URL hinzufügen', notSupported: 'Nicht unterstützt',
    addViaUrlMessage: '"Per URL hinzufügen" ist auf Web und iOS verfügbar. Fügen Sie vorerst Fotos über Geräte-Upload oder Web hinzu.',
    monday: 'Mo', tuesday: 'Di', wednesday: 'Mi', thursday: 'Do', friday: 'Fr', saturday: 'Sa', sunday: 'So',
    morning: 'Morgen', afternoon: 'Nachmittag', evening: 'Abend',
    friendship: 'Freundschaft', training_partner: 'Trainingspartner', competition: 'Wettbewerb',
    coaching: 'Coaching', any: 'alle', male: 'Mann', female: 'Frau', non_binary: 'nicht-binär',
    profileSettings: 'Profileinstellungen', language: 'Sprache / Language',
    ageRange18to99: 'Alter muss zwischen 18 und 99 liegen', nameRequired: 'Name ist erforderlich',
    allFieldsRequired: 'Alle Felder sind erforderlich', passwordMin6: 'Passwort mind. 8 Zeichen',
    findYourFit: 'Finde deinen Sportpartner.',
    verificationSent: 'Eine Verifizierungs-E-Mail wurde gesendet. Überprüfen Sie Ihren Posteingang.',
    enterVerificationCode: 'Geben Sie den Verifizierungscode aus Ihrer E-Mail ein',
    code: 'Code', verify: 'Verifizieren', resendCode: 'Code erneut senden',
    sessionExpired: 'Sitzung abgelaufen', sessionExpiredMessage: 'Bitte melden Sie sich erneut an.',
    logoutConfirm: 'Möchten Sie sich wirklich abmelden?',
    profilePhoto: 'Profilfoto',
    theme: 'Thema', system: 'System', light: 'Hell', dark: 'Dunkel',
    chatStyle: 'Chat-Stil',
    preferencesStored: 'Ihre Einstellungen werden lokal gespeichert und beim nächsten Start beibehalten.',
    ageExample: 'z.B. 25',
    loginFailed: 'Anmeldung fehlgeschlagen', registrationFailed: 'Registrierung fehlgeschlagen',
    profileLoadFailed: 'Profil konnte nicht geladen werden', profileSaveFailed: 'Profil konnte nicht gespeichert werden',
    noUserIdAvailable: 'Keine Benutzer-ID verfügbar',
  },
  es: {
    login: 'Iniciar sesión', register: 'Registrarse', username: 'Nombre de usuario', password: 'Contraseña',
    name: 'Nombre', age: 'Edad', bio: 'Bio', email: 'Correo', verifyEmail: 'Verificar correo',
    discover: 'Descubrir', matches: 'Matches', chat: 'Chat', profile: 'Perfil',
    settings: 'Ajustes', logout: 'Cerrar sesión', save: 'Guardar', cancel: 'Cancelar',
    workouts: 'Entrenamientos', distance: 'Distancia', hours: 'Horas', kmAway: 'km',
    like: 'Me gusta', dislike: 'No me gusta', noMoreProfiles: 'No hay más perfiles',
    itsAMatch: '¡Es un Match!', sendMessage: 'Enviar mensaje', keepSwiping: 'Seguir deslizando',
    typeMessage: 'Escribe un mensaje...', send: 'Enviar', noMessages: 'Sin mensajes aún',
    matchGoal: 'Objetivo de match', preferredGender: 'Género preferido', maxDistance: 'Distancia máx (km)',
    minAge: 'Edad mínima', maxAge: 'Edad máxima', notifications: 'Notificaciones push',
    saveSettings: 'Guardar ajustes', settingsSaved: '¡Ajustes guardados!', saveProfile: 'Guardar perfil', photos: 'Fotos',
    uploadPhoto: 'Subir foto', setAsProfile: 'Como perfil', deletePhoto: 'Eliminar',
    availability: 'Disponibilidad', saveAvailability: 'Guardar disponibilidad',
    availabilities: 'Disponibilidades', availabilitySaved: 'Guardado',
    addViaUrl: 'Añadir por URL', notSupported: 'No soportado',
    addViaUrlMessage: '"Añadir por URL" está disponible en web e iOS. Por ahora, añade fotos mediante carga desde dispositivo o web.',
    monday: 'Lu', tuesday: 'Ma', wednesday: 'Mi', thursday: 'Ju', friday: 'Vi', saturday: 'Sá', sunday: 'Do',
    morning: 'Mañana', afternoon: 'Tarde', evening: 'Noche',
    friendship: 'amistad', training_partner: 'compañero de entrenamiento', competition: 'competición',
    coaching: 'coaching', any: 'cualquiera', male: 'hombre', female: 'mujer', non_binary: 'no binario',
    profileSettings: 'Ajustes del perfil', language: 'Idioma / Language',
    ageRange18to99: 'La edad debe estar entre 18 y 99', nameRequired: 'El nombre es obligatorio',
    allFieldsRequired: 'Todos los campos son obligatorios', passwordMin6: 'Contraseña mín 8 caracteres',
    findYourFit: 'Encuentra tu compañero.',
    verificationSent: 'Se ha enviado un correo de verificación. Revisa tu bandeja de entrada.',
    enterVerificationCode: 'Ingresa el código de verificación de tu correo',
    code: 'Código', verify: 'Verificar', resendCode: 'Reenviar código',
    sessionExpired: 'Sesión expirada', sessionExpiredMessage: 'Por favor, inicia sesión nuevamente.',
    logoutConfirm: '¿Estás seguro de que quieres cerrar sesión?',
    profilePhoto: 'Foto de perfil',
    theme: 'Tema', system: 'Sistema', light: 'Claro', dark: 'Oscuro',
    chatStyle: 'Estilo de chat',
    preferencesStored: 'Tus opciones se guardan localmente y se mantendrán en el próximo inicio.',
    ageExample: 'ej. 25',
    loginFailed: 'Inicio de sesión fallido', registrationFailed: 'Registro fallido',
    profileLoadFailed: 'Error al cargar el perfil', profileSaveFailed: 'Error al guardar el perfil',
    noUserIdAvailable: 'ID de usuario no disponible',
  },
  it: {
    login: 'Accedi', register: 'Registrati', username: 'Nome utente', password: 'Password',
    name: 'Nome', age: 'Età', bio: 'Bio', email: 'Email', verifyEmail: 'Verifica email',
    discover: 'Scopri', matches: 'Match', chat: 'Chat', profile: 'Profilo',
    settings: 'Impostazioni', logout: 'Esci', save: 'Salva', cancel: 'Annulla',
    workouts: 'Allenamenti', distance: 'Distanza', hours: 'Ore', kmAway: 'km',
    like: 'Mi piace', dislike: 'Non mi piace', noMoreProfiles: 'Nessun altro profilo',
    itsAMatch: 'È un Match!', sendMessage: 'Invia messaggio', keepSwiping: 'Continua a scorrere',
    typeMessage: 'Scrivi un messaggio...', send: 'Invia', noMessages: 'Nessun messaggio ancora',
    matchGoal: 'Obiettivo match', preferredGender: 'Genere preferito', maxDistance: 'Distanza max (km)',
    minAge: 'Età minima', maxAge: 'Età massima', notifications: 'Notifiche push',
    saveSettings: 'Salva impostazioni', settingsSaved: 'Impostazioni salvate!', saveProfile: 'Salva profilo', photos: 'Foto',
    uploadPhoto: 'Carica foto', setAsProfile: 'Come profilo', deletePhoto: 'Elimina',
    availability: 'Disponibilità', saveAvailability: 'Salva disponibilità',
    availabilities: 'Disponibilità', availabilitySaved: 'Salvato',
    addViaUrl: 'Aggiungi tramite URL', notSupported: 'Non supportato',
    addViaUrlMessage: '"Aggiungi tramite URL" è disponibile su web e iOS. Per ora, aggiungi foto tramite caricamento dal dispositivo o web.',
    monday: 'Lu', tuesday: 'Ma', wednesday: 'Me', thursday: 'Gi', friday: 'Ve', saturday: 'Sa', sunday: 'Do',
    morning: 'Mattina', afternoon: 'Pomeriggio', evening: 'Sera',
    friendship: 'amicizia', training_partner: 'compagno di allenamento', competition: 'competizione',
    coaching: 'coaching', any: 'qualsiasi', male: 'uomo', female: 'donna', non_binary: 'non binario',
    profileSettings: 'Impostazioni profilo', language: 'Lingua / Language',
    ageRange18to99: 'L\'età deve essere tra 18 e 99', nameRequired: 'Il nome è obbligatorio',
    allFieldsRequired: 'Tutti i campi sono obbligatori', passwordMin6: 'Password min 8 caratteri',
    findYourFit: 'Trova il tuo compagno.',
    verificationSent: 'È stata inviata un\'email di verifica. Controlla la tua casella di posta.',
    enterVerificationCode: 'Inserisci il codice di verifica dalla tua email',
    code: 'Codice', verify: 'Verifica', resendCode: 'Invia di nuovo',
    sessionExpired: 'Sessione scaduta', sessionExpiredMessage: 'Effettua nuovamente l\'accesso.',
    logoutConfirm: 'Sei sicuro di voler uscire?',
    profilePhoto: 'Foto profilo',
    theme: 'Tema', system: 'Sistema', light: 'Chiaro', dark: 'Scuro',
    chatStyle: 'Stile chat',
    preferencesStored: 'Le tue preferenze sono salvate localmente e saranno conservate al prossimo avvio.',
    ageExample: 'es. 25',
    loginFailed: 'Accesso fallito', registrationFailed: 'Registrazione fallita',
    profileLoadFailed: 'Impossibile caricare il profilo', profileSaveFailed: 'Impossibile salvare il profilo',
    noUserIdAvailable: 'ID utente non disponibile',
  },
  pt: {
    login: 'Entrar', register: 'Registrar', username: 'Nome de usuário', password: 'Senha',
    name: 'Nome', age: 'Idade', bio: 'Bio', email: 'Email', verifyEmail: 'Verificar email',
    discover: 'Descobrir', matches: 'Matches', chat: 'Chat', profile: 'Perfil',
    settings: 'Configurações', logout: 'Sair', save: 'Salvar', cancel: 'Cancelar',
    workouts: 'Treinos', distance: 'Distância', hours: 'Horas', kmAway: 'km',
    like: 'Curtir', dislike: 'Não curtir', noMoreProfiles: 'Sem mais perfis',
    itsAMatch: 'É um Match!', sendMessage: 'Enviar mensagem', keepSwiping: 'Continuar deslizando',
    typeMessage: 'Digite uma mensagem...', send: 'Enviar', noMessages: 'Sem mensagens ainda',
    matchGoal: 'Objetivo de match', preferredGender: 'Gênero preferido', maxDistance: 'Distância máx (km)',
    minAge: 'Idade mínima', maxAge: 'Idade máxima', notifications: 'Notificações push',
    saveSettings: 'Salvar configurações', settingsSaved: 'Configurações salvas!', saveProfile: 'Salvar perfil', photos: 'Fotos',
    uploadPhoto: 'Carregar foto', setAsProfile: 'Como perfil', deletePhoto: 'Excluir',
    availability: 'Disponibilidade', saveAvailability: 'Salvar disponibilidade',
    availabilities: 'Disponibilidades', availabilitySaved: 'Salvo',
    addViaUrl: 'Adicionar via URL', notSupported: 'Não suportado',
    addViaUrlMessage: '"Adicionar via URL" está disponível na web e iOS. Por enquanto, adicione fotos através de upload do dispositivo ou web.',
    monday: 'Seg', tuesday: 'Ter', wednesday: 'Qua', thursday: 'Qui', friday: 'Sex', saturday: 'Sáb', sunday: 'Dom',
    morning: 'Manhã', afternoon: 'Tarde', evening: 'Noite',
    friendship: 'amizade', training_partner: 'parceiro de treino', competition: 'competição',
    coaching: 'coaching', any: 'qualquer', male: 'homem', female: 'mulher', non_binary: 'não-binário',
    profileSettings: 'Configurações do perfil', language: 'Idioma / Language',
    ageRange18to99: 'A idade deve estar entre 18 e 99', nameRequired: 'O nome é obrigatório',
    allFieldsRequired: 'Todos os campos são obrigatórios', passwordMin6: 'Senha mín 8 caracteres',
    findYourFit: 'Encontre seu parceiro.',
    verificationSent: 'Um email de verificação foi enviado. Verifique sua caixa de entrada.',
    enterVerificationCode: 'Digite o código de verificação do seu email',
    code: 'Código', verify: 'Verificar', resendCode: 'Reenviar código',
    sessionExpired: 'Sessão expirada', sessionExpiredMessage: 'Por favor, faça login novamente.',
    logoutConfirm: 'Tem certeza de que deseja sair?',
    profilePhoto: 'Foto de perfil',
    theme: 'Tema', system: 'Sistema', light: 'Claro', dark: 'Escuro',
    chatStyle: 'Estilo de chat',
    preferencesStored: 'Suas escolhas são armazenadas localmente e serão mantidas no próximo início.',
    ageExample: 'ex. 25',
    loginFailed: 'Login falhou', registrationFailed: 'Registro falhou',
    profileLoadFailed: 'Falha ao carregar perfil', profileSaveFailed: 'Falha ao salvar perfil',
    noUserIdAvailable: 'ID de usuário não disponível',
  },
};

const LanguageContext = createContext({ lang: 'nl', setLang: () => {}, t: (key) => key });

// Global ref to access t() function from outside React components
const tFunctionRef = { current: (key) => key };

function LanguageProvider({ children }) {
  const [lang, setLang] = useState('nl');
  
  // Load saved language from SecureStore on mount
  useEffect(() => {
    (async () => {
      try {
        const saved = await SecureStore.getItemAsync('user_language');
        if (saved && translations[saved]) {
          setLang(saved);
        }
      } catch (e) {
        // Ignore - default to 'nl'
      }
    })();
  }, []);
  
  // Custom setLang that also saves to SecureStore
  const setLangPersistent = useCallback(async (newLang) => {
    if (newLang && translations[newLang]) {
      setLang(newLang);
      try {
        await SecureStore.setItemAsync('user_language', newLang);
      } catch (e) {
        // Ignore storage errors
      }
    }
  }, []);
  
  const t = useCallback((key) => {
    return translations[lang]?.[key] || key;
  }, [lang]);
  
  // Update global ref whenever t() changes
  useEffect(() => {
    tFunctionRef.current = t;
  }, [t]);
  
  const value = useMemo(() => ({ lang, setLang: setLangPersistent, t }), [lang, setLangPersistent, t]);
  
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

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
const BASE_URL = 'https://97bfdb52-3064-4532-9a91-48fd1291b1af-00-2t59ltt1vcb8u.riker.replit.dev:8000';
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
        const t = tFunctionRef.current;
        Alert.alert(t('sessionExpired'), t('sessionExpiredMessage'));
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
      const t = tFunctionRef.current;
      const errMsg = data && data.detail ? data.detail : t('loginFailed');
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
      const t = tFunctionRef.current;
      return { ok: false, error: data?.detail ?? t('registrationFailed') };
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
    if (!res.ok) {
      const t = tFunctionRef.current;
      throw new Error(data?.detail ?? `${t('profileLoadFailed')} (status ${res.status})`);
    }
    return data; // { id, username, name, age, bio }
  }, [authFetch]);

  const updateProfile = useCallback(async (partial) => {
    const uid = userId;
    if (!uid) {
      const t = tFunctionRef.current;
      throw new Error(t('noUserIdAvailable'));
    }
    const res = await authFetch(`/users/${uid}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(partial),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const t = tFunctionRef.current;
      throw new Error(data?.detail ?? `${t('profileSaveFailed')} (status ${res.status})`);
    }
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
  const { t } = useContext(LanguageContext);
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
      Alert.alert(t('login'), t('login'));
      navigation.reset({ index: 0, routes: [{ name: 'Main' }] });
    } else {
      Alert.alert(t('login'), error);
    }
  }, [api, form.username, form.password, navigation, t]);

  const handleRegister = useCallback(async () => {
    const e = {};
    ['username', 'name', 'age', 'password'].forEach((r) => {
      if (!form[r] || String(form[r]).trim() === '') e[r] = t('allFieldsRequired');
    });
    const ageNum = parseInt(form.age, 10);
    if (isNaN(ageNum) || ageNum < 18 || ageNum > 99) e.age = t('ageRange18to99');
    if ((form.password ?? '').length < 8) e.password = t('passwordMin6');
    setErrors(e);
    if (Object.keys(e).length) return;

    const { ok, error, data } = await api.register({
      username: form.username,
      name: form.name,
      age: ageNum,
      bio: form.bio,
      password: form.password,
    });
    if (!ok) return Alert.alert(t('register'), error);
    Alert.alert(
      t('register'), 
      data?.message || t('verificationSent'),
      [{ text: 'OK', onPress: () => setIsLogin(true) }]
    );
  }, [api, form, t]);

  const LOGO_TRANSPARENT = 'https://i.imgur.com/hEpZh82.png';
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.color.surface }}>
      <ScrollView contentContainerStyle={styles.authContainer}>
        <LogoBox theme={theme} uri={LOGO_TRANSPARENT} size={120} />
        <Text style={styles.authTitle}>{isLogin ? t('login') : t('register')}</Text>

        <TextInput
          style={styles.input}
          placeholder={t('username')}
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
              placeholder={t('name')}
              value={form.name}
              onChangeText={(v) => set('name', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
            {errors.name ? <Text style={styles.error}>{errors.name}</Text> : null}

            <TextInput
              style={styles.input}
              placeholder={t('age')}
              keyboardType="numeric"
              value={form.age}
              onChangeText={(v) => set('age', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
            {errors.age ? <Text style={styles.error}>{errors.age}</Text> : null}

            <TextInput
              style={styles.input}
              placeholder={t('bio')}
              value={form.bio}
              onChangeText={(v) => set('bio', v)}
              placeholderTextColor={theme.color.textSecondary}
            />
          </>
        ) : null}

        <TextInput
          style={styles.input}
          placeholder={t('password')}
          secureTextEntry
          autoCapitalize="none"
          value={form.password}
          onChangeText={(v) => set('password', v)}
          placeholderTextColor={theme.color.textSecondary}
        />
        {errors.password ? <Text style={styles.error}>{errors.password}</Text> : null}

        <TouchableOpacity onPress={isLogin ? handleLogin : handleRegister} style={styles.primaryBtn}>
          <Text style={styles.primaryBtnText}>{isLogin ? t('login') : t('register')}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setIsLogin(!isLogin)} style={{ marginTop: theme.gap.m }}>
          <Text style={styles.switchText}>
            {isLogin ? t('register') : t('login')}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

/* ---- DiscoverScreen ---- */
function DiscoverScreen({ api, theme, user }) {
  const { t } = useContext(LanguageContext);
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [suggestions, setSuggestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [swiping, setSwiping] = useState(false);
  const [matchCount, setMatchCount] = useState(12);
  const [stats, setStats] = useState({ workouts: 24, distance: 185, hours: 36 });
  const suggestionsRef = useRef([]);
  const currentIndexRef = useRef(0);

  useEffect(() => {
    suggestionsRef.current = suggestions;
  }, [suggestions]);

  useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  const load = useCallback(async () => {
    if (swiping || loading) return [];
    
    try {
      setLoading(true);
      const res = await api.authFetch('/suggestions');
      const data = await res.json();
      const errMsg = data && data.detail ? data.detail : 'Fout';
      if (!res.ok) throw new Error(errMsg);
      const newSuggestions = Array.isArray(data?.suggestions) ? data.suggestions : [];
      setSuggestions(newSuggestions);
      setCurrentIndex(0);
      return newSuggestions;
    } catch (e) {
      Alert.alert(t('discover'), e.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [api, swiping, loading, t]);

  useEffect(() => { load(); }, [load]);

  const doSwipe = useCallback(async (liked) => {
    if (swiping || loading) return;
    
    const idx = currentIndexRef.current;
    const suggs = suggestionsRef.current;
    
    if (idx >= suggs.length) return;
    
    const currentUser = suggs[idx];
    
    try {
      setSwiping(true);
      const res = await api.authFetch(`/swipe/${currentUser.id}?liked=${liked}`, { 
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Fout');
      
      if (data.match) {
        Alert.alert(t('itsAMatch'), `${currentUser.name}!`);
      }
      
      const nextIndex = idx + 1;
      if (nextIndex < suggestionsRef.current.length) {
        setCurrentIndex(nextIndex);
        setSwiping(false);
      } else {
        setSwiping(false);
        await load();
      }
    } catch (e) {
      Alert.alert(t('discover'), e.message);
      setSwiping(false);
    }
  }, [api, swiping, loading, load, t]);

  const currentProfile = suggestions[currentIndex];
  const photoUrl = currentProfile?.profile_photo_url || (currentProfile?.photos && currentProfile.photos[0]);
  const distance = currentProfile?.distance_km || 0;
  const city = currentProfile?.city || 'Amsterdam';

  return (
    <View style={styles.discoverContainer}>
      <View style={styles.discoverHeader}>
        <View style={styles.headerLeft}>
          <Avatar theme={theme} size={44} uri={user?.profile_photo_url} />
        </View>

        <View style={styles.headerCenter}>
          <View style={{ alignItems: 'center' }}>
            <Ionicons name="heart-circle" size={48} color="#FF6B35" />
            <Text style={{ 
              fontSize: 10, 
              color: theme.color.textSecondary, 
              marginTop: 2,
              fontFamily: 'Montserrat_600SemiBold'
            }}>ATHLO</Text>
          </View>
        </View>

        <View style={styles.headerRight}>
          <View style={styles.matchCounter}>
            <Ionicons name="heart" size={18} color="#FF6B35" />
            <Text style={styles.matchCount}>{matchCount}</Text>
          </View>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>{t('workouts')}</Text>
          <Text style={styles.statValue}>{stats.workouts}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>{t('distance')}</Text>
          <Text style={styles.statValue}>{stats.distance} km</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>{t('hours')}</Text>
          <Text style={styles.statValue}>{stats.hours}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.swipeCardContainer}>
          <LoaderBar theme={theme} />
        </View>
      ) : !currentProfile ? (
        <View style={styles.swipeCardContainer}>
          <EmptyState
            theme={theme}
            title={t('noMoreProfiles')}
            subtitle={t('noMoreProfiles')}
          />
          <TouchableOpacity style={styles.reloadBtn} onPress={load}>
            <Text style={styles.reloadBtnText}>{t('discover')}</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <View style={styles.swipeCardContainer}>
            <View style={styles.swipeCard}>
              <View style={styles.swipePhotoContainer}>
                {photoUrl ? (
                  <Image
                    source={{ uri: photoUrl }}
                    style={styles.swipePhoto}
                    resizeMode="cover"
                  />
                ) : (
                  <View style={styles.swipePhotoPlaceholder}>
                    <Ionicons name="person" size={80} color="#666" />
                  </View>
                )}
              </View>

              <View style={styles.swipeButtons}>
                <TouchableOpacity 
                  style={[styles.dislikeBtn, swiping && styles.swipeBtnDisabled]}
                  onPress={() => doSwipe(false)}
                  disabled={swiping}
                >
                  <Ionicons name="close" size={32} color="#FF6B35" />
                </TouchableOpacity>

                <TouchableOpacity 
                  style={[styles.likeBtn, swiping && styles.swipeBtnDisabled]}
                  onPress={() => doSwipe(true)}
                  disabled={swiping}
                >
                  <Ionicons name="heart" size={32} color="#32D74B" />
                </TouchableOpacity>
              </View>

              <View style={styles.swipeInfo}>
                <Text style={styles.swipeName}>{currentProfile.name}, {currentProfile.age}</Text>
                
                {currentProfile.bio && (
                  <Text style={styles.swipeBio} numberOfLines={2}>{currentProfile.bio}</Text>
                )}
                
                <View style={styles.swipeDetails}>
                  <View style={styles.swipeDetailItem}>
                    <Ionicons name="location" size={16} color="#32D74B" />
                    <Text style={styles.swipeDetailText}>{city}</Text>
                  </View>
                  
                  {distance > 0 && (
                    <View style={styles.swipeDetailItem}>
                      <Ionicons name="triangle" size={14} color="#32D74B" />
                      <Text style={styles.swipeDetailText}>{distance} km away</Text>
                    </View>
                  )}
                </View>
              </View>
            </View>
          </View>

          <Text style={styles.swipeCounter}>
            {currentIndex + 1} / {suggestions.length}
          </Text>
        </>
      )}
    </View>
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
          placeholder={t('typeMessage')}
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

// ==== Language-aware helpers for dropdown options ====
function useDayLabels() {
  const { t } = useContext(LanguageContext);
  return useMemo(() => [
    t('monday'), t('tuesday'), t('wednesday'), t('thursday'), 
    t('friday'), t('saturday'), t('sunday')
  ], [t]);
}

function useAvailabilityBlocks() {
  const { t } = useContext(LanguageContext);
  return useMemo(() => [
    { key: 'morning',   label: t('morning'),   start: '06:00', end: '12:00' },
    { key: 'afternoon', label: t('afternoon'), start: '12:00', end: '18:00' },
    { key: 'evening',   label: t('evening'),   start: '18:00', end: '22:00' },
  ], [t]);
}

/* ================= SETTINGS (PROFIEL) ================= */
function SettingsScreen({ api }) {
  const { theme, mode, setUserMode, preset, setUserPreset } = useContext(ThemeContext);
  const { t, setLang } = useContext(LanguageContext);
  const styles = useMemo(() => createStyles(theme), [theme]);
  
  // Language-aware dropdown options
  const DAY_LABELS = useDayLabels();
  const BLOCKS = useAvailabilityBlocks();

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

  /* ================= ALL STATE HOOKS FIRST ================= */
  const USER_ID = api.userId;
  
  // Settings state
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Profile state
  const [profile, setProfile] = useState({ name: '', age: '', bio: '' });
  const [profileError, setProfileError] = useState(null);
  const [ownId, setOwnId] = useState(null);
  
  // Language state (separate from profile for clarity)
  const [selectedLanguage, setSelectedLanguage] = useState('nl');
  
  // Track if user manually changed language (prevent loadProfile from overwriting)
  const languageDirtyRef = useRef(false);
  
  const setProfileField = (k, v) => setProfile((prev) => ({ ...prev, [k]: v }));
  const updateField = (key, value) => setSettings((prev) => ({ ...prev, [key]: value }));

  /* ================= LOAD FUNCTIONS (minimal dependencies) ================= */
  const loadProfile = useCallback(async () => {
    try {
      setProfileError(null);
      const res = await api.authFetch('/me');
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const t = tFunctionRef.current;
        throw new Error(data?.detail ?? `${t('profileLoadFailed')} (status ${res.status})`);
      }
      setOwnId(data?.id ?? null);
      setProfile({
        name: data?.name ?? '',
        age: data?.age != null ? String(data.age) : '',
        bio: data?.bio ?? '',
      });
      // Only update language if user hasn't manually changed it
      if (data?.language && !languageDirtyRef.current) {
        setSelectedLanguage(data.language);
        setLang(data.language);
      }
    } catch (e) {
      setProfileError(e.message);
    }
  }, [api, setLang]);

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
    loadProfile();
    if (USER_ID) loadSettings();
  }, [loadProfile, loadSettings, USER_ID]);

  /* ================= UNIFIED SAVE FUNCTION ================= */
  const saveAll = useCallback(async () => {
    if (!USER_ID) { 
      const t = tFunctionRef.current;
      Alert.alert(t('settings'), `${t('noUserIdAvailable')}. ${t('sessionExpiredMessage')}`); 
      return; 
    }
    
    // Validate age range before saving
    const minAge = settings?.preferred_min_age;
    const maxAge = settings?.preferred_max_age;
    if (minAge != null && (minAge < 18 || minAge > 99)) {
      Alert.alert(t('settings'), t('ageRange18to99') || 'Leeftijd moet tussen 18 en 99 zijn');
      return;
    }
    if (maxAge != null && (maxAge < 18 || maxAge > 99)) {
      Alert.alert(t('settings'), t('ageRange18to99') || 'Leeftijd moet tussen 18 en 99 zijn');
      return;
    }
    
    try {
      setLoading(true);
      
      // Save both settings AND language in parallel
      const promises = [];
      
      // Save settings if present
      if (settings) {
        promises.push(
          api.authFetch(`/users/${USER_ID}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
          })
        );
      }
      
      // Save language if different from current
      if (selectedLanguage) {
        promises.push(
          api.authFetch(`/users/${USER_ID}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: selectedLanguage }),
          })
        );
      }
      
      const results = await Promise.all(promises);
      
      // Check all results
      for (const res of results) {
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          throw new Error(data?.detail ?? 'Fout bij opslaan');
        }
      }
      
      // Reload both settings and profile from backend
      languageDirtyRef.current = false;  // Reset dirty flag after successful save
      await Promise.all([loadSettings(), loadProfile()]);
      
      Alert.alert(t('settings'), t('settingsSaved') || 'Instellingen opgeslagen');
    } catch (e) {
      Alert.alert('Instellingen', e.message);
    } finally {
      setLoading(false);
    }
  }, [api, settings, selectedLanguage, USER_ID, loadSettings, loadProfile, t]);

  /* ---- Profiel validation and save logic ---- */
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

  const saveProfile = useCallback(async () => {
    const { ok, errs, payload } = validateAndBuildProfilePayload();
    if (!ok) { setProfileError(Object.values(errs).join('\n')); return; }
    try {
      setProfileError(null);
      const uid = ownId ?? api.userId;
      if (!uid) {
        const t = tFunctionRef.current;
        throw new Error(t('noUserIdAvailable'));
      }
      const res = await api.authFetch(`/users/${uid}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const t = tFunctionRef.current;
        throw new Error(data?.detail ?? `${t('profileSaveFailed')} (status ${res.status})`);
      }
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

    const t = tFunctionRef.current; Alert.alert(t('notSupported'), t('addViaUrlMessage'));
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
  }, [api]);

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
      const t = tFunctionRef.current;
      Alert.alert(t('availabilities'), t('availabilitySaved'));
    } catch (e) {
      const t = tFunctionRef.current;
      Alert.alert(t('availabilities'), e.message);
    }
  }, [api, availabilityGrid]);

  /* ---- Uitloggen ---- */
  const handleLogout = useCallback(() => {
    Alert.alert(t('logout'), t('logoutConfirm'), [
      { text: t('cancel'), style: 'cancel' },
      { text: t('logout'), style: 'destructive', onPress: async () => { await api.logout(); } },
    ]);
  }, [api, t]);

  /* ================= RENDER ================= */
  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      {/* THEMA */}
      <Text style={styles.sectionTitle}>{t('theme')}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: theme.gap.m, flexWrap: 'wrap' }}>
        <Chip label={t('system')} active={mode === 'system'} onPress={() => setUserMode('system')} />
        <Chip label={t('light')} active={mode === 'light'} onPress={() => setUserMode('light')} />
        <Chip label={t('dark')} active={mode === 'dark'} onPress={() => setUserMode('dark')} />
      </View>

      <Text style={styles.sectionTitle}>{t('chatStyle')}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' }}>
        <Chip label="iOS" active={preset === 'ios'} onPress={() => setUserPreset('ios')} />
        <Chip label="WhatsApp" active={preset === 'whatsapp'} onPress={() => setUserPreset('whatsapp')} />
      </View>

      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>{t('language')}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        {[
          { code: 'nl', label: 'Nederlands' },
          { code: 'en', label: 'English' },
          { code: 'fr', label: 'Français' },
          { code: 'de', label: 'Deutsch' },
          { code: 'es', label: 'Español' },
          { code: 'it', label: 'Italiano' },
          { code: 'pt', label: 'Português' }
        ].map((lang) => (
          <Chip 
            key={lang.code} 
            label={lang.label} 
            active={selectedLanguage === lang.code} 
            onPress={() => {
              languageDirtyRef.current = true;  // Mark as manually changed
              setSelectedLanguage(lang.code);
              setLang(lang.code);
            }} 
          />
        ))}
      </View>

      <View style={{ marginTop: theme.gap.l }}>
        <Text style={{ color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>
          {t('preferencesStored')}
        </Text>
      </View>

      {/* PROFIEL (naam, leeftijd, bio) */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>{t('profile')}</Text>
      <View style={[styles.card, { gap: 10 }]}>
        <TextInput
          style={styles.input}
          placeholder={t('name')}
          placeholderTextColor={theme.color.textSecondary}
          value={profile.name}
          onChangeText={(v) => setProfileField('name', v)}
        />
        <TextInput
          style={styles.input}
          placeholder={t('age')}
          keyboardType="numeric"
          placeholderTextColor={theme.color.textSecondary}
          value={profile.age}
          onChangeText={(v) => setProfileField('age', v)}
        />
        <TextInput
          style={[styles.input, { height: 100, textAlignVertical: 'top' }]}
          placeholder={t('bio')}
          multiline
          placeholderTextColor={theme.color.textSecondary}
          value={profile.bio}
          onChangeText={(v) => setProfileField('bio', v)}
        />
        {profileError ? (
          <Text style={{ color: theme.color.danger, fontFamily: theme.font.bodyFamily }}>{profileError}</Text>
        ) : null}
        <TouchableOpacity onPress={saveProfile} style={[styles.primaryBtn, { marginTop: theme.gap.s }]}>
          <Text style={styles.primaryBtnText}>{t('saveProfile')}</Text>
        </TouchableOpacity>
      </View>

      {/* FOTO'S */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>{t('photos')}</Text>
      <View style={[styles.card, { gap: 10 }]}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
          {photos.map((p) => (
            <View key={p.id} style={{ width: 120, alignItems: 'center' }}>
              <Image
                source={{ uri: p.photo_url }}
                style={{ width: 120, height: 120, borderRadius: 12, borderWidth: 1, borderColor: theme.color.border }}
              />
              <Text style={{ marginTop: 6, color: theme.color.textSecondary, fontFamily: theme.font.bodyFamily }}>
                {p.is_profile_pic ? t('profilePhoto') : '—'}
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
          <SmallChip theme={theme} color={theme.color.secondary} label={t('addViaUrl')} onPress={addPhotoByUrl} />
        </View>
      </View>

      {/* BESCHIKBAARHEDEN */}
      <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>{t('availabilities')}</Text>
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
          <Text style={styles.primaryBtnText}>{t('saveAvailability')}</Text>
        </TouchableOpacity>
      </View>

      {/* PROFIELINSTELLINGEN (match instellingen) */}
      {loading && <LoaderBar theme={theme} color={theme.color.accent} />}
      {!settings ? (
        <ActivityIndicator style={{ margin: 16 }} />
      ) : (
        <>
          <Text style={[styles.sectionTitle, { marginTop: theme.gap.l }]}>{t('profileSettings')}</Text>
          <Text style={{ marginBottom: 8 }}>{t('matchGoal')}</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {['friendship', 'training_partner', 'competition', 'coaching'].map((goal) => (
              <Chip key={goal} label={t(goal)} active={settings.match_goal === goal} onPress={() => updateField('match_goal', goal)} />
            ))}
          </View>

          <Text style={{ marginTop: 16, marginBottom: 8 }}>{t('preferredGender')}</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {['any', 'male', 'female', 'non_binary'].map((gender) => (
              <Chip key={gender} label={t(gender)} active={settings.preferred_gender === gender} onPress={() => updateField('preferred_gender', gender)} />
            ))}
          </View>

          <Text style={{ marginTop: 16 }}>{t('maxDistance')}</Text>
          <TextInput
            style={styles.input}
            keyboardType="numeric"
            value={String(settings.max_distance_km ?? '')}
            onChangeText={(v) => {
              const n = parseInt(v, 10);
              updateField('max_distance_km', Number.isFinite(n) ? n : 0);
            }}
            placeholder={t('ageExample')}
            placeholderTextColor={theme.color.textSecondary}
          />

          <Text style={{ marginTop: 16 }}>{t('minAge')}</Text>
          <TextInput
            style={styles.input}
            keyboardType="numeric"
            value={String(settings.preferred_min_age ?? '')}
            onChangeText={(v) => {
              if (v === '') {
                updateField('preferred_min_age', null);
              } else {
                const n = parseInt(v, 10);
                if (Number.isFinite(n)) {
                  updateField('preferred_min_age', n);
                }
              }
            }}
            placeholder="18"
            placeholderTextColor={theme.color.textSecondary}
          />

          <Text style={{ marginTop: 16 }}>{t('maxAge')}</Text>
          <TextInput
            style={styles.input}
            keyboardType="numeric"
            value={String(settings.preferred_max_age ?? '')}
            onChangeText={(v) => {
              if (v === '') {
                updateField('preferred_max_age', null);
              } else {
                const n = parseInt(v, 10);
                if (Number.isFinite(n)) {
                  updateField('preferred_max_age', n);
                }
              }
            }}
            placeholder="99"
            placeholderTextColor={theme.color.textSecondary}
          />

          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 16 }}>
            <Text style={{ flex: 1 }}>{t('notifications')}</Text>
            <Switch
              value={!!settings.notifications_enabled}
              onValueChange={(v) => updateField('notifications_enabled', v)}
            />
          </View>

          <TouchableOpacity onPress={saveAll} style={[styles.primaryBtn, { marginTop: theme.gap.m }]}>
            <Text style={styles.primaryBtnText}>{t('saveSettings')}</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Uitloggen */}
      <View style={{ height: theme.gap.l }} />
      <TouchableOpacity onPress={handleLogout} style={[styles.primaryBtn, { backgroundColor: theme.color.danger }]}>
        <Text style={styles.primaryBtnText}>{t('logout')}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

/* ================= NAVIGATION WRAPPER ================= */
function AppContent() {
  const api = useApi();
  const { theme } = useContext(ThemeContext);
  const { setLang } = useContext(LanguageContext);
  const [fontsLoaded] = useFonts({
    Montserrat_400Regular,
    Montserrat_600SemiBold,
    Montserrat_700Bold,
  });

  // Load user's language preference on startup
  useEffect(() => {
    if (api.isAuthenticated && api.userId) {
      (async () => {
        try {
          const res = await api.authFetch('/me');
          const data = await res.json().catch(() => null);
          if (data?.language && data.language !== '') {
            setLang(data.language);
          }
        } catch (e) {
          // Silent fail - language will default to 'nl'
        }
      })();
    }
  }, [api, setLang]);

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
  const { t } = useContext(LanguageContext);
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
      <Tabs.Screen name="Ontdekken" options={{ title: t('discover') }}>
        {(props) => <DiscoverScreen {...props} api={api} theme={theme} user={{ profile_photo_url: profilePhotoUrl }} />}
      </Tabs.Screen>
      <Tabs.Screen name="Matches" options={{ title: t('matches') }}>
        {(props) => <MatchesScreen {...props} api={api} theme={theme} />}
      </Tabs.Screen>
      <Tabs.Screen name="Profiel" options={{ title: t('profile') }}>
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
  // Discover Screen
  discoverContainer: {
    flex: 1,
    backgroundColor: THEME.color.background,
  },
  discoverContent: {
    padding: 16,
    paddingBottom: 100,
  },
  discoverHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerLeft: {
    width: 44,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerRight: {
    width: 44,
    alignItems: 'flex-end',
  },
  logoContainer: {
    marginBottom: 8,
  },
  heartIcon: {
    width: 60,
    height: 60,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heartLeft: {
    position: 'absolute',
    width: 30,
    height: 40,
    backgroundColor: '#0A84FF',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    left: 0,
    transform: [{ rotate: '-45deg' }],
  },
  heartRight: {
    position: 'absolute',
    width: 30,
    height: 40,
    backgroundColor: '#32D74B',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    right: 0,
    transform: [{ rotate: '45deg' }],
  },
  athloText: {
    fontSize: 40,
    fontFamily: THEME.font.bodyBold,
    color: '#FFFFFF',
    textAlign: 'center',
    marginTop: 4,
  },
  tagline: {
    fontSize: 16,
    color: '#32D74B',
    fontFamily: THEME.font.bodyFamily,
    textAlign: 'center',
  },
  matchCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,107,53,0.15)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  matchCount: {
    fontSize: 16,
    fontFamily: THEME.font.bodyBold,
    color: THEME.color.textPrimary,
  },
  findPartnerBtn: {
    backgroundColor: '#0A84FF',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  findPartnerText: {
    fontSize: 18,
    fontFamily: THEME.font.bodyBold,
    color: '#FFFFFF',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 24,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 14,
    color: THEME.color.textSecondary,
    fontFamily: THEME.font.bodyFamily,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 24,
    fontFamily: THEME.font.bodyBold,
    color: THEME.color.textPrimary,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#444',
  },
  cardsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  userCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 12,
  },
  cardPhotoContainer: {
    width: '100%',
    height: 180,
    backgroundColor: '#E5E7EB',
  },
  cardPhoto: {
    width: '100%',
    height: '100%',
  },
  cardPhotoPlaceholder: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E5E7EB',
  },
  cardInfo: {
    padding: 12,
  },
  cardName: {
    fontSize: 16,
    fontFamily: THEME.font.bodyBold,
    color: '#000',
    marginBottom: 6,
  },
  cardDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 4,
  },
  cardDistance: {
    fontSize: 12,
    color: '#32D74B',
    fontFamily: THEME.font.bodyFamily,
  },
  cardCity: {
    fontSize: 12,
    color: '#999',
    fontFamily: THEME.font.bodyFamily,
  },
  connectBtn: {
    backgroundColor: '#FF6B35',
    paddingVertical: 10,
    alignItems: 'center',
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    marginTop: 8,
  },
  connectBtnText: {
    fontSize: 16,
    fontFamily: THEME.font.bodyBold,
    color: '#FFFFFF',
  },
  // Swipe Interface
  swipeCardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  swipeCard: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 8,
  },
  swipePhotoContainer: {
    width: '100%',
    height: 400,
    backgroundColor: '#E5E7EB',
  },
  swipePhoto: {
    width: '100%',
    height: '100%',
  },
  swipePhotoPlaceholder: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E5E7EB',
  },
  swipeInfo: {
    padding: 20,
  },
  swipeName: {
    fontSize: 28,
    fontFamily: THEME.font.bodyBold,
    color: '#000',
    marginBottom: 8,
  },
  swipeBio: {
    fontSize: 16,
    fontFamily: THEME.font.bodyFamily,
    color: '#666',
    marginBottom: 12,
    lineHeight: 22,
  },
  swipeDetails: {
    flexDirection: 'row',
    gap: 16,
  },
  swipeDetailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  swipeDetailText: {
    fontSize: 14,
    fontFamily: THEME.font.bodyFamily,
    color: '#999',
  },
  swipeButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 40,
    paddingVertical: 20,
  },
  dislikeBtn: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#FFF',
    borderWidth: 3,
    borderColor: '#FF6B35',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  likeBtn: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#FFF',
    borderWidth: 3,
    borderColor: '#32D74B',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  swipeBtnDisabled: {
    opacity: 0.5,
  },
  swipeCounter: {
    textAlign: 'center',
    fontSize: 14,
    fontFamily: THEME.font.bodyFamily,
    color: '#999',
    marginTop: 10,
  },
  reloadBtn: {
    backgroundColor: '#0A84FF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginTop: 20,
  },
  reloadBtnText: {
    fontSize: 16,
    fontFamily: THEME.font.bodyBold,
    color: '#FFFFFF',
  },
});

/* ---- MatchesScreen ---- */
function MatchesScreen({ api, theme, navigation }) {
  const { t } = useContext(LanguageContext);
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.authFetch('/matches');
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail ?? t('matches'));
      setMatches(Array.isArray(data?.matches) ? data.matches : []);
    } catch (e) {
      Alert.alert(t('matches'), e.message);
    } finally {
      setLoading(false);
    }
  }, [api, t]);

  useEffect(() => { load(); }, [load]);

  return (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <View style={styles.rowBetween}>
        <Text style={styles.sectionTitle}>{t('matches')}</Text>
        <TouchableOpacity onPress={load} style={styles.ghostBtn}>
          <Text style={styles.ghostBtnText}>{t('discover')}</Text>
        </TouchableOpacity>
      </View>

      {loading ? <LoaderBar theme={theme} /> : null}

      {(!matches || matches.length === 0) ? (
        <EmptyState theme={theme} title={t('matches')}
          subtitle={t('discover')} />
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
    <LanguageProvider>
      <ThemeProvider makeBaseTheme={makeBaseTheme}>
        <AppContent />
      </ThemeProvider>
    </LanguageProvider>
  );
}
