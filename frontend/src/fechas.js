/**
 * Fecha de hoy para los formularios de ingresos, gastos y facturas.
 *
 * Devuelve el día calendario de la computadora del usuario como "AAAA-MM-DD",
 * el formato de un <input type="date">. No usa toISOString(): esa función da
 * el día en UTC, y en Argentina (UTC-3) desde las 21 h ya es "mañana", así que
 * los formularios proponían la fecha del día siguiente (un gasto del 30/09 a
 * la noche quedaba en octubre, y el cobro de una factura, rechazado por futuro).
 */
export function todayISO(ahora = new Date()) {
  const dos = (n) => String(n).padStart(2, '0');
  return `${ahora.getFullYear()}-${dos(ahora.getMonth() + 1)}-${dos(ahora.getDate())}`;
}
