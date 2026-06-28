/**
 * Punto de entrada del frontend (React).
 *
 * Monta el componente raíz <App /> dentro del div #root del index.html. Es lo
 * primero que ejecuta el navegador al cargar la aplicación web.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Crea la raíz de React sobre el contenedor del HTML y renderiza la app.
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
