/**
 * Pantalla Proyecciones — predicción de ingresos.
 *
 * Permite generar y visualizar (en un gráfico) la proyección de ingresos
 * futuros calculada por el modelo Prophet en el backend. Muestra el monto
 * estimado por período junto con su rango de confianza.
 */
import { useState, useEffect, useRef } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const MESES_ES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];

function mesLabel(str) {
  if (!str) return '';
  const d = new Date(str);
  const m = MESES_ES[d.getMonth()];
  return m.charAt(0).toUpperCase() + m.slice(1) + ' ' + d.getFullYear();
}

function formatFechaLarga(str) {
  if (!str) return '—';
  const d = new Date(str);
  const m = MESES_ES[d.getMonth()];
  return m.charAt(0).toUpperCase() + m.slice(1) + ' ' + d.getFullYear();
}

function fmtMonto(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtK(n) {
  const v = Number(n || 0);
  if (v >= 1000000) return '$' + (v / 1000000).toFixed(1) + 'M';
  if (v >= 1000)    return '$' + Math.round(v / 1000) + 'k';
  return '$' + Math.round(v);
}

function avg(arr, key) {
  if (!arr.length) return 0;
  return arr.reduce((s, p) => s + parseFloat(p[key] || 0), 0) / arr.length;
}

// ── Chart.js loader ────────────────────────────────────────────────────────────

function loadChartJS(callback) {
  if (window.Chart) { callback(); return; }
  const existing = document.querySelector('script[data-chartjs]');
  if (existing) { existing.addEventListener('load', callback, { once: true }); return; }
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js';
  script.setAttribute('data-chartjs', '1');
  script.onload = callback;
  document.head.appendChild(script);
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function Proyecciones() {
  const [proyecciones, setProyecciones] = useState([]);
  const [historico, setHistorico]       = useState([]);  // ingresos reales agrupados por mes
  const [loading, setLoading]           = useState(true);
  const [generando, setGenerando]       = useState(false);
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  async function fetchProyecciones() {
    setLoading(true);
    try {
      // Traemos proyecciones + ingresos reales (para dibujar el histórico).
      const [resP, resI] = await Promise.all([
        api.get('/proyecciones/', { params: { limite: 12 } }),
        api.get('/ingresos/', { params: { limite: 200 } }),
      ]);
      setProyecciones(resP.data);

      // Agrupamos los ingresos reales por mes (misma lógica que usa Prophet).
      const porMes = {};
      for (const ing of resI.data) {
        const d = new Date(ing.fecha);
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01T00:00:00`;
        porMes[key] = (porMes[key] || 0) + parseFloat(ing.monto || 0);
      }
      const hist = Object.entries(porMes)
        .map(([ds, y]) => ({ ds, y }))
        .sort((a, b) => new Date(a.ds) - new Date(b.ds));
      setHistorico(hist);
    } catch (_) {
      setProyecciones([]);
      setHistorico([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchProyecciones(); }, []);

  // ── Construir gráfico cuando llegan los datos ────────────────────────────────
  useEffect(() => {
    if (!proyecciones.length) return;

    function buildChart() {
      if (!canvasRef.current || !window.Chart) return;

      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }

      const Chart = window.Chart;

      // Eje X = meses históricos + meses proyectados.
      const labels = [
        ...historico.map(h => mesLabel(h.ds)),
        ...proyecciones.map(p => mesLabel(p.fecha_proyeccion)),
      ];

      const H = historico.length;
      const P = proyecciones.length;

      // Serie histórica real (null en los meses futuros).
      const histData = [...historico.map(h => h.y), ...Array(P).fill(null)];

      // Las series de proyección arrancan en el ÚLTIMO punto histórico (conexión
      // visual), por eso van con null hasta ahí y luego los valores proyectados.
      const lastHistY = H > 0 ? historico[H - 1].y : null;
      const pad = Array(Math.max(H - 1, 0)).fill(null);
      const conexion = H > 0 ? [lastHistY] : [];
      const lower = [...pad, ...conexion, ...proyecciones.map(p => parseFloat(p.monto_lower))];
      const yhat  = [...pad, ...conexion, ...proyecciones.map(p => parseFloat(p.monto_proyectado))];
      const upper = [...pad, ...conexion, ...proyecciones.map(p => parseFloat(p.monto_upper))];

      chartRef.current = new Chart(canvasRef.current, {
        type: 'line',
        data: {
          labels,
          datasets: [
            // ── Relleno de área de confianza (lower → upper) ──────────────────
            {
              label: 'Área de confianza',
              data: lower,
              borderColor: 'transparent',
              backgroundColor: 'rgba(59,130,246,0.12)',
              pointRadius: 0,
              fill: '+1',          // rellena hasta el siguiente dataset (upper_area)
              tension: 0.3,
            },
            {
              label: '_upper_area', // prefijo _ → excluido del tooltip
              data: upper,
              borderColor: 'transparent',
              backgroundColor: 'transparent',
              pointRadius: 0,
              fill: false,
              tension: 0.3,
            },
            // ── Líneas visibles ───────────────────────────────────────────────
            {
              label: 'Pesimista',
              data: lower,
              borderColor: '#ef4444',
              borderWidth: 1.5,
              borderDash: [5, 4],
              backgroundColor: 'transparent',
              pointRadius: 4,
              pointBackgroundColor: '#ef4444',
              fill: false,
              tension: 0.3,
            },
            {
              label: 'Proyectado',
              data: yhat,
              borderColor: '#3b82f6',
              borderWidth: 3,
              backgroundColor: 'transparent',
              pointRadius: 6,
              pointBackgroundColor: '#3b82f6',
              fill: false,
              tension: 0.3,
            },
            {
              label: 'Optimista',
              data: upper,
              borderColor: '#22c55e',
              borderWidth: 1.5,
              borderDash: [5, 4],
              backgroundColor: 'transparent',
              pointRadius: 4,
              pointBackgroundColor: '#22c55e',
              fill: false,
              tension: 0.3,
            },
            // ── Histórico real (lo que efectivamente ingresó) ────────────────
            {
              label: 'Histórico (real)',
              data: histData,
              borderColor: '#e2e8f0',
              borderWidth: 2.5,
              backgroundColor: 'transparent',
              pointRadius: 4,
              pointBackgroundColor: '#e2e8f0',
              fill: false,
              tension: 0.3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0f172a',
              borderColor: '#1e293b',
              borderWidth: 1,
              titleColor: '#e2e8f0',
              bodyColor: '#94a3b8',
              padding: 12,
              // Excluir los datasets de relleno del tooltip
              filter: (item) =>
                item.dataset.label !== 'Área de confianza' &&
                !item.dataset.label.startsWith('_'),
              callbacks: {
                label: (ctx) => ` ${ctx.dataset.label}: ${fmtMonto(ctx.raw)}`,
              },
            },
          },
          scales: {
            x: {
              grid:   { color: 'rgba(255,255,255,0.05)' },
              border: { color: 'rgba(255,255,255,0.05)' },
              ticks:  { color: '#64748b', font: { size: 12 } },
            },
            y: {
              grid:   { color: 'rgba(255,255,255,0.05)' },
              border: { color: 'rgba(255,255,255,0.05)' },
              ticks: {
                color: '#64748b',
                font: { size: 12 },
                callback: (v) => fmtK(v),
              },
            },
          },
        },
      });
    }

    loadChartJS(buildChart);

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [proyecciones, historico]);

  const promedio  = avg(proyecciones, 'monto_proyectado');
  const pesimista = avg(proyecciones, 'monto_lower');
  const optimista = avg(proyecciones, 'monto_upper');
  const histPromedio = avg(historico, 'y');  // promedio mensual real, para verificar coherencia

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
          onClick={async () => {
            setGenerando(true);
            try {
              await api.post('/proyecciones/generar', { periodos: 6 });
              await fetchProyecciones();
            } catch (_) {
            } finally {
              setGenerando(false);
            }
          }}
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
          {/* ── Métricas resumen ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
            {[
              { label: 'Promedio proyectado', value: promedio,  color: '#3b82f6' },
              { label: 'Escenario pesimista', value: pesimista, color: '#ef4444' },
              { label: 'Escenario optimista', value: optimista, color: '#22c55e' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
                <p style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 600, color }}>{fmtMonto(value)}</p>
                <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>{label}</p>
              </div>
            ))}
          </div>

          {/* ── Gráfico Chart.js ── */}
          <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <p style={{ margin: 0, fontSize: '13px', color: '#64748b', fontWeight: 500 }}>
                  Histórico real + proyección a 6 meses
                </p>
                {historico.length > 0 && (
                  <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: '#475569' }}>
                    Promedio histórico mensual: <strong style={{ color: '#94a3b8' }}>{fmtMonto(histPromedio)}</strong> · la proyección parte de ahí
                  </p>
                )}
              </div>
              {/* ── Leyenda HTML personalizada ── */}
              <div style={{ display: 'flex', gap: '20px' }}>
                {[
                  { color: '#e2e8f0', dash: false, label: 'Histórico'  },
                  { color: '#3b82f6', dash: false, label: 'Proyectado' },
                  { color: '#ef4444', dash: true,  label: 'Pesimista'  },
                  { color: '#22c55e', dash: true,  label: 'Optimista'  },
                ].map(({ color, dash, label }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <svg width="22" height="10">
                      <line
                        x1="0" y1="5" x2="22" y2="5"
                        stroke={color}
                        strokeWidth={label === 'Proyectado' ? 3 : 1.5}
                        strokeDasharray={dash ? '5 4' : undefined}
                      />
                    </svg>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ height: '320px', position: 'relative' }}>
              <canvas ref={canvasRef} />
            </div>
          </div>

          {/* ── Tabla ── */}
          <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: COLS, borderBottom: '1px solid #1e293b' }}>
              {['Mes', 'Pesimista', 'Proyectado', 'Optimista'].map((h) => (
                <div key={h} style={thStyle}>{h}</div>
              ))}
            </div>
            {proyecciones.map((p, idx) => (
              <div
                key={p.id}
                style={{
                  display: 'grid', gridTemplateColumns: COLS, alignItems: 'center',
                  borderBottom: idx < proyecciones.length - 1 ? '1px solid #1e293b' : 'none',
                }}
              >
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#64748b' }}>
                  {formatFechaLarga(p.fecha_proyeccion)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#ef4444' }}>
                  {fmtMonto(p.monto_lower)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '14px', fontWeight: 600, color: '#3b82f6' }}>
                  {fmtMonto(p.monto_proyectado)}
                </div>
                <div style={{ padding: '11px 16px', fontSize: '13px', color: '#22c55e' }}>
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
