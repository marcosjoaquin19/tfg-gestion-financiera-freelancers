import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function formatFecha(str) {
  if (!str) return '—';
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]} ${d.getFullYear()}`;
}

function fmtMonto(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const TIPO_CONFIG = {
  gasto_duplicado:           { color: '#fbbf24', label: 'Gasto duplicado' },
  anomalia_estadistica:      { color: '#f87171', label: 'Anomalía estadística' },
  discrepancia_facturacion:  { color: '#f87171', label: 'Discrepancia facturación' },
};

function ResolverBtn({ onClick }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: 'transparent',
        border: `1px solid ${hover ? '#4ade80' : '#475569'}`,
        color: hover ? '#4ade80' : '#475569',
        borderRadius: '6px', padding: '4px 12px',
        fontSize: '12px', cursor: 'pointer',
        transition: 'color 0.1s, border-color 0.1s',
      }}
    >
      Resolver
    </button>
  );
}

export default function Auditoria() {
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ejecutando, setEjecutando] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [soloPendientes, setSoloPendientes] = useState(false);

  async function fetchAlertas() {
    setLoading(true);
    try {
      const res = await api.get('/alertas/', { params: { limite: 200 } });
      setAlertas(res.data);
    } catch (_) {
      setAlertas([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchAlertas(); }, []);

  async function handleEjecutar() {
    setEjecutando(true);
    setMensaje('');
    try {
      const res = await api.post('/alertas/ejecutar-auditoria');
      const detalle = res.data?.detalle ?? {};
      const total = Object.values(detalle).reduce((acc, v) => acc + v, 0);
      setMensaje(`Auditoría completada: ${total} alertas generadas`);
      await fetchAlertas();
    } catch (_) {
      setMensaje('Error al ejecutar la auditoría');
    } finally {
      setEjecutando(false);
    }
  }

  async function handleResolver(id) {
    try {
      await api.patch(`/alertas/${id}/resolver`, { resuelta: true });
      setAlertas((prev) => prev.map((a) => a.id === id ? { ...a, resuelta: true } : a));
    } catch (_) {}
  }

  let alertasFiltradas = alertas;
  if (filtroTipo) {
    alertasFiltradas = alertasFiltradas.filter((a) => a.tipo === filtroTipo);
  }
  if (soloPendientes) {
    alertasFiltradas = alertasFiltradas.filter((a) => !a.resuelta);
  }

  // Métricas
  const duplicados    = alertas.filter((a) => a.tipo === 'gasto_duplicado').length;
  const anomalias     = alertas.filter((a) => a.tipo === 'anomalia_estadistica').length;
  const discrepancias = alertas.filter((a) => a.tipo === 'discrepancia_facturacion').length;
  const monImpago     = alertas.filter((a) => a.tipo === 'factura_impaga').length;

  return (
    <Layout activeSection="Auditoría">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Auditoría</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {mensaje && (
            <span style={{ fontSize: '13px', color: mensaje.startsWith('Error') ? '#f87171' : '#4ade80' }}>
              {mensaje}
            </span>
          )}
          <button
            onClick={handleEjecutar}
            disabled={ejecutando}
            style={{
              background: '#3b82f6', color: '#fff', border: 'none',
              borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
              fontWeight: 500, cursor: ejecutando ? 'not-allowed' : 'pointer',
              opacity: ejecutando ? 0.7 : 1,
            }}
          >
            {ejecutando ? 'Ejecutando...' : 'Ejecutar auditoría'}
          </button>
        </div>
      </div>

      {/* Resumen */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${monImpago > 0 ? 4 : 3}, 1fr)`, gap: '12px', marginBottom: '16px' }}>
        {[
          { label: 'Gastos duplicados',    value: duplicados,    color: '#fbbf24' },
          { label: 'Anomalías estadísticas', value: anomalias,   color: '#f87171' },
          { label: 'Discrepancias',         value: discrepancias, color: '#f87171' },
          ...(monImpago > 0 ? [{ label: 'Monotributo impago', value: monImpago, color: '#fbbf24' }] : []),
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
            <p style={{ margin: '0 0 4px 0', fontSize: '28px', fontWeight: 600, color }}>{value}</p>
            <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>{label}</p>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <select
          value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)}
          style={{
            background: '#0f1117', border: '1px solid #1e293b', color: '#e2e8f0',
            borderRadius: '8px', padding: '10px 14px', fontSize: '14px',
            outline: 'none', cursor: 'pointer', minWidth: '220px',
          }}
        >
          <option value="">Todos los tipos</option>
          <option value="gasto_duplicado">Gasto duplicado</option>
          <option value="anomalia_estadistica">Anomalía estadística</option>
          <option value="discrepancia_facturacion">Discrepancia facturación</option>
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#94a3b8', cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox" checked={soloPendientes} onChange={(e) => setSoloPendientes(e.target.checked)}
            style={{ accentColor: '#3b82f6', width: '15px', height: '15px' }}
          />
          Solo pendientes
        </label>
      </div>

      {/* Lista de alertas */}
      {loading ? (
        <div style={{ textAlign: 'center', color: '#64748b', fontSize: '14px', padding: '32px' }}>
          Cargando...
        </div>
      ) : alertasFiltradas.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#475569', fontSize: '14px', padding: '32px' }}>
          No hay alertas activas
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {alertasFiltradas.map((alerta) => {
            const cfg = TIPO_CONFIG[alerta.tipo] || { color: '#64748b', label: alerta.tipo };
            return (
              <div
                key={alerta.id}
                style={{
                  background: '#161b27',
                  border: '1px solid #1e293b',
                  borderLeft: `3px solid ${cfg.color}`,
                  borderRadius: '8px',
                  padding: '16px',
                  opacity: alerta.resuelta ? 0.6 : 1,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <p style={{ margin: 0, fontSize: '14px', color: '#e2e8f0', flex: 1, paddingRight: '12px', lineHeight: 1.5 }}>
                    {alerta.descripcion}
                  </p>
                  <span style={{
                    background: cfg.color + '22', color: cfg.color,
                    fontSize: '11px', fontWeight: 600, padding: '3px 8px',
                    borderRadius: '4px', whiteSpace: 'nowrap', flexShrink: 0,
                  }}>
                    {cfg.label}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    {alerta.monto_involucrado != null && (
                      <span style={{ fontSize: '13px', color: '#64748b' }}>
                        Monto: {fmtMonto(alerta.monto_involucrado)}
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: '#475569' }}>
                      {formatFecha(alerta.fecha_deteccion)}
                    </span>
                  </div>
                  {alerta.resuelta ? (
                    <span style={{
                      background: '#1a2e1a', color: '#4ade80',
                      fontSize: '11px', fontWeight: 600,
                      padding: '3px 10px', borderRadius: '4px',
                    }}>
                      Resuelta
                    </span>
                  ) : (
                    <ResolverBtn onClick={() => handleResolver(alerta.id)} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
