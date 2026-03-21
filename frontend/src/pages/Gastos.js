import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const CATEGORIAS = [
  'Software', 'Hardware', 'Infraestructura', 'Marketing', 'Servicios',
  'Capacitación', 'Suscripciones', 'Transporte', 'Alimentación',
  'Impuestos', 'Monotributo', 'Otros',
];

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function formatFecha(str) {
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]} ${d.getFullYear()}`;
}

function fmtMonto(n) {
  return '-$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
        borderRadius: '6px', padding: '4px 10px',
        fontSize: '12px', cursor: 'pointer',
        transition: 'color 0.1s, border-color 0.1s',
      }}
    >
      Eliminar
    </button>
  );
}

export default function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [clasificando, setClasificando] = useState(false);
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [soloDuplicados, setSoloDuplicados] = useState(false);
  const [form, setForm] = useState({
    descripcion: '', monto: '', categoria: 'Software', fecha: todayISO(),
  });

  async function fetchGastos() {
    setLoading(true);
    try {
      const res = await api.get('/gastos/', { params: { limite: 200 } });
      setGastos(res.data);
    } catch (_) {
      setGastos([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchGastos(); }, []);

  function handleFormChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleClasificar() {
    if (!form.descripcion.trim()) return;
    setClasificando(true);
    try {
      const res = await api.post('/gastos/clasificar', { descripcion: form.descripcion });
      setForm((prev) => ({ ...prev, categoria: res.data.categoria_sugerida }));
    } catch (_) {
    } finally {
      setClasificando(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/gastos/', {
        descripcion: form.descripcion,
        monto: parseFloat(form.monto),
        categoria: form.categoria,
        fecha: form.fecha + 'T00:00:00',
      });
      setShowForm(false);
      setForm({ descripcion: '', monto: '', categoria: 'Software', fecha: todayISO() });
      await fetchGastos();
    } catch (_) {
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('¿Eliminar este gasto?')) return;
    try {
      await api.delete(`/gastos/${id}`);
      setGastos((prev) => prev.filter((g) => g.id !== id));
    } catch (_) {}
  }

  let gastosFiltrados = filtroCategoria
    ? gastos.filter((g) => g.categoria === filtroCategoria)
    : gastos;
  if (soloDuplicados) {
    gastosFiltrados = gastosFiltrados.filter((g) => g.es_duplicado);
  }

  const thStyle = {
    padding: '12px 16px', fontSize: '12px', color: '#475569',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
    textAlign: 'left',
  };

  return (
    <Layout activeSection="Gastos">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Gastos</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
            fontWeight: 500, cursor: 'pointer',
          }}
        >
          ＋ Nuevo gasto
        </button>
      </div>

      {/* Formulario */}
      {showForm && (
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
          <p style={{ margin: '0 0 16px 0', fontSize: '15px', fontWeight: 500, color: '#e2e8f0' }}>Nuevo gasto</p>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>

              {/* Descripción + botón IA */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Descripción</label>
                <input
                  name="descripcion" required value={form.descripcion} onChange={handleFormChange}
                  placeholder="Ej: Suscripción Adobe"
                  style={inputStyle}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
                <button
                  type="button" onClick={handleClasificar} disabled={clasificando || !form.descripcion.trim()}
                  style={{
                    marginTop: '6px', background: 'transparent',
                    border: '1px solid #3b82f6', color: '#3b82f6',
                    borderRadius: '6px', padding: '4px 10px',
                    fontSize: '12px', cursor: 'pointer',
                    opacity: !form.descripcion.trim() ? 0.5 : 1,
                  }}
                >
                  {clasificando ? 'Clasificando...' : 'Clasificar con IA'}
                </button>
              </div>

              {/* Monto */}
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

              {/* Categoría */}
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

              {/* Fecha */}
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <select
          value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)}
          style={{ ...inputStyle, width: 'auto', minWidth: '180px', cursor: 'pointer' }}
        >
          <option value="">Todas las categorías</option>
          {CATEGORIAS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#94a3b8', cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox" checked={soloDuplicados} onChange={(e) => setSoloDuplicados(e.target.checked)}
            style={{ accentColor: '#3b82f6', width: '15px', height: '15px' }}
          />
          Solo duplicados
        </label>
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
        ) : gastosFiltrados.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#475569', fontSize: '14px' }}>
            No hay gastos registrados
          </div>
        ) : (
          gastosFiltrados.map((gasto, idx) => (
            <div
              key={gasto.id}
              style={{
                display: 'grid', gridTemplateColumns: '3fr 1.5fr 1.5fr 1.5fr 90px',
                alignItems: 'center',
                borderBottom: idx < gastosFiltrados.length - 1 ? '1px solid #1e293b' : 'none',
              }}
            >
              <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '14px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {gasto.descripcion}
                </span>
                {gasto.es_duplicado && (
                  <span style={{
                    fontSize: '11px', background: '#2d1f00', color: '#fbbf24',
                    borderRadius: '4px', padding: '2px 6px', whiteSpace: 'nowrap', flexShrink: 0,
                  }}>
                    Duplicado
                  </span>
                )}
              </div>
              <div style={{ padding: '12px 16px' }}>
                <span style={{
                  background: '#1c1010', color: '#f87171',
                  fontSize: '12px', padding: '3px 8px', borderRadius: '4px',
                }}>
                  {gasto.categoria}
                </span>
              </div>
              <div style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b' }}>
                {formatFecha(gasto.fecha)}
              </div>
              <div style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: '#f87171' }}>
                {fmtMonto(gasto.monto)}
              </div>
              <div style={{ padding: '4px 8px' }}>
                <DeleteBtn onDelete={() => handleDelete(gasto.id)} />
              </div>
            </div>
          ))
        )}
      </div>
    </Layout>
  );
}
