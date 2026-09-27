/**
 * Pantalla Recomendaciones — consejos financieros.
 *
 * Muestra las recomendaciones que el backend calcula de forma determinística
 * a partir de los datos del usuario (endpoint /recomendaciones), ordenadas por
 * urgencia, cada una con el dato concreto que la disparó ("Por qué").
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import AvisoAlcance from '../components/AvisoAlcance';
import api, { extraerMensajeError } from '../api';

// Espacio no separable tras "$": un monto no se parte entre renglones.
const sinCortes = (t) => (t || '').replace(/\$ /g, '$\u00a0');

// Prioridad de la regla → cómo se rotula (1 = más urgente).
function nivel(prioridad) {
  if (prioridad <= 1) return { etiqueta: 'Urgente', color: '#f87171', fondo: '#2a1215' };
  if (prioridad <= 3) return { etiqueta: 'Atención', color: '#fbbf24', fondo: '#2a2210' };
  return { etiqueta: 'Sugerencia', color: '#93c5fd', fondo: '#1e3a5f' };
}

export default function Recomendaciones() {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');

  async function fetchRecomendaciones() {
    setCargando(true);
    setError('');
    try {
      const res = await api.get('/recomendaciones/');
      setData(res.data);
    } catch (err) {
      setData(null);
      setError(extraerMensajeError(err, 'No se pudieron calcular las recomendaciones. Probá de nuevo en unos segundos.'));
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { fetchRecomendaciones(); }, []);

  // `detalle` trae regla, prioridad y dato; si faltara (respuesta vieja), se
  // arma con los textos solos para no romper la pantalla.
  const recomendaciones = data?.detalle
    || (data?.recomendaciones || []).map((texto) => ({ texto, prioridad: 5, dato: '' }));

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
      ) : error ? (
        <div style={{
          background: '#1f0d0d', border: '1px solid #4d1a1a', borderLeft: '3px solid #f87171',
          borderRadius: '12px', padding: '20px 24px', maxWidth: '700px',
          color: '#fca5a5', fontSize: '14px', lineHeight: 1.6,
        }}>
          {error}
        </div>
      ) : recomendaciones.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#475569', fontSize: '14px', padding: '48px' }}>
          No hay recomendaciones disponibles
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '700px' }}>
          {recomendaciones.map((rec, idx) => {
            const n = nivel(rec.prioridad);
            return (
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
                <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#e2e8f0', lineHeight: 1.6 }}>
                  {sinCortes(rec.texto)}
                </p>
                {rec.dato && (
                  <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#64748b', lineHeight: 1.6 }}>
                    <strong style={{ color: '#94a3b8', fontWeight: 600 }}>Por qué: </strong>{sinCortes(rec.dato)}
                  </p>
                )}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: '11px', fontWeight: 600,
                    background: n.fondo, color: n.color,
                    borderRadius: '4px', padding: '2px 8px',
                  }}>
                    {n.etiqueta}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    background: '#1e293b', color: '#64748b',
                    borderRadius: '4px', padding: '2px 8px',
                  }}>
                    basado en tus datos
                  </span>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}
      <AvisoAlcance detalle="Las sugerencias surgen de reglas aplicadas sobre sus propios datos, sin intervención de servicios externos, y son de carácter orientativo: cada una indica el dato que la originó. Las decisiones de ahorro, inversión o recategorización son del usuario y, cuando corresponda, de su contador." />
    </Layout>
  );
}
