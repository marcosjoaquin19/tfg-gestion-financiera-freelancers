import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import api from '../api';

const inputStyle = {
  background: '#0f1117', border: '1px solid #1e3a5f',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '12px 14px', width: '100%',
  fontSize: '14px', outline: 'none',
  resize: 'vertical', fontFamily: 'inherit',
};

export default function Clasificador() {
  const [descripcion, setDescripcion] = useState('');
  const [clasificando, setClasificando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const navigate = useNavigate();

  async function handleClasificar() {
    if (!descripcion.trim()) return;
    setClasificando(true);
    setResultado(null);
    try {
      const res = await api.post('/gastos/clasificar', { descripcion: descripcion.trim() });
      const categoria = res.data.categoria_sugerida;
      setResultado(categoria);
      setHistorial((prev) => [{ descripcion: descripcion.trim(), categoria }, ...prev].slice(0, 10));
    } catch (_) {
      setResultado('Otros');
    } finally {
      setClasificando(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && e.ctrlKey) handleClasificar();
  }

  return (
    <Layout activeSection="Clasificador">
      <h1 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>
        Clasificador de Gastos IA
      </h1>

      {/* Card principal */}
      <div style={{ background: '#0f1e35', border: '1px solid #1e3a5f', borderRadius: '12px', padding: '24px', maxWidth: '600px' }}>
        {/* Badge */}
        <div style={{ marginBottom: '16px' }}>
          <span style={{
            background: '#1e3a5f', color: '#3b82f6', fontSize: '12px',
            fontWeight: 600, padding: '4px 12px', borderRadius: '20px',
            display: 'inline-flex', alignItems: 'center', gap: '6px',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
            Inteligencia Artificial
          </span>
        </div>

        <p style={{ margin: '0 0 20px 0', fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
          Describí tu gasto y la IA sugiere automáticamente la categoría correcta.
        </p>

        {/* Textarea */}
        <div style={{ marginBottom: '14px' }}>
          <textarea
            rows={3}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: Suscripción mensual a Adobe Creative Cloud"
            style={inputStyle}
            onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
            onBlur={(e) => (e.target.style.borderColor = '#1e3a5f')}
          />
          <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#475569' }}>Ctrl + Enter para clasificar</p>
        </div>

        {/* Botón */}
        <button
          onClick={handleClasificar}
          disabled={clasificando || !descripcion.trim()}
          style={{
            width: '100%', background: '#3b82f6', color: '#fff',
            border: 'none', borderRadius: '8px', padding: '11px',
            fontSize: '15px', fontWeight: 500, cursor: clasificando || !descripcion.trim() ? 'not-allowed' : 'pointer',
            opacity: !descripcion.trim() ? 0.5 : 1,
          }}
        >
          {clasificando ? 'Clasificando...' : 'Clasificar con IA'}
        </button>

        {/* Resultado */}
        {resultado && (
          <div style={{
            marginTop: '20px', background: '#0a1628',
            border: '1px solid #1e3a5f', borderRadius: '10px', padding: '20px',
            textAlign: 'center',
          }}>
            <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#64748b' }}>Categoría sugerida:</p>
            <p style={{ margin: '0 0 16px 0', fontSize: '28px', fontWeight: 700, color: '#3b82f6' }}>
              {resultado}
            </p>
            <button
              onClick={() => navigate('/gastos')}
              style={{
                background: 'transparent', border: '1px solid #3b82f6',
                color: '#3b82f6', borderRadius: '8px',
                padding: '8px 20px', fontSize: '13px',
                cursor: 'pointer', fontWeight: 500,
              }}
            >
              Crear gasto con esta categoría →
            </button>
          </div>
        )}
      </div>

      {/* Historial */}
      {historial.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Historial de la sesión
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {historial.map((h, i) => (
              <button
                key={i}
                onClick={() => setDescripcion(h.descripcion)}
                style={{
                  background: '#161b27', border: '1px solid #1e293b',
                  color: '#94a3b8', borderRadius: '20px',
                  padding: '5px 12px', fontSize: '12px', cursor: 'pointer',
                }}
              >
                <span style={{ color: '#64748b' }}>
                  {h.descripcion.length > 30 ? h.descripcion.slice(0, 30) + '…' : h.descripcion}
                </span>
                <span style={{ color: '#475569', margin: '0 4px' }}>→</span>
                <span style={{ color: '#3b82f6', fontWeight: 500 }}>{h.categoria}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </Layout>
  );
}
