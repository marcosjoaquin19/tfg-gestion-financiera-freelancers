/**
 * Pantalla Proyecciones — predicción de ingresos.
 *
 * Permite generar y visualizar (en un gráfico) la proyección de ingresos
 * futuros calculada por el modelo Prophet en el backend. Muestra el monto
 * estimado por período junto con su rango de confianza, con qué método se
 * calculó y cuándo.
 */
import { useState, useEffect, useRef } from 'react';
import Layout from '../components/Layout';
import AvisoAlcance from '../components/AvisoAlcance';
// Chart.js empaquetado con la app (npm), no descargado de un CDN: la única
// salida a internet del sistema es la llamada a Groq del resumen, y el gráfico
// tiene que verse aunque no haya conexión.
import Chart from 'chart.js/auto';
import api from '../api';

const MESES_ES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];

// Las proyecciones llegan como el 1° de cada mes a medianoche UTC ("...T00:00:00Z"):
// se leen con getters UTC para que la etiqueta no retroceda al mes anterior (ART).
function formatFechaLarga(str) {
  if (!str) return '—';
  const d = new Date(str);
  const m = MESES_ES[d.getUTCMonth()];
  return m.charAt(0).toUpperCase() + m.slice(1) + ' ' + d.getUTCFullYear();
}

// Clave "AAAA-MM" de una fecha UTC de la API (1° de mes a medianoche UTC).
function claveMes(str) {
  const d = new Date(str);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

function sumarMes(clave, n) {
  const [a, m] = clave.split('-').map(Number);
  const d = new Date(Date.UTC(a, m - 1 + n, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

function etiquetaMes(clave) {
  const [a, m] = clave.split('-').map(Number);
  const nombre = MESES_ES[m - 1];
  return nombre.charAt(0).toUpperCase() + nombre.slice(1) + ' ' + a;
}

// fecha_generacion es un instante real: se muestra en la hora local.
function formatFechaHora(str) {
  if (!str) return '—';
  const d = new Date(str);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${d.getDate()} ${MESES_ES[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}

// Texto que declara con qué se calculó la proyección (campo `metodo`).
function describirMetodo(metodo, mesesHistoricos) {
  switch (metodo) {
    case 'prophet':
      return {
        titulo: 'Calculado con Prophet',
        detalle: `Tendencia ajustada sobre ${mesesHistoricos} meses cerrados de ingresos.`,
        color: '#3b82f6',
      };
    case 'media_movil':
      return {
        titulo: 'Promedio simple (arranque en frío)',
        detalle: `Promedio de los últimos ${Math.min(mesesHistoricos, 3)} meses cerrados. Prophet se usa a partir de 10 ingresos en al menos 3 meses cerrados.`,
        color: '#fbbf24',
      };
    case 'mes_en_curso':
      return {
        titulo: 'Estimación provisoria',
        detalle: 'Solo hay ingresos del mes en curso, que todavía no terminó: la proyección es un piso.',
        color: '#fbbf24',
      };
    case 'sin_datos':
      return {
        titulo: 'Sin ingresos cargados',
        detalle: 'No hay historial para proyectar: todos los meses quedan en $0.',
        color: '#64748b',
      };
    default:
      return {
        titulo: 'Proyección de una versión anterior',
        detalle: 'Volvé a generarla para ver con qué método se calcula.',
        color: '#64748b',
      };
  }
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


// ── Component ──────────────────────────────────────────────────────────────────

export default function Proyecciones() {
  const [proyecciones, setProyecciones] = useState([]);
  const [historico, setHistorico]       = useState([]);  // meses cerrados con los que se entrena
  const [enCurso, setEnCurso]           = useState(null);  // mes que todavía no terminó (no entra al cálculo)
  const [loading, setLoading]           = useState(true);
  const [generando, setGenerando]       = useState(false);
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  async function fetchProyecciones() {
    setLoading(true);
    try {
      // Proyecciones + la serie mensual EXACTA con la que se entrena el modelo
      // (meses cerrados, huecos en $0), calculada por el backend.
      const [resP, resH] = await Promise.all([
        api.get('/proyecciones/', { params: { limite: 12 } }),
        api.get('/proyecciones/historico'),
      ]);
      setProyecciones(resP.data);
      setHistorico(resH.data.meses.map((m) => ({ ds: m.mes, y: m.total })));
      setEnCurso({ ds: resH.data.mes_en_curso, y: resH.data.total_mes_en_curso });
    } catch (_) {
      setProyecciones([]);
      setHistorico([]);
      setEnCurso(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchProyecciones(); }, []);

  // ── Construir gráfico cuando llegan los datos ────────────────────────────────
  useEffect(() => {
    if (!proyecciones.length) return;

    function buildChart() {
      if (!canvasRef.current) return;

      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }


      // Eje X continuo, mes a mes: si faltan datos de algún mes (por ejemplo,
      // extractos todavía no importados) se ve el hueco en lugar de pegar
      // meses que no son consecutivos.
      const histPorMes = Object.fromEntries(historico.map(h => [claveMes(h.ds), h.y]));
      const proyPorMes = Object.fromEntries(proyecciones.map(p => [claveMes(p.fecha_proyeccion), p]));
      const claveEnCurso = enCurso ? claveMes(enCurso.ds) : null;
      const claves = [...Object.keys(histPorMes), ...Object.keys(proyPorMes), ...(claveEnCurso ? [claveEnCurso] : [])].sort();
      const meses = [];
      for (let c = claves[0]; c <= claves[claves.length - 1]; c = sumarMes(c, 1)) meses.push(c);
      const labels = meses.map(etiquetaMes);

      // Serie histórica real: solo meses cerrados.
      const histData = meses.map(c => (c in histPorMes ? histPorMes[c] : null));

      // El mes en curso va aparte, como un punto hueco: todavía no terminó y
      // no entra en el cálculo.
      const enCursoData = meses.map(c => (c === claveEnCurso && enCurso && enCurso.y > 0 ? enCurso.y : null));

      // Las series de proyección arrancan en el último mes cerrado cuando es el
      // mes anterior al actual (conexión visual por encima del mes en curso).
      // Si el historial termina antes, no se dibuja una línea inventada.
      const ultimaHist = historico.length ? claveMes(historico[historico.length - 1].ds) : null;
      const conecta = ultimaHist && claveEnCurso && sumarMes(ultimaHist, 1) === claveEnCurso;
      const serieProy = (campo) => meses.map(c => {
        if (c in proyPorMes) return parseFloat(proyPorMes[c][campo]);
        if (conecta && c === ultimaHist) return histPorMes[c];
        return null;
      });
      const lower = serieProy('monto_lower');
      const yhat  = serieProy('monto_proyectado');
      const upper = serieProy('monto_upper');

      chartRef.current = new Chart(canvasRef.current, {
        type: 'line',
        data: {
          labels,
          datasets: [
            // ── Relleno de área de confianza (lower → upper) ──────────────────
            {
              label: 'Área de confianza',
              spanGaps: true,
              data: lower,
              borderColor: 'transparent',
              backgroundColor: 'rgba(59,130,246,0.12)',
              pointRadius: 0,
              fill: '+1',          // rellena hasta el siguiente dataset (upper_area)
              tension: 0.3,
            },
            {
              label: '_upper_area', // prefijo _ → excluido del tooltip
              spanGaps: true,
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
              spanGaps: true,
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
              spanGaps: true,
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
              spanGaps: true,
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
            // ── Mes en curso: parcial, fuera del cálculo ──────────────────────
            {
              label: 'Mes en curso (parcial)',
              data: enCursoData,
              borderColor: '#94a3b8',
              backgroundColor: '#161b27',
              pointRadius: 6,
              pointBorderWidth: 2,
              pointStyle: 'circle',
              showLine: false,
              fill: false,
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
              // desde $0: no exagera subas ni bajas, y con datos casi
              // constantes el eje no se estira a centavos de diferencia
              beginAtZero: true,
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

    buildChart();

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [proyecciones, historico, enCurso]);

  const promedio  = avg(proyecciones, 'monto_proyectado');
  const pesimista = avg(proyecciones, 'monto_lower');
  const optimista = avg(proyecciones, 'monto_upper');
  const histPromedio = avg(historico, 'y');  // promedio mensual real, para verificar coherencia
  const metodo = describirMetodo(proyecciones[0]?.metodo, historico.length);

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
          {/* ── Cómo y cuándo se calculó ── */}
          <div style={{
            background: '#161b27', border: '1px solid #1e293b', borderLeft: `3px solid ${metodo.color}`,
            borderRadius: '8px', padding: '12px 16px', marginBottom: '16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px',
          }}>
            <div>
              <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: metodo.color }}>{metodo.titulo}</p>
              <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                {metodo.detalle} El mes en curso no entra en el cálculo porque todavía no terminó.
              </p>
            </div>
            <p style={{ margin: 0, fontSize: '12px', color: '#64748b', whiteSpace: 'nowrap' }}>
              Calculada el {formatFechaHora(proyecciones[0]?.fecha_generacion)}
            </p>
          </div>

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
                    Promedio mensual de los meses cerrados: <strong style={{ color: '#94a3b8' }}>{fmtMonto(histPromedio)}</strong>
                  </p>
                )}
              </div>
              {/* ── Leyenda HTML personalizada ── */}
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {[
                  { color: '#e2e8f0', dash: false, label: 'Histórico'  },
                  { color: '#94a3b8', dash: false, label: 'Mes en curso', punto: true },
                  { color: '#3b82f6', dash: false, label: 'Proyectado' },
                  { color: '#ef4444', dash: true,  label: 'Pesimista'  },
                  { color: '#22c55e', dash: true,  label: 'Optimista'  },
                ].map(({ color, dash, label, punto }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <svg width="22" height="10">
                      {punto ? (
                        <circle cx="11" cy="5" r="4" fill="none" stroke={color} strokeWidth="2" />
                      ) : (
                      <line
                        x1="0" y1="5" x2="22" y2="5"
                        stroke={color}
                        strokeWidth={label === 'Proyectado' ? 3 : 1.5}
                        strokeDasharray={dash ? '5 4' : undefined}
                      />
                      )}
                    </svg>
                    <span style={{ fontSize: '11px', color: '#64748b', whiteSpace: 'nowrap' }}>{label}</span>
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
      <AvisoAlcance detalle="Las proyecciones son estimaciones estadísticas sobre su historial: no son una garantía de ingresos futuros." />
    </Layout>
  );
}
