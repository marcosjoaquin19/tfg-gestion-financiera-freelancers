import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Ingresos from './pages/Ingresos';
import Gastos from './pages/Gastos';
import Facturas from './pages/Facturas';
import Auditoria from './pages/Auditoria';
import Proyecciones from './pages/Proyecciones';
import Clasificador from './pages/Clasificador';
import ResumenIA from './pages/ResumenIA';
import Recomendaciones from './pages/Recomendaciones';
import ImportarCSV from './pages/ImportarCSV';
import Layout from './components/Layout';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

function PlaceholderPage({ section }) {
  return (
    <Layout activeSection={section}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '200px', color: '#64748b', fontSize: '15px',
      }}>
        {section} — próximamente
      </div>
    </Layout>
  );
}

const placeholders = [
];

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/ingresos" element={<PrivateRoute><Ingresos /></PrivateRoute>} />
        <Route path="/gastos"    element={<PrivateRoute><Gastos /></PrivateRoute>} />
        <Route path="/facturas"   element={<PrivateRoute><Facturas /></PrivateRoute>} />
        <Route path="/auditoria"     element={<PrivateRoute><Auditoria /></PrivateRoute>} />
        <Route path="/proyecciones"    element={<PrivateRoute><Proyecciones /></PrivateRoute>} />
        <Route path="/clasificador"    element={<PrivateRoute><Clasificador /></PrivateRoute>} />
        <Route path="/resumen-ia"      element={<PrivateRoute><ResumenIA /></PrivateRoute>} />
        <Route path="/recomendaciones" element={<PrivateRoute><Recomendaciones /></PrivateRoute>} />
        <Route path="/importar"        element={<PrivateRoute><ImportarCSV /></PrivateRoute>} />
        {placeholders.map(({ path, section }) => (
          <Route
            key={path}
            path={path}
            element={<PrivateRoute><PlaceholderPage section={section} /></PrivateRoute>}
          />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
