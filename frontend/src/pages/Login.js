/**
 * Pantalla de Login.
 *
 * Permite al usuario iniciar sesión. Envía email y contraseña al endpoint
 * /auth/login del backend; si las credenciales son válidas, guarda el token
 * JWT en localStorage y redirige al Dashboard. Si fallan, muestra el error.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';

// Estilos en línea de la pantalla (tema oscuro). Solo presentación.
const styles = {
  page: {
    minHeight: '100vh',
    background: '#0f1117',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    background: '#161b27',
    border: '1px solid #1e293b',
    borderRadius: '12px',
    padding: '40px',
    width: '100%',
    maxWidth: '400px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '8px',
  },
  dot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    background: '#3b82f6',
    flexShrink: 0,
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: '600',
    color: '#f8fafc',
  },
  subtitle: {
    margin: '0 0 28px 0',
    color: '#64748b',
    fontSize: '14px',
  },
  label: {
    display: 'block',
    marginBottom: '6px',
    fontSize: '13px',
    color: '#e2e8f0',
  },
  formGroup: {
    marginBottom: '16px',
  },
  button: {
    width: '100%',
    padding: '11px',
    background: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '500',
    cursor: 'pointer',
    marginTop: '8px',
  },
  aviso: {
    background: '#1f1a0d',
    border: '1px solid #4d3d1a',
    color: '#fbbf24',
    borderRadius: '8px',
    padding: '10px 12px',
    fontSize: '13px',
    margin: '0 0 16px 0',
  },
  error: {
    color: '#f87171',
    fontSize: '13px',
    marginBottom: '14px',
  },
  linkRow: {
    textAlign: 'center',
    marginTop: '20px',
    fontSize: '13px',
    color: '#64748b',
  },
  link: {
    color: '#3b82f6',
    textDecoration: 'none',
  },
};

const inputStyle = {
  background: '#0f1117',
  border: '1px solid #1e293b',
  color: '#e2e8f0',
  borderRadius: '8px',
  padding: '10px 14px',
  width: '100%',
  fontSize: '14px',
  outline: 'none',
};

export default function Login() {
  // Estado del formulario: credenciales, mensaje de error y flag de carga.
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  // Si se llegó acá porque la API respondió 401 (ver api.js), se explica por
  // qué. La marca se lee una sola vez y se borra.
  const [sesionExpirada] = useState(() => {
    const marca = sessionStorage.getItem('sesionExpirada') === '1';
    sessionStorage.removeItem('sesionExpirada');
    return marca;
  });
  const navigate = useNavigate();

  // Envía las credenciales al backend y maneja el resultado del login.
  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // El endpoint de login espera los datos como form-urlencoded (estándar
      // de OAuth2), por eso se usa URLSearchParams y no un JSON.
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      const res = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      // Login exitoso: se guarda el token para autenticar los próximos pedidos.
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('userEmail', email);
      navigate('/');
    } catch (err) {
      // Muestra el mensaje de error que devuelve la API (ej: credenciales inválidas).
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div style={styles.dot} />
          <h1 style={styles.title}>FreelanceControl</h1>
        </div>
        <p style={{ margin: '-4px 0 14px 18px', fontSize: '12px', color: '#475569' }}>Gestión financiera para monotributistas</p>
        <p style={styles.subtitle}>Ingresá a tu cuenta</p>

        {sesionExpirada && (
          <p role="status" style={styles.aviso}>
            Tu sesión expiró. Ingresá de nuevo para continuar.
          </p>
        )}

        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label htmlFor="login-email" style={styles.label}>Email</label>
            <input
              id="login-email"
              autoComplete="email"
              type="email"
              placeholder="tu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
            />
          </div>
          <div style={styles.formGroup}>
            <label htmlFor="login-password" style={styles.label}>Contraseña</label>
            <input
              id="login-password"
              autoComplete="current-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
            />
          </div>

          {error && <p role="alert" style={styles.error}>{error}</p>}

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        <div style={styles.linkRow}>
          ¿No tenés cuenta?{' '}
          <Link to="/register" style={styles.link}>
            Registrate
          </Link>
        </div>
      </div>
    </div>
  );
}
