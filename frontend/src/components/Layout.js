/**
 * Layout — estructura común de las pantallas privadas.
 *
 * Renderiza la barra lateral de navegación (sidebar) con los accesos a cada
 * módulo y envuelve el contenido de cada página. Recibe `activeSection` para
 * resaltar el ítem activo y muestra el contenido (children) a su derecha.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Definición del menú lateral: secciones y sus accesos a cada módulo de la app.
const SIDEBAR_SECTIONS = [
  {
    title: 'GENERAL',
    items: [
      { label: 'Dashboard',     route: '/' },
      { label: 'Ingresos',      route: '/ingresos' },
      { label: 'Gastos',        route: '/gastos' },
      { label: 'Facturas',      route: '/facturas' },
      { label: 'Auditoría',     route: '/auditoria' },
      { label: 'Proyecciones',  route: '/proyecciones' },
      { label: 'Importar CSV',  route: '/importar' },
      { label: 'Monotributo',   route: '/monotributo' },
    ],
  },
  {
    title: 'INTELIGENCIA IA',
    items: [
      { label: 'Clasificador',    route: '/clasificador' },
      { label: 'Estado ML',       route: '/clasificador' },
      { label: 'Resumen IA',      route: '/resumen-ia' },
      { label: 'Recomendaciones', route: '/recomendaciones' },
    ],
  },
];

function SidebarItem({ label, active, onClick }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: '8px 16px',
        fontSize: '13px',
        cursor: 'pointer',
        borderLeft: active ? '2px solid #3b82f6' : '2px solid transparent',
        color: active ? '#93c5fd' : hover ? '#e2e8f0' : '#64748b',
        background: active ? '#0f1e35' : hover ? '#1e293b' : 'transparent',
        transition: 'all 0.1s',
        userSelect: 'none',
      }}
    >
      {label}
    </div>
  );
}

export default function Layout({ children, activeSection }) {
  const navigate = useNavigate();
  const userEmail = localStorage.getItem('userEmail') || 'Usuario';

  function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    navigate('/login');
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0f1117', overflow: 'hidden' }}>

      {/* Topbar */}
      <div style={{
        height: '48px', minHeight: '48px',
        background: '#161b27', borderBottom: '1px solid #1e293b',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }} />
          <p style={{ margin: 0, fontSize: '15px', fontWeight: 500, color: '#f8fafc' }}>
            Gestión Financiera
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>{userEmail}</span>
          <button
            onClick={handleLogout}
            style={{
              background: 'transparent', border: '1px solid #1e293b',
              color: '#64748b', borderRadius: '6px', padding: '4px 12px',
              fontSize: '12px', cursor: 'pointer',
            }}
          >
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Sidebar */}
        <div style={{
          width: '200px', minWidth: '200px',
          background: '#161b27', borderRight: '1px solid #1e293b',
          overflowY: 'auto', padding: '16px 0',
        }}>
          {SIDEBAR_SECTIONS.map((section) => (
            <div key={section.title}>
              <div style={{
                fontSize: '11px', color: '#475569', fontWeight: 600,
                letterSpacing: '0.05em', padding: '8px 16px 4px',
                textTransform: 'uppercase',
              }}>
                {section.title}
              </div>
              {section.items.map(({ label, route }) => (
                <SidebarItem
                  key={label}
                  label={label}
                  active={activeSection === label}
                  onClick={() => navigate(route)}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Main */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
