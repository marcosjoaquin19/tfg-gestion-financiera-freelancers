/**
 * Pantalla Monotributo — control fiscal.
 *
 * Muestra la situación del usuario frente al monotributo argentino: su
 * facturación del año en curso, el porcentaje del límite anual consumido, la
 * proyección hasta diciembre con el semáforo de riesgo (HU-10) y el estado del
 * pago mensual. Permite también elegir/actualizar la categoría (endpoints de
 * /monotributo).
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import AvisoAlcance from '../components/AvisoAlcance';
import api, { extraerMensajeError } from '../api';

// La escala de categorías se trae del backend (GET /monotributo/categorias, que
// lee la tabla `categorias_monotributo`). Única fuente de verdad: se actualiza en
// un solo lugar (seed_categorias_monotributo.py) y el frontend la consume.

function fmt(n) {
  return Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

// Porcentajes con coma decimal, como el resto de la app ("84,4").
function fmtPct(n) {
  return Number(n || 0).toLocaleString('es-AR', { maximumFractionDigits: 1 });
}

const ESTADO_COLORS = {
  verde:    { fondo: '#0d1f0d', borde: '#1a4d1a', color: '#4ade80' },
  amarillo: { fondo: '#1f1a0d', borde: '#4d3d1a', color: '#fbbf24' },
  rojo:     { fondo: '#1f0d0d', borde: '#4d1a1a', color: '#f87171' },
};

const ESTADO_MSG = {
  verde:    '✓ Tu facturación está bajo control',
  amarillo: 'Estás acercándote al límite de tu categoría',
  rojo:     '⚠️ En riesgo de recategorización',
};

const selectStyle = {
  background: '#0f1117', border: '1px solid #1e293b',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '10px 14px', width: '100%',
  fontSize: '14px', outline: 'none', cursor: 'pointer',
};

export default function Monotributo() {
  const [estado, setEstado] = useState(null);
  const [pago, setPago] = useState(null);
  const [categorias, setCategorias] = useState({});  // escala traída del backend, key = letra
  const [loading, setLoading] = useState(true);
  const [catSeleccionada, setCatSeleccionada] = useState('A');
  const [guardando, setGuardando] = useState(false);
  // Error al guardar la categoría (backend o red): visible, no silencioso.
  const [catError, setCatError] = useState('');
  const [showCambiarCat, setShowCambiarCat] = useState(false);
  const navigate = useNavigate();

  async function fetchData() {
    setLoading(true);
    const [estRes, pagRes, catRes] = await Promise.allSettled([
      api.get('/monotributo/estado'),
      api.get('/monotributo/pago'),
      api.get('/monotributo/categorias'),
    ]);
    if (estRes.status === 'fulfilled') setEstado(estRes.value.data);
    if (pagRes.status === 'fulfilled') setPago(pagRes.value.data);
    if (catRes.status === 'fulfilled') {
      const obj = {};
      for (const c of catRes.value.data) obj[c.letra] = c;
      setCategorias(obj);
    }
    setLoading(false);
  }

  useEffect(() => { fetchData(); }, []);

  async function handleGuardarCategoria(cat) {
    setGuardando(true);
    setCatError('');
    try {
      await api.patch('/monotributo/categoria', { categoria_monotributo: cat });
      await fetchData();
      setShowCambiarCat(false);
    } catch (err) {
      setCatError(extraerMensajeError(err, 'No se pudo actualizar la categoría'));
    } finally {
      setGuardando(false);
    }
  }

  if (loading) {
    return (
      <Layout activeSection="Monotributo">
        <div style={{ textAlign: 'center', color: '#64748b', fontSize: '14px', padding: '48px' }}>
          Cargando...
        </div>
      </Layout>
    );
  }

  // ── Estado sin categoría ─────────────────────────────────────────────────

  if (!estado || estado.sin_categoria) {
    const infoPreview = catSeleccionada ? categorias[catSeleccionada] : null;
    return (
      <Layout activeSection="Monotributo">
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{
            background: '#161b27', border: '1px solid #1e293b',
            borderRadius: '12px', padding: '40px',
            maxWidth: '500px', width: '100%',
          }}>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>
              Configurá tu categoría de monotributo
            </h2>
            <p style={{ margin: '0 0 28px 0', fontSize: '14px', color: '#64748b', lineHeight: 1.6 }}>
              Necesitamos saber tu categoría para hacer el seguimiento de tu facturación.
            </p>

            <label style={{ display: 'block', fontSize: '12px', color: '#e2e8f0', marginBottom: '8px' }}>
              Categoría
            </label>
            <select
              value={catSeleccionada}
              onChange={(e) => setCatSeleccionada(e.target.value)}
              style={{ ...selectStyle, marginBottom: '12px' }}
            >
              {Object.keys(categorias).map((c) => (
                <option key={c} value={c}>Categoría {c}</option>
              ))}
            </select>

            {infoPreview && (
              <p style={{ margin: '0 0 20px 0', fontSize: '13px', color: '#94a3b8' }}>
                Límite anual:{' '}
                <strong style={{ color: '#e2e8f0' }}>${fmt(infoPreview.limite_anual)}</strong>
                {' · '}
                Cuota mensual:{' '}
                <strong style={{ color: '#e2e8f0' }}>${fmt(infoPreview.cuota_mensual)}</strong>
              </p>
            )}

            {catError && (
              <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 12px 0' }}>{catError}</p>
            )}

            <button
              onClick={() => handleGuardarCategoria(catSeleccionada)}
              disabled={guardando}
              style={{
                width: '100%', background: '#3b82f6', color: '#fff',
                border: 'none', borderRadius: '8px', padding: '11px',
                fontSize: '15px', fontWeight: 500,
                cursor: guardando ? 'not-allowed' : 'pointer',
                opacity: guardando ? 0.7 : 1,
              }}
            >
              {guardando ? 'Guardando...' : 'Guardar categoría'}
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  // ── Estado con categoría ─────────────────────────────────────────────────

  const colores = ESTADO_COLORS[estado.estado] || ESTADO_COLORS.verde;
  const pct = Math.min(estado.porcentaje_usado, 100);
  const catSiguienteInfo = estado.categoria_siguiente
    ? categorias[estado.categoria_siguiente]
    : null;
  const catSugeridaInfo = estado.categoria_sugerida
    ? categorias[estado.categoria_sugerida]
    : null;
  const catMaxima = Object.values(categorias).reduce(
    (max, c) => (!max || c.limite_anual > max.limite_anual ? c : max), null,
  );
  const mensajeEstado = estado.limite_superado
    ? '⚠️ Ya superaste el límite anual de tu categoría'
    : ESTADO_MSG[estado.estado];

  return (
    <Layout activeSection="Monotributo">

      {/* ── Alerta de pago ── */}
      {pago && (
        <div style={{
          background: pago.pagado ? '#0d1f0d' : '#1f1a0d',
          borderLeft: `3px solid ${pago.pagado ? '#4ade80' : '#fbbf24'}`,
          borderRadius: '8px', padding: '14px 18px',
          marginBottom: '16px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px',
        }}>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#e2e8f0', fontWeight: 500 }}>
              {pago.pagado
                ? `✓ Monotributo de ${pago.mes} ${pago.anio} registrado como pagado`
                : pago.pago_parcial
                ? `⚠️ El pago registrado de ${pago.mes} ${pago.anio} no cubre la cuota`
                : `⚠️ No registramos el pago del monotributo de ${pago.mes} ${pago.anio}`}
            </p>
            {!pago.pagado && pago.monto_esperado && (
              <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>
                Cuota esperada: <strong style={{ color: '#fbbf24' }}>${fmt(pago.monto_esperado)}</strong>
                {pago.pago_parcial && pago.gasto_encontrado && (
                  <> · Registrado: <strong style={{ color: '#fbbf24' }}>${fmt(pago.gasto_encontrado.monto)}</strong></>
                )}
              </p>
            )}
          </div>
          {!pago.pagado && (
            /* Manda el formulario de Gastos pre-cargado (misma mecánica que
               usa el Clasificador): descripción, categoría y la cuota esperada. */
            <button
              onClick={() => navigate('/gastos', {
                state: {
                  descripcion: `Pago monotributo ${pago.mes} ${pago.anio}`,
                  categoria: 'Monotributo',
                  monto: pago.monto_esperado || '',
                },
              })}
              title="Cargá el gasto con categoría Monotributo"
              style={{
                background: 'transparent', border: '1px solid #fbbf24',
                color: '#fbbf24', borderRadius: '6px',
                padding: '6px 14px', fontSize: '13px', cursor: 'pointer',
              }}
            >
              Registrar pago ahora →
            </button>
          )}
        </div>
      )}

      {/* ── Card principal ── */}
      <div style={{
        background: colores.fondo, border: `1px solid ${colores.borde}`,
        borderRadius: '12px', padding: '24px',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '28px', fontWeight: 600, color: '#f8fafc' }}>
              Categoría {estado.categoria_actual}
            </p>
            <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Prestación de servicios</p>
          </div>
          {!showCambiarCat ? (
            <button
              onClick={() => { setShowCambiarCat(true); setCatSeleccionada(estado.categoria_actual); }}
              style={{
                background: '#3b82f6', color: '#fff', border: 'none',
                borderRadius: '8px', padding: '10px 18px',
                fontSize: '13px', fontWeight: 500, cursor: 'pointer',
              }}
            >
              ✏️ Cambiar categoría
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              {catError && (
                <span style={{ color: '#f87171', fontSize: '12px' }}>{catError}</span>
              )}
              <select
                value={catSeleccionada}
                onChange={(e) => setCatSeleccionada(e.target.value)}
                style={{ ...selectStyle, width: 'auto', padding: '5px 10px', fontSize: '13px' }}
              >
                {Object.keys(categorias).map((c) => (
                  <option key={c} value={c}>Categoría {c}</option>
                ))}
              </select>
              <button
                onClick={() => handleGuardarCategoria(catSeleccionada)}
                disabled={guardando}
                style={{
                  background: '#3b82f6', color: '#fff', border: 'none',
                  borderRadius: '6px', padding: '5px 12px',
                  fontSize: '12px', cursor: 'pointer',
                }}
              >
                {guardando ? '...' : 'Guardar'}
              </button>
              <button
                onClick={() => setShowCambiarCat(false)}
                style={{
                  background: 'transparent', border: '1px solid #1e293b',
                  color: '#64748b', borderRadius: '6px',
                  padding: '5px 10px', fontSize: '12px', cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Barra de progreso */}
        <div style={{ marginBottom: '10px' }}>
          <div style={{ height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden', marginBottom: '8px' }}>
            <div style={{ height: '8px', width: `${pct}%`, background: colores.color, borderRadius: '4px', transition: 'width 0.3s' }} />
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>
            <strong style={{ color: colores.color }}>${fmt(estado.facturado_anual)}</strong>
            {' facturado de '}
            <strong>${fmt(estado.limite_anual)}</strong>
            {' anuales '}
            <span style={{ color: '#64748b' }}>({fmtPct(estado.porcentaje_usado)}%)</span>
          </p>
        </div>

        <p style={{ margin: 0, fontSize: '13px', color: colores.color, fontWeight: 500 }}>
          {mensajeEstado}
        </p>
      </div>

      {/* ── Métricas ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <p style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 600, color: '#3b82f6' }}>
            ${fmt(estado.cuota_mensual)}
          </p>
          <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>Cuota mensual</p>
        </div>
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <p style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 600, color: '#f8fafc' }}>
            ${fmt(estado.proyeccion_anual)}
          </p>
          <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0' }}>Proyección anual</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#64748b' }}>
            {fmtPct(estado.porcentaje_proyectado)}% del límite al cierre del año
            {estado.meses_estimados_con_promedio > 0 &&
              ` · ${estado.meses_estimados_con_promedio} ${estado.meses_estimados_con_promedio === 1 ? 'mes estimado' : 'meses estimados'} con el promedio proyectado`}
          </p>
        </div>
        <div style={{ background: '#161b27', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          {(() => {
            // El modelo es anual (HU-10): solo se informa un mes si el tope se
            // cruza antes de diciembre. "Sin fecha" no significa "sin riesgo"
            // si ya se superó o si el semáforo está en amarillo o rojo.
            const m = estado.meses_para_limite;
            if (estado.limite_superado) return (
              <>
                <p style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: 600, color: '#f87171' }}>⚠️ Límite superado</p>
                <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Lo facturado este año ya pasó el tope</p>
              </>
            );
            if (m === null) return estado.estado === 'verde' ? (
              <>
                <p style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: 600, color: '#4ade80' }}>✓ Sin riesgo este año</p>
                <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Tu proyección no llega al límite</p>
              </>
            ) : (
              <>
                <p style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: 600, color: colores.color }}>Este año no lo superarías</p>
                <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Pero quedás cerca: {fmtPct(estado.porcentaje_proyectado)}% del límite</p>
              </>
            );
            return (
              <>
                <p style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 600, color: '#f87171' }}>
                  ⚠️ {m === 0 ? 'Este mes' : estado.mes_limite}
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
                  {m === 0 ? 'Al ritmo proyectado lo superás este mes' : `En ${m} ${m === 1 ? 'mes' : 'meses'} al ritmo proyectado`}
                </p>
              </>
            );
          })()}
          <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#e2e8f0' }}>Riesgo de recategorización</p>
        </div>
      </div>

      {/* ── Alerta recategorización ── */}
      {(estado.estado === 'amarillo' || estado.estado === 'rojo' || estado.limite_superado) && (
        <div style={{
          background: colores.fondo, border: `1px solid ${colores.borde}`,
          borderLeft: `3px solid ${colores.color}`,
          borderRadius: '8px', padding: '16px', marginBottom: '16px',
        }}>
          <p style={{ margin: 0, fontSize: '14px', color: '#e2e8f0', lineHeight: 1.6 }}>
            {estado.limite_superado ? (
              <>Lo que facturaste este año ya superó el límite de <strong>Categoría {estado.categoria_actual}</strong>.</>
            ) : estado.mes_limite ? (
              <>A este ritmo de facturación superarías el límite de <strong>Categoría {estado.categoria_actual}</strong> en <strong>{estado.mes_limite}</strong>.</>
            ) : (
              <>Tu proyección anual llega al <strong>{fmtPct(estado.porcentaje_proyectado)}%</strong> del límite de <strong>Categoría {estado.categoria_actual}</strong>: este año no lo superarías, pero estás cerca.</>
            )}
            {estado.excede_regimen ? (
              <>
                {' '}Tu proyección anual (<strong>${fmt(estado.proyeccion_anual)}</strong>) supera incluso el tope de la categoría más alta
                {catMaxima && <> (<strong>Categoría {catMaxima.letra}</strong>, ${fmt(catMaxima.limite_anual)})</>}:{' '}
                <strong style={{ color: '#f87171' }}>hay riesgo de exclusión del régimen de Monotributo.</strong>
              </>
            ) : catSugeridaInfo ? (
              <>
                {' '}Para cubrir tu proyección anual de <strong>${fmt(estado.proyeccion_anual)}</strong> necesitarías la{' '}
                <strong style={{ color: colores.color }}>Categoría {estado.categoria_sugerida}</strong>
                {' '}(tope ${fmt(catSugeridaInfo.limite_anual)}, cuota mensual ${fmt(catSugeridaInfo.cuota_mensual)}).
              </>
            ) : catSiguienteInfo ? (
              <>
                {' '}Si tu facturación sigue creciendo, la siguiente es la{' '}
                <strong style={{ color: colores.color }}>Categoría {estado.categoria_siguiente}</strong>
                {' '}con una cuota mensual de <strong>${fmt(catSiguienteInfo.cuota_mensual)}</strong>.
              </>
            ) : null}
            {' '}Te sugerimos consultar con tu contador antes de la próxima recategorización semestral.
          </p>
        </div>
      )}

      <AvisoAlcance detalle="El cálculo se basa en la escala publicada por ARCA y en los ingresos registrados en el sistema; la categorización definitiva la determina ARCA." />
    </Layout>
  );
}
