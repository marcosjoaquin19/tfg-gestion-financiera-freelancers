/**
 * Pantalla Dashboard — panel de inicio.
 *
 * Es la primera vista tras iniciar sesión. Muestra un resumen general de la
 * situación financiera del freelancer: totales de ingresos y gastos, balance,
 * facturas pendientes y métricas clave consultadas a la API del backend.
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api, { extraerMensajeError } from '../api';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

// Períodos que se pueden pedir en el reporte PDF: los últimos 12 meses hasta
// el mes en curso, del más reciente al más viejo. El valor es "AAAA-MM".
function periodosReporte(hoy) {
  const lista = [];
  for (let i = 0; i < 12; i += 1) {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
    const valor = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    lista.push({ valor, etiqueta: `${MESES[d.getMonth()]} ${d.getFullYear()}${i === 0 ? ' (en curso)' : ''}` });
  }
  return lista;
}

// Ancho de la ventana, para elegir cuántas tarjetas van por fila.
function useAnchoVentana() {
  const [ancho, setAncho] = useState(() => window.innerWidth);
  useEffect(() => {
    const alCambiar = () => setAncho(window.innerWidth);
    window.addEventListener('resize', alCambiar);
    return () => window.removeEventListener('resize', alCambiar);
  }, []);
  return ancho;
}

function fmt(n) {
  return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function MetricCard({ value, label, color, pct }) {
  return (
    <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px', minWidth: 0 }}>
      {/* El tamaño se adapta al ancho para que un monto largo no se corte. */}
      <p style={{ fontSize: 'clamp(18px, 1.9vw, 24px)', fontWeight: 600, margin: '0 0 4px 0', color, overflowWrap: 'anywhere' }}>
        ${fmt(value)}
      </p>
      <p style={{ fontSize: '13px', color: '#e2e8f0', margin: '0 0 10px 0' }}>{label}</p>
      <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{ height: '3px', width: `${Math.min(pct, 100)}%`, background: color, borderRadius: '2px' }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  // Movimientos del mes en curso (para los totales) y los últimos 5 de cada
  // tipo (para la lista). Se piden filtrados a la API: antes se bajaban los
  // últimos 200 y se filtraba acá, y pasado ese número el total quedaba corto.
  const [ingresos, setIngresos] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [ultimos, setUltimos] = useState([]);
  const [proyecciones, setProyecciones] = useState([]);
  const [recomendaciones, setRecomendaciones] = useState(null);
  const [descargando, setDescargando] = useState(false);
  // 4 tarjetas por fila en pantallas anchas; 2×2 en las angostas (por ejemplo,
  // un proyector de 1024 px), en lugar de 3 y una suelta.
  const columnasMetricas = useAnchoVentana() >= 1180 ? 4 : 2;

  const now = new Date();
  const mesActual = now.getMonth() + 1;
  const anioActual = now.getFullYear();
  const periodoLabel = `${MESES[now.getMonth()]} ${anioActual}`;
  const periodos = periodosReporte(now);
  // HU-13: el reporte es del mes cerrado, así que se propone el último.
  const [periodoReporte, setPeriodoReporte] = useState(periodos[1].valor);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const delMes = { mes: mesActual, anio: anioActual, limite: 200 };
      const [ingRes, gasRes, ultIngRes, ultGasRes, proyRes, recRes] = await Promise.allSettled([
        api.get('/ingresos/', { params: delMes }),
        api.get('/gastos/', { params: delMes }),
        api.get('/ingresos/', { params: { limite: 5 } }),
        api.get('/gastos/', { params: { limite: 5 } }),
        api.get('/proyecciones/', { params: { limite: 30 } }),
        api.get('/recomendaciones/'),
      ]);
      if (ingRes.status === 'fulfilled') setIngresos(ingRes.value.data);
      if (gasRes.status === 'fulfilled') setGastos(gasRes.value.data);
      setUltimos([
        ...(ultIngRes.status === 'fulfilled' ? ultIngRes.value.data : []).map((i) => ({ ...i, tipo: 'ingreso' })),
        ...(ultGasRes.status === 'fulfilled' ? ultGasRes.value.data : []).map((g) => ({ ...g, tipo: 'gasto' })),
      ]);
      if (proyRes.status === 'fulfilled') setProyecciones(proyRes.value.data);
      if (recRes.status === 'fulfilled') setRecomendaciones(recRes.value.data);
      setLoading(false);
    }
    fetchData();
  }, [mesActual, anioActual]);

  const totalIngresos = ingresos.reduce((s, i) => s + parseFloat(i.monto || 0), 0);
  const totalGastos = gastos.reduce((s, g) => s + parseFloat(g.monto || 0), 0);
  const balance = totalIngresos - totalGastos;

  // Proyección del mes SIGUIENTE exacto. Antes se buscaba "dentro de los
  // próximos 30 días", y el día 1 de cada mes la proyección del mes que viene
  // quedaba afuera: la tarjeta mostraba $0. Las proyecciones llegan como el
  // 1° del mes en UTC, así que se comparan con getters UTC.
  const siguiente = new Date(anioActual, mesActual, 1);   // mesActual es 1-12: esto es el mes que viene
  const proySiguiente = proyecciones.find((p) => {
    const d = new Date(p.fecha_proyeccion);
    return d.getUTCFullYear() === siguiente.getFullYear() && d.getUTCMonth() === siguiente.getMonth();
  });
  const proyPromedio = proySiguiente ? parseFloat(proySiguiente.monto_proyectado || 0) : 0;

  const maxVal = Math.max(totalIngresos, totalGastos, Math.abs(balance), proyPromedio, 1);

  const movimientos = [...ultimos]
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    .slice(0, 5);

  const primeraRec = recomendaciones?.recomendaciones?.[0] || 'Sin recomendaciones disponibles.';
  const genConIA = recomendaciones?.generado_con_ia ?? false;

  // Descarga el reporte mensual en PDF. El endpoint devuelve el archivo binario,
  // así que lo pedimos como blob y forzamos la descarga creando un enlace temporal.
  async function descargarReportePDF() {
    setDescargando(true);
    const [anioRep, mesRep] = periodoReporte.split('-').map(Number);
    try {
      const res = await api.get('/reportes/pdf', {
        params: { mes: mesRep, anio: anioRep },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = `reporte_${periodoReporte}.pdf`;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      // La respuesta de error llega como blob: se lee para mostrar el motivo real.
      let mensaje = 'No se pudo generar el reporte. Intentá nuevamente en unos segundos.';
      if (e?.response?.data instanceof Blob) {
        try {
          const cuerpo = JSON.parse(await e.response.data.text());
          if (typeof cuerpo.detail === 'string') mensaje = cuerpo.detail;
        } catch (_) { /* se queda el mensaje genérico */ }
      } else {
        mensaje = extraerMensajeError(e, mensaje);
      }
      alert(mensaje);
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
          <select
            value={periodoReporte}
            onChange={(e) => setPeriodoReporte(e.target.value)}
            title="Período del reporte PDF"
            aria-label="Período del reporte PDF"
            style={{
              background: '#0f1117', border: '1px solid #1e293b', color: '#e2e8f0',
              borderRadius: '6px', padding: '7px 10px', fontSize: '13px', cursor: 'pointer',
            }}
          >
            {periodos.map((p) => <option key={p.valor} value={p.valor}>{p.etiqueta}</option>)}
          </select>
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
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columnasMetricas}, minmax(0, 1fr))`, gap: '12px', marginBottom: '16px' }}>
        <MetricCard value={totalIngresos} label="Ingresos del mes"    color="#3b82f6" pct={(totalIngresos / maxVal) * 100} />
        <MetricCard value={totalGastos}   label="Gastos del mes"      color="#f87171" pct={(totalGastos / maxVal) * 100} />
        <MetricCard value={balance}       label="Balance neto"        color={balance >= 0 ? '#4ade80' : '#f87171'} pct={(Math.abs(balance) / maxVal) * 100} />
        <MetricCard value={proyPromedio}  label="Proyección próx. mes" color="#f8fafc" pct={(proyPromedio / maxVal) * 100} />
      </div>

      {/* Dos columnas */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>

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
                  <span title={m.descripcion} style={{ fontSize: '13px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '60%' }}>
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
          </div>
          <p style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.6, margin: '0 0 12px 0' }}>{primeraRec.replace(/\$ /g, '$\u00a0')}</p>
          <span style={{ display: 'inline-block', fontSize: '11px', background: '#1e3a5f', color: '#93c5fd', borderRadius: '4px', padding: '2px 10px' }}>
            {/* Misma leyenda que la pantalla de Recomendaciones: se calcula con
                reglas sobre los datos del usuario, sin servicios externos. */}
            {genConIA ? 'generado con IA' : 'basado en tus datos'}
          </span>
        </div>
      </div>
    </Layout>
  );
}
