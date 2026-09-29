import { todayISO } from './fechas';

// Un reloj que responde como una computadora en Argentina el 30/09 a las
// 22:30: en el calendario local es 30/09, pero en UTC ya es 1/10. No depende
// del huso del contenedor donde corren las pruebas (UTC).
const las2230Del30DeSeptiembre = {
  getFullYear: () => 2026,
  getMonth: () => 8,          // septiembre (enero = 0)
  getDate: () => 30,
  toISOString: () => '2026-10-01T01:30:00.000Z',
};

test('a las 22:30 del 30/09 propone el 30/09 del calendario local, no el 1/10 de UTC', () => {
  expect(todayISO(las2230Del30DeSeptiembre)).toBe('2026-09-30');
});

test('completa con cero el mes y el día', () => {
  expect(todayISO(new Date(2026, 0, 5, 12))).toBe('2026-01-05');
});
