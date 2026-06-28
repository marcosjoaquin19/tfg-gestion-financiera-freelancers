/**
 * Pantalla Gastos — gestión de gastos.
 *
 * Permite listar, crear, editar y eliminar gastos (endpoint /gastos). Al cargar
 * un gasto, el backend puede sugerir su categoría con el clasificador de ML.
 * Ofrece filtros, incluido el de "solo duplicados" detectados por la auditoría.
 */
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
  // Resultado de la última clasificación con IA: categoría sugerida, confianza
  // y si quedó marcada como sujeta a revisión (confianza por debajo del umbral).
  const [clasificacion, setClasificacion] = useState(null);
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [soloDuplicados, setSoloDuplicados] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  // Ordenamiento por columna (mismo comportamiento que Ingresos): el primer
  // criterio manda. Click en Fecha/Monto: inactivo→desc, desc→asc, asc→se quita.
  const [orden, setOrden] = useState([{ campo: 'fecha', dir: 'desc' }]);
  const [form, setForm] = useState({
    descripcion: '', monto: '', categoria: 'Software', fecha: todayISO(),
  });
  const location = useLocation();

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

  // Si venimos desde el Clasificador con una descripción/categoría ya elegida,
  // abrimos el formulario pre-cargado para que el usuario no reescriba nada.
  useEffect(() => {
    const st = location.state;
    if (st && (st.descripcion || st.categoria)) {
      setForm((prev) => ({
        ...prev,
        descripcion: st.descripcion || prev.descripcion,
        categoria: st.categoria || prev.categoria,
      }));
      setShowForm(true);
      // Limpiamos el state para que un refresh no vuelva a pre-cargar.
      window.history.replaceState({}, '');
    }
  }, [location.state]);

  function handleFormChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    // Si cambia la descripción, la clasificación previa deja de corresponder.
    if (e.target.name === 'descripcion') setClasificacion(null);
  }

  async function handleClasificar() {
    if (!form.descripcion.trim()) return;
    setClasificando(true);
    try {
      const res = await api.post('/gastos/clasificar', { descripcion: form.descripcion });
      setForm((prev) => ({ ...prev, categoria: res.data.categoria_sugerida }));
      setClasificacion({
        confianza: res.data.confianza,
        requiereRevision: res.data.requiere_revision,
      });
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
      setClasificacion(null);
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

  function toggleOrden(campo) {
    setOrden((prev) => {
      const actual = prev.find((c) => c.campo === campo);
      if (!actual) return [...prev, { campo, dir: 'desc' }];
      if (actual.dir === 'desc') {
        return prev.map((c) => (c.campo === campo ? { ...c, dir: 'asc' } : c));
      }
      return prev.filter((c) => c.campo !== campo);
    });
  }

  function indicadorOrden(campo) {
    const idx = orden.findIndex((c) => c.campo === campo);
    if (idx === -1) return '';
    const flecha = orden[idx].dir === 'asc' ? '↑' : '↓';
    const prio = orden.length > 1 ? ` ${idx + 1}°` : '';
    return ` ${flecha}${prio}`;
  }

  const periodoMes = (f) => {
    const d = new Date(f);
    return d.getFullYear() * 12 + d.getMonth();
  };

  let gastosFiltrados = filtroCategoria
    ? gastos.filter((g) => g.categoria === filtroCategoria)
    : gastos;
  if (soloDuplicados) {
    gastosFiltrados = gastosFiltrados.filter((g) => g.es_duplicado);
  }
  // Búsqueda libre: matchea descripción o categoría (sin distinguir mayúsculas).
  const termino = busqueda.trim().toLowerCase();
  if (termino) {
    gastosFiltrados = gastosFiltrados.filter(
      (g) =>
        g.descripcion.toLowerCase().includes(termino) ||
        g.categoria.toLowerCase().includes(termino)
    );
  }

  gastosFiltrados = [...gastosFiltrados].sort((a, b) => {
    for (const criterio of orden) {
      const cmp =
        criterio.campo === 'monto'
          ? a.monto - b.monto
          : periodoMes(a.fecha) - periodoMes(b.fecha);
      if (cmp !== 0) return criterio.dir === 'asc' ? cmp : -cmp;
    }
    return new Date(b.fecha) - new Date(a.fecha);
  });

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

                {/* Resultado de la clasificación: confianza y aviso de revisión.
                    Si la confianza quedó por debajo del umbral, el backend marca
                    requiere_revision y le pedimos al usuario que verifique. */}
                {clasificacion && (
                  <div style={{ marginTop: '8px' }}>
                    {clasificacion.requiereRevision ? (
                      <span style={{
                        display: 'inline-block', fontSize: '12px',
                        background: '#2d1f00', color: '#fbbf24',
                        borderRadius: '4px', padding: '4px 9px',
                      }}>
                        ⚠ Confianza baja ({Math.round((clasificacion.confianza || 0) * 100)}%).
                        Revisá la categoría sugerida antes de guardar.
                      </span>
                    ) : (
                      <span style={{ fontSize: '12px', color: '#4ade80' }}>
                        Categoría sugerida con {Math.round((clasificacion.confianza || 0) * 100)}% de confianza.
                      </span>
                    )}
                  </div>
                )}
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {/* Buscador con lupa */}
        <div style={{ position: 'relative', flex: '1 1 240px', minWidth: '200px', maxWidth: '360px' }}>
          <span style={{
            position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
            color: '#64748b', fontSize: '14px', pointerEvents: 'none',
          }}>🔍</span>
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por descripción o categoría..."
            style={{ ...inputStyle, paddingLeft: '36px' }}
            onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
            onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
          />
          {busqueda && (
            <span
              onClick={() => setBusqueda('')}
              style={{
                position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                color: '#64748b', fontSize: '15px', cursor: 'pointer', userSelect: 'none',
              }}
              title="Limpiar búsqueda"
            >×</span>
          )}
        </div>
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
