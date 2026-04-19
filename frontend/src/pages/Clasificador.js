import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import api from '../api';

const CATEGORIAS_VALIDAS = [
  'Software', 'Hardware', 'Infraestructura', 'Marketing', 'Servicios',
  'Capacitación', 'Suscripciones', 'Transporte', 'Alimentación',
  'Impuestos', 'Monotributo', 'Otros',
];

const inputStyle = {
  background: '#0f1117', border: '1px solid #1e3a5f',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '12px 14px', width: '100%',
  fontSize: '14px', outline: 'none',
  resize: 'vertical', fontFamily: 'inherit',
};

const selectStyle = {
  background: '#0f1117', border: '1px solid #1e3a5f',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '8px 12px', fontSize: '13px',
  outline: 'none', width: '100%', cursor: 'pointer',
};

function BadgeFuente({ fuente }) {
  const isML = fuente === 'ml_propio';
  return (
    <span style={{
      background: isML ? '#14532d' : '#1e3a5f',
      color: isML ? '#4ade80' : '#3b82f6',
      fontSize: '11px', fontWeight: 600,
      padding: '3px 10px', borderRadius: '20px',
      display: 'inline-block',
    }}>
      {isML ? 'ML Propio' : 'Groq IA'}
    </span>
  );
}

function BarraConfianza({ confianza }) {
  if (confianza == null) return null;
  const pct = Math.round(confianza * 100);
  const color = pct >= 85 ? '#4ade80' : pct >= 65 ? '#facc15' : '#f87171';
  return (
    <div style={{ marginTop: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '11px', color: '#64748b' }}>Confianza</span>
        <span style={{ fontSize: '11px', color, fontWeight: 600 }}>{pct}%</span>
      </div>
      <div style={{ background: '#1e293b', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, background: color, height: '100%', borderRadius: '4px', transition: 'width 0.4s' }} />
      </div>
    </div>
  );
}

function CardEstadoML({ estado, cargando, onReentrenar, reentrenando }) {
  if (cargando) {
    return (
      <div style={{ background: '#0f1e35', border: '1px solid #1e293b', borderRadius: '12px', padding: '16px', maxWidth: '600px', marginBottom: '20px' }}>
        <span style={{ fontSize: '13px', color: '#475569' }}>Cargando estado del modelo...</span>
      </div>
    );
  }

  if (!estado) return null;

  const { tiene_modelo_propio, algoritmo, precision, n_ejemplos, fecha_entrenamiento, usa_modelo_base } = estado;
  const precisionPct = precision != null ? Math.round(precision * 100) : null;
  const fechaStr = fecha_entrenamiento ? new Date(fecha_entrenamiento).toLocaleDateString('es-AR') : null;
  const algoLabel = algoritmo === 'svm' ? 'SVM' : algoritmo === 'naive_bayes' ? 'Naive Bayes' : '—';

  return (
    <div style={{ background: '#0f1e35', border: `1px solid ${tiene_modelo_propio ? '#166534' : '#1e3a5f'}`, borderRadius: '12px', padding: '16px', maxWidth: '600px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div>
          <p style={{ margin: '0 0 4px 0', fontSize: '13px', fontWeight: 600, color: tiene_modelo_propio ? '#4ade80' : '#94a3b8' }}>
            {tiene_modelo_propio ? 'Modelo personalizado activo' : 'Usando modelo base'}
          </p>
          {!tiene_modelo_propio && (
            <p style={{ margin: 0, fontSize: '12px', color: '#475569' }}>
              Clasificá más gastos para personalizar tu modelo
            </p>
          )}
        </div>
        <span style={{
          background: '#1e293b', color: '#93c5fd',
          fontSize: '11px', fontWeight: 600,
          padding: '3px 10px', borderRadius: '20px',
        }}>
          {algoLabel}
        </span>
      </div>

      <div style={{ display: 'flex', gap: '24px', fontSize: '12px', color: '#64748b', flexWrap: 'wrap' }}>
        {precisionPct != null && <span>Precisión: <strong style={{ color: '#e2e8f0' }}>{precisionPct}%</strong></span>}
        <span>Ejemplos: <strong style={{ color: '#e2e8f0' }}>{n_ejemplos}</strong></span>
        {fechaStr && <span>Último entrenamiento: <strong style={{ color: '#e2e8f0' }}>{fechaStr}</strong></span>}
      </div>

      <button
        onClick={onReentrenar}
        disabled={reentrenando}
        style={{
          marginTop: '12px', background: 'transparent',
          border: '1px solid #1e3a5f', color: '#3b82f6',
          borderRadius: '8px', padding: '6px 16px',
          fontSize: '12px', cursor: reentrenando ? 'not-allowed' : 'pointer',
          opacity: reentrenando ? 0.6 : 1,
        }}
      >
        {reentrenando ? 'Reentrenando...' : 'Re-entrenar modelo'}
      </button>
    </div>
  );
}

export default function Clasificador() {
  const [descripcion, setDescripcion] = useState('');
  const [clasificando, setClasificando] = useState(false);
  const [resultado, setResultado] = useState(null);   // { categoria, fuente, confianza }
  const [historial, setHistorial] = useState([]);
  const [estado, setEstado] = useState(null);
  const [cargandoEstado, setCargandoEstado] = useState(true);
  const [reentrenando, setReentrenando] = useState(false);
  const [msgReentrenamiento, setMsgReentrenamiento] = useState(null);
  const [corrigiendoCategoria, setCorrigiendoCategoria] = useState(false);
  const [categoriaCorrecta, setCategoriaCorrecta] = useState('');
  const [msgCorreccion, setMsgCorreccion] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    cargarEstado();
  }, []);

  async function cargarEstado() {
    setCargandoEstado(true);
    try {
      const res = await api.get('/ml/estado');
      setEstado(res.data);
    } catch (_) {
      setEstado(null);
    } finally {
      setCargandoEstado(false);
    }
  }

  async function handleClasificar() {
    if (!descripcion.trim()) return;
    setClasificando(true);
    setResultado(null);
    setCorrigiendoCategoria(false);
    setMsgCorreccion(null);
    try {
      const res = await api.post('/gastos/clasificar', { descripcion: descripcion.trim() });
      const { categoria_sugerida, fuente, confianza } = res.data;
      setResultado({ categoria: categoria_sugerida, fuente, confianza });
      setCategoriaCorrecta(categoria_sugerida);
      setHistorial((prev) =>
        [{ descripcion: descripcion.trim(), categoria: categoria_sugerida, fuente }, ...prev].slice(0, 10)
      );
    } catch (_) {
      setResultado({ categoria: 'Otros', fuente: null, confianza: null });
    } finally {
      setClasificando(false);
    }
  }

  async function handleReentrenar() {
    setReentrenando(true);
    setMsgReentrenamiento(null);
    try {
      const res = await api.post('/ml/reentrenar');
      setMsgReentrenamiento(res.data.mensaje || 'Modelo actualizado.');
      await cargarEstado();
    } catch (_) {
      setMsgReentrenamiento('Error al re-entrenar.');
    } finally {
      setReentrenando(false);
    }
  }

  async function handleCorregir() {
    if (!categoriaCorrecta || !descripcion.trim()) return;
    setMsgCorreccion(null);
    try {
      await api.post('/ml/corregir', {
        descripcion: descripcion.trim(),
        categoria_correcta: categoriaCorrecta,
      });
      setMsgCorreccion('¡Modelo actualizado con tu corrección!');
      setCorrigiendoCategoria(false);
      await cargarEstado();
    } catch (_) {
      setMsgCorreccion('Error al guardar la corrección.');
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && e.ctrlKey) handleClasificar();
  }

  return (
    <Layout activeSection="Clasificador">
      <h1 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>
        Clasificador de Gastos IA
      </h1>

      {/* Card estado ML */}
      <CardEstadoML
        estado={estado}
        cargando={cargandoEstado}
        onReentrenar={handleReentrenar}
        reentrenando={reentrenando}
      />
      {msgReentrenamiento && (
        <p style={{ fontSize: '12px', color: '#4ade80', marginBottom: '16px', maxWidth: '600px' }}>
          {msgReentrenamiento}
        </p>
      )}

      {/* Card principal */}
      <div style={{ background: '#0f1e35', border: '1px solid #1e3a5f', borderRadius: '12px', padding: '24px', maxWidth: '600px' }}>
        {/* Badge */}
        <div style={{ marginBottom: '16px' }}>
          <span style={{
            background: '#1e3a5f', color: '#3b82f6', fontSize: '12px',
            fontWeight: 600, padding: '4px 12px', borderRadius: '20px',
            display: 'inline-flex', alignItems: 'center', gap: '6px',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
            Inteligencia Artificial
          </span>
        </div>

        <p style={{ margin: '0 0 20px 0', fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
          Describí tu gasto y la IA sugiere automáticamente la categoría correcta.
        </p>

        {/* Textarea */}
        <div style={{ marginBottom: '14px' }}>
          <textarea
            rows={3}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: Suscripción mensual a Adobe Creative Cloud"
            style={inputStyle}
            onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
            onBlur={(e) => (e.target.style.borderColor = '#1e3a5f')}
          />
          <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#475569' }}>Ctrl + Enter para clasificar</p>
        </div>

        {/* Botón */}
        <button
          onClick={handleClasificar}
          disabled={clasificando || !descripcion.trim()}
          style={{
            width: '100%', background: '#3b82f6', color: '#fff',
            border: 'none', borderRadius: '8px', padding: '11px',
            fontSize: '15px', fontWeight: 500, cursor: clasificando || !descripcion.trim() ? 'not-allowed' : 'pointer',
            opacity: !descripcion.trim() ? 0.5 : 1,
          }}
        >
          {clasificando ? 'Clasificando...' : 'Clasificar con IA'}
        </button>

        {/* Resultado */}
        {resultado && (
          <div style={{
            marginTop: '20px', background: '#0a1628',
            border: '1px solid #1e3a5f', borderRadius: '10px', padding: '20px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>Categoría sugerida:</p>
              {resultado.fuente && <BadgeFuente fuente={resultado.fuente} />}
            </div>
            <p style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 700, color: '#3b82f6', textAlign: 'center' }}>
              {resultado.categoria}
            </p>

            <BarraConfianza confianza={resultado.confianza} />

            <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
              <button
                onClick={() => navigate('/gastos')}
                style={{
                  flex: 1, background: 'transparent', border: '1px solid #3b82f6',
                  color: '#3b82f6', borderRadius: '8px',
                  padding: '8px 20px', fontSize: '13px',
                  cursor: 'pointer', fontWeight: 500,
                }}
              >
                Crear gasto con esta categoría →
              </button>
              <button
                onClick={() => { setCorrigiendoCategoria((v) => !v); setMsgCorreccion(null); }}
                style={{
                  background: 'transparent', border: '1px solid #475569',
                  color: '#94a3b8', borderRadius: '8px',
                  padding: '8px 16px', fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Corregir categoría
              </button>
            </div>

            {/* Corrección de categoría */}
            {corrigiendoCategoria && (
              <div style={{ marginTop: '14px' }}>
                <select
                  value={categoriaCorrecta}
                  onChange={(e) => setCategoriaCorrecta(e.target.value)}
                  style={selectStyle}
                >
                  {CATEGORIAS_VALIDAS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <button
                  onClick={handleCorregir}
                  style={{
                    marginTop: '8px', width: '100%',
                    background: '#166534', border: 'none',
                    color: '#4ade80', borderRadius: '8px',
                    padding: '8px', fontSize: '13px',
                    cursor: 'pointer', fontWeight: 500,
                  }}
                >
                  Confirmar corrección
                </button>
              </div>
            )}

            {msgCorreccion && (
              <p style={{ margin: '10px 0 0 0', fontSize: '12px', color: '#4ade80', textAlign: 'center' }}>
                {msgCorreccion}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Historial */}
      {historial.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Historial de la sesión
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {historial.map((h, i) => (
              <button
                key={i}
                onClick={() => setDescripcion(h.descripcion)}
                style={{
                  background: '#161b27', border: '1px solid #1e293b',
                  color: '#94a3b8', borderRadius: '20px',
                  padding: '5px 12px', fontSize: '12px', cursor: 'pointer',
                }}
              >
                <span style={{ color: '#64748b' }}>
                  {h.descripcion.length > 30 ? h.descripcion.slice(0, 30) + '…' : h.descripcion}
                </span>
                <span style={{ color: '#475569', margin: '0 4px' }}>→</span>
                <span style={{ color: '#3b82f6', fontWeight: 500 }}>{h.categoria}</span>
                {h.fuente && (
                  <span style={{ marginLeft: '6px', color: h.fuente === 'ml_propio' ? '#4ade80' : '#3b82f6', fontSize: '10px' }}>
                    {h.fuente === 'ml_propio' ? '·ML' : '·Groq'}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </Layout>
  );
}
