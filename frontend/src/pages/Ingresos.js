import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const CATEGORIAS = [
  'Desarrollo', 'Desarrollo Web', 'Desarrollo Mobile', 'Diseño',
  'Consultoría', 'Marketing Digital', 'Redacción y Contenido',
  'Soporte y Mantenimiento', 'Capacitación', 'Servicios', 'Otros',
];

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function formatFecha(str) {
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]} ${d.getFullYear()}`;
}

function fmtMonto(n) {
  return '+$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

const inputStyle = {
  background: '#0f1117',
  border: '1px solid #1e293b',
  color: '#e2e8f0',
  borderRadius: '8px',
  padding: '10px 14px',
  width: '100%',
  fontSize: '14px',
  outline: 'none',
};

function DeleteBtn({ onDelete }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onDelete}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: 'transparent',
        border: `1px solid ${hover ? '#f87171' : '#475569'}`,
        color: hover ? '#f87171' : '#475569',
        borderRadius: '6px',
        padding: '4px 10px',
        fontSize: '12px',
        cursor: 'pointer',
        transition: 'color 0.1s, border-color 0.1s',
      }}
    >
      Eliminar
    </button>
  );
}

export default function Ingresos() {
  const [ingresos, setIngresos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [filtroCategoria, setFiltroCategoria] = useState('');
  // Ordenamiento multi-criterio: lista de {campo, dir}. El PRIMER elemento manda
  // y el resto desempata. "Fecha" agrupa por MES (no por día), así dos ingresos
  // del mismo mes empatan y el siguiente criterio (monto) los ordena adentro.
  // Click en un encabezado:
  //   no activo  → se suma como desc al final (desempate del que ya estaba)
  //   activo desc → cambia a asc
  //   activo asc  → se saca del orden
  const [orden, setOrden] = useState([{ campo: 'fecha', dir: 'desc' }]);
  const [formError, setFormError] = useState('');
  const [form, setForm] = useState({
    descripcion: '', monto: '', categoria: 'Desarrollo', fecha: todayISO(),
  });

  async function fetchIngresos() {
    setLoading(true);
    try {
      const res = await api.get('/ingresos/', { params: { limite: 200 } });
      setIngresos(res.data);
    } catch (_) {
      setIngresos([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchIngresos(); }, []);

  function handleFormChange(e) {
    if (e.target.name === 'monto') setFormError('');
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function toggleOrden(campo) {
    setOrden((prev) => {
      const actual = prev.find((c) => c.campo === campo);
      // No estaba activo → se suma como desempate al final.
      if (!actual) return [...prev, { campo, dir: 'desc' }];
      // Estaba en desc → cambia a asc.
      if (actual.dir === 'desc') {
        return prev.map((c) => (c.campo === campo ? { ...c, dir: 'asc' } : c));
      }
      // Estaba en asc → se saca del orden.
      return prev.filter((c) => c.campo !== campo);
    });
  }

  function indicadorOrden(campo) {
    const idx = orden.findIndex((c) => c.campo === campo);
    if (idx === -1) return '';
    const flecha = orden[idx].dir === 'asc' ? '↑' : '↓';
    // Si hay más de un criterio activo, mostramos número de prioridad (1°, 2°...)
    const prio = orden.length > 1 ? ` ${idx + 1}°` : '';
    return ` ${flecha}${prio}`;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError('');
    const montoNum = parseFloat(form.monto);
    if (!(montoNum > 0)) {
      setFormError('El monto debe ser mayor a 0');
      return;
    }
    setSaving(true);
    try {
      await api.post('/ingresos/', {
        descripcion: form.descripcion,
        monto: montoNum,
        categoria: form.categoria,
        fecha: form.fecha + 'T00:00:00',
      });
      setShowForm(false);
      setForm({ descripcion: '', monto: '', categoria: 'Desarrollo', fecha: todayISO() });
      await fetchIngresos();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setFormError(detail.map((d) => d.msg).join(', '));
      } else {
        setFormError(detail || 'No se pudo guardar el ingreso');
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('¿Eliminar este ingreso?')) return;
    try {
      await api.delete(`/ingresos/${id}`);
      setIngresos((prev) => prev.filter((i) => i.id !== id));
    } catch (_) {}
  }

  // El filtro ofrece TODAS las categorías canónicas (las mismas que el alta)
  // MÁS cualquier categoría que ya exista en los datos cargados (registros viejos
  // como "Software", "Infraestructura", "Servicios"). Así el filtro y el alta
  // coinciden, y nunca se pierde la posibilidad de filtrar un registro existente.
  const categoriasDisponibles = Array.from(
    new Set([...CATEGORIAS, ...ingresos.map((i) => i.categoria)])
  ).sort((a, b) => a.localeCompare(b, 'es'));

  const ingresosFiltrados = filtroCategoria
    ? ingresos.filter((i) => i.categoria === filtroCategoria)
    : ingresos;

  // "Fecha" se compara por período año-mes (no por día), para que los ingresos
  // del mismo mes empaten y el monto pueda ordenarlos dentro del mes.
  const periodoMes = (f) => {
    const d = new Date(f);
    return d.getFullYear() * 12 + d.getMonth();
  };

  const ingresosOrdenados = [...ingresosFiltrados].sort((a, b) => {
    for (const criterio of orden) {
      const cmp =
        criterio.campo === 'monto'
          ? a.monto - b.monto
          : periodoMes(a.fecha) - periodoMes(b.fecha);
      if (cmp !== 0) return criterio.dir === 'asc' ? cmp : -cmp;
    }
    // Desempate final: fecha exacta, más reciente primero.
    return new Date(b.fecha) - new Date(a.fecha);
  });

  // ── Render ─────────────────────────────────────────────────────────────────

  const thStyle = {
    padding: '12px 16px', fontSize: '12px', color: '#475569',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
    textAlign: 'left',
  };

  return (
    <Layout activeSection="Ingresos">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Ingresos</h1>
        <button
          onClick={() => { setShowForm((v) => !v); setFormError(''); }}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
            fontWeight: 500, cursor: 'pointer',
          }}
        >
          ＋ Nuevo ingreso
        </button>
      </div>

      {/* Formulario */}
      {showForm && (
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
          <p style={{ margin: '0 0 16px 0', fontSize: '15px', fontWeight: 500, color: '#e2e8f0' }}>Nuevo ingreso</p>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Descripción</label>
                <input
                  name="descripcion" required value={form.descripcion} onChange={handleFormChange}
                  placeholder="Ej: Proyecto web cliente A"
                  style={inputStyle}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Monto</label>
                <input
                  name="monto" type="number" step="0.01" required value={form.monto} onChange={handleFormChange}
                  placeholder="0.00"
                  style={inputStyle}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Categoría</label>
                <select
                  name="categoria" value={form.categoria} onChange={handleFormChange}
                  style={{ ...inputStyle, cursor: 'pointer' }}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                >
                  {CATEGORIAS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Fecha</label>
                <input
                  name="fecha" type="date" required value={form.fecha} onChange={handleFormChange}
                  style={{ ...inputStyle, colorScheme: 'dark' }}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
            </div>
            {formError && (
              <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 12px 0' }}>{formError}</p>
            )}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="submit" disabled={saving}
                style={{
                  background: '#3b82f6', color: '#fff', border: 'none',
                  borderRadius: '8px', padding: '8px 20px', fontSize: '14px',
                  fontWeight: 500, cursor: 'pointer',
                }}
              >
                {saving ? 'Guardando...' : 'Guardar'}
              </button>
              <button
                type="button" onClick={() => { setShowForm(false); setFormError(''); }}
                style={{
                  background: 'transparent', color: '#94a3b8',
                  border: '1px solid #1e293b', borderRadius: '8px',
                  padding: '8px 20px', fontSize: '14px', cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filtros */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <select
          value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)}
          style={{ ...inputStyle, width: 'auto', minWidth: '180px', cursor: 'pointer' }}
        >
          <option value="">Todas las categorías</option>
          {categoriasDisponibles.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Tabla */}
      <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1.5fr 1.5fr 1.5fr 90px', borderBottom: '1px solid #1e293b' }}>
          <div style={thStyle}>Descripción</div>
          <div style={thStyle}>Categoría</div>
          <div style={{ ...thStyle, cursor: 'pointer', userSelect: 'none' }} onClick={() => toggleOrden('fecha')}>
            Fecha{indicadorOrden('fecha')}
          </div>
          <div style={{ ...thStyle, cursor: 'pointer', userSelect: 'none' }} onClick={() => toggleOrden('monto')}>
            Monto{indicadorOrden('monto')}
          </div>
          <div style={thStyle}></div>
        </div>

        {/* Filas */}
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
            Cargando...
          </div>
        ) : ingresosOrdenados.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#475569', fontSize: '14px' }}>
            No hay ingresos registrados
          </div>
        ) : (
          ingresosOrdenados.map((ingreso, idx) => (
            <div
              key={ingreso.id}
              style={{
                display: 'grid', gridTemplateColumns: '3fr 1.5fr 1.5fr 1.5fr 90px',
                alignItems: 'center',
                borderBottom: idx < ingresosOrdenados.length - 1 ? '1px solid #1e293b' : 'none',
              }}
            >
              <div style={{ padding: '12px 16px', fontSize: '14px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {ingreso.descripcion}
              </div>
              <div style={{ padding: '12px 16px' }}>
                <span style={{
                  background: '#0f1e35', color: '#3b82f6',
                  fontSize: '12px', padding: '3px 8px', borderRadius: '4px',
                }}>
                  {ingreso.categoria}
                </span>
              </div>
              <div style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b' }}>
                {formatFecha(ingreso.fecha)}
              </div>
              <div style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: '#4ade80' }}>
                {fmtMonto(ingreso.monto)}
              </div>
              <div style={{ padding: '4px 8px' }}>
                <DeleteBtn onDelete={() => handleDelete(ingreso.id)} />
              </div>
            </div>
          ))
        )}
      </div>
    </Layout>
  );
}
