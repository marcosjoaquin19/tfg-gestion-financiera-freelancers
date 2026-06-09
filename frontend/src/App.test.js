import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

// Las llamadas reales al backend no aplican en tests de humo: se reemplaza el
// cliente axios completo para que ningún test dependa de la API levantada.
// Funciones planas (no jest.fn) porque CRA corre con resetMocks: true y
// borraría la implementación entre tests, devolviendo undefined.
jest.mock('./api', () => ({
  get: () => new Promise(() => {}),
  post: () => new Promise(() => {}),
  defaults: { headers: { common: {} } },
}));

beforeEach(() => {
  localStorage.clear();
  window.history.pushState({}, '', '/');
});

test('sin token redirige al login', () => {
  render(<App />);
  expect(screen.getByText('Ingresá a tu cuenta')).toBeInTheDocument();
});

test('el login tiene formulario completo: email, contraseña y botón Ingresar', () => {
  render(<App />);
  expect(screen.getByPlaceholderText('tu@email.com')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /ingresar/i })).toBeInTheDocument();
});

test('desde el login se puede navegar al registro', () => {
  render(<App />);
  fireEvent.click(screen.getByText('Registrate'));
  expect(screen.getByText('Creá tu cuenta')).toBeInTheDocument();
});

test('con token muestra el Dashboard con la navegación completa', () => {
  localStorage.setItem('token', 'jwt-de-prueba');
  render(<App />);
  ['Dashboard', 'Ingresos', 'Gastos', 'Facturas', 'Auditoría', 'Proyecciones',
   'Importar CSV', 'Monotributo', 'Clasificador', 'Resumen IA', 'Recomendaciones']
    .forEach((item) => expect(screen.getAllByText(item).length).toBeGreaterThan(0));
});
