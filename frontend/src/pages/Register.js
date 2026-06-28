/**
 * Pantalla de Registro.
 *
 * Permite crear una cuenta nueva. Envía nombre, email y contraseña al endpoint
 * /auth/register; si el registro es exitoso, redirige al login. Muestra los
 * errores de validación que devuelve el backend (ej: email ya registrado).
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
  error: {
    color: '#f87171',
    fontSize: '13px',
    marginBottom: '14px',
  },
  success: {
    color: '#4ade80',
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

export default function Register() {
  // Estado del formulario: datos de la cuenta, mensaje de error y flag de carga.
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Crea la cuenta en el backend y, si sale bien, lleva al usuario al login.
  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/register', { nombre, email, password });
      navigate('/login');
    } catch (err) {
      // El backend puede devolver el error como texto o como lista de errores
      // de validación de Pydantic; se contemplan ambos formatos.
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError(detail || 'Error al crear la cuenta');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div style={styles.dot} />
          <h1 style={styles.title}>Gestión Financiera</h1>
        </div>
        <p style={styles.subtitle}>Creá tu cuenta</p>

        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Nombre</label>
            <input
              type="text"
              placeholder="Tu nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
            />
          </div>
          <div style={styles.formGroup}>
            <label style={styles.label}>Email</label>
            <input
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
            <label style={styles.label}>Contraseña</label>
            <input
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

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>

        <div style={styles.linkRow}>
          ¿Ya tenés cuenta?{' '}
          <Link to="/login" style={styles.link}>
            Ingresá
          </Link>
        </div>
      </div>
    </div>
  );
}
