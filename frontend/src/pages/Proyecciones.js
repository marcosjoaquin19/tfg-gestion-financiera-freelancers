import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function formatFecha(str) {
  if (!str) return '—';
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]}`;
}

function formatFechaLarga(str) {
  if (!str) return '—';
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]} ${d.getFullYear()}`;
}

function fmtMonto(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtCompacto(n) {
  const v = Number(n || 0);
  if (v >= 1000000) return '$' + (v / 1000000).toFixed(1) + 'M';
  if (v >= 1000)    return '$' + (v / 1000).toFixed(1) + 'k';
  return '$' + v.toFixed(0);
}

function avg(arr, key) {
  if (!arr.length) return 0;
  return arr.reduce((s, p) => s + parseFloat(p[key] || 0), 0) / arr.length;
}

// ── SVG Chart ─────────────────────────────────────────────────────────────────

function ProyeccionChart({ data }) {
  if (!data.length) return null;

  const W = 800;
  const H = 200;
  const PAD = { top: 15, right: 20, bottom: 30, left: 58 };
  const cW = W - PAD.left - PAD.right;
  const cH = H - PAD.top - PAD.bottom;

  const allValues = data.flatMap((p) => [parseFloat(p.monto_lower), parseFloat(p.monto_upper)]);
  const rawMin = Math.min(...allValues);
  const rawMax = Math.max(...allValues);
  const range  = rawMax - rawMin || 1;
  const yMin   = rawMin - range * 0.08;
  const yMax   = rawMax + range * 0.08;

  function xPos(i) { return PAD.left + (i / (data.length - 1)) * cW; }
  function yPos(v) { return PAD.top + cH - ((parseFloat(v) - yMin) / (yMax - yMin)) * cH; }

  function toPoints(key) {
    return data.map((p, i) => `${xPos(i)},${yPos(p[key])}`).join(' ');
  }

  // Area polygon: upper points + lower points reversed
  const upperPts = data.map((p, i) => `${xPos(i)},${yPos(p.monto_upper)}`);
  const lowerPts = [...data].reverse().map((p, i) => `${xPos(data.length - 1 - i)},${yPos(p.monto_lower)}`);
  const areaPoints = [...upperPts, ...lowerPts].join(' ');

  // Y axis labels (4 ticks)
  const yTicks = [0, 1, 2, 3].map((i) => yMin + (i / 3) * (yMax - yMin));

  // X axis labels (every 5th point)
  const xLabels = data.filter((_, i) => i % 5 === 0 || i === data.length - 1);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="200"
      style={{ display: 'block' }}
    >
      {/* Grid lines */}
      {yTicks.map((v, i) => (
        <line
          key={i}
          x1={PAD.left} y1={yPos(v)}
          x2={W - PAD.right} y2={yPos(v)}
          stroke="#1e293b" strokeWidth="1"
        />
      ))}

      {/* Y axis labels */}
      {yTicks.map((v, i) => (
        <text
          key={i}
          x={PAD.left - 6} y={yPos(v) + 4}
          textAnchor="end" fontSize="10" fill="#475569"
        >
          {fmtCompacto(v)}
        </text>
      ))}

      {/* X axis labels */}
      {xLabels.map((p, i) => {
        const idx = data.indexOf(p);
        return (
          <text
            key={i}
            x={xPos(idx)} y={H - 4}
            textAnchor="middle" fontSize="10" fill="#475569"
          >
            {formatFecha(p.fecha_proyeccion)}
          </text>
        );
      })}

      {/* Area between lower and upper */}
      <polygon points={areaPoints} fill="#3b82f6" opacity="0.1" />

      {/* Lower line (dashed, red) */}
      <polyline
        points={toPoints('monto_lower')}
        fill="none" stroke="#f87171" strokeWidth="1.5"
        strokeDasharray="4 4" opacity="0.5"
      />

      {/* Upper line (dashed, green) */}
      <polyline
        points={toPoints('monto_upper')}
        fill="none" stroke="#4ade80" strokeWidth="1.5"
        strokeDasharray="4 4" opacity="0.5"
      />

      {/* Main line */}
      <polyline
        points={toPoints('monto_proyectado')}
        fill="none" stroke="#3b82f6" strokeWidth="2"
      />

      {/* Dots on main line (every 5th) */}
      {data.filter((_, i) => i % 5 === 0 || i === data.length - 1).map((p, i) => {
        const idx = data.indexOf(p);
        return (
          <circle
            key={i}
            cx={xPos(idx)} cy={yPos(p.monto_proyectado)}
            r="3" fill="#3b82f6"
          />
        );
      })}
    </svg>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Proyecciones() {
  const [proyecciones, setProyecciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generando, setGenerando] = useState(false);

  async function fetchProyecciones() {
    setLoading(true);
    try {
      const res = await api.get('/proyecciones/', { params: { limite: 30 } });
      setProyecciones(res.data);
    } catch (_) {
      setProyecciones([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchProyecciones(); }, []);

  async function handleGenerar() {
    setGenerando(true);
    try {
      await api.post('/proyecciones/generar', { periodos: 30 });
      await fetchProyecciones();
    } catch (_) {
    } finally {
      setGenerando(false);
    }
  }

  const promedio   = avg(proyecciones, 'monto_proyectado');
  const pesimista  = avg(proyecciones, 'monto_lower');
  const optimista  = avg(proyecciones, 'monto_upper');

  const thStyle = {
    padding: '12px 16px', fontSize: '12px', color: '#475569',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
    textAlign: 'left',
  };

  const COLS = '2fr 1.5fr 1.5fr 1.5fr';

  return (
    <Layout activeSection="Proyecciones">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Proyecciones</h1>
        <button
          onClick={handleGenerar}
          disabled={generando}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
            fontWeight: 500, cursor: generando ? 'not-allowed' : 'pointer',
            opacity: generando ? 0.7 : 1,
          }}
        >
          {generando ? 'Generando...' : 'Generar proyecciones'}
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: '#64748b', fontSize: '14px', padding: '32px' }}>
          Cargando...
        </div>
      ) : proyecciones.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#475569', fontSize: '14px', padding: '48px 32px', lineHeight: 1.6 }}>
          No hay proyecciones generadas.<br />
          Hacé click en <strong style={{ color: '#3b82f6' }}>Generar proyecciones</strong> para comenzar.
        </div>
      ) : (
        <>
          {/* Resumen */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
            {[
              { label: 'Proyección promedio',  value: promedio,  color: '#3b82f6' },
              { label: 'Escenario pesimista',  value: pesimista, color: '#f87171' },
              { label: 'Escenario optimista',  value: optimista, color: '#4ade80' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
                <p style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 600, color }}>{fmtMonto(value)}</p>
                <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>{label}</p>
              </div>
            ))}
          </div>

          {/* Gráfico */}
          <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b', fontWeight: 500 }}>
              Proyección de ingresos — próximos 30 días
            </p>
            {/* Leyenda */}
            <div style={{ display: 'flex', gap: '20px', marginBottom: '12px' }}>
              {[
                { color: '#3b82f6', dash: false, label: 'Proyectado' },
                { color: '#f87171', dash: true,  label: 'Pesimista' },
                { color: '#4ade80', dash: true,  label: 'Optimista' },
              ].map(({ color, dash, label }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <svg width="20" height="10">
                    <line x1="0" y1="5" x2="20" y2="5" stroke={color} strokeWidth="2"
                      strokeDasharray={dash ? '4 3' : undefined} />
                  </svg>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>{label}</span>
                </div>
              ))}
            </div>
            <ProyeccionChart data={proyecciones} />
          </div>

          {/* Tabla */}
          <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: COLS, borderBottom: '1px solid #1e293b' }}>
              {['Fecha', 'Pesimista', 'Proyectado', 'Optimista'].map((h) => (
                <div key={h} style={thStyle}>{h}</div>
              ))}
            </div>
            {proyecciones.slice(0, 10).map((p, idx) => (
              <div
                key={p.id}
                style={{
                  display: 'grid', gridTemplateColumns: COLS, alignItems: 'center',
                  borderBottom: idx < 9 ? '1px solid #1e293b' : 'none',
                }}
              >
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#64748b' }}>
                  {formatFechaLarga(p.fecha_proyeccion)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#f87171' }}>
                  {fmtMonto(p.monto_lower)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '14px', fontWeight: 600, color: '#3b82f6' }}>
                  {fmtMonto(p.monto_proyectado)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#4ade80' }}>
                  {fmtMonto(p.monto_upper)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Layout>
  );
}
