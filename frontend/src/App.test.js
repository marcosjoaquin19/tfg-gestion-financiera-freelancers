import { render, screen, fireEvent, within } from '@testing-library/react';
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

test('la marca es FreelanceControl en el login', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'FreelanceControl' })).toBeInTheDocument();
});

test('las etiquetas del login están asociadas a sus campos', () => {
  render(<App />);
  expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email');
  expect(screen.getByLabelText('Contraseña')).toHaveAttribute('type', 'password');
});

test('si la sesión expiró, el login lo explica una sola vez', () => {
  sessionStorage.setItem('sesionExpirada', '1');
  const { unmount } = render(<App />);
  expect(screen.getByText('Tu sesión expiró. Ingresá de nuevo para continuar.')).toBeInTheDocument();
  expect(sessionStorage.getItem('sesionExpirada')).toBeNull();
  unmount();
  render(<App />);
  expect(screen.queryByText('Tu sesión expiró. Ingresá de nuevo para continuar.')).not.toBeInTheDocument();
});

test('el menú lateral se puede usar con teclado (son botones)', () => {
  localStorage.setItem('token', 'jwt-de-prueba');
  render(<App />);
  const menu = screen.getByRole('navigation', { name: 'Menú principal' });
  ['Dashboard', 'Ingresos', 'Monotributo', 'Recomendaciones'].forEach((item) => {
    expect(within(menu).getByRole('button', { name: item })).toBeInTheDocument();
  });
  expect(within(menu).getByRole('button', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page');
});
