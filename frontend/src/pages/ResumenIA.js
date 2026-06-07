import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../api';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const selectStyle = {
  background: '#0f1117', border: '1px solid #1e293b',
  color: '#e2e8f0', borderRadius: '8px',
  padding: '8px 12px', fontSize: '14px',
  outline: 'none', cursor: 'pointer',
};

export default function ResumenIA() {
  const now = new Date();
  const [mes, setMes] = useState(now.getMonth() + 1);
  const [anio, setAnio] = useState(now.getFullYear());
  const [cargando, setCargando] = useState(false);
  const [resumen, setResumen] = useState(null);

  async function fetchResumen(m, a) {
    setCargando(true);
    setResumen(null);
    try {
      const res = await api.get('/resumen/financiero', { params: { mes: m, anio: a } });
      setResumen(res.data);
    } catch (_) {
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { fetchResumen(mes, anio); }, []);

  const anios = Array.from({ length: 5 }, (_, i) => now.getFullYear() - 2 + i);

  return (
    <Layout activeSection="Resumen IA">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 500, color: '#f8fafc' }}>Resumen Financiero IA</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select value={mes} onChange={(e) => setMes(Number(e.target.value))} style={selectStyle}>
            {MESES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
          </select>
          <select value={anio} onChange={(e) => setAnio(Number(e.target.value))} style={selectStyle}>
            {anios.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <button
            onClick={() => fetchResumen(mes, anio)}
            disabled={cargando}
            style={{
              background: '#3b82f6', color: '#fff', border: 'none',
              borderRadius: '8px', padding: '8px 16px', fontSize: '14px',
              fontWeight: 500, cursor: cargando ? 'not-allowed' : 'pointer',
              opacity: cargando ? 0.7 : 1,
            }}
          >
            {cargando ? 'Generando...' : 'Generar resumen'}
          </button>
        </div>
      </div>

      {/* Card resumen */}
      {cargando ? (
        <div style={{ textAlign: 'center', color: '#64748b', fontSize: '14px', padding: '48px' }}>
          Generando resumen...
        </div>
      ) : resumen && resumen.sin_datos ? (
        <div style={{
          background: '#161b27', border: '1px solid #1e293b',
          borderRadius: '12px', padding: '28px', maxWidth: '700px',
          display: 'flex', alignItems: 'center', gap: '14px',
        }}>
          <span style={{ fontSize: '26px' }}>📭</span>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '15px', color: '#e2e8f0', fontWeight: 500 }}>
              {resumen.periodo}: sin movimientos
            </p>
            <p style={{ margin: 0, fontSize: '14px', color: '#64748b', lineHeight: 1.6 }}>
              {resumen.resumen}
            </p>
          </div>
        </div>
      ) : resumen ? (
        <div style={{ background: '#0f1e35', border: '1px solid #1e3a5f', borderRadius: '12px', padding: '28px', maxWidth: '700px' }}>
          {/* Header de la card */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <span style={{
              background: resumen.generado_con_ia ? '#1e3a5f' : '#1e293b',
              color: resumen.generado_con_ia ? '#3b82f6' : '#64748b',
              fontSize: '12px', fontWeight: 600,
              padding: '4px 12px', borderRadius: '20px',
              display: 'inline-flex', alignItems: 'center', gap: '6px',
            }}>
              {resumen.generado_con_ia && (
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
              )}
              {resumen.generado_con_ia ? 'Generado con IA' : 'Sin IA'}
            </span>
            <span style={{ fontSize: '13px', color: '#64748b' }}>{resumen.periodo}</span>
          </div>

          {/* Texto */}
          <p style={{
            margin: 0, fontSize: '15px', color: '#e2e8f0',
            lineHeight: 1.8, fontStyle: 'italic',
          }}>
            "{resumen.resumen.replace(/\*\*/g, '')}"
          </p>
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: '#475569', fontSize: '14px', padding: '48px' }}>
          Seleccioná un período y hacé click en Generar resumen.
        </div>
      )}
    </Layout>
  );
}
