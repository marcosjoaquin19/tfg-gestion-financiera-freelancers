import { render, screen, fireEvent, within, act } from '@testing-library/react';
import App from './App';
import api from './api';

// Las llamadas reales al backend no aplican en tests de humo: se reemplaza el
// cliente axios completo para que ningún test dependa de la API levantada.
// Funciones planas (no jest.fn) porque CRA corre con resetMocks: true y
// borraría la implementación entre tests, devolviendo undefined.
jest.mock('./api', () => ({
  get: () => new Promise(() => {}),
  post: () => new Promise(() => {}),
  defaults: { headers: { common: {} } },
  extraerMensajeError: (err, porDefecto) => porDefecto,
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

// Para estas pruebas la API responde: se reemplazan get/patch del cliente
// falso solo durante cada test y se restauran al final.
function conApi(respuestas, prueba) {
  const original = { get: api.get, patch: api.patch };
  Object.assign(api, respuestas);
  return Promise.resolve(prueba()).finally(() => Object.assign(api, original));
}

const FACTURA = {
  id: 7, cliente_nombre: 'Brand Studio', descripcion: 'Consultoría', monto: 980000,
  fecha_emision: '2026-09-08T00:00:00', fecha_vencimiento: '2026-10-08T00:00:00', estado: 'pendiente',
};

test('marcar pagada con doble clic manda un solo pedido', () => {
  // Regresión: "Confirmar" no se bloqueaba y salían dos PATCH; si el segundo
  // llegaba con la factura ya pagada, la API lo rechazaba y aparecía un error.
  let pedidos = 0;
  return conApi({
    get: () => Promise.resolve({ data: [FACTURA] }),
    patch: () => { pedidos += 1; return new Promise(() => {}); },
  }, async () => {
  localStorage.setItem('token', 'jwt-de-prueba');
  window.history.pushState({}, '', '/facturas');
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'Marcar pagada' }));
  const confirmar = screen.getByRole('button', { name: 'Confirmar' });
  fireEvent.click(confirmar);
  fireEvent.click(confirmar);
  expect(pedidos).toBe(1);
  expect(screen.getByRole('button', { name: 'Guardando...' })).toBeDisabled();
  });
});

test('el registro valida la contraseña corta y el largo de los campos antes de llamar a la API', () => {
  // Si llegaban a la API, la respuesta era el mensaje genérico de Pydantic, en inglés.
  window.history.pushState({}, '', '/register');
  render(<App />);
  expect(screen.getByLabelText('Nombre')).toHaveAttribute('maxLength', '100');
  expect(screen.getByLabelText('Email')).toHaveAttribute('maxLength', '150');
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Ana' } });
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'ana@test.com' } });
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'corta' } });
  fireEvent.click(screen.getByRole('button', { name: /crear cuenta/i }));
  expect(screen.getByRole('alert')).toHaveTextContent('La contraseña debe tener al menos 8 caracteres');
});

test('el clasificador informa la exactitud, como la tesis (no "precisión")', () => conApi({
  get: () => Promise.resolve({ data: { tiene_modelo_propio: false, algoritmo: 'svm', precision: 0.76,
                                       n_ejemplos: 600, fecha_entrenamiento: '2026-04-19T00:00:00' } }),
}, async () => {
  localStorage.setItem('token', 'jwt-de-prueba');
  window.history.pushState({}, '', '/clasificador');
  render(<App />);
  expect(await screen.findByText(/Exactitud:/)).toHaveTextContent('Exactitud: 76%');
  expect(screen.queryByText(/Precisión:/)).not.toBeInTheDocument();
}));

test('si la API no responde, Monotributo no pide configurar la categoría y se avisa la falta de conexión', () => conApi({
  get: () => Promise.reject(Object.assign(new Error('Network Error'), { message: 'Network Error' })),
}, async () => {
  // Regresión: con la API caída se mostraba "Configurá tu categoría de
  // monotributo", como si el usuario no la tuviera cargada.
  localStorage.setItem('token', 'jwt-de-prueba');
  window.history.pushState({}, '', '/monotributo');
  render(<App />);
  expect(await screen.findByText('No se pudo cargar el estado del monotributo')).toBeInTheDocument();
  expect(screen.queryByText('Configurá tu categoría de monotributo')).not.toBeInTheDocument();
  act(() => { window.dispatchEvent(new Event('api-sin-conexion')); });
  expect(screen.getByRole('alert')).toHaveTextContent('No se pudo conectar con el servidor.');
  act(() => { window.dispatchEvent(new Event('api-conectada')); });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
}));
