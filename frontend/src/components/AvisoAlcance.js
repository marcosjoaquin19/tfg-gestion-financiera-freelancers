/**
 * AvisoAlcance — descargo de responsabilidad sobre el alcance del sistema.
 *
 * FreelanceControl **informa, proyecta y alerta**: ordena datos que el usuario
 * ya posee, estima escenarios a futuro y avisa desvíos. En ningún caso emite
 * una opinión profesional ni reemplaza a un contador, asesor fiscal o asesor
 * financiero matriculado.
 *
 * El aviso se muestra en las pantallas donde la salida del sistema podría
 * confundirse con asesoramiento profesional:
 *   - Monotributo      → situación fiscal y riesgo de recategorización.
 *   - Proyecciones     → estimaciones de ingresos futuros (modelo predictivo).
 *   - Recomendaciones  → sugerencias financieras calculadas por reglas.
 *   - Resumen IA       → texto generado por un modelo de lenguaje.
 *   - Auditoría        → alertas sobre posibles inconsistencias.
 *
 * Decisión de diseño: el descargo vive en un único componente reutilizable y
 * no duplicado en cada pantalla. Si el texto legal cambia, se edita en un solo
 * lugar y queda consistente en toda la aplicación (misma política que el
 * formateo de moneda, centralizado en app/services/formato.py del backend).
 *
 * PATRÓN: Componente compartido / Single Source of Truth para el texto legal.
 */

// Texto base común a todas las pantallas. Se mantiene exportado para que el
// mismo enunciado pueda reutilizarse fuera del componente (por ejemplo en un
// tooltip o en un test que verifique su presencia).
export const TEXTO_ALCANCE =
  'FreelanceControl informa, proyecta y alerta sobre la base de los datos que usted carga. ' +
  'No constituye asesoramiento contable, fiscal ni financiero, y no reemplaza la intervención ' +
  'de un profesional matriculado.';

/**
 * @param {string} detalle  Aclaración específica de la pantalla (opcional).
 *                          Se agrega después del texto base.
 * @param {object} style    Estilos extra para ajustar el margen en la pantalla.
 */
function AvisoAlcance({ detalle, style }) {
  return (
    <div
      // role="note" + aria-label: el descargo también queda expuesto a lectores
      // de pantalla, no solo visible. Es información legal, no decorativa.
      role="note"
      aria-label="Alcance del sistema"
      style={{
        display: 'flex',
        gap: '10px',
        alignItems: 'flex-start',
        background: '#0f1117',
        border: '1px solid #1e293b',
        borderLeft: '3px solid #64748b',
        borderRadius: '8px',
        padding: '12px 14px',
        marginTop: '20px',
        fontSize: '12px',
        lineHeight: 1.6,
        color: '#94a3b8',
        ...style,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: '14px', lineHeight: 1.4 }}>ⓘ</span>
      <span>
        <strong style={{ color: '#cbd5e1', fontWeight: 600 }}>Alcance del sistema. </strong>
        {TEXTO_ALCANCE}
        {detalle ? ` ${detalle}` : ''}
      </span>
    </div>
  );
}

export default AvisoAlcance;
