/**
 * Pantalla Recomendaciones — consejos financieros.
 *
 * Muestra la lista de recomendaciones que el backend calcula de forma
 * determinística a partir de los datos del usuario (endpoint /recomendaciones).
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

export default function Recomendaciones() {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function fetchRecomendaciones() {
    setCargando(true);
    try {
      const res = await api.get('/recomendaciones/');
      setData(res.data);
    } catch (_) {
      setData(null);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { fetchRecomendaciones(); }, []);

  const recomendaciones = data?.recomendaciones || [];
  const genConIA = data?.generado_con_ia ?? false;

  return (
    <Layout activeSection="Recomendaciones">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Recomendaciones IA</h1>
        <button
          onClick={fetchRecomendaciones}
          disabled={cargando}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
            fontWeight: 500, cursor: cargando ? 'not-allowed' : 'pointer',
            opacity: cargando ? 0.7 : 1,
          }}
        >
          {cargando ? 'Actualizando...' : 'Actualizar recomendaciones'}
        </button>
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', color: '#64748b', fontSize: '14px', padding: '48px' }}>
          Generando recomendaciones...
        </div>
      ) : recomendaciones.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#475569', fontSize: '14px', padding: '48px' }}>
          No hay recomendaciones disponibles
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '700px' }}>
          {recomendaciones.map((rec, idx) => (
            <div
              key={idx}
              style={{
                background: '#0f1e35', border: '1px solid #1e3a5f',
                borderRadius: '12px', padding: '20px',
                display: 'flex', gap: '16px', alignItems: 'flex-start',
              }}
            >
              {/* Número */}
              <div style={{
                width: '32px', height: '32px', borderRadius: '50%',
                background: '#1e3a5f', color: '#3b82f6',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '14px', fontWeight: 700, flexShrink: 0,
              }}>
                {idx + 1}
              </div>

              {/* Contenido */}
              <div style={{ flex: 1 }}>
                <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0', lineHeight: 1.6 }}>
                  {rec}
                </p>
                <span style={{
                  fontSize: '11px',
                  background: genConIA ? '#1e3a5f' : '#1e293b',
                  color: genConIA ? '#93c5fd' : '#64748b',
                  borderRadius: '4px', padding: '2px 8px',
                }}>
                  {genConIA ? 'generado con IA' : 'basado en tus datos'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
