/**
 * Cliente HTTP central del frontend (axios).
 *
 * Todas las pantallas usan esta instancia para hablar con la API del backend.
 * Concentra dos comportamientos transversales:
 *  - Request: adjunta automáticamente el token JWT (guardado en localStorage)
 *    en el header Authorization de cada pedido.
 *  - Response: si la API responde 401 (sesión inválida/expirada) en un endpoint
 *    que no sea login/registro, borra el token y redirige al login.
 */
import axios from 'axios';

// Instancia de axios apuntando a la URL del backend (configurable por entorno).
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

// Interceptor de request: agrega el token JWT a cada llamada si el usuario está logueado.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de response: maneja de forma global el cierre de sesión por token inválido.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || '';
    // En login/registro un 401 es "credenciales incorrectas", no sesión expirada:
    // en esos casos no redirigimos para que la pantalla muestre el error.
    const esAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register');
    if (error.response?.status === 401 && !esAuthEndpoint) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Traduce un error de axios a un mensaje legible para mostrar en pantalla.
// Cubre los dos formatos de error de FastAPI: `detail` como string
// (HTTPException) y `detail` como array (validaciones 422 de Pydantic).
// Las pantallas lo usan para no "tragarse" los errores en silencio.
export function extraerMensajeError(err, fallback = 'Ocurrió un error inesperado') {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || String(d)).join(' · ');
  if (err?.message === 'Network Error') return 'No se pudo conectar con el servidor';
  return fallback;
}

export default api;
