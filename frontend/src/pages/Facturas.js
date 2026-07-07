/**
 * Pantalla Facturas — emisión y seguimiento de facturas.
 *
 * Permite emitir facturas, listarlas con filtros (por estado y cliente) y
 * cambiar su estado (marcar como pagada o vencida) contra el endpoint /facturas.
 * Refleja las reglas de negocio: una factura pagada no se edita ni elimina.
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api, { extraerMensajeError } from '../api';

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// La API devuelve las fechas en UTC ("...T00:00:00Z"): hay que leerlas con los
// getters UTC para que el día calendario no retroceda en husos negativos (ART).
function formatFecha(str) {
  if (!str) return '—';
  const d = new Date(str);
  return `${d.getUTCDate()} ${MESES_CORTOS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

function fmtMonto(n) {
  return '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

function toDateInput(str) {
  if (!str) return '';
  return str.split('T')[0];
}

const ESTADO_BADGE = {
  pendiente: { background: '#1f1a0d', color: '#fbbf24' },
  pagada:    { background: '#0d1f0d', color: '#4ade80' },
  vencida:   { background: '#1f0d0d', color: '#f87171' },
};

const inputStyle = {
  background: '#0f1117', border: '1px solid #1e293b',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '10px 14px', width: '100%',
  fontSize: '14px', outline: 'none',
};

const smallInputStyle = {
  background: '#0f1117', border: '1px solid #1e293b',
  color: '#e2e8f0', borderRadius: '6px',
  padding: '5px 10px', fontSize: '12px',
  outline: 'none', colorScheme: 'dark',
};

function EliminarBtn({ disabled, onDelete }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={disabled ? undefined : onDelete}
      onMouseEnter={() => !disabled && setHover(true)}
      onMouseLeave={() => setHover(false)}
      disabled={disabled}
      style={{
        background: 'transparent',
        border: `1px solid ${disabled ? '#2d3748' : hover ? '#f87171' : '#475569'}`,
        color: disabled ? '#2d3748' : hover ? '#f87171' : '#475569',
        borderRadius: '6px', padding: '4px 10px',
        fontSize: '12px', cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'color 0.1s, border-color 0.1s',
      }}
    >
      Eliminar
    </button>
  );
}

export default function Facturas() {
  const [facturas, setFacturas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [pagandoId, setPagandoId] = useState(null);
  const [fechaPago, setFechaPago] = useState(todayISO());
  const [editando, setEditando] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editSaving, setEditSaving] = useState(false);
  // Errores de backend/red visibles en cada formulario (no silenciosos).
  const [formError, setFormError] = useState('');
  const [editError, setEditError] = useState('');
  const [form, setForm] = useState({
    cliente_nombre: '', monto: '', descripcion: '',
    fecha_emision: todayISO(), fecha_vencimiento: '',
  });

  async function fetchFacturas() {
    setLoading(true);
    try {
      const res = await api.get('/facturas/', { params: { limite: 200 } });
      const ahora = new Date();
      const vencidas = res.data.filter(
        (f) => f.estado === 'pendiente' && new Date(f.fecha_vencimiento) < ahora
      );
      if (vencidas.length > 0) {
        await Promise.all(
          vencidas.map((f) => api.patch(`/facturas/${f.id}/estado`, { estado: 'vencida', fecha_pago: null }))
        );
        const actualizado = await api.get('/facturas/', { params: { limite: 200 } });
        setFacturas(actualizado.data);
      } else {
        setFacturas(res.data);
      }
    } catch (_) {
      setFacturas([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchFacturas(); }, []);

  function handleFormChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setFormError('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      await api.post('/facturas/', {
        cliente_nombre: form.cliente_nombre,
        monto: parseFloat(form.monto),
        descripcion: form.descripcion,
        fecha_emision: form.fecha_emision + 'T00:00:00',
        fecha_vencimiento: form.fecha_vencimiento + 'T00:00:00',
      });
      setShowForm(false);
      setForm({ cliente_nombre: '', monto: '', descripcion: '', fecha_emision: todayISO(), fecha_vencimiento: '' });
      await fetchFacturas();
    } catch (err) {
      setFormError(extraerMensajeError(err, 'No se pudo emitir la factura'));
    } finally {
      setSaving(false);
    }
  }

  async function handleMarcarPagada(id) {
    try {
      await api.patch(`/facturas/${id}/estado`, {
        estado: 'pagada',
        fecha_pago: fechaPago + 'T00:00:00',
      });
      setPagandoId(null);
      await fetchFacturas();
    } catch (err) {
      window.alert(extraerMensajeError(err, 'No se pudo marcar la factura como pagada'));
    }
  }

  function handleAbrirEditar(factura) {
    setEditando(factura);
    setEditError('');
    setEditForm({
      cliente_nombre: factura.cliente_nombre,
      monto: factura.monto,
      descripcion: factura.descripcion,
      fecha_emision: toDateInput(factura.fecha_emision),
      fecha_vencimiento: toDateInput(factura.fecha_vencimiento),
    });
  }

  function handleEditChange(e) {
    setEditForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setEditError('');
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    setEditSaving(true);
    try {
      await api.put(`/facturas/${editando.id}`, {
        cliente_nombre: editForm.cliente_nombre,
        monto: parseFloat(editForm.monto),
        descripcion: editForm.descripcion,
        fecha_emision: editForm.fecha_emision + 'T00:00:00',
        fecha_vencimiento: editForm.fecha_vencimiento + 'T00:00:00',
      });
      setEditando(null);
      await fetchFacturas();
    } catch (err) {
      setEditError(extraerMensajeError(err, 'No se pudo guardar la factura'));
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('¿Eliminar esta factura?')) return;
    try {
      await api.delete(`/facturas/${id}`);
      setFacturas((prev) => prev.filter((f) => f.id !== id));
    } catch (err) {
      window.alert(extraerMensajeError(err, 'No se pudo eliminar la factura'));
    }
  }

  let facturasFiltradas = facturas;
  if (filtroEstado) {
    facturasFiltradas = facturasFiltradas.filter((f) => f.estado === filtroEstado);
  }
  if (busqueda.trim()) {
    const q = busqueda.toLowerCase();
    facturasFiltradas = facturasFiltradas.filter((f) => f.cliente_nombre.toLowerCase().includes(q));
  }

  const thStyle = {
    padding: '12px 16px', fontSize: '12px', color: '#475569',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
    textAlign: 'left',
  };

  const COLS = '1.5fr 2fr 1fr 1fr 1fr 1fr 2.2fr';

  const modalInputStyle = {
    background: '#0f1117', border: '1px solid #1e293b',
    color: '#e2e8f0', borderRadius: '8px',
    padding: '10px 14px', width: '100%',
    fontSize: '14px', outline: 'none', boxSizing: 'border-box',
  };

  return (
    <>
    {editando && (
      <div
        onClick={(e) => { if (e.target === e.currentTarget) setEditando(null); }}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.7)',
          zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >
        <div style={{
          background: '#161b27', border: '1px solid #1e293b',
          borderRadius: '10px', padding: '24px',
          maxWidth: '560px', width: '90%',
        }}>
          <p style={{ margin: '0 0 20px 0', fontSize: '17px', fontWeight: 600, color: '#f8fafc' }}>
            Editar factura
          </p>
          <form onSubmit={handleSaveEdit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Cliente</label>
                <input
                  name="cliente_nombre" required value={editForm.cliente_nombre} onChange={handleEditChange}
                  style={modalInputStyle}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Monto</label>
                <input
                  name="monto" type="number" step="0.01" min="0" required value={editForm.monto} onChange={handleEditChange}
                  style={modalInputStyle}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Descripción</label>
              <input
                name="descripcion" required value={editForm.descripcion} onChange={handleEditChange}
                style={modalInputStyle}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Fecha de emisión</label>
                <input
                  name="fecha_emision" type="date" required value={editForm.fecha_emision} onChange={handleEditChange}
                  style={{ ...modalInputStyle, colorScheme: 'dark' }}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Fecha de vencimiento</label>
                <input
                  name="fecha_vencimiento" type="date" required value={editForm.fecha_vencimiento} onChange={handleEditChange}
                  style={{ ...modalInputStyle, colorScheme: 'dark' }}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
            </div>
            {editError && (
              <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 12px 0' }}>{editError}</p>
            )}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="submit" disabled={editSaving}
                style={{
                  background: '#3b82f6', color: '#fff', border: 'none',
                  borderRadius: '8px', padding: '9px 22px',
                  fontSize: '14px', fontWeight: 500, cursor: 'pointer',
                  opacity: editSaving ? 0.7 : 1,
                }}
              >
                {editSaving ? 'Guardando...' : 'Guardar cambios'}
              </button>
              <button
                type="button" onClick={() => setEditando(null)}
                style={{
                  background: 'transparent', color: '#94a3b8',
                  border: '1px solid #1e293b', borderRadius: '8px',
                  padding: '9px 22px', fontSize: '14px', cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    )}
    <Layout activeSection="Facturas">

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Facturas</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
            fontWeight: 500, cursor: 'pointer',
          }}
        >
          ＋ Nueva factura
        </button>
      </div>

      {/* Formulario */}
      {showForm && (
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
          <p style={{ margin: '0 0 16px 0', fontSize: '15px', fontWeight: 500, color: '#e2e8f0' }}>Nueva factura</p>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Cliente</label>
                <input
                  name="cliente_nombre" required value={form.cliente_nombre} onChange={handleFormChange}
                  placeholder="Nombre del cliente"
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
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Descripción</label>
              <input
                name="descripcion" required value={form.descripcion} onChange={handleFormChange}
                placeholder="Servicio o trabajo facturado"
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Fecha de emisión</label>
                <input
                  name="fecha_emision" type="date" required value={form.fecha_emision} onChange={handleFormChange}
                  style={{ ...inputStyle, colorScheme: 'dark' }}
                  onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                  onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '6px' }}>Fecha de vencimiento</label>
                <input
                  name="fecha_vencimiento" type="date" required value={form.fecha_vencimiento} onChange={handleFormChange}
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
          value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}
          style={{ ...inputStyle, width: 'auto', minWidth: '160px', cursor: 'pointer' }}
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="pagada">Pagada</option>
          <option value="vencida">Vencida</option>
        </select>
        <input
          value={busqueda} onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar cliente..."
          style={{ ...inputStyle, width: '220px' }}
          onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
          onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
        />
      </div>

      {/* Tabla */}
      <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ display: 'grid', gridTemplateColumns: COLS, borderBottom: '1px solid #1e293b' }}>
          {['Cliente', 'Descripción', 'Emisión', 'Vencimiento', 'Monto', 'Estado', 'Acciones'].map((h) => (
            <div key={h} style={thStyle}>{h}</div>
          ))}
        </div>

        {/* Filas */}
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
            Cargando...
          </div>
        ) : facturasFiltradas.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#475569', fontSize: '14px' }}>
            No hay facturas registradas
          </div>
        ) : (
          facturasFiltradas.map((factura, idx) => {
            const badgeStyle = ESTADO_BADGE[factura.estado] || ESTADO_BADGE.pendiente;
            const isPagando = pagandoId === factura.id;

            return (
              <div key={factura.id}>
                <div
                  style={{
                    display: 'grid', gridTemplateColumns: COLS,
                    alignItems: 'center',
                    borderBottom: (idx < facturasFiltradas.length - 1 || isPagando) ? '1px solid #1e293b' : 'none',
                  }}
                >
                  <div style={{ padding: '12px 16px', fontSize: '14px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {factura.cliente_nombre}
                  </div>
                  <div style={{ padding: '12px 16px', fontSize: '13px', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {factura.descripcion}
                  </div>
                  <div style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b' }}>
                    {formatFecha(factura.fecha_emision)}
                  </div>
                  <div style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b' }}>
                    {formatFecha(factura.fecha_vencimiento)}
                  </div>
                  <div style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: '#e2e8f0' }}>
                    {fmtMonto(factura.monto)}
                  </div>
                  <div style={{ padding: '12px 16px' }}>
                    <span style={{ ...badgeStyle, fontSize: '12px', padding: '3px 8px', borderRadius: '4px' }}>
                      {factura.estado}
                    </span>
                  </div>
                  <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    {factura.estado === 'pendiente' && (
                      <button
                        onClick={() => { setPagandoId(isPagando ? null : factura.id); setFechaPago(todayISO()); }}
                        style={{
                          background: isPagando ? '#1e3a5f' : 'transparent',
                          border: '1px solid #3b82f6', color: '#3b82f6',
                          borderRadius: '6px', padding: '4px 10px',
                          fontSize: '12px', cursor: 'pointer',
                        }}
                      >
                        Marcar pagada
                      </button>
                    )}
                    {factura.estado !== 'pagada' && (
                      <button
                        onClick={() => handleAbrirEditar(factura)}
                        style={{
                          background: '#3b82f6', color: '#fff', border: 'none',
                          borderRadius: '6px', padding: '4px 10px',
                          fontSize: '12px', cursor: 'pointer',
                        }}
                      >
                        ✏️ Editar
                      </button>
                    )}
                    <EliminarBtn
                      disabled={factura.estado === 'pagada'}
                      onDelete={() => handleDelete(factura.id)}
                    />
                  </div>
                </div>

                {/* Inline form fecha de pago */}
                {isPagando && (
                  <div style={{
                    padding: '12px 16px', background: '#0f1e35',
                    borderBottom: idx < facturasFiltradas.length - 1 ? '1px solid #1e293b' : 'none',
                    display: 'flex', alignItems: 'center', gap: '10px',
                  }}>
                    <span style={{ fontSize: '12px', color: '#93c5fd' }}>Fecha de pago:</span>
                    <input
                      type="date"
                      value={fechaPago}
                      onChange={(e) => setFechaPago(e.target.value)}
                      style={smallInputStyle}
                      onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                      onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
                    />
                    <button
                      onClick={() => handleMarcarPagada(factura.id)}
                      style={{
                        background: '#3b82f6', color: '#fff', border: 'none',
                        borderRadius: '6px', padding: '5px 14px',
                        fontSize: '12px', cursor: 'pointer', fontWeight: 500,
                      }}
                    >
                      Confirmar
                    </button>
                    <button
                      onClick={() => setPagandoId(null)}
                      style={{
                        background: 'transparent', color: '#64748b',
                        border: '1px solid #1e293b', borderRadius: '6px',
                        padding: '5px 14px', fontSize: '12px', cursor: 'pointer',
                      }}
                    >
                      Cancelar
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </Layout>
    </>
  );
}
