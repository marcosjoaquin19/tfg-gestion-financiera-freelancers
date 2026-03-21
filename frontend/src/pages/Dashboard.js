import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const SIDEBAR_SECTIONS = [
  {
    title: 'GENERAL',
    items: ['Dashboard', 'Ingresos', 'Gastos', 'Facturas', 'Auditoría', 'Proyecciones'],
  },
  {
    title: 'INTELIGENCIA IA',
    items: ['Clasificador', 'Resumen IA', 'Recomendaciones'],
  },
];

// ── Styles ────────────────────────────────────────────────────────────────────

const s = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0f1117',
    overflow: 'hidden',
  },
  topbar: {
    height: '48px',
    minHeight: '48px',
    background: '#161b27',
    borderBottom: '1px solid #1e293b',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 20px',
  },
  topbarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  topbarDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#3b82f6',
    flexShrink: 0,
  },
  topbarTitle: {
    margin: 0,
    fontSize: '15px',
    fontWeight: 500,
    color: '#f8fafc',
  },
  topbarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
  },
  topbarUser: {
    fontSize: '13px',
    color: '#64748b',
  },
  logoutBtn: {
    background: 'transparent',
    border: '1px solid #1e293b',
    color: '#64748b',
    borderRadius: '6px',
    padding: '4px 12px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  body: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  sidebar: {
    width: '200px',
    minWidth: '200px',
    background: '#161b27',
    borderRight: '1px solid #1e293b',
    overflowY: 'auto',
    padding: '16px 0',
  },
  sectionTitle: {
    fontSize: '11px',
    color: '#475569',
    fontWeight: 600,
    letterSpacing: '0.05em',
    padding: '8px 16px 4px',
    textTransform: 'uppercase',
  },
  main: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
  },
  pageHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '20px',
  },
  pageTitle: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 500,
    color: '#f8fafc',
  },
  periodLabel: {
    fontSize: '13px',
    color: '#64748b',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '12px',
    marginBottom: '16px',
  },
  card: {
    background: '#161b27',
    border: '1px solid #1e293b',
    borderRadius: '8px',
    padding: '16px',
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: 600,
    margin: '0 0 4px 0',
  },
  metricLabel: {
    fontSize: '13px',
    color: '#e2e8f0',
    margin: '0 0 10px 0',
  },
  progressBg: {
    height: '3px',
    background: '#1e293b',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  twoCol: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  cardTitle: {
    fontSize: '13px',
    color: '#64748b',
    margin: '0 0 12px 0',
    fontWeight: 500,
  },
  movRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '9px 0',
    borderBottom: '1px solid #1e293b',
  },
  movDesc: {
    fontSize: '13px',
    color: '#e2e8f0',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: '60%',
  },
  iaCard: {
    background: '#0f1e35',
    border: '1px solid #1e3a5f',
    borderRadius: '8px',
    padding: '16px',
  },
  iaHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '12px',
  },
  iaHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  iaDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#3b82f6',
    flexShrink: 0,
  },
  iaTitle: {
    fontSize: '13px',
    fontWeight: 500,
    color: '#93c5fd',
    margin: 0,
  },
  iaBadge: {
    fontSize: '11px',
    background: '#1e3a5f',
    color: '#3b82f6',
    borderRadius: '4px',
    padding: '2px 8px',
    fontWeight: 600,
  },
  iaText: {
    fontSize: '13px',
    color: '#e2e8f0',
    lineHeight: 1.6,
    margin: '0 0 12px 0',
  },
  iaChip: {
    display: 'inline-block',
    fontSize: '11px',
    background: '#1e3a5f',
    color: '#93c5fd',
    borderRadius: '4px',
    padding: '2px 10px',
  },
  placeholder: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '200px',
    color: '#64748b',
    fontSize: '15px',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#64748b',
    fontSize: '14px',
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n) {
  return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function SidebarItem({ label, active, onClick }) {
  const [hover, setHover] = useState(false);

  const style = {
    padding: '8px 16px',
    fontSize: '13px',
    cursor: 'pointer',
    borderLeft: active ? '2px solid #3b82f6' : '2px solid transparent',
    color: active ? '#93c5fd' : hover ? '#e2e8f0' : '#64748b',
    background: active ? '#0f1e35' : hover ? '#1e293b' : 'transparent',
    transition: 'all 0.1s',
    userSelect: 'none',
  };

  return (
    <div
      style={style}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {label}
    </div>
  );
}

function MetricCard({ value, label, color, pct }) {
  return (
    <div style={s.card}>
      <p style={{ ...s.metricValue, color }}>${fmt(value)}</p>
      <p style={s.metricLabel}>{label}</p>
      <div style={s.progressBg}>
        <div style={{ height: '3px', width: `${Math.min(pct, 100)}%`, background: color, borderRadius: '2px' }} />
      </div>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [active, setActive] = useState('Dashboard');
  const [loading, setLoading] = useState(true);
  const [ingresos, setIngresos] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [proyecciones, setProyecciones] = useState([]);
  const [recomendaciones, setRecomendaciones] = useState(null);
  const navigate = useNavigate();

  const userEmail = localStorage.getItem('userEmail') || 'Usuario';
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

  function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    navigate('/login');
  }

  // ── Métricas ────────────────────────────────────────────────────────────────

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

  // ── Últimos movimientos ─────────────────────────────────────────────────────

  const movimientos = [
    ...ingresos.map((i) => ({ ...i, tipo: 'ingreso' })),
    ...gastos.map((g) => ({ ...g, tipo: 'gasto' })),
  ]
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    .slice(0, 5);

  // ── Render sección activa ───────────────────────────────────────────────────

  function renderContent() {
    if (active !== 'Dashboard') {
      return (
        <div style={s.placeholder}>
          {active} — próximamente
        </div>
      );
    }

    if (loading) {
      return <div style={s.loading}>Cargando...</div>;
    }

    const primeraRec = recomendaciones?.recomendaciones?.[0] || 'Sin recomendaciones disponibles.';
    const genConIA = recomendaciones?.generado_con_ia ?? false;

    return (
      <>
        {/* Header */}
        <div style={s.pageHeader}>
          <h1 style={s.pageTitle}>Dashboard</h1>
          <span style={s.periodLabel}>{periodoLabel}</span>
        </div>

        {/* Métricas */}
        <div style={s.metricsGrid}>
          <MetricCard
            value={totalIngresos}
            label="Ingresos del mes"
            color="#3b82f6"
            pct={(totalIngresos / maxVal) * 100}
          />
          <MetricCard
            value={totalGastos}
            label="Gastos del mes"
            color="#f87171"
            pct={(totalGastos / maxVal) * 100}
          />
          <MetricCard
            value={balance}
            label="Balance neto"
            color={balance >= 0 ? '#4ade80' : '#f87171'}
            pct={(Math.abs(balance) / maxVal) * 100}
          />
          <MetricCard
            value={proyPromedio}
            label="Proyección próx. mes"
            color="#f8fafc"
            pct={(proyPromedio / maxVal) * 100}
          />
        </div>

        {/* Dos columnas */}
        <div style={s.twoCol}>
          {/* Últimos movimientos */}
          <div style={s.card}>
            <p style={s.cardTitle}>Últimos movimientos</p>
            {movimientos.length === 0 ? (
              <p style={{ color: '#64748b', fontSize: '13px' }}>Sin movimientos registrados.</p>
            ) : (
              movimientos.map((m, idx) => {
                const esIngreso = m.tipo === 'ingreso';
                const badge = {
                  background: esIngreso ? '#0f1e35' : '#1c1010',
                  color: esIngreso ? '#3b82f6' : '#f87171',
                  fontSize: '12px',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                };
                return (
                  <div
                    key={idx}
                    style={{
                      ...s.movRow,
                      borderBottom: idx === movimientos.length - 1 ? 'none' : '1px solid #1e293b',
                    }}
                  >
                    <span style={s.movDesc}>{m.descripcion}</span>
                    <span style={badge}>
                      {esIngreso ? '+' : '-'}${fmt(m.monto)}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          {/* Recomendación IA */}
          <div style={s.iaCard}>
            <div style={s.iaHeader}>
              <div style={s.iaHeaderLeft}>
                <div style={s.iaDot} />
                <p style={s.iaTitle}>Recomendación IA</p>
              </div>
              <span style={s.iaBadge}>IA</span>
            </div>
            <p style={s.iaText}>{primeraRec}</p>
            <span style={s.iaChip}>
              {genConIA ? 'generado con IA' : 'generado sin IA'}
            </span>
          </div>
        </div>
      </>
    );
  }

  // ── Layout ──────────────────────────────────────────────────────────────────

  return (
    <div style={s.root}>
      {/* Topbar */}
      <div style={s.topbar}>
        <div style={s.topbarLeft}>
          <div style={s.topbarDot} />
          <p style={s.topbarTitle}>Gestión Financiera</p>
        </div>
        <div style={s.topbarRight}>
          <span style={s.topbarUser}>{userEmail}</span>
          <button style={s.logoutBtn} onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={s.body}>
        {/* Sidebar */}
        <div style={s.sidebar}>
          {SIDEBAR_SECTIONS.map((section) => (
            <div key={section.title}>
              <div style={s.sectionTitle}>{section.title}</div>
              {section.items.map((item) => (
                <SidebarItem
                  key={item}
                  label={item}
                  active={active === item}
                  onClick={() => setActive(item)}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Main */}
        <div style={s.main}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
