/**
 * Pantalla Importar CSV — carga masiva de movimientos.
 *
 * Permite subir un extracto bancario (CSV/XLSX). El backend detecta las
 * columnas, clasifica cada movimiento como ingreso o gasto y marca posibles
 * duplicados; esta pantalla muestra la previsualización y, tras la confirmación
 * del usuario, dispara el guardado (endpoints de /importar).
 */
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import api from '../api';

function fmt(n) {
  return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
function formatFecha(str) {
  if (!str) return '—';
  const d = new Date(str);
  return `${d.getDate()} ${MESES_CORTOS[d.getMonth()]} ${d.getFullYear()}`;
}

const PASO = { SUBIR: 'subir', PREVIEW: 'preview', EXITO: 'exito' };

export default function ImportarCSV() {
  const [paso, setPaso] = useState(PASO.SUBIR);
  const [archivo, setArchivo] = useState(null);
  const [drag, setDrag] = useState(false);
  const [analizando, setAnalizando] = useState(false);
  const [importando, setImportando] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [preview, setPreview] = useState([]);
  const [totalFilas, setTotalFilas] = useState(0);
  const [mapeo, setMapeo] = useState(null);
  const [resultado, setResultado] = useState(null);
  const inputRef = useRef();
  const navigate = useNavigate();

  // ── Paso 1: subir ──────────────────────────────────────────────────────────

  function handleFile(f) {
    if (!f) return;
    const nombre = f.name.toLowerCase();
    if (!nombre.endsWith('.csv') && !nombre.endsWith('.xlsx')) {
      setErrorMsg('Solo se aceptan archivos .csv o .xlsx');
      return;
    }
    setErrorMsg('');
    setArchivo(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDrag(false);
    handleFile(e.dataTransfer.files[0]);
  }

  async function handleAnalizar() {
    if (!archivo) return;
    setAnalizando(true);
    setErrorMsg('');
    try {
      const form = new FormData();
      form.append('archivo', archivo);
      const res = await api.post('/importar/preview', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setPreview(res.data.preview);
      setTotalFilas(res.data.total_filas);
      setMapeo(res.data.mapeo_detectado);
      setPaso(PASO.PREVIEW);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Error al analizar el archivo');
    } finally {
      setAnalizando(false);
    }
  }

  // ── Paso 2: confirmar ──────────────────────────────────────────────────────

  async function handleConfirmar() {
    setImportando(true);
    try {
      const res = await api.post('/importar/confirmar', {
        movimientos: preview,
        mapeo: mapeo,
      });
      setResultado(res.data);
      setPaso(PASO.EXITO);
    } catch (_) {
      setErrorMsg('Error al importar los movimientos');
    } finally {
      setImportando(false);
    }
  }

  function handleReiniciar() {
    setPaso(PASO.SUBIR);
    setArchivo(null);
    setPreview([]);
    setMapeo(null);
    setResultado(null);
    setErrorMsg('');
  }

  // ── Cálculos preview ───────────────────────────────────────────────────────
  // `preview` contiene el archivo COMPLETO ya clasificado (es lo que se envía
  // a /confirmar); la tabla solo muestra las primeras 20 filas como muestra.

  const filasVisibles = preview.slice(0, 20);
  const ingresosPrev  = preview.filter((m) => m.tipo === 'ingreso');
  const gastosPrev    = preview.filter((m) => m.tipo === 'gasto');
  const totalIngresos = ingresosPrev.reduce((s, m) => s + m.monto, 0);
  const totalGastos   = gastosPrev.reduce((s, m) => s + m.monto, 0);

  // ── Render ─────────────────────────────────────────────────────────────────

  const thStyle = {
    padding: '10px 14px', fontSize: '11px', color: '#475569',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
    textAlign: 'left',
  };

  return (
    <Layout activeSection="Importar CSV">

      {/* ── PASO 1 ── */}
      {paso === PASO.SUBIR && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{
            background: '#0f1e35', border: '1px solid #1e3a5f',
            borderRadius: '12px', padding: '40px',
            width: '100%', maxWidth: '600px',
          }}>
            {/* Badge */}
            <div style={{ marginBottom: '16px' }}>
              <span style={{
                background: '#1e3a5f', color: '#3b82f6',
                fontSize: '12px', fontWeight: 600,
                padding: '4px 12px', borderRadius: '20px',
                display: 'inline-flex', alignItems: 'center', gap: '6px',
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
                Importador Universal IA
              </span>
            </div>

            <h1 style={{ margin: '0 0 10px 0', fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>
              Importá tus movimientos bancarios
            </h1>
            <p style={{ margin: '0 0 28px 0', fontSize: '14px', color: '#64748b', lineHeight: 1.6 }}>
              Compatible con cualquier banco argentino: Galicia, Santander, Nación, BBVA, Mercado Pago, Naranja X y más.
            </p>

            {/* Zona drop */}
            <div
              onClick={() => inputRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={handleDrop}
              style={{
                border: `2px dashed ${drag ? '#3b82f6' : archivo ? '#4ade80' : '#1e3a5f'}`,
                borderRadius: '8px', padding: '30px',
                textAlign: 'center', cursor: 'pointer',
                background: drag ? '#0a1628' : 'transparent',
                transition: 'all 0.15s',
                marginBottom: '20px',
              }}
            >
              <div style={{ fontSize: '36px', marginBottom: '10px' }}>📄</div>
              {archivo ? (
                <>
                  <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#4ade80', fontWeight: 500 }}>
                    {archivo.name}
                  </p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
                    {(archivo.size / 1024).toFixed(1)} KB — Click para cambiar
                  </p>
                </>
              ) : (
                <>
                  <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#94a3b8' }}>
                    Arrastrá tu CSV acá o hacé click para seleccionar
                  </p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#475569' }}>Archivos .csv o .xlsx (Excel)</p>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.xlsx"
                style={{ display: 'none' }}
                onChange={(e) => handleFile(e.target.files[0])}
              />
            </div>

            {errorMsg && (
              <p style={{ margin: '0 0 14px 0', fontSize: '13px', color: '#f87171' }}>{errorMsg}</p>
            )}

            <button
              onClick={handleAnalizar}
              disabled={!archivo || analizando}
              style={{
                width: '100%', background: '#3b82f6', color: '#fff',
                border: 'none', borderRadius: '8px', padding: '12px',
                fontSize: '15px', fontWeight: 500,
                cursor: !archivo || analizando ? 'not-allowed' : 'pointer',
                opacity: !archivo ? 0.5 : 1,
              }}
            >
              {analizando ? 'Analizando con IA...' : 'Analizar con IA'}
            </button>
          </div>
        </div>
      )}

      {/* ── PASO 2 ── */}
      {paso === PASO.PREVIEW && (
        <>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px', flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>
              Se detectaron {totalFilas} movimientos
            </h1>
            <span style={{
              background: '#1a2e1a', color: '#4ade80',
              fontSize: '12px', fontWeight: 600,
              padding: '4px 12px', borderRadius: '20px',
            }}>
              Listo para importar
            </span>
            {totalFilas > 20 && (
              <span style={{ fontSize: '12px', color: '#64748b' }}>
                (mostrando los primeros 20)
              </span>
            )}
          </div>

          {/* Tabla */}
          <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden', marginBottom: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 3fr 1fr 1.5fr 1.2fr', borderBottom: '1px solid #1e293b' }}>
              {['Fecha', 'Descripción', 'Tipo', 'Categoría', 'Monto'].map((h) => (
                <div key={h} style={thStyle}>{h}</div>
              ))}
            </div>
            {filasVisibles.map((m, idx) => (
              <div
                key={idx}
                style={{
                  display: 'grid', gridTemplateColumns: '1.2fr 3fr 1fr 1.5fr 1.2fr',
                  alignItems: 'center',
                  borderBottom: idx < filasVisibles.length - 1 ? '1px solid #1e293b' : 'none',
                }}
              >
                <div style={{ padding: '10px 14px', fontSize: '12px', color: '#64748b' }}>
                  {formatFecha(m.fecha)}
                </div>
                <div style={{ padding: '10px 14px', fontSize: '13px', color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {m.descripcion}
                </div>
                <div style={{ padding: '10px 14px' }}>
                  <span style={{
                    fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px',
                    background: m.tipo === 'ingreso' ? '#1a2e1a' : '#1c1010',
                    color: m.tipo === 'ingreso' ? '#4ade80' : '#f87171',
                  }}>
                    {m.tipo === 'ingreso' ? 'Ingreso' : 'Gasto'}
                  </span>
                </div>
                <div style={{ padding: '10px 14px' }}>
                  <span style={{ fontSize: '11px', background: '#0f1e35', color: '#3b82f6', padding: '3px 8px', borderRadius: '4px' }}>
                    {m.categoria}
                  </span>
                </div>
                <div style={{
                  padding: '10px 14px', fontSize: '13px', fontWeight: 600,
                  color: m.tipo === 'ingreso' ? '#4ade80' : '#f87171',
                }}>
                  {m.tipo === 'ingreso' ? '+' : '-'}${fmt(m.monto)}
                </div>
              </div>
            ))}
          </div>

          {/* Resumen + botones */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
            <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
              <span style={{ color: '#4ade80' }}>{ingresosPrev.length} ingresos</span>
              {' · '}
              <span style={{ color: '#f87171' }}>{gastosPrev.length} gastos</span>
              {' · Total neto: '}
              <span style={{ color: '#f8fafc', fontWeight: 600 }}>
                ${fmt(totalIngresos - totalGastos)}
              </span>
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleReiniciar}
                style={{
                  background: 'transparent', color: '#94a3b8',
                  border: '1px solid #1e293b', borderRadius: '8px',
                  padding: '9px 20px', fontSize: '14px', cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmar}
                disabled={importando}
                style={{
                  background: '#3b82f6', color: '#fff', border: 'none',
                  borderRadius: '8px', padding: '9px 24px',
                  fontSize: '14px', fontWeight: 500,
                  cursor: importando ? 'not-allowed' : 'pointer',
                  opacity: importando ? 0.7 : 1,
                }}
              >
                {importando ? 'Importando...' : 'Confirmar importación'}
              </button>
            </div>
          </div>

          {errorMsg && (
            <p style={{ marginTop: '12px', fontSize: '13px', color: '#f87171' }}>{errorMsg}</p>
          )}
        </>
      )}

      {/* ── PASO 3 ── */}
      {paso === PASO.EXITO && resultado && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{
            background: '#0f1e35', border: '1px solid #1e3a5f',
            borderRadius: '12px', padding: '48px 40px',
            maxWidth: '500px', width: '100%', textAlign: 'center',
          }}>
            <div style={{ fontSize: '56px', marginBottom: '16px' }}>✓</div>
            <h2 style={{ margin: '0 0 12px 0', fontSize: '24px', fontWeight: 700, color: '#4ade80' }}>
              ¡Importación exitosa!
            </h2>
            <p style={{ margin: '0 0 28px 0', fontSize: '15px', color: '#94a3b8', lineHeight: 1.6 }}>
              Se importaron <strong style={{ color: '#f8fafc' }}>{resultado.importados} movimientos</strong>
              <br />
              <span style={{ color: '#4ade80' }}>{resultado.ingresos_creados} ingresos</span>
              {' · '}
              <span style={{ color: '#f87171' }}>{resultado.gastos_creados} gastos</span>
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <button
                  onClick={() => navigate('/ingresos')}
                  style={{
                    background: 'transparent', color: '#3b82f6',
                    border: '1px solid #3b82f6', borderRadius: '8px',
                    padding: '9px 20px', fontSize: '14px', cursor: 'pointer',
                  }}
                >
                  Ver ingresos
                </button>
                <button
                  onClick={() => navigate('/gastos')}
                  style={{
                    background: 'transparent', color: '#f87171',
                    border: '1px solid #f87171', borderRadius: '8px',
                    padding: '9px 20px', fontSize: '14px', cursor: 'pointer',
                  }}
                >
                  Ver gastos
                </button>
              </div>
              <button
                onClick={handleReiniciar}
                style={{
                  background: '#3b82f6', color: '#fff', border: 'none',
                  borderRadius: '8px', padding: '9px 20px',
                  fontSize: '14px', fontWeight: 500, cursor: 'pointer',
                }}
              >
                Importar otro archivo
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
