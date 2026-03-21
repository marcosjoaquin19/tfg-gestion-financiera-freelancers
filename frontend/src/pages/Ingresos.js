import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const CATEGORIAS = ['Desarrollo', 'Consultoría', 'Diseño', 'Marketing', 'Otros'];

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
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/ingresos/', {
        descripcion: form.descripcion,
        monto: parseFloat(form.monto),
        categoria: form.categoria,
        fecha: form.fecha + 'T00:00:00',
      });
      setShowForm(false);
      setForm({ descripcion: '', monto: '', categoria: 'Desarrollo', fecha: todayISO() });
      await fetchIngresos();
    } catch (_) {
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

  const ingresosFiltrados = filtroCategoria
    ? ingresos.filter((i) => i.categoria === filtroCategoria)
    : ingresos;

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
          onClick={() => setShowForm((v) => !v)}
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
                  name="monto" type="number" step="0.01" min="0" required value={form.monto} onChange={handleFormChange}
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
                type="button" onClick={() => setShowForm(false)}
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
          {CATEGORIAS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Tabla */}
      <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1.5fr 1.5fr 1.5fr 90px', borderBottom: '1px solid #1e293b' }}>
          {['Descripción', 'Categoría', 'Fecha', 'Monto', ''].map((h) => (
            <div key={h} style={thStyle}>{h}</div>
          ))}
        </div>

        {/* Filas */}
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
            Cargando...
          </div>
        ) : ingresosFiltrados.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#475569', fontSize: '14px' }}>
            No hay ingresos registrados
          </div>
        ) : (
          ingresosFiltrados.map((ingreso, idx) => (
            <div
              key={ingreso.id}
              style={{
                display: 'grid', gridTemplateColumns: '3fr 1.5fr 1.5fr 1.5fr 90px',
                alignItems: 'center',
                borderBottom: idx < ingresosFiltrados.length - 1 ? '1px solid #1e293b' : 'none',
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
