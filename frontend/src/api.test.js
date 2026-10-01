import api from './api';

// Jest (CRA) no puede cargar axios directamente (es un módulo ES): se lo
// reemplaza por una instancia mínima que solo guarda los interceptores.
jest.mock('axios', () => {
  const respuestas = [];
  return {
    create: () => ({
      interceptors: {
        request: { use: () => {} },
        response: { use: (fulfilled, rejected) => respuestas.push({ fulfilled, rejected }), handlers: respuestas },
      },
    }),
  };
});

// El interceptor de respuestas avisa al Layout cuando el servidor no contesta
// (sin respuesta HTTP) y cuando vuelve a contestar.
const alRechazar = api.interceptors.response.handlers[0].rejected;
const alResponder = api.interceptors.response.handlers[0].fulfilled;

function escuchar(evento) {
  const recibidos = [];
  const anotar = () => recibidos.push(evento);
  window.addEventListener(evento, anotar);
  return { recibidos, dejar: () => window.removeEventListener(evento, anotar) };
}

test('sin respuesta del servidor avisa la falta de conexión', async () => {
  const caida = escuchar('api-sin-conexion');
  await expect(alRechazar({ message: 'Network Error', config: { url: '/gastos/' } })).rejects.toBeTruthy();
  expect(caida.recibidos).toHaveLength(1);
  caida.dejar();
});

test('un error con respuesta (por ejemplo, un 422) no es falta de conexión', async () => {
  const caida = escuchar('api-sin-conexion');
  const vuelta = escuchar('api-conectada');
  await expect(alRechazar({ response: { status: 422 }, config: { url: '/gastos/' } })).rejects.toBeTruthy();
  alResponder({ data: [] });
  expect(caida.recibidos).toHaveLength(0);
  expect(vuelta.recibidos).toHaveLength(2);
  caida.dejar();
  vuelta.dejar();
});
