/**
 * Componente raíz de la aplicación (frontend React).
 *
 * Define el enrutamiento (qué componente se muestra en cada URL) usando
 * react-router. Separa las rutas públicas (login, registro) de las privadas,
 * que solo son accesibles con sesión iniciada gracias al envoltorio PrivateRoute.
 * Cada ruta privada corresponde a un módulo de la app (Dashboard, Ingresos,
 * Gastos, Facturas, Auditoría, Proyecciones, Clasificador, etc.).
 *
 * Cómo leer cualquier pantalla de React de este proyecto (carpeta pages/):
 *  - Componente: cada pantalla es una función que devuelve lo que se dibuja
 *    (export default function Gastos() { ... return (<Layout>...</Layout>); }).
 *  - JSX: ese "HTML dentro de JavaScript" del return. Lo que va entre llaves
 *    {...} es código: {fmtMonto(total)} muestra el resultado de la función.
 *  - useState: la "memoria" de la pantalla. const [gastos, setGastos] =
 *    useState([]) crea el dato "gastos" (arranca vacío) y la función para
 *    cambiarlo; cada vez que se llama a setGastos, React vuelve a dibujar.
 *  - useEffect: código que corre cuando la pantalla aparece (o cuando cambia
 *    algún dato de la lista del final, como [periodo]). Se usa para pedir los
 *    datos a la API al entrar.
 *  - api.get / api.post / api.delete: los pedidos al backend (ver api.js, que
 *    les agrega el token solo). async/await = "esperá la respuesta y seguí".
 *  - Las funciones handleAlgo (handleSubmit, handleDelete...) son las que
 *    corren al tocar un botón o enviar un formulario.
 *  - Props: los datos que un componente le pasa a otro, como atributos
 *    (<Layout activeSection="Gastos">).
 */

// PATRÓN: Guard / Protected Route — PrivateRoute envuelve las rutas que exigen sesión iniciada.
// Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md
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
import Monotributo from './pages/Monotributo';
import Layout from './components/Layout';

// Guarda de rutas privadas: si hay token (sesión activa) muestra el contenido;
// si no, redirige al login. Envuelve a todas las pantallas que requieren login.
function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

// PlaceholderPage y la lista "placeholders" quedaron del armado inicial, cuando
// algunas pantallas todavía no existían ("próximamente"). Hoy la lista está
// vacía: todas las secciones del menú tienen su pantalla real.
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
      {/* Tabla de rutas: asocia cada URL con su pantalla. Las privadas van
          envueltas en PrivateRoute para exigir sesión iniciada. */}
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
        <Route path="/monotributo"     element={<PrivateRoute><Monotributo /></PrivateRoute>} />
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
