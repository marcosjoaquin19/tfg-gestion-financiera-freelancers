// =============================================================================
// Slides de la defensa oral — FreelanceControl (35 min + 10 de preguntas)
//
// Acompañan bloque por bloque a 01_GUION_DEFENSA_35MIN.md. Si se cambia el
// guion, se cambia acá: la numeración de los bloques es la misma.
//
// Reproducible:  node defensa_final/gen_slides_defensa.js
// Requiere:      npm i -g pptxgenjs
// Salida:        defensa_final/slides/FreelanceControl_Defensa_Final.pptx
//
// Todos los datos numéricos salen de la tesis aprobada (defensa_final/tesis/)
// o de una medición sobre el código. No hay cifras estimadas.
// =============================================================================

const PptxGenJS = require("/opt/homebrew/lib/node_modules/pptxgenjs");
const pptx = new PptxGenJS();
pptx.defineLayout({ name: "W", width: 13.33, height: 7.5 });
pptx.layout = "W";
pptx.author = "Marcos Gamaliel Joaquín";
pptx.title = "FreelanceControl — Defensa oral";
pptx.subject = "Trabajo Final de Grado — Ingeniería de Software — Universidad Siglo 21";

// ── Paleta (heredada del deck anterior, para mantener identidad visual) ──────
const NAVY = "0D2B45", NAVY2 = "14395E", TEAL = "1C7293", TEAL_L = "5BB3C4";
const MINT = "02C39A", ICE = "CADCFC", WHITE = "FFFFFF", GREY = "8FA3B5";
const VERDE = "2E9E5B", AMARILLO = "E0A82E", ROJO = "D14D4D";
const CREAM = "F4F7FB", INK = "16222E", TEXTO = "4A5A68", BORDE = "DCE4EC";
const DOCS = "/Users/marcosjoaquin/proyecto-tfg/docs";
const FH = "Georgia", FB = "Calibri", FM = "Consolas";

let n = 0;

// ── Helpers ─────────────────────────────────────────────────────────────────
const bgDark  = s => { s.background = { color: NAVY  }; };
const bgLight = s => { s.background = { color: CREAM }; };

function kicker(s, txt, color) {
  s.addText(txt.toUpperCase(), { x:0.7, y:0.55, w:11.9, h:0.35, fontFace:FB,
    fontSize:13, color: color || MINT, bold:true, charSpacing:3 });
}
function title(s, txt, color, size) {
  s.addText(txt, { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH,
    fontSize: size || 32, bold:true, color: color || INK });
}
function footer(s) {
  s.addText("FreelanceControl · Defensa TFG · M. G. Joaquín", { x:0.7, y:7.08, w:7, h:0.3,
    fontFace:FB, fontSize:9, color:GREY });
  s.addText(String(n), { x:12.4, y:7.08, w:0.5, h:0.3, fontFace:FB, fontSize:9,
    color:GREY, align:"right" });
}
/** Marca de bloque del guion, arriba a la derecha: te ubica en el reloj. */
function bloque(s, txt, dark) {
  s.addText(txt, { x:9.4, y:0.55, w:3.2, h:0.35, fontFace:FB, fontSize:10.5,
    color: dark ? TEAL_L : GREY, align:"right", italic:true });
}
function slide(dark) {
  n++;
  const s = pptx.addSlide();
  dark ? bgDark(s) : bgLight(s);
  return s;
}
/** Tarjeta blanca sobre fondo claro. */
function card(s, x, y, w, h, acento) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, fill:{color:WHITE},
    line:{color:BORDE, width:1}, rectRadius:0.08,
    shadow:{type:"outer", color:"AAB7C4", blur:6, offset:2, angle:90, opacity:0.28} });
  if (acento) s.addShape(pptx.ShapeType.roundRect, { x, y, w:0.15, h, fill:{color:acento}, rectRadius:0.04 });
}
/** Bloque de código monoespaciado sobre fondo oscuro. */
function codigo(s, x, y, w, h, ruta, lineas) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, fill:{color:"0B1B2B"},
    line:{color:NAVY2, width:1}, rectRadius:0.08 });
  s.addText(ruta, { x:x+0.28, y:y+0.16, w:w-0.5, h:0.3, fontFace:FM, fontSize:10.5, color:TEAL_L });
  s.addText(lineas.join("\n"), { x:x+0.28, y:y+0.55, w:w-0.5, h:h-0.75,
    fontFace:FM, fontSize:12.5, color:ICE, lineSpacingMultiple:1.25 });
}

// =============================================================================
// BLOQUE 1 · APERTURA: EL PROBLEMA          (guion 0:00 – 3:00)
// =============================================================================

// ── 1 · Portada ─────────────────────────────────────────────────────────────
let s = slide(true);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:7.5, fill:{color:MINT} });
s.addText("TRABAJO FINAL DE GRADO · INGENIERÍA DE SOFTWARE · UNIVERSIDAD SIGLO 21", {
  x:0.9, y:1.55, w:11.9, h:0.4, fontFace:FB, fontSize:12.5, color:TEAL_L, bold:true, charSpacing:2 });
s.addText("FreelanceControl", { x:0.85, y:2.05, w:11.7, h:1.3, fontFace:FH, fontSize:58, bold:true, color:WHITE });
s.addText("Sistema de gestión financiera para monotributistas argentinos", {
  x:0.9, y:3.45, w:11.0, h:0.6, fontFace:FB, fontSize:20, color:ICE });
s.addText("Modalidad: prototipado tecnológico", {
  x:0.9, y:4.05, w:11.0, h:0.4, fontFace:FB, fontSize:14, italic:true, color:GREY });

const chips = ["Clasificación NLP local", "Predicción Prophet", "Estado fiscal", "Auditoría automatizada"];
let cx = 0.9;
chips.forEach(c => {
  const w = 0.45 + c.length * 0.108;
  s.addShape(pptx.ShapeType.roundRect, { x:cx, y:4.75, w, h:0.5, fill:{color:NAVY2},
    line:{color:TEAL, width:1}, rectRadius:0.1 });
  s.addText(c, { x:cx, y:4.75, w, h:0.5, fontFace:FB, fontSize:12.5, color:ICE, align:"center", valign:"middle" });
  cx += w + 0.25;
});
s.addText("Marcos Gamaliel Joaquín  ·  Legajo SOF02218", {
  x:0.9, y:6.25, w:7, h:0.4, fontFace:FB, fontSize:15, color:WHITE });
s.addText("Profesor TFG: Alejandro Mainero  ·  Córdoba, Argentina", {
  x:0.9, y:6.65, w:7, h:0.35, fontFace:FB, fontSize:12.5, color:GREY });

// ── 2 · El tamaño del problema ──────────────────────────────────────────────
s = slide(false);
kicker(s, "El punto de partida", TEAL);
bloque(s, "Bloque 1 · 0:00");
title(s, "Un segmento grande, y creciendo");
const cifras = [
  ["24,5 %", "del empleo total en Argentina es trabajo por cuenta propia", "INDEC · EPH 3.er trim. 2025", TEAL],
  ["3,3 M", "de personas trabajan por cuenta propia", "+42,2 % respecto de 2016", MINT],
  ["+35 %", "crecieron los inscriptos al régimen simplificado", "Secretaría de Trabajo, 2026", AMARILLO],
];
cifras.forEach((c, i) => {
  const x = 0.7 + i * 4.05;
  card(s, x, 2.3, 3.8, 3.3);
  s.addText(c[0], { x:x+0.35, y:2.6, w:3.1, h:1.0, fontFace:FH, fontSize:46, bold:true, color:c[3] });
  s.addText(c[1], { x:x+0.35, y:3.7, w:3.15, h:1.1, fontFace:FB, fontSize:15, color:INK });
  s.addText(c[2], { x:x+0.35, y:4.95, w:3.15, h:0.5, fontFace:FB, fontSize:11, italic:true, color:GREY });
});
s.addText("Ese universo es el que enfrenta las cuatro problemáticas relevadas.", {
  x:0.7, y:6.1, w:11.9, h:0.5, fontFace:FB, fontSize:15, italic:true, color:TEAL, align:"center" });
footer(s);

// ── 3 · Las cuatro problemáticas ────────────────────────────────────────────
s = slide(false);
kicker(s, "Diagnóstico", TEAL);
bloque(s, "Bloque 1 · 1:00");
title(s, "Cuatro problemáticas concretas");
const probs = [
  ["Flujo de caja variable",
   "Los ingresos dependen de cuándo termina un entregable y cuándo paga cada cliente. Las herramientas registran, pero no proyectan."],
  ["Control de la categoría fiscal",
   "Superar el límite anual fuerza la recategorización o la exclusión del régimen. Monitorearlo a mano es propenso a omisiones."],
  ["Ausencia de auditoría",
   "Duplicados, facturas vencidas y cuotas impagas dependen del cruce manual, que se posterga hasta el cierre fiscal anual."],
  ["Fragmentación documental",
   "Planillas, apps móviles, correos con comprobantes, PDF de facturas y exportaciones CSV del homebanking. Nada consolidado."],
];
probs.forEach((p, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.7 + col * 6.1, y = 2.2 + row * 2.35;
  card(s, x, y, 5.75, 2.05);
  s.addShape(pptx.ShapeType.roundRect, { x:x+0.3, y:y+0.32, w:0.55, h:0.55, fill:{color:TEAL}, rectRadius:0.27 });
  s.addText(String(i + 1), { x:x+0.3, y:y+0.32, w:0.55, h:0.55, fontFace:FH, fontSize:22,
    bold:true, color:WHITE, align:"center", valign:"middle" });
  s.addText(p[0], { x:x+1.05, y:y+0.3, w:4.5, h:0.55, fontFace:FH, fontSize:17, bold:true, color:INK, valign:"middle" });
  s.addText(p[1], { x:x+0.32, y:y+1.0, w:5.2, h:0.95, fontFace:FB, fontSize:12.5, color:TEXTO });
});
footer(s);

// ── 4 · El mercado no lo resuelve ───────────────────────────────────────────
s = slide(true);
kicker(s, "Relevamiento de la competencia", MINT);
bloque(s, "Bloque 1 · 2:00", true);
title(s, "Ninguna solución del mercado cubre el núcleo", WHITE);
s.addText("Contabilium · Xubio · Colppy · QuickBooks · FreshBooks", {
  x:0.7, y:2.05, w:11.9, h:0.45, fontFace:FB, fontSize:16, color:ICE });
s.addText("Todas están diseñadas para pymes con estructura administrativa formal, no para operadores individuales bajo regímenes simplificados.", {
  x:0.7, y:2.5, w:11.9, h:0.6, fontFace:FB, fontSize:14, color:GREY });
const faltan = [
  ["Clasificación automática de gastos", "Ninguna"],
  ["Predicción de ingresos", "Ninguna"],
  ["Auditoría automatizada de registros", "Ninguna"],
];
faltan.forEach((f, i) => {
  const x = 0.7 + i * 4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:3.35, w:3.8, h:1.65, fill:{color:NAVY2},
    line:{color:ROJO, width:1.5}, rectRadius:0.1 });
  s.addText(f[0], { x:x+0.3, y:3.6, w:3.2, h:0.85, fontFace:FB, fontSize:14.5, color:ICE });
  s.addText("✕  " + f[1], { x:x+0.3, y:4.45, w:3.2, h:0.4, fontFace:FH, fontSize:17, bold:true, color:ROJO });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.4, w:11.9, h:1.15, fill:{color:MINT}, rectRadius:0.12 });
s.addText("¿Puede un software ANTICIPAR ese riesgo, en lugar de solamente registrarlo?", {
  x:0.9, y:5.4, w:11.5, h:1.15, fontFace:FH, fontSize:23, bold:true, color:NAVY, valign:"middle" });
footer(s);

// =============================================================================
// BLOQUE 2 · LA PROPUESTA Y SUS LÍMITES     (guion 3:00 – 6:00)
// =============================================================================

// ── 5 · Objetivo general ────────────────────────────────────────────────────
s = slide(false);
kicker(s, "Objetivo general", TEAL);
bloque(s, "Bloque 2 · 3:00");
title(s, "Qué se propuso este trabajo");
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.15, w:11.9, h:1.5, fill:{color:WHITE},
  line:{color:TEAL, width:2}, rectRadius:0.1 });
s.addText("Desarrollar un sistema web de gestión financiera para monotributistas argentinos que integre un clasificador de gastos por procesamiento de lenguaje natural entrenado localmente, un motor de predicción de ingresos, un módulo fiscal de monitoreo de la categoría de Monotributo y un componente de auditoría automatizada de los registros financieros.", {
  x:1.0, y:2.15, w:11.3, h:1.5, fontFace:FB, fontSize:15.5, color:INK, valign:"middle", italic:true });
const cuatro = [
  ["Clasificar", "Gastos por PLN local,\nreentrenable con\ncorrecciones", MINT],
  ["Predecir", "Ingresos a 6 meses\ncon intervalos de\nconfianza", TEAL_L],
  ["Controlar", "Estado fiscal de la\ncategoría de\nMonotributo", AMARILLO],
  ["Auditar", "Inconsistencias en\nlos registros\nfinancieros", ROJO],
];
cuatro.forEach((c, i) => {
  const x = 0.7 + i * 3.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:4.05, w:2.8, h:2.4, fill:{color:NAVY}, rectRadius:0.1 });
  s.addText(c[0], { x:x+0.25, y:4.3, w:2.3, h:0.6, fontFace:FH, fontSize:22, bold:true, color:c[2] });
  s.addText(c[1], { x:x+0.25, y:5.0, w:2.4, h:1.3, fontFace:FB, fontSize:13, color:ICE });
});
footer(s);

// ── 6 · Objetivos específicos y su cumplimiento ─────────────────────────────
s = slide(false);
kicker(s, "Objetivos específicos", TEAL);
bloque(s, "Bloque 2 · 3:45");
title(s, "Cuatro objetivos, cuatro cumplidos");
const objs = [
  ["Módulo de gestión transaccional", "Ingresos, gastos y facturas con aislamiento por usuario, más importación masiva CSV y Excel.", "Cumplido"],
  ["Clasificador por PLN", "Entrenado localmente, reentrenable con las correcciones del usuario.", "76 % · meta 70 %"],
  ["Módulo fiscal y de auditoría", "Utilización del límite anual, duplicados y anomalías estadísticas.", "Cumplido"],
  ["Pipeline predictivo y reportería", "Proyección a 6 meses con intervalos de confianza y reporte PDF descargable.", "Cumplido"],
];
objs.forEach((o, i) => {
  const y = 2.15 + i * 1.12;
  const destacado = i === 1;
  card(s, 0.7, y, 11.9, 0.95, destacado ? MINT : TEAL);
  s.addText(o[0], { x:1.05, y:y+0.13, w:4.6, h:0.4, fontFace:FH, fontSize:15.5, bold:true, color:INK });
  s.addText(o[1], { x:1.05, y:y+0.53, w:7.6, h:0.4, fontFace:FB, fontSize:12.5, color:TEXTO });
  s.addShape(pptx.ShapeType.roundRect, { x:10.3, y:y+0.26, w:2.0, h:0.48,
    fill:{color: destacado ? MINT : VERDE}, rectRadius:0.1 });
  s.addText(o[2], { x:10.3, y:y+0.26, w:2.0, h:0.48, fontFace:FB, fontSize:12.5, bold:true,
    color: destacado ? NAVY : WHITE, align:"center", valign:"middle" });
});
s.addText("El único objetivo con meta numérica era el del clasificador. Se midió por validación cruzada de 5 particiones.", {
  x:0.7, y:6.6, w:11.9, h:0.4, fontFace:FB, fontSize:12, italic:true, color:GREY, align:"center" });
footer(s);

// ── 7 · ⭐ ALCANCE: lo que hace y lo que NO hace ─────────────────────────────
s = slide(true);
kicker(s, "Alcance y responsabilidad", AMARILLO);
bloque(s, "Bloque 2 · 4:30", true);
title(s, "Lo que el sistema hace — y lo que no", WHITE, 33);

s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.0, w:5.85, h:3.5, fill:{color:NAVY2},
  line:{color:MINT, width:2}, rectRadius:0.1 });
s.addText("HACE", { x:1.0, y:2.2, w:5.2, h:0.5, fontFace:FH, fontSize:24, bold:true, color:MINT });
[["Informa", "Consolida y muestra lo que el usuario cargó"],
 ["Proyecta", "Estima escenarios futuros con su intervalo"],
 ["Alerta", "Señala desvíos y riesgos para su revisión"]].forEach((h, i) => {
  const y = 2.85 + i * 0.85;
  s.addText(h[0], { x:1.0, y, w:1.8, h:0.4, fontFace:FH, fontSize:17, bold:true, color:WHITE });
  s.addText(h[1], { x:2.65, y:y+0.03, w:3.6, h:0.65, fontFace:FB, fontSize:12.5, color:ICE });
});

s.addShape(pptx.ShapeType.roundRect, { x:6.75, y:2.0, w:5.85, h:3.5, fill:{color:NAVY2},
  line:{color:ROJO, width:2}, rectRadius:0.1 });
s.addText("NO HACE", { x:7.05, y:2.2, w:5.2, h:0.5, fontFace:FH, fontSize:24, bold:true, color:ROJO });
[["No asesora", "No dice qué decisión tomar"],
 ["No dictamina", "Señala un posible error, no lo determina"],
 ["No garantiza", "Una proyección no es una certeza"]].forEach((h, i) => {
  const y = 2.85 + i * 0.85;
  s.addText(h[0], { x:7.05, y, w:2.1, h:0.4, fontFace:FH, fontSize:17, bold:true, color:WHITE });
  s.addText(h[1], { x:9.0, y:y+0.03, w:3.35, h:0.65, fontFace:FB, fontSize:12.5, color:ICE });
});

s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.75, w:11.9, h:1.05, fill:{color:AMARILLO}, rectRadius:0.1 });
s.addText("No constituye asesoramiento contable, fiscal ni financiero, y no reemplaza la intervención de un profesional matriculado.", {
  x:1.0, y:5.75, w:11.3, h:1.05, fontFace:FH, fontSize:17, bold:true, color:NAVY, valign:"middle" });
footer(s);

// ── 8 · El descargo está en el producto ─────────────────────────────────────
s = slide(false);
kicker(s, "Alcance implementado", TEAL);
bloque(s, "Bloque 2 · 5:00");
title(s, "No es una nota al pie: está en el producto");
const avisos = [
  ["Monotributo", "La categorización definitiva la determina ARCA"],
  ["Proyecciones", "Son estimaciones estadísticas, no una garantía de ingresos"],
  ["Recomendaciones", "Reglas sobre sus propios datos, de carácter orientativo"],
  ["Resumen IA", "Redactado por un modelo de lenguaje: verificar las cifras"],
  ["Auditoría", "Señala posibles inconsistencias, no dictamina un error"],
  ["Reporte PDF", "Además: verificar contra la documentación respaldatoria"],
];
avisos.forEach((a, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.7 + col * 6.1, y = 2.2 + row * 1.35;
  const esPdf = i === 5;
  card(s, x, y, 5.75, 1.1, esPdf ? AMARILLO : TEAL);
  s.addText(a[0], { x:x+0.4, y:y+0.12, w:5.1, h:0.42, fontFace:FH, fontSize:15.5, bold:true,
    color: esPdf ? "8A6410" : INK });
  s.addText(a[1], { x:x+0.4, y:y+0.55, w:5.1, h:0.45, fontFace:FB, fontSize:12, color:TEXTO });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:6.22, w:11.9, h:0.72, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("El reporte PDF es el único artefacto que sale de la aplicación y circula fuera de ella: tiene que llevar el límite consigo.", {
  x:1.0, y:6.22, w:11.3, h:0.72, fontFace:FB, fontSize:13.5, italic:true, color:ICE, valign:"middle" });
footer(s);

// ── 9 · Límites del prototipo ───────────────────────────────────────────────
s = slide(false);
kicker(s, "Límites del prototipo", TEAL);
bloque(s, "Bloque 2 · 5:30");
title(s, "Qué quedó deliberadamente fuera");
const fuera = [
  ["Facturación electrónica", "Integración con el sistema del organismo recaudador"],
  ["Conciliación bancaria", "Cruce automatizado contra cuentas reales del usuario"],
  ["Gestión de clientes", "Como entidad independiente de las facturas emitidas"],
  ["Venta de productos", "El prototipo se orienta a la prestación de servicios"],
];
fuera.forEach((f, i) => {
  const x = 0.7 + i * 3.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.3, w:2.8, h:2.5, fill:{color:WHITE},
    line:{color:BORDE, width:1, dashType:"dash"}, rectRadius:0.08 });
  s.addText("✕", { x:x+0.25, y:2.55, w:0.6, h:0.5, fontFace:FB, fontSize:22, bold:true, color:"C3CEDA" });
  s.addText(f[0], { x:x+0.25, y:3.1, w:2.35, h:0.75, fontFace:FH, fontSize:15.5, bold:true, color:INK });
  s.addText(f[1], { x:x+0.25, y:3.85, w:2.4, h:0.85, fontFace:FB, fontSize:12, color:TEXTO });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.3, w:11.9, h:1.5, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("CÓMO SE CONSTRUYÓ", { x:1.0, y:5.5, w:4, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:MINT, charSpacing:2 });
[["17", "historias de usuario"], ["17", "ítems de backlog"], ["8", "sprints"], ["4", "meses"], ["Scrum", "marco de trabajo"]]
  .forEach((m, i) => {
    const x = 1.0 + i * 2.35;
    s.addText(m[0], { x, y:5.85, w:2.2, h:0.5, fontFace:FH, fontSize:26, bold:true, color:WHITE });
    s.addText(m[1], { x, y:6.32, w:2.2, h:0.35, fontFace:FB, fontSize:11.5, color:GREY });
  });
footer(s);

// =============================================================================
// BLOQUE 3 · VIDEO                           (guion 6:00 – 10:00)
// =============================================================================

// ── 10 · Transición al video ────────────────────────────────────────────────
s = slide(true);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:7.5, fill:{color:MINT} });
bloque(s, "Bloque 3 · 6:00", true);
s.addText("VIDEO EXPLICATIVO", { x:0.9, y:2.6, w:11.9, h:0.5, fontFace:FB, fontSize:14,
  bold:true, color:MINT, charSpacing:3 });
s.addText("El sistema, de principio a fin", { x:0.85, y:3.15, w:11.7, h:1.1,
  fontFace:FH, fontSize:44, bold:true, color:WHITE });
s.addText("Recorrido del ciclo completo de uso, en el mismo orden en que fueron diagnosticados los problemas.", {
  x:0.9, y:4.3, w:10.5, h:0.6, fontFace:FB, fontSize:17, color:ICE });
s.addText("▶   4 minutos", { x:0.9, y:5.2, w:5, h:0.6, fontFace:FH, fontSize:22, bold:true, color:MINT });
footer(s);

// =============================================================================
// BLOQUE 4 · DEMO EN VIVO                    (guion 10:00 – 24:00)
// =============================================================================

// ── 11 · Guion de la demo ───────────────────────────────────────────────────
s = slide(true);
kicker(s, "Demostración en vivo", MINT);
bloque(s, "Bloque 4 · 10:00", true);
title(s, "El recorrido", WHITE);
const demo = [
  ["1", "Clasificador de gastos", "Sugerencia automática, umbral de confianza y aprendizaje por corrección", MINT],
  ["2", "Importación bancaria", "Nueve formatos de homebanking, detección heurística local", TEAL_L],
  ["3", "Auditoría automatizada", "Cinco detectores sobre los registros del usuario", TEAL_L],
  ["4", "Estado fiscal", "Facturación móvil de 12 meses contra el límite de la categoría", AMARILLO],
  ["5", "Proyección de ingresos", "Seis meses con intervalo de confianza y arranque en frío", TEAL_L],
  ["6", "Reporte PDF", "Documento mensual consolidado para el contador", MINT],
];
demo.forEach((d, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.7 + col * 6.1, y = 2.15 + row * 1.5;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.75, h:1.25, fill:{color:NAVY2},
    line:{color:d[3], width:1}, rectRadius:0.08 });
  s.addShape(pptx.ShapeType.roundRect, { x:x+0.28, y:y+0.33, w:0.6, h:0.6, fill:{color:d[3]}, rectRadius:0.3 });
  s.addText(d[0], { x:x+0.28, y:y+0.33, w:0.6, h:0.6, fontFace:FH, fontSize:20, bold:true,
    color:NAVY, align:"center", valign:"middle" });
  s.addText(d[1], { x:x+1.05, y:y+0.2, w:4.5, h:0.45, fontFace:FH, fontSize:15.5, bold:true, color:WHITE });
  s.addText(d[2], { x:x+1.05, y:y+0.65, w:4.5, h:0.5, fontFace:FB, fontSize:11.5, color:ICE });
});
s.addText("Cada módulo responde a una de las cuatro problemáticas del diagnóstico.", {
  x:0.7, y:6.72, w:11.9, h:0.4, fontFace:FB, fontSize:13, italic:true, color:GREY, align:"center" });
footer(s);

// =============================================================================
// BLOQUE 5 · CÓDIGO Y DECISIONES             (guion 24:00 – 33:00)
// =============================================================================

// ── 12 · Transición: qué → cómo → por qué ───────────────────────────────────
s = slide(true);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:7.5, fill:{color:TEAL} });
bloque(s, "Bloque 5 · 24:00", true);
s.addText("ARQUITECTURA Y DECISIONES DE DISEÑO", { x:0.9, y:2.5, w:11.9, h:0.5,
  fontFace:FB, fontSize:14, bold:true, color:TEAL_L, charSpacing:3 });
s.addText("Del qué al porqué", { x:0.85, y:3.05, w:11.7, h:1.1, fontFace:FH, fontSize:44, bold:true, color:WHITE });
[["QUÉ", "hace el sistema", GREY, true],
 ["CÓMO", "está construido", WHITE, false],
 ["POR QUÉ", "está construido así", MINT, false]].forEach((t, i) => {
  const x = 0.9 + i * 4.0;
  s.addText(t[0], { x, y:4.5, w:3.6, h:0.6, fontFace:FH, fontSize:28, bold:true, color:t[2] });
  s.addText(t[1], { x, y:5.1, w:3.6, h:0.4, fontFace:FB, fontSize:14, color: t[3] ? GREY : ICE });
  if (t[3]) s.addText("✓  ya visto", { x, y:5.55, w:3.6, h:0.35, fontFace:FB, fontSize:11.5, italic:true, color:GREY });
});
footer(s);

// ── 13 · Arquitectura: tres contenedores ────────────────────────────────────
s = slide(false);
kicker(s, "Arquitectura", TEAL);
bloque(s, "Bloque 5 · 24:00");
title(s, "Tres contenedores, una red interna");
const capas = [
  ["Frontend", "React 19 · React Router · Axios · Chart.js · 13 pantallas", "Puerto 3000", TEAL],
  ["Backend API", "FastAPI 0.111 · Python 3.11 · ASGI · JWT · Pydantic", "Puerto 8000", MINT],
  ["Base de datos", "PostgreSQL 15 · SQLAlchemy 2.0 · Alembic · 9 tablas", "Puerto 5432", NAVY2],
];
capas.forEach((c, i) => {
  const y = 2.25 + i * 1.35;
  card(s, 0.7, y, 8.3, 1.15, c[3]);
  s.addText(c[0], { x:1.05, y:y+0.16, w:3.2, h:0.5, fontFace:FH, fontSize:19, bold:true, color:INK });
  s.addText(c[1], { x:1.05, y:y+0.63, w:6.2, h:0.4, fontFace:FB, fontSize:12.5, color:TEXTO });
  s.addShape(pptx.ShapeType.roundRect, { x:7.4, y:y+0.35, w:1.45, h:0.45, fill:{color:c[3]}, rectRadius:0.1 });
  s.addText(c[2], { x:7.4, y:y+0.35, w:1.45, h:0.45, fontFace:FB, fontSize:11, color:WHITE,
    align:"center", valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:9.35, y:2.25, w:3.25, h:4.05, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("STACK CLAVE", { x:9.6, y:2.47, w:2.8, h:0.4, fontFace:FB, fontSize:12, bold:true, color:MINT, charSpacing:2 });
["scikit-learn — TF-IDF + SVM", "Prophet — series temporales", "ReportLab — PDF programático",
 "Groq — solo datos agregados", "Docker Compose", "pytest — 115 pruebas"].forEach((t, i) => {
  s.addText("›", { x:9.6, y:3.0 + i * 0.52, w:0.3, h:0.4, fontFace:FB, fontSize:15, color:MINT, bold:true });
  s.addText(t, { x:9.9, y:3.0 + i * 0.52, w:2.6, h:0.45, fontFace:FB, fontSize:11.5, color:ICE, valign:"middle" });
});
s.addText("Orquestados con Docker Compose. Todo el stack es software de código abierto: costo de licencias nulo.", {
  x:0.7, y:6.5, w:11.9, h:0.45, fontFace:FB, fontSize:12.5, italic:true, color:TEAL, align:"center" });
footer(s);

// ── 14 · Las cuatro capas del backend ───────────────────────────────────────
s = slide(true);
kicker(s, "Arquitectura en capas", MINT);
bloque(s, "Bloque 5 · 25:00", true);
title(s, "Un router no calcula nada", WHITE);
const back = [
  ["routers/", "12 archivos", "HTTP: rutas, códigos de estado y permisos", TEAL_L],
  ["schemas/", "6 archivos", "DTO: validación de entrada y salida con Pydantic", TEAL_L],
  ["services/", "9 archivos", "LÓGICA DE NEGOCIO — el corazón del trabajo", MINT],
  ["models/", "9 archivos", "ORM: mapeo objeto-relacional con SQLAlchemy", TEAL_L],
];
back.forEach((b, i) => {
  const y = 2.1 + i * 1.02;
  const destacado = i === 2;
  s.addShape(pptx.ShapeType.roundRect, { x:0.7, y, w:7.9, h:0.85,
    fill:{color: destacado ? MINT : NAVY2}, rectRadius:0.08 });
  s.addText(b[0], { x:1.0, y, w:1.7, h:0.85, fontFace:FM, fontSize:16, bold:true,
    color: destacado ? NAVY : WHITE, valign:"middle" });
  s.addText(b[1], { x:2.65, y, w:1.3, h:0.85, fontFace:FB, fontSize:11.5,
    color: destacado ? NAVY2 : GREY, valign:"middle" });
  s.addText(b[2], { x:4.0, y, w:4.4, h:0.85, fontFace:FB, fontSize:12.5,
    color: destacado ? NAVY : ICE, valign:"middle" });
  if (i < 3) s.addText("↓", { x:4.4, y:y+0.83, w:0.4, h:0.2, fontFace:FB, fontSize:13, color:GREY, align:"center" });
});
s.addShape(pptx.ShapeType.roundRect, { x:8.85, y:2.1, w:3.75, h:3.9, fill:{color:NAVY2},
  line:{color:TEAL, width:1}, rectRadius:0.1 });
s.addText("QUÉ ME DIO", { x:9.15, y:2.32, w:3.2, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:MINT, charSpacing:2 });
[["Testeabilidad", "115 pruebas contra SQLite en memoria, sin levantar HTTP. 35 segundos."],
 ["Reutilización", "La regla de la cuota la usan el módulo fiscal y la auditoría."],
 ["Un solo lugar", "El formato de moneda lo comparten las alertas y el PDF."]].forEach((v, i) => {
  const y = 2.8 + i * 1.05;
  s.addText(v[0], { x:9.15, y, w:3.2, h:0.35, fontFace:FH, fontSize:14.5, bold:true, color:WHITE });
  s.addText(v[1], { x:9.15, y:y+0.34, w:3.2, h:0.65, fontFace:FB, fontSize:11, color:ICE });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:6.2, w:11.9, h:0.85, fill:{color:NAVY2},
  line:{color:ROJO, width:1}, rectRadius:0.08 });
s.addText("Alternativa descartada:  un monolito con la lógica en las vistas. El núcleo del trabajo es la lógica financiera y de ML: necesitaba estar aislada y probada, no acoplada al ciclo de un request HTTP.", {
  x:1.0, y:6.2, w:11.3, h:0.85, fontFace:FB, fontSize:12.5, color:ICE, valign:"middle" });
footer(s);

// ── 15 · Mapa de módulos ────────────────────────────────────────────────────
s = slide(false);
kicker(s, "Mapa de módulos", TEAL);
bloque(s, "Bloque 5 · 26:00");
title(s, "Dónde se maneja cada cosa");
const filas = [
  ["Registro y login",            "auth",            "auth",                 "usuario"],
  ["Ingresos",                    "ingresos",        "—",                    "ingreso"],
  ["Gastos + clasificación",      "gastos",          "ia → ml_service",      "gasto"],
  ["Facturas",                    "facturas",        "—",                    "factura"],
  ["Auditoría",                   "alertas",         "auditoria",            "alerta_auditoria"],
  ["Proyecciones",                "proyecciones",    "prophet_service",      "proyeccion"],
  ["Importación CSV / Excel",     "importar",        "csv_service",          "ingreso + gasto"],
  ["Monotributo",                 "monotributo",     "monotributo_service",  "categoria_monotributo"],
  ["Clasificador (playground)",   "ml",              "ml_service",           "modelo_clasificador"],
  ["Resumen y recomendaciones",   "resumen",         "ia_service",           "—"],
  ["Reporte PDF",                 "reportes",        "reportes_service",     "—"],
];
s.addTable(
  [[
    { text:"Funcionalidad", options:{ bold:true, color:WHITE, fill:{color:NAVY} } },
    { text:"Router",        options:{ bold:true, color:WHITE, fill:{color:NAVY} } },
    { text:"Servicio",      options:{ bold:true, color:WHITE, fill:{color:NAVY} } },
    { text:"Modelo",        options:{ bold:true, color:WHITE, fill:{color:NAVY} } },
  ]].concat(filas.map((f, i) => f.map((c, j) => ({
    text: c,
    options: { color: j === 0 ? INK : TEXTO, fontFace: j === 0 ? FB : FM,
               fill: { color: i % 2 ? "EDF2F7" : WHITE } },
  })))),
  { x:0.7, y:2.15, w:11.9, colW:[3.6, 2.4, 3.0, 2.9], rowH:0.36,
    fontFace:FB, fontSize:12, border:{ type:"solid", color:BORDE, pt:0.5 }, valign:"middle" }
);
s.addText("6.140 líneas de backend  ·  4.609 de frontend  ·  115 pruebas  ·  9 tablas  ·  13 pantallas", {
  x:0.7, y:6.65, w:11.9, h:0.45, fontFace:FB, fontSize:13, bold:true, color:TEAL, align:"center" });
footer(s);

// ── 16 · Panorama de patrones ───────────────────────────────────────────────
s = slide(true);
kicker(s, "Patrones de diseño", MINT);
bloque(s, "Bloque 5 · 26:30", true);
title(s, "32 decisiones anotadas en el código", WHITE);
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.0, w:11.9, h:0.8, fill:{color:"0B1B2B"},
  line:{color:MINT, width:1}, rectRadius:0.08 });
s.addText('grep -rn "PATRÓN:" app frontend/src', { x:1.05, y:2.0, w:7, h:0.8,
  fontFace:FM, fontSize:16, color:MINT, valign:"middle" });
s.addText("→  32 resultados en 16 archivos", { x:8.2, y:2.0, w:4.2, h:0.8,
  fontFace:FB, fontSize:14, color:ICE, valign:"middle" });

const pats = [
  ["Strategy", "ml_service · prophet_service", MINT],
  ["Adapter", "csv_service — 9 bancos", MINT],
  ["Cache-Aside", "ia_service — correcciones", MINT],
  ["Chain of Responsibility", "ia_service — 3 eslabones", TEAL_L],
  ["Factory Method", "auditoria — alertas", TEAL_L],
  ["Builder", "reportes_service — PDF", TEAL_L],
  ["Template Method", "reportes_service — pie", TEAL_L],
  ["Pipeline", "ml_service — TF-IDF + clf", TEAL_L],
  ["Memento", "ml_service — modelo en BD", TEAL_L],
  ["Inyección de dependencias", "dependencies · database", TEAL_L],
  ["Guard / Protected Route", "dependencies · App.js", TEAL_L],
  ["Interceptor", "api.js — JWT y 401", TEAL_L],
  ["Singleton", "database · api.js", GREY],
  ["Factory", "database — sessionmaker", GREY],
  ["Unit of Work", "database — Session", GREY],
  ["Facade", "services · ia_service", GREY],
];
pats.forEach((p, i) => {
  const col = i % 4, row = Math.floor(i / 4);
  const x = 0.7 + col * 3.05, y = 3.05 + row * 0.9;
  const destacado = p[2] === MINT;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:2.85, h:0.78, fill:{color:NAVY2},
    line:{ color: p[2], width: destacado ? 1.8 : 0.75 }, rectRadius:0.06 });
  s.addText(p[0], { x:x+0.18, y:y+0.06, w:2.55, h:0.36, fontFace:FH,
    fontSize: destacado ? 13.5 : 12.5, bold:true, color: destacado ? MINT : WHITE });
  s.addText(p[1], { x:x+0.18, y:y+0.43, w:2.55, h:0.32, fontFace:FM, fontSize:9.5, color:GREY });
});
s.addText("Los tres destacados son los que resolvieron los problemas más difíciles. Se desarrollan a continuación.", {
  x:0.7, y:6.62, w:11.9, h:0.4, fontFace:FB, fontSize:12, italic:true, color:GREY, align:"center" });
footer(s);

// ── 17 · Patrón 1: Strategy ─────────────────────────────────────────────────
s = slide(false);
kicker(s, "Patrón 1 de 3 · Strategy", TEAL);
bloque(s, "Bloque 5 · 27:00");
title(s, "Dos algoritmos, dos escenarios");
// Se parte el return en varias líneas: en una sola no entra en el ancho
// de la caja y LibreOffice lo corta a mitad del literal.
codigo(s, 0.7, 2.1, 6.3, 2.15, "app/services/ml_service.py:728", [
  'def _elegir_algoritmo(n_ejemplos: int) -> str:',
  '    if n_ejemplos >= 100:',
  '        return "svm"',
  '    return "naive_bayes"',
]);
s.addText("El clasificador tiene que funcionar el primer día, sin datos propios, y también con cientos de gastos acumulados. Son dos escenarios estadísticos distintos y ningún algoritmo gana en los dos.", {
  x:0.7, y:4.4, w:6.3, h:1.0, fontFace:FB, fontSize:13.5, color:TEXTO });
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.45, w:6.3, h:1.3, fill:{color:WHITE},
  line:{color:ROJO, width:1}, rectRadius:0.08 });
s.addText("Alternativa descartada", { x:1.0, y:5.6, w:5.7, h:0.3, fontFace:FB, fontSize:11.5, bold:true, color:ROJO });
s.addText("Fijar un solo algoritmo. Medí los dos: con el dataset base gana Naive Bayes, con datos de usuario gana el SVM. Elegir uno era aceptar el peor caso en la mitad de los escenarios.", {
  x:1.0, y:5.9, w:5.75, h:0.8, fontFace:FB, fontSize:11.5, color:TEXTO });

[["Naive Bayes multinomial", "< 100 ejemplos propios",
  "Asume independencia entre términos: con pocos datos no sobreajusta.", TEAL],
 ["LinearSVC", "≥ 100 ejemplos propios",
  "Hiperplano de máximo margen: necesita volumen, pero después supera claramente a Naive Bayes.", MINT]
].forEach((a, i) => {
  const y = 2.1 + i * 2.3;
  s.addShape(pptx.ShapeType.roundRect, { x:7.4, y, w:5.2, h:2.05, fill:{color:NAVY}, rectRadius:0.1 });
  s.addText(a[0], { x:7.7, y:y+0.2, w:4.6, h:0.45, fontFace:FH, fontSize:18, bold:true, color:a[3] });
  s.addText(a[1], { x:7.7, y:y+0.68, w:4.6, h:0.35, fontFace:FM, fontSize:11.5, color:GREY });
  s.addText(a[2], { x:7.7, y:y+1.1, w:4.6, h:0.95, fontFace:FB, fontSize:12.5, color:ICE });
});
s.addText("El resto del código no sabe cuál se usó:\nmisma interfaz, familia intercambiable.", {
  x:7.4, y:6.55, w:5.2, h:0.5, fontFace:FB, fontSize:11.5, italic:true, color:TEAL, align:"center" });
footer(s);

// ── 18 · Patrón 2: Adapter ──────────────────────────────────────────────────
s = slide(true);
kicker(s, "Patrón 2 de 3 · Adapter", MINT);
bloque(s, "Bloque 5 · 28:15", true);
title(s, "Nueve bancos, un modelo interno", WHITE);
s.addText("Galicia · Santander · BBVA · Macro · Nación · Brubank · ICBC · Mercado Pago · Naranja X", {
  x:0.7, y:1.95, w:11.9, h:0.4, fontFace:FB, fontSize:14, color:TEAL_L });
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.55, w:4.3, h:2.5, fill:{color:NAVY2},
  line:{color:ROJO, width:1}, rectRadius:0.08 });
s.addText("CAOS EXTERNO", { x:1.0, y:2.72, w:3.7, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:ROJO, charSpacing:2 });
s.addText('"Fecha"\n"Fecha Mov."\n"Fecha de Operación"\n"F. Mov"\n\ndébito/crédito separados\n· o ·\nimporte único con signo', {
  x:1.0, y:3.1, w:3.7, h:1.85, fontFace:FM, fontSize:12, color:ICE });
s.addText("→", { x:5.1, y:3.45, w:0.8, h:0.7, fontFace:FB, fontSize:32, bold:true, color:MINT, align:"center" });
s.addShape(pptx.ShapeType.roundRect, { x:6.0, y:2.55, w:3.2, h:2.5, fill:{color:MINT}, rectRadius:0.08 });
s.addText("ADAPTER", { x:6.3, y:2.72, w:2.6, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:NAVY, charSpacing:2 });
s.addText("Diccionario de\nsinónimos\n+\nheurísticas\nlocales", { x:6.3, y:3.2, w:2.6, h:1.6,
  fontFace:FH, fontSize:16, bold:true, color:NAVY });
s.addText("→", { x:9.3, y:3.45, w:0.8, h:0.7, fontFace:FB, fontSize:32, bold:true, color:MINT, align:"center" });
s.addShape(pptx.ShapeType.roundRect, { x:10.2, y:2.55, w:2.4, h:2.5, fill:{color:NAVY2},
  line:{color:MINT, width:1}, rectRadius:0.08 });
s.addText("MODELO ÚNICO", { x:10.4, y:2.72, w:2.1, h:0.35, fontFace:FB, fontSize:10.5, bold:true, color:MINT, charSpacing:1 });
s.addText("fecha\ndescripción\nmonto\ntipo", { x:10.4, y:3.25, w:2.1, h:1.5, fontFace:FM, fontSize:14, color:ICE });

s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.3, w:5.85, h:1.5, fill:{color:NAVY2},
  line:{color:MINT, width:1}, rectRadius:0.08 });
s.addText("Por qué así", { x:1.0, y:5.45, w:5.3, h:0.32, fontFace:FB, fontSize:11.5, bold:true, color:MINT });
s.addText("El mapeo es declarativo: agregar un décimo banco es agregar un sinónimo a una lista, sin tocar una línea de lógica.", {
  x:1.0, y:5.78, w:5.3, h:0.9, fontFace:FB, fontSize:12.5, color:ICE });
s.addShape(pptx.ShapeType.roundRect, { x:6.75, y:5.3, w:5.85, h:1.5, fill:{color:NAVY2},
  line:{color:ROJO, width:1}, rectRadius:0.08 });
s.addText("Alternativas descartadas", { x:7.05, y:5.45, w:5.3, h:0.32, fontFace:FB, fontSize:11.5, bold:true, color:ROJO });
s.addText("Un parser por banco: no escala, y los bancos cambian sus exportaciones sin avisar. Que el usuario mapee a mano: elimina el valor de la funcionalidad.", {
  x:7.05, y:5.78, w:5.3, h:0.9, fontFace:FB, fontSize:12.5, color:ICE });
footer(s);

// ── 19 · Patrón 3: Cache-Aside + Chain of Responsibility ────────────────────
s = slide(false);
kicker(s, "Patrón 3 de 3 · Cache-Aside + Chain of Responsibility", TEAL);
bloque(s, "Bloque 5 · 29:00");
title(s, "Clasificar es una cadena de tres eslabones");
const cadena = [
  ["1", "¿Ya lo corrigió el usuario?", "Devolver su corrección con confianza 1.0.\nEs dato real: no hay nada que predecir.", MINT, "Cache-Aside"],
  ["2", "Clasificador ML local", "TF-IDF + Naive Bayes o SVM, según el\nvolumen de ejemplos del usuario.", TEAL, "Strategy"],
  ["3", "¿Confianza bajo el umbral?", "Devolver 'Otros' y marcar para revisión\nmanual. El modelo dice que no sabe.", AMARILLO, "Política de diseño"],
];
cadena.forEach((c, i) => {
  const y = 2.2 + i * 1.5;
  card(s, 0.7, y, 8.6, 1.28, c[3]);
  s.addShape(pptx.ShapeType.roundRect, { x:1.0, y:y+0.34, w:0.6, h:0.6, fill:{color:c[3]}, rectRadius:0.3 });
  s.addText(c[0], { x:1.0, y:y+0.34, w:0.6, h:0.6, fontFace:FH, fontSize:22, bold:true,
    color:WHITE, align:"center", valign:"middle" });
  s.addText(c[1], { x:1.8, y:y+0.18, w:4.4, h:0.42, fontFace:FH, fontSize:16, bold:true, color:INK });
  s.addText(c[2], { x:1.8, y:y+0.62, w:5.1, h:0.6, fontFace:FB, fontSize:12, color:TEXTO });
  s.addShape(pptx.ShapeType.roundRect, { x:7.1, y:y+0.42, w:2.0, h:0.44, fill:{color:c[3]}, rectRadius:0.1 });
  s.addText(c[4], { x:7.1, y:y+0.42, w:2.0, h:0.44, fontFace:FB, fontSize:10.5, bold:true,
    color:WHITE, align:"center", valign:"middle" });
  if (i < 2) s.addText("↓", { x:1.15, y:y+1.28, w:0.3, h:0.22, fontFace:FB, fontSize:14, color:GREY });
});
s.addShape(pptx.ShapeType.roundRect, { x:9.6, y:2.2, w:3.0, h:4.28, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("POR QUÉ", { x:9.85, y:2.42, w:2.5, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:MINT, charSpacing:2 });
s.addText("Si el usuario ya me dijo que «Adobe Photoshop» es Software, volver a equivocarme en esa misma descripción es inaceptable.", {
  x:9.85, y:2.85, w:2.5, h:1.5, fontFace:FB, fontSize:12, color:ICE });
s.addText("Y cuando el modelo duda, lo dice. Prefiero un sistema que diga «no sé» a uno que invente una categoría.", {
  x:9.85, y:4.5, w:2.5, h:1.4, fontFace:FB, fontSize:12, color:ICE });
s.addText("ia_service.py:276", { x:9.85, y:6.05, w:2.5, h:0.3, fontFace:FM, fontSize:10, color:TEAL_L });
s.addText("La comparación usa una forma canónica: sin tildes, sin mayúsculas y sin espacios de más.", {
  x:0.7, y:6.6, w:8.6, h:0.4, fontFace:FB, fontSize:12, italic:true, color:TEAL });
footer(s);

// ── 20 · Seguridad: acceso ──────────────────────────────────────────────────
s = slide(true);
kicker(s, "Seguridad", MINT);
bloque(s, "Bloque 5 · 30:00", true);
title(s, "Control de acceso", WHITE);
const seg = [
  ["bcrypt", "Las contraseñas nunca se guardan en texto plano. Función de derivación de clave adaptable en costo, con valor único por usuario.", "Ni ante una filtración completa de la base se recuperarían las originales."],
  ["JWT · HMAC-SHA256", "Token firmado con vigencia de siete días. La clave de firma vive en una variable de entorno, fuera del código fuente.", "Cada petición viaja con el token en el encabezado de autorización."],
  ["Aislamiento por usuario", "Todas las consultas se filtran por el identificador obtenido del token.", "La separación entre cuentas se garantiza en cada operación, no en la interfaz."],
];
seg.forEach((g, i) => {
  const x = 0.7 + i * 4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.1, w:3.8, h:3.2, fill:{color:NAVY2},
    line:{color:TEAL, width:1}, rectRadius:0.1 });
  s.addText(g[0], { x:x+0.3, y:2.32, w:3.2, h:0.5, fontFace:FH, fontSize:17, bold:true, color:MINT });
  s.addText(g[1], { x:x+0.3, y:2.88, w:3.2, h:1.5, fontFace:FB, fontSize:12.5, color:ICE });
  s.addText(g[2], { x:x+0.3, y:4.45, w:3.2, h:0.75, fontFace:FB, fontSize:11, italic:true, color:GREY });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.6, w:11.9, h:1.25, fill:{color:MINT}, rectRadius:0.1 });
s.addText("El identificador del usuario se obtiene siempre del token, nunca del cuerpo de la petición.", {
  x:1.0, y:5.7, w:11.3, h:0.55, fontFace:FH, fontSize:19, bold:true, color:NAVY });
s.addText("Principio transversal del diseño: un cliente no puede manipular a quién pertenecen los datos.", {
  x:1.0, y:6.25, w:11.3, h:0.45, fontFace:FB, fontSize:13, color:NAVY2 });
footer(s);

// ── 21 · Soberanía de datos ─────────────────────────────────────────────────
s = slide(false);
kicker(s, "Decisión de diseño central", TEAL);
bloque(s, "Bloque 5 · 31:00");
title(s, "Soberanía de los datos");
s.addText("La descripción de un gasto puede revelar clientes, proveedores y hábitos de consumo. Es información financiera sensible.", {
  x:0.7, y:2.05, w:7.4, h:0.75, fontFace:FB, fontSize:15, color:INK });
const sob = [
  ["Clasificación de gastos", "100 % LOCAL", "Entrenamiento y ejecución dentro del mismo entorno donde vive la base.", VERDE],
  ["Detección de formato de archivos", "100 % LOCAL", "Heurísticas sobre un diccionario de sinónimos relevado a mano.", VERDE],
  ["Resumen mensual en lenguaje natural", "ÚNICO SERVICIO EXTERNO", "Solo totales numéricos agregados. Nunca texto libre ni datos identificables.", AMARILLO],
];
sob.forEach((g, i) => {
  const y = 3.0 + i * 1.25;
  card(s, 0.7, y, 7.4, 1.05, g[3]);
  s.addText(g[0], { x:1.05, y:y+0.13, w:4.6, h:0.4, fontFace:FH, fontSize:15, bold:true, color:INK });
  s.addText(g[2], { x:1.05, y:y+0.55, w:5.5, h:0.42, fontFace:FB, fontSize:11.5, color:TEXTO });
  s.addShape(pptx.ShapeType.roundRect, { x:6.0, y:y+0.28, w:1.9, h:0.48, fill:{color:g[3]}, rectRadius:0.1 });
  s.addText(g[1], { x:6.0, y:y+0.28, w:1.9, h:0.48, fontFace:FB, fontSize:9.5, bold:true,
    color: g[3] === AMARILLO ? NAVY : WHITE, align:"center", valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:8.45, y:2.05, w:4.15, h:4.65, fill:{color:MINT}, rectRadius:0.12 });
s.addText("Auditable\nen un punto", { x:8.75, y:2.4, w:3.6, h:1.3, fontFace:FH, fontSize:28, bold:true, color:NAVY });
s.addText("Verificar la política de privacidad de este sistema se reduce a inspeccionar el único lugar del código donde se invoca al servicio externo.", {
  x:8.75, y:3.85, w:3.6, h:1.9, fontFace:FB, fontSize:14.5, color:NAVY });
s.addText("Y si esa clave no está configurada, el resumen usa un fallback local: la aplicación funciona igual.", {
  x:8.75, y:5.75, w:3.6, h:0.8, fontFace:FB, fontSize:11.5, italic:true, color:NAVY2 });
footer(s);

// ── 22 · Lo más difícil ─────────────────────────────────────────────────────
s = slide(true);
kicker(s, "Lo que más costó", AMARILLO);
bloque(s, "Bloque 5 · 32:00", true);
title(s, "No fue entrenar el modelo: fue medir la confianza", WHITE, 29);
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.1, w:5.85, h:2.1, fill:{color:NAVY2},
  line:{color:ROJO, width:1.5}, rectRadius:0.1 });
s.addText("INTENTO 1 · softmax sobre decision_function()", { x:1.0, y:2.28, w:5.3, h:0.35,
  fontFace:FB, fontSize:11.5, bold:true, color:ROJO, charSpacing:1 });
s.addText("LinearSVC no devuelve probabilidades: devuelve distancias al hiperplano. Con 12 clases, softmax reparte la densidad entre todas y hasta los aciertos claros quedaban en ~0,20.", {
  x:1.0, y:2.7, w:5.3, h:1.3, fontFace:FB, fontSize:13, color:ICE });
s.addText("✕  El sistema mandaba todo a revisión manual.", { x:1.0, y:3.85, w:5.3, h:0.3,
  fontFace:FB, fontSize:12, bold:true, color:ROJO });

s.addShape(pptx.ShapeType.roundRect, { x:6.75, y:2.1, w:5.85, h:2.1, fill:{color:NAVY2},
  line:{color:MINT, width:1.5}, rectRadius:0.1 });
s.addText("INTENTO 2 · brecha entre las dos mejores clases", { x:7.05, y:2.28, w:5.3, h:0.35,
  fontFace:FB, fontSize:11.5, bold:true, color:MINT, charSpacing:1 });
s.addText("Cambiar la pregunta: en vez de «¿qué probabilidad tiene esta clase?», «¿cuánto le saca la primera a la segunda?». Vale 0 ante un empate y crece cuando hay una dominante.", {
  x:7.05, y:2.7, w:5.3, h:1.3, fontFace:FB, fontSize:13, color:ICE });
s.addText("✓  El umbral de revisión manual empezó a funcionar.", { x:7.05, y:3.85, w:5.3, h:0.3,
  fontFace:FB, fontSize:12, bold:true, color:MINT });

codigo(s, 0.7, 4.45, 11.9, 1.5, "app/services/ml_service.py:826  ·  _confianza_svm()", [
  "brecha    = scores[top1] - scores[top2]",
  "confianza = 1 - exp(-brecha)        # monótona y acotada en [0, 1)",
]);
s.addText("Este cambio de enfoque es lo que permitió que el sistema supiera cuándo no sabe.", {
  x:0.7, y:6.2, w:11.9, h:0.5, fontFace:FB, fontSize:14, italic:true, color:TEAL_L, align:"center" });
footer(s);

// ── 23 · El riesgo R2 se materializó ────────────────────────────────────────
s = slide(false);
kicker(s, "Validación del diseño", TEAL);
bloque(s, "Bloque 5 · 32:45");
title(s, "Un riesgo previsto que efectivamente ocurrió");
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.15, w:11.9, h:0.95, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("R2 · «El organismo recaudador actualiza la escala del régimen durante o después del desarrollo»", {
  x:1.0, y:2.15, w:11.3, h:0.95, fontFace:FB, fontSize:15, color:ICE, valign:"middle" });
const r2 = [
  ["Qué pasó", "El 1/8/2026 se publicó una escala nueva, con un ajuste del 16,8 % sobre los topes de facturación y las cuotas mensuales de las once categorías.", AMARILLO],
  ["Qué hice", "Cargar los valores nuevos en el catálogo de escalas del proyecto. Cada escala publicada se conserva como una constante fechada.", TEAL],
  ["Qué NO hice", "Tocar una sola línea de código de la aplicación. La acción preventiva definida en la matriz de riesgos funcionó.", VERDE],
];
r2.forEach((r, i) => {
  const x = 0.7 + i * 4.05;
  card(s, x, 3.35, 3.8, 2.6, r[2]);
  s.addText(r[0], { x:x+0.35, y:3.6, w:3.2, h:0.45, fontFace:FH, fontSize:18, bold:true, color:INK });
  s.addText(r[1], { x:x+0.35, y:4.15, w:3.25, h:1.6, fontFace:FB, fontSize:13, color:TEXTO });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:6.2, w:11.9, h:0.85, fill:{color:MINT}, rectRadius:0.1 });
s.addText("Lo que cambia por afuera del sistema no debería obligar a tocar el sistema. El mismo principio aplica al modelo de lenguaje: su nombre se lee de una variable de entorno.", {
  x:1.0, y:6.2, w:11.3, h:0.85, fontFace:FB, fontSize:13.5, bold:true, color:NAVY, valign:"middle" });
footer(s);

// =============================================================================
// BLOQUE 6 · CIERRE                          (guion 33:00 – 35:00)
// =============================================================================

// ── 24 · Métricas por categoría ─────────────────────────────────────────────
s = slide(false);
kicker(s, "Resultados medidos", TEAL);
bloque(s, "Bloque 6 · 33:00");
title(s, "Desempeño del clasificador");
s.addImage({ path:`${DOCS}/metricas_f1_por_categoria.png`, x:0.75, y:2.15, w:6.78, h:4.9 });
s.addShape(pptx.ShapeType.roundRect, { x:8.0, y:2.15, w:4.65, h:4.9, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("76 %", { x:8.25, y:2.35, w:4.2, h:1.0, fontFace:FH, fontSize:52, bold:true, color:MINT });
s.addText("exactitud global  ·  meta: 70 %", { x:8.3, y:3.35, w:4.1, h:0.4, fontFace:FB, fontSize:13.5, color:ICE });
s.addText("Validación cruzada de 5 particiones sobre 600 ejemplos balanceados (50 por categoría).", {
  x:8.3, y:3.78, w:4.1, h:0.7, fontFace:FB, fontSize:11.5, color:GREY });
s.addShape(pptx.ShapeType.line, { x:8.3, y:4.5, w:4.0, h:0, line:{color:TEAL, width:1} });
s.addText("MEJORES", { x:8.3, y:4.62, w:4.1, h:0.32, fontFace:FB, fontSize:11, bold:true, color:TEAL_L, charSpacing:1.5 });
s.addText("Monotributo   F1 0,96\nImpuestos   F1 0,91\nTransporte   F1 0,88", {
  x:8.3, y:4.95, w:4.1, h:0.95, fontFace:FB, fontSize:13, color:ICE });
s.addText("A MEJORAR", { x:8.3, y:5.95, w:4.1, h:0.32, fontFace:FB, fontSize:11, bold:true, color:AMARILLO, charSpacing:1.5 });
s.addText("Marketing   F1 0,58\nServicios   F1 0,63", { x:8.3, y:6.28, w:4.1, h:0.7, fontFace:FB, fontSize:13, color:ICE });
footer(s);

// ── 25 · Matriz de confusión ────────────────────────────────────────────────
s = slide(false);
kicker(s, "Resultados medidos", TEAL);
bloque(s, "Bloque 6 · 33:30");
title(s, "Dónde se confunde, y por qué");
s.addImage({ path:`${DOCS}/metricas_matriz_confusion.png`, x:0.7, y:2.0, w:5.80, h:5.0 });
s.addShape(pptx.ShapeType.roundRect, { x:6.95, y:2.05, w:5.7, h:4.95, fill:{color:WHITE},
  line:{color:BORDE, width:1}, rectRadius:0.1 });
s.addText("Cómo leerla", { x:7.2, y:2.25, w:5.2, h:0.5, fontFace:FH, fontSize:18, bold:true, color:INK });
[ "La diagonal son los aciertos: concentra la mayoría de los casos.",
  "Las confusiones son coherentes: las categorías que se solapan comparten vocabulario.",
  "«Diseño de logo» puede ser Marketing o Servicios. Honestamente, una persona también dudaría.",
  "Por eso el umbral de revisión manual no es un parche: es parte del diseño."
].forEach((r, i) => {
  const y = 2.95 + i * 1.0;
  s.addShape(pptx.ShapeType.roundRect, { x:7.2, y:y+0.05, w:0.14, h:0.78, fill:{color:MINT}, rectRadius:0.04 });
  s.addText(r, { x:7.5, y, w:4.9, h:0.92, fontFace:FB, fontSize:12.5, color:"3A4A58", valign:"middle" });
});
footer(s);

// ── 26 · Trabajo futuro ─────────────────────────────────────────────────────
s = slide(true);
kicker(s, "Trabajo futuro", MINT);
bloque(s, "Bloque 6 · 34:00", true);
title(s, "Tres líneas de continuidad", WHITE);
[["Facturación electrónica", "Integrar el sistema del organismo recaudador para emitir y conciliar comprobantes desde la propia aplicación."],
 ["Banca abierta", "Conciliación bancaria contra cuentas reales del usuario mediante interfaces de banca abierta, sin carga de archivos."],
 ["Ampliar el dataset", "Incorporar datos reales de usuarios para levantar el desempeño de las categorías que hoy se confunden entre sí."]
].forEach((t, i) => {
  const x = 0.7 + i * 4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.3, w:3.8, h:3.0, fill:{color:NAVY2},
    line:{color:TEAL, width:1}, rectRadius:0.1 });
  s.addShape(pptx.ShapeType.roundRect, { x:x+0.3, y:2.6, w:0.6, h:0.6, fill:{color:MINT}, rectRadius:0.3 });
  s.addText(String(i + 1), { x:x+0.3, y:2.6, w:0.6, h:0.6, fontFace:FH, fontSize:22, bold:true,
    color:NAVY, align:"center", valign:"middle" });
  s.addText(t[0], { x:x+0.3, y:3.35, w:3.2, h:0.8, fontFace:FH, fontSize:17, bold:true, color:WHITE });
  s.addText(t[1], { x:x+0.3, y:4.15, w:3.2, h:1.0, fontFace:FB, fontSize:12.5, color:ICE });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:5.65, w:11.9, h:1.2, fill:{color:AMARILLO}, rectRadius:0.1 });
s.addText("El sistema informa, proyecta y alerta. La decisión y el asesoramiento siguen siendo de un profesional y del propio usuario.", {
  x:1.0, y:5.65, w:11.3, h:1.2, fontFace:FH, fontSize:18, bold:true, color:NAVY, valign:"middle" });
footer(s);

// ── 27 · Cierre ─────────────────────────────────────────────────────────────
s = slide(true);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:7.5, fill:{color:MINT} });
s.addText("FreelanceControl", { x:0.85, y:2.35, w:11.7, h:1.2, fontFace:FH, fontSize:50, bold:true, color:WHITE });
s.addText("Gracias.", { x:0.9, y:3.6, w:11.0, h:0.8, fontFace:FH, fontSize:30, color:MINT });
const cierre = [["76 %", "exactitud"], ["115", "pruebas"], ["17", "historias"], ["9", "bancos"], ["5", "detectores"], ["13", "pantallas"]];
cierre.forEach((c, i) => {
  const x = 0.9 + i * 1.95;
  s.addText(c[0], { x, y:4.8, w:1.8, h:0.55, fontFace:FH, fontSize:26, bold:true, color:WHITE });
  s.addText(c[1], { x, y:5.35, w:1.8, h:0.35, fontFace:FB, fontSize:11.5, color:GREY });
});
s.addText("Marcos Gamaliel Joaquín  ·  Legajo SOF02218  ·  Ingeniería de Software  ·  Universidad Siglo 21", {
  x:0.9, y:6.5, w:11.5, h:0.4, fontFace:FB, fontSize:13, color:GREY });

// =============================================================================
// ANEXO · Slides de respaldo para la ronda de preguntas
// =============================================================================

// ── A1 · Los cinco detectores de auditoría ──────────────────────────────────
s = slide(false);
kicker(s, "Anexo · respaldo para preguntas", GREY);
title(s, "Los cinco detectores de auditoría");
const det = [
  ["Gastos duplicados", "Mismo monto y categoría dentro de una ventana de 3 días.", TEAL],
  ["Anomalías estadísticas", "Montos que se desvían del comportamiento histórico de la categoría en los últimos 6 meses.", MINT],
  ["Facturas vencidas o impagas", "Plata que debería haber entrado y no entró. Cubre los estados PENDIENTE y VENCIDA.", AMARILLO],
  ["Cuota de Monotributo sin registrar", "Ausencia del pago de la cuota en el mes corriente, con tolerancia del 1 %.", ROJO],
  ["Transferencias entre cuentas propias", "Un movimiento entre cuentas del usuario contado como ingreso le inflaría la facturación acumulada, que es el número del que depende su categoría fiscal.", NAVY2],
];
det.forEach((d, i) => {
  const y = 2.1 + i * 0.92;
  card(s, 0.7, y, 11.9, 0.8, d[2]);
  s.addShape(pptx.ShapeType.roundRect, { x:1.0, y:y+0.19, w:0.45, h:0.45, fill:{color:d[2]}, rectRadius:0.22 });
  s.addText(String(i + 1), { x:1.0, y:y+0.19, w:0.45, h:0.45, fontFace:FH, fontSize:16, bold:true,
    color:WHITE, align:"center", valign:"middle" });
  s.addText(d[0], { x:1.65, y, w:3.7, h:0.82, fontFace:FH, fontSize:14.5, bold:true, color:INK, valign:"middle" });
  s.addText(d[1], { x:5.4, y, w:7.0, h:0.82, fontFace:FB, fontSize:11.5, color:TEXTO, valign:"middle" });
});
s.addText("Idempotencia: cada condición tiene una huella estable (tipo + monto). Una alerta que el usuario marcó como resuelta no se regenera en la corrida siguiente.", {
  x:0.7, y:6.72, w:11.9, h:0.4, fontFace:FB, fontSize:12, italic:true, color:TEAL, align:"center" });
footer(s);

// ── A2 · Costos ─────────────────────────────────────────────────────────────
s = slide(false);
kicker(s, "Anexo · respaldo para preguntas", GREY);
title(s, "Análisis de costos");
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.2, w:5.85, h:2.4, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("DESARROLLO", { x:1.0, y:2.42, w:5.2, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:MINT, charSpacing:2 });
s.addText("$ 4.400.000", { x:1.0, y:2.85, w:5.2, h:0.85, fontFace:FH, fontSize:40, bold:true, color:WHITE });
s.addText("Un desarrollador full-stack junior · $1.100.000 mensuales · 4 meses.\nReferencia: mercado de tecnología argentino 2026.", {
  x:1.0, y:3.75, w:5.2, h:0.75, fontFace:FB, fontSize:12, color:ICE });
s.addShape(pptx.ShapeType.roundRect, { x:6.75, y:2.2, w:5.85, h:2.4, fill:{color:NAVY2}, rectRadius:0.1 });
s.addText("OPERATIVOS", { x:7.05, y:2.42, w:5.2, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:TEAL_L, charSpacing:2 });
s.addText("Licencias: $ 0", { x:7.05, y:2.85, w:5.2, h:0.7, fontFace:FH, fontSize:30, bold:true, color:WHITE });
s.addText("Todo el stack es software de código abierto: FastAPI, PostgreSQL, React, Scikit-learn, Prophet y ReportLab. El único servicio de pago es la inferencia externa, acotada por diseño a valores marginales.", {
  x:7.05, y:3.6, w:5.2, h:0.9, fontFace:FB, fontSize:12, color:ICE });
s.addText("Tipo de cambio de referencia: dólar vendedor del Banco de la Nación Argentina, junio de 2026 (USD 1 = $1.460). No se calcula retorno sobre la inversión: el prototipo no se orienta a una explotación comercial inmediata.", {
  x:0.7, y:4.85, w:11.9, h:0.8, fontFace:FB, fontSize:12.5, italic:true, color:TEXTO });
footer(s);

// ── A3 · Índice de consulta rápida ──────────────────────────────────────────
s = slide(true);
kicker(s, "Anexo · respaldo para preguntas", GREY);
title(s, "¿Dónde se maneja…?", WHITE);
const idx = [
  ["Conexión a la base", "database.py:38"],
  ["Protección de rutas", "dependencies.py:40"],
  ["Hash de contraseñas", "services/auth.py"],
  ["Elección de algoritmo", "ml_service.py:728"],
  ["Modelo entrenado en BD", "ml_service.py:713"],
  ["Confianza del SVM", "ml_service.py:826"],
  ["Arranque en frío", "prophet_service.py:91"],
  ["Formatos de banco", "csv_service.py:41"],
  ["Transferencias propias", "csv_service.py:581"],
  ["Cadena de clasificación", "ia_service.py:276"],
  ["Creación de alertas", "auditoria.py:48"],
  ["Idempotencia de alertas", "auditoria.py:66"],
  ["Armado del PDF", "reportes_service.py:406"],
  ["Cálculo fiscal", "monotributo_service.py:36"],
  ["Token en el frontend", "api.js:23"],
  ["Rutas privadas", "App.js:31"],
];
idx.forEach((r, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.7 + col * 6.1, y = 2.05 + row * 0.585;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.8, h:0.5, fill:{color:NAVY2}, rectRadius:0.05 });
  s.addText(r[0], { x:x+0.25, y, w:2.75, h:0.5, fontFace:FB, fontSize:12, color:ICE, valign:"middle" });
  // La columna de rutas va más ancha: "monotributo_service.py:36" no entraba.
  s.addText(r[1], { x:x+3.0, y, w:2.65, h:0.5, fontFace:FM, fontSize:10.5, color:MINT, valign:"middle" });
});
s.addText('Desarrollo completo en defensa_final/02_ARQUITECTURA_Y_PATRONES.md  ·  grep -rn "PATRÓN:" app frontend/src', {
  x:0.7, y:6.72, w:11.9, h:0.4, fontFace:FM, fontSize:10.5, color:GREY, align:"center" });
footer(s);

// =============================================================================
pptx.writeFile({ fileName: "/Users/marcosjoaquin/proyecto-tfg/defensa_final/slides/FreelanceControl_Defensa_Final.pptx" })
  .then(f => console.log(`OK · ${n} slides · ${f}`));
