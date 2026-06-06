import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const authEnabled = import.meta.env.VITE_ENABLE_AUTH === "true";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDYks1RZahh-4AqpXc7ccH6l8eLSXF1B4Q",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "todo-b8152.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "todo-b8152",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "todo-b8152.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "980194458318",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:980194458318:web:d1caca2212ecbe46a0ae9f",
};

let auth = null;
let provider = null;

if (authEnabled) {
  const app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  provider = new GoogleAuthProvider();
}

export { auth, provider, authEnabled };
