// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// --- CORRECT IMPORT: Import getAuth ---
import { getAuth } from "firebase/auth"; 

// Your web app's Firebase configuration
// --- UPDATED with your actual config ---
const firebaseConfig = {
  apiKey: "AIzaSyACJ5ZK8DgzRgzLVkIDFCI3qojrNuhRQ44",
  authDomain: "medq-clinic-app.firebaseapp.com",
  projectId: "medq-clinic-app",
  storageBucket: "medq-clinic-app.firebasestorage.app",
  messagingSenderId: "384442039181",
  appId: "1:384442039181:web:d6f6c24620efb9533fdbc4",
  measurementId: "G-R3G6K823GN"
};
// --- END UPDATE ---

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// --- CORRECT SETUP: Initialize Firebase Authentication ---
const auth = getAuth(app); 

// --- CORRECT EXPORT: Export the auth instance ---
export { auth }; 

