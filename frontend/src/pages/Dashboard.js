/**
 * Pantalla Dashboard — panel de inicio.
 *
 * Es la primera vista tras iniciar sesión. Muestra un resumen general de la
 * situación financiera del freelancer: totales de ingresos y gastos, balance,
 * facturas pendientes y métricas clave consultadas a la API del backend.
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

function fmt(n) {
  return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function MetricCard({ value, label, color, pct }) {
  return (
    <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
      <p style={{ fontSize: '24px', fontWeight: 600, margin: '0 0 4px 0', color }}>${fmt(value)}</p>
      <p style={{ fontSize: '13px', color: '#e2e8f0', margin: '0 0 10px 0' }}>{label}</p>
      <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{ height: '3px', width: `${Math.min(pct, 100)}%`, background: color, borderRadius: '2px' }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [ingresos, setIngresos] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [proyecciones, setProyecciones] = useState([]);
  const [recomendaciones, setRecomendaciones] = useState(null);
  const [descargando, setDescargando] = useState(false);

  const now = new Date();
  const mesActual = now.getMonth() + 1;
  const anioActual = now.getFullYear();
  const periodoLabel = `${MESES[now.getMonth()]} ${anioActual}`;

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const [ingRes, gasRes, proyRes, recRes] = await Promise.allSettled([
        api.get('/ingresos/', { params: { limite: 200 } }),
        api.get('/gastos/', { params: { limite: 200 } }),
        api.get('/proyecciones/', { params: { limite: 30 } }),
        api.get('/recomendaciones/'),
      ]);
      if (ingRes.status === 'fulfilled') setIngresos(ingRes.value.data);
      if (gasRes.status === 'fulfilled') setGastos(gasRes.value.data);
      if (proyRes.status === 'fulfilled') setProyecciones(proyRes.value.data);
      if (recRes.status === 'fulfilled') setRecomendaciones(recRes.value.data);
      setLoading(false);
    }
    fetchData();
  }, []);

  const ingresosMes = ingresos.filter((i) => {
    const d = new Date(i.fecha);
    return d.getMonth() + 1 === mesActual && d.getFullYear() === anioActual;
  });
  const gastosMes = gastos.filter((g) => {
    const d = new Date(g.fecha);
    return d.getMonth() + 1 === mesActual && d.getFullYear() === anioActual;
  });

  const totalIngresos = ingresosMes.reduce((s, i) => s + parseFloat(i.monto || 0), 0);
  const totalGastos = gastosMes.reduce((s, g) => s + parseFloat(g.monto || 0), 0);
  const balance = totalIngresos - totalGastos;

  const hoy = new Date();
  const en30 = new Date(hoy.getTime() + 30 * 24 * 60 * 60 * 1000);
  const proyNext30 = proyecciones.filter((p) => {
    const d = new Date(p.fecha_proyeccion);
    return d >= hoy && d <= en30;
  });
  const proyPromedio =
    proyNext30.length > 0
      ? proyNext30.reduce((s, p) => s + parseFloat(p.monto_proyectado || 0), 0) / proyNext30.length
      : 0;

  const maxVal = Math.max(totalIngresos, totalGastos, Math.abs(balance), proyPromedio, 1);

  const movimientos = [
    ...ingresos.map((i) => ({ ...i, tipo: 'ingreso' })),
    ...gastos.map((g) => ({ ...g, tipo: 'gasto' })),
  ]
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    .slice(0, 5);

  const primeraRec = recomendaciones?.recomendaciones?.[0] || 'Sin recomendaciones disponibles.';
  const genConIA = recomendaciones?.generado_con_ia ?? false;

  // Descarga el reporte mensual en PDF. El endpoint devuelve el archivo binario,
  // así que lo pedimos como blob y forzamos la descarga creando un enlace temporal.
  async function descargarReportePDF() {
    setDescargando(true);
    try {
      const res = await api.get('/reportes/pdf', {
        params: { mes: mesActual, anio: anioActual },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = `reporte_${anioActual}-${String(mesActual).padStart(2, '0')}.pdf`;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('No se pudo generar el reporte. Intentá nuevamente en unos segundos.');
    } finally {
      setDescargando(false);
    }
  }

  if (loading) {
    return (
      <Layout activeSection="Dashboard">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b', fontSize: '14px' }}>
          Cargando...
        </div>
      </Layout>
    );
  }

  return (
    <Layout activeSection="Dashboard">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Dashboard</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>{periodoLabel}</span>
          <button
            onClick={descargarReportePDF}
            disabled={descargando}
            style={{
              background: descargando ? '#1e293b' : '#3b82f6',
              color: descargando ? '#64748b' : '#ffffff',
              border: 'none', borderRadius: '6px', padding: '8px 14px',
              fontSize: '13px', fontWeight: 500,
              cursor: descargando ? 'not-allowed' : 'pointer',
            }}
          >
            {descargando ? 'Generando...' : 'Descargar reporte PDF'}
          </button>
        </div>
      </div>

      {/* Métricas */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <MetricCard value={totalIngresos} label="Ingresos del mes"    color="#3b82f6" pct={(totalIngresos / maxVal) * 100} />
        <MetricCard value={totalGastos}   label="Gastos del mes"      color="#f87171" pct={(totalGastos / maxVal) * 100} />
        <MetricCard value={balance}       label="Balance neto"        color={balance >= 0 ? '#4ade80' : '#f87171'} pct={(Math.abs(balance) / maxVal) * 100} />
        <MetricCard value={proyPromedio}  label="Proyección próx. mes" color="#f8fafc" pct={(proyPromedio / maxVal) * 100} />
      </div>

      {/* Dos columnas */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

        {/* Últimos movimientos */}
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 12px 0', fontWeight: 500 }}>Últimos movimientos</p>
          {movimientos.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '13px' }}>Sin movimientos registrados.</p>
          ) : (
            movimientos.map((m, idx) => {
              const esIngreso = m.tipo === 'ingreso';
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '9px 0',
                    borderBottom: idx < movimientos.length - 1 ? '1px solid #1e293b' : 'none',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '60%' }}>
                    {m.descripcion}
                  </span>
                  <span style={{
                    background: esIngreso ? '#0f1e35' : '#1c1010',
                    color: esIngreso ? '#3b82f6' : '#f87171',
                    fontSize: '12px', borderRadius: '4px', padding: '2px 8px',
                    fontWeight: 500, whiteSpace: 'nowrap',
                  }}>
                    {esIngreso ? '+' : '-'}${fmt(m.monto)}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Recomendación IA */}
        <div style={{ background: '#0f1e35', border: '1px solid #1e3a5f', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }} />
              <p style={{ margin: 0, fontSize: '13px', fontWeight: 500, color: '#93c5fd' }}>Recomendación IA</p>
            </div>
            <span style={{ fontSize: '11px', background: '#1e3a5f', color: '#3b82f6', borderRadius: '4px', padding: '2px 8px', fontWeight: 600 }}>IA</span>
          </div>
          <p style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.6, margin: '0 0 12px 0' }}>{primeraRec}</p>
          <span style={{ display: 'inline-block', fontSize: '11px', background: '#1e3a5f', color: '#93c5fd', borderRadius: '4px', padding: '2px 10px' }}>
            {genConIA ? 'generado con IA' : 'generado sin IA'}
          </span>
        </div>
      </div>
    </Layout>
  );
}
