// =============================================================================
// Filminas de la defensa oral — FreelanceControl (35 min + 10 de preguntas)
//
// Centradas en lo que pidió la cátedra: el prototipo funcionando (importación,
// clasificador, auditoría, estado fiscal, proyección y reporte PDF), los
// límites del clasificador, del motor predictivo y de las recomendaciones, y
// que el sistema no se presente como asesoramiento.
//
// Reglas de estas filminas:
//   · Sin cifras: conceptos, capturas reales y analogías. Los gráficos no
//     llevan números; su forma sale de los datos reales de la demo.
//   · El clasificador se explica con capturas (no se escribe en vivo).
//   · La demo en vivo va en cuatro tramos; la filmina anterior a cada tramo
//     lo anuncia abajo a la derecha ("Ahora, en vivo: …").
//   · El reloj, lo que hay que decir y los datos de respaldo van en las
//     notas del orador (vista del presentador), no en la filmina.
//
// El orden, el reloj y las notas siguen el guion de la demo en vivo
// (03_GUION_DEMO_EN_VIVO.md, 10 de octubre): si cambia el guion, se revisan acá.
//
// Las capturas son del 14/10/2026 a las 12:00 simulado, con el seed de la
// defensa y el extracto importado (ver slides/fuentes/LEEME.md).
//
// Reproducible:  node defensa_final/gen_slides_defensa.js
// Requiere:      npm i -g pptxgenjs
// Salida:        defensa_final/slides/FreelanceControl_Defensa_Final.pptx
// =============================================================================

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("/opt/homebrew/lib/node_modules/pptxgenjs");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";            // 13,33 × 7,5 pulgadas
pptx.author = "Marcos Gamaliel Joaquín";
pptx.title = "FreelanceControl — Defensa oral";
pptx.subject = "Trabajo Final de Grado — Ingeniería de Software — Universidad Siglo 21";

const RAIZ = __dirname;
const CAP = path.join(RAIZ, "slides", "capturas");
const ICO = path.join(RAIZ, "slides", "iconos");
const SALIDA = path.join(RAIZ, "slides", "FreelanceControl_Defensa_Final.pptx");

// ── Paleta: el azul noche de la aplicación, para que las capturas no desentonen ──
const NAVY = "0D2B45", NAVY2 = "14395E", NAVY3 = "0B1B2B", TEAL = "1C7293", TEAL_L = "5BB3C4";
const MINT = "02C39A", ICE = "CADCFC", WHITE = "FFFFFF", GREY = "8FA3B5";
const ROJO = "D14D4D", AMARILLO = "E0A82E", VERDE = "2E9E5B";
const CLARO = "F4F7FB", INK = "16222E", TEXTO = "44546A", BORDE = "DCE4EC", PISTA = "E3EAF1";
// Georgia y Arial vienen con macOS (Keynote) y con Office.
const FH = "Georgia", FB = "Arial", FM = "Courier New";

let n = 0;

// ── Ayudas ──────────────────────────────────────────────────────────────────
function slide(oscura, notas) {
  n++;
  const s = pptx.addSlide();
  s.background = { color: oscura ? NAVY : CLARO };
  s.addText("FreelanceControl · Defensa oral", { x:0.6, y:7.05, w:6, h:0.3, fontFace:FB,
    fontSize:9, color: oscura ? "6F8AA3" : GREY, isTextBox:true });
  s.addText(String(n), { x:12.2, y:7.05, w:0.55, h:0.3, fontFace:FB, fontSize:9,
    color: oscura ? "6F8AA3" : GREY, align:"right", isTextBox:true });
  if (notas) s.addNotes(notas);
  return s;
}
function kicker(s, txt, color) {
  s.addText(txt.toUpperCase(), { x:0.6, y:0.4, w:12.1, h:0.32, fontFace:FB, fontSize:12,
    bold:true, color: color || TEAL, charSpacing:3, margin:0, isTextBox:true });
}
function titulo(s, txt, oscura, size) {
  s.addText(txt, { x:0.6, y:0.72, w:12.1, h:0.85, fontFace:FH, fontSize: size || 32, bold:true,
    color: oscura ? WHITE : INK, margin:0, valign:"top", isTextBox:true });
}
function texto(s, txt, o) {
  s.addText(txt, Object.assign({ fontFace:FB, fontSize:15, color:TEXTO, valign:"top",
    margin:0, isTextBox:true }, o));
}
/** Anuncia el tramo en vivo que sigue a esta filmina. */
function enVivo(s, que) {
  s.addShape(pptx.ShapeType.roundRect, { x:8.35, y:6.62, w:4.38, h:0.42, fill:{color:MINT},
    rectRadius:0.21, line:{color:MINT, width:0} });
  s.addText([{ text:"Ahora, en vivo:  ", options:{ bold:true } }, { text:que }], {
    x:8.35, y:6.62, w:4.38, h:0.42, fontFace:FB, fontSize:12.5, color:NAVY, align:"center",
    valign:"middle", margin:0, isTextBox:true });
}
function card(s, x, y, w, h, o) {
  o = o || {};
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, fill:{color: o.fill || WHITE},
    line:{color: o.line || BORDE, width: o.lw || 1}, rectRadius: o.r || 0.1,
    shadow: o.sombra === false ? undefined :
      { type:"outer", color:"9AA9B8", blur:8, offset:2, angle:90, opacity:0.22 } });
}
/** Ícono blanco (o azul noche) dentro de un círculo de color: el motivo de todo el deck. */
function icono(s, nombre, x, y, d, fondo, variante) {
  s.addShape(pptx.ShapeType.ellipse, { x, y, w:d, h:d, fill:{color:fondo}, line:{color:fondo, width:0} });
  const i = d * 0.54;
  s.addImage({ path: path.join(ICO, `${nombre}_${variante || "b"}.png`), x:x+(d-i)/2, y:y+(d-i)/2, w:i, h:i });
}
function pngSize(archivo) {
  const b = fs.readFileSync(archivo);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
/**
 * Captura dentro de una "ventana" de navegador: el otro motivo del deck.
 * Se le da el ancho, o el alto con {alto}; devuelve el tamaño que ocupó.
 */
function ventana(s, nombre, x, y, w, o) {
  o = o || {};
  const archivo = path.join(CAP, nombre + ".png");
  const t = pngSize(archivo), barra = 0.24, pad = 0.05;
  if (o.alto) w = (o.alto - barra - pad) * t.w / t.h + 2 * pad;
  const ih = (w - 2 * pad) * t.h / t.w, h = barra + ih + pad;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, fill:{color:NAVY3}, line:{color:"23415F", width:1},
    rectRadius:0.07, shadow:{ type:"outer", color:"0A1622", blur:10, offset:3, angle:90, opacity:0.35 } });
  ["FF5F57", "FEBC2E", "28C840"].forEach((c, i) =>
    s.addShape(pptx.ShapeType.ellipse, { x:x+0.12+i*0.15, y:y+0.075, w:0.09, h:0.09, fill:{color:c}, line:{color:c, width:0} }));
  s.addImage({ path:archivo, x:x+pad, y:y+barra, w:w-2*pad, h:ih });
  return { w, h, ix:x+pad, iy:y+barra, iw:w-2*pad, ih };
}
/** Polilínea o polígono (puntos en pulgadas, relativos a la caja). */
function trazo(s, x, y, w, h, puntos, o) {
  s.addShape(pptx.ShapeType.custGeom, Object.assign({ x, y, w, h, points:puntos }, o));
}
function linea(s, x1, y1, x2, y2, o) {
  trazo(s, Math.min(x1, x2), Math.min(y1, y2), Math.max(Math.abs(x2 - x1), 0.01), Math.max(Math.abs(y2 - y1), 0.01),
    [{ x:x1 - Math.min(x1, x2), y:y1 - Math.min(y1, y2) }, { x:x2 - Math.min(x1, x2), y:y2 - Math.min(y1, y2) }],
    { line:o });
}
function flecha(s, x, y, w, color) {
  s.addShape(pptx.ShapeType.rightArrow, { x, y, w, h:0.34, fill:{color: color || TEAL_L}, line:{color: color || TEAL_L, width:0} });
}
function chip(s, txt, x, y, w, o) {
  o = o || {};
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: o.h || 0.42, fill:{color: o.fill || WHITE},
    line:{color: o.line || BORDE, width:1}, rectRadius:(o.h || 0.42) / 2 });
  s.addText(txt, { x, y, w, h: o.h || 0.42, fontFace: o.mono ? FM : FB, fontSize: o.size || 12.5,
    color: o.color || INK, bold: !!o.bold, align:"center", valign:"middle", margin:0, isTextBox:true });
}

// =============================================================================
// 1 · EL PROBLEMA                                                (0:00 – 3:30)
// =============================================================================

// ── Portada ─────────────────────────────────────────────────────────────────
let s = slide(true, `RELOJ 0:00 · 20 s.
Presentate: nombre, carrera, y el título del trabajo. "Durante los próximos minutos les voy a contar qué problema resuelve FreelanceControl, mostrarlo funcionando y explicar hasta dónde llega."`);
s.addText("TRABAJO FINAL DE GRADO · INGENIERÍA DE SOFTWARE · UNIVERSIDAD SIGLO 21", {
  x:0.7, y:1.35, w:7.2, h:0.6, fontFace:FB, fontSize:11.5, color:TEAL_L, bold:true, charSpacing:2, margin:0, isTextBox:true });
s.addText("FreelanceControl", { x:0.7, y:2.05, w:7.0, h:1.1, fontFace:FH, fontSize:50, bold:true, color:WHITE, margin:0, isTextBox:true });
texto(s, "Gestión financiera para monotributistas: un sistema que, además de registrar, clasifica, proyecta, controla y audita.", {
  x:0.7, y:3.25, w:6.4, h:1.0, fontSize:18, color:ICE });
texto(s, "Modalidad: prototipado tecnológico", { x:0.7, y:4.35, w:6.4, h:0.4, fontSize:14, italic:true, color:GREY });
texto(s, "Marcos Gamaliel Joaquín  ·  Legajo SOF02218", { x:0.7, y:5.75, w:6.6, h:0.4, fontSize:16, color:WHITE });
texto(s, "Profesor TFG: Alejandro Mainero", { x:0.7, y:6.15, w:6.6, h:0.4, fontSize:13, color:GREY });
ventana(s, "dashboard", 7.65, 1.55, 5.1);

// ── A quién le pasa ─────────────────────────────────────────────────────────
s = slide(false, `RELOJ 0:20 · 40 s.
· El usuario: el freelancer que presta servicios y cobra por proyecto, inscripto en el monotributo.
· Es un grupo grande y que crece. Respaldo, si preguntan: el trabajo por cuenta propia llegó al 24,5 % del empleo (INDEC, EPH 3.er trim. 2025), unas 3,3 millones de personas; los inscriptos en el monotributo crecieron un 35 % (Secretaría de Trabajo, 2026).`);
kicker(s, "A quién le pasa");
titulo(s, "El freelancer que factura por su cuenta");
[["Palette", "Diseñadores", TEAL], ["Code", "Programadores", MINT], ["Presentation", "Consultores", AMARILLO]].forEach((p, i) => {
  const x = 1.2 + i * 3.9;
  icono(s, p[0], x + 0.75, 2.15, 1.5, p[2]);
  s.addText(p[1], { x, y:3.8, w:3.0, h:0.5, fontFace:FH, fontSize:20, bold:true, color:INK, align:"center", margin:0, isTextBox:true });
});
card(s, 0.6, 4.75, 12.1, 1.55, { sombra:false });
texto(s, "Prestan servicios, cobran por proyecto y están en el monotributo.", {
  x:1.0, y:4.98, w:11.3, h:0.5, fontSize:19, color:INK, bold:true });
texto(s, "Es un grupo grande en Argentina y viene creciendo. Ese es el usuario del sistema.", {
  x:1.0, y:5.55, w:11.3, h:0.5, fontSize:16 });

// ── Los cuatro problemas ────────────────────────────────────────────────────
s = slide(false, `RELOJ 1:00 · 1:30.
1. La plata entra irregular: depende de cuándo termina cada trabajo y cuándo paga cada cliente. Las apps registran lo que ya pasó, ninguna dice qué viene. (En la demo se ve: meses muy altos y meses muy bajos.)
2. El tope: cada categoría tiene un límite anual que ARCA actualiza. Si lo pasás, te recategorizan de oficio o, en casos extremos, te excluyen. Controlarlo a mano es fácil de olvidar.
3. Nadie revisa: gasto cargado dos veces, gasto fuera de lo común, factura vencida sin cobrar, cuota impaga. Cruzarlo a mano se deja para fin de año.
4. Desparramado: planillas, apps, mails, PDF, extractos del homebanking.`);
kicker(s, "El problema");
titulo(s, "Lo que le pasa a un monotributista todos los meses");
[["ChartSpline", "La plata entra irregular", "Un mes entra mucho y al siguiente casi nada. Las aplicaciones registran lo que pasó, pero ninguna dice qué viene.", TEAL],
 ["Gauge", "El tope del monotributo", "Cada categoría tiene un límite anual. Pasarlo obliga a recategorizarse y, en casos extremos, excluye del régimen.", ROJO],
 ["EyeOff", "Nadie revisa los registros", "Un gasto cargado dos veces, una factura sin cobrar o la cuota impaga se descubren tarde.", AMARILLO],
 ["Files", "Todo está desparramado", "Planillas, aplicaciones, mails con comprobantes, PDF de facturas y extractos del banco. Nada junto.", MINT],
].forEach((p, i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.95 + Math.floor(i / 2) * 2.45;
  card(s, x, y, 5.95, 2.2);
  icono(s, p[0], x + 0.35, y + 0.35, 0.95, p[3]);
  s.addText(p[1], { x:x+1.55, y:y+0.38, w:4.2, h:0.5, fontFace:FH, fontSize:19, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, p[2], { x:x+1.55, y:y+0.95, w:4.15, h:1.15, fontSize:14 });
});

// ── El mercado y la pregunta ────────────────────────────────────────────────
s = slide(true, `RELOJ 2:30 · 1:00.
· Contabilium, Xubio, Colppy, QuickBooks y FreshBooks facturan e integran con el fisco, pero están pensadas para pymes con estructura administrativa, no para una persona sola en el monotributo.
· Ninguna clasifica los gastos sola, proyecta los ingresos ni revisa los registros automáticamente.
· Cerrá con la pregunta del trabajo, despacio.`);
kicker(s, "Lo que hay en el mercado", MINT);
titulo(s, "Las herramientas que existen no lo resuelven", true);
texto(s, "Contabilium · Xubio · Colppy · QuickBooks · FreshBooks", { x:0.6, y:1.75, w:12.1, h:0.4, fontSize:17, color:ICE });
texto(s, "Facturan e integran con el fisco, pero están pensadas para pymes con estructura administrativa, no para una persona sola en el monotributo.", {
  x:0.6, y:2.2, w:12.1, h:0.7, fontSize:14.5, color:GREY });
[["Tags", "Clasificar los gastos sola"], ["TrendingUp", "Proyectar los ingresos"], ["ScanSearch", "Revisar los registros sola"]].forEach((f, i) => {
  const x = 0.6 + i * 4.1;
  s.addShape(pptx.ShapeType.roundRect, { x, y:3.15, w:3.85, h:1.45, fill:{color:NAVY2}, line:{color:ROJO, width:1.25}, rectRadius:0.1 });
  icono(s, f[0], x + 0.3, 3.5, 0.75, TEAL);
  s.addText(f[1], { x:x+1.25, y:3.3, w:2.45, h:0.75, fontFace:FB, fontSize:15, color:ICE, valign:"middle", margin:0, isTextBox:true });
  s.addText("Ninguna lo hace", { x:x+1.25, y:4.02, w:2.45, h:0.4, fontFace:FH, fontSize:15, bold:true, color:ROJO, margin:0, isTextBox:true });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:5.0, w:12.1, h:1.3, fill:{color:MINT}, rectRadius:0.12, line:{color:MINT, width:0} });
s.addText("¿Puede un software anticipar el riesgo, en vez de solo registrarlo?", {
  x:0.9, y:5.0, w:11.5, h:1.3, fontFace:FH, fontSize:25, bold:true, color:NAVY, valign:"middle", margin:0, isTextBox:true });

// =============================================================================
// 2 · LA PROPUESTA Y HASTA DÓNDE LLEGA                           (3:30 – 6:50)
// =============================================================================

// ── La propuesta ────────────────────────────────────────────────────────────
s = slide(false, `RELOJ 3:30 · 1:00.
La app en una frase: "FreelanceControl junta la plata del freelancer en un solo lugar, la ordena sola y le avisa antes de que haya un problema. Es un copiloto: no maneja por vos, pero te avisa que viene una curva."
Un sistema web para monotributistas que, además de registrar, trabaja solo:
· Junta todo: en vez de tipear, se sube el extracto del banco (CSV o Excel).
· Clasifica los gastos leyendo la descripción, con un modelo que se entrena en la propia computadora y aprende de las correcciones.
· Proyecta los ingresos de los próximos meses con un escenario pesimista y uno optimista.
· Controla la categoría: avisa si a este ritmo te pasarías del tope y en qué mes.
· Revisa los registros solo y arma el reporte mensual en PDF: el resumen del mes cerrado.
(El copiloto se dice: en la filmina no está escrito.)
Si te preguntan "¿es un reporte para el contador?": "No es un documento contable: es el resumen del mes cerrado. La tesis (HU-13) lo plantea para que el usuario lo archive o, si quiere, lo comparta con su contador. Por eso lleva el aviso de que no reemplaza su asesoramiento."`);
kicker(s, "La propuesta");
titulo(s, "Un sistema que, además de registrar, trabaja solo");
[["Layers", "Junta todo", "Ingresos, gastos y facturas. Se sube el extracto del banco.", TEAL],
 ["Tags", "Clasifica solo", "Lee la descripción del gasto y sugiere la categoría.", MINT],
 ["TrendingUp", "Proyecta", "Los ingresos que vienen, con un escenario pesimista y uno optimista.", TEAL],
 ["Gauge", "Vigila el tope", "Avisa si a este ritmo te pasarías del monotributo, y en qué mes.", ROJO],
 ["ScanSearch", "Revisa solo", "Duplicados, gastos irregulares, facturas vencidas y más.", AMARILLO],
 ["FileText", "Reporte mensual", "El resumen del mes cerrado en PDF, para archivarlo o compartirlo.", MINT],
].forEach((c, i) => {
  const x = 0.6 + (i % 2) * 3.45, y = 1.9 + Math.floor(i / 2) * 1.6;
  icono(s, c[0], x, y + 0.05, 0.72, c[3]);
  s.addText(c[1], { x:x+0.88, y, w:2.45, h:0.42, fontFace:FH, fontSize:15.5, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, c[2], { x:x+0.88, y:y+0.44, w:2.45, h:0.95, fontSize:12.5 });
});
// El panel, centrado en la altura de la lista. La analogía del copiloto se dice, no se escribe.
const panel = ventana(s, "dashboard", 7.55, 2.55, 5.15);
texto(s, "El panel principal, con los datos de la demo.", { x:7.55, y:2.55 + panel.h + 0.15, w:5.15, h:0.35, fontSize:11.5, italic:true, color:GREY, align:"center" });

// ── Cómo está construido: las tecnologías ───────────────────────────────────
// Sin versiones (son cifras): van en las notas.
s = slide(true, `RELOJ 4:30 · 45 s.
DECÍ: "Es una aplicación web en capas. Las pantallas están hechas en React; el servidor, en Python con FastAPI; los datos, en PostgreSQL. La inteligencia corre dentro del servidor: scikit-learn para el clasificador de gastos y Prophet para la proyección de ingresos. Y todo se levanta junto con Docker."
Una línea por columna, si da el tiempo:
· Pantallas: React arma las pantallas; Chart.js dibuja los gráficos; Axios lleva cada pedido al servidor.
· Servidor: FastAPI recibe cada pedido y Pydantic valida lo que entra; pandas y openpyxl leen los extractos (CSV y Excel); ReportLab arma el PDF.
· Inteligencia: scikit-learn, con TF-IDF y SVM (y Naive Bayes, como prevé la tesis); Prophet, de Meta, para las proyecciones; Groq, un modelo de lenguaje externo, solo para redactar el Resumen del mes, y solo con totales.
· Datos y seguridad: PostgreSQL guarda todo; SQLAlchemy y Alembic arman las tablas y sus cambios; bcrypt, el hash de la contraseña; JWT, el pase firmado de la sesión.
· Abajo: Docker Compose levanta la base, el servidor y las pantallas con un comando; pytest y Testing Library corren las pruebas automáticas.
Si te preguntan "¿por qué Python?": "Porque el clasificador y la proyección se hacen en Python: scikit-learn y Prophet son de Python. Con el servidor en el mismo lenguaje, los modelos corren adentro, sin otro servicio."
Si te preguntan "¿por qué PostgreSQL?": "Es relacional y transaccional: la importación guarda todo junto o nada."
Respaldo (versiones): React 19, FastAPI 0.110, PostgreSQL 15, scikit-learn 1.4, Prophet 1.1, Python 3.11.`);
kicker(s, "Cómo está construido", MINT);
titulo(s, "Las tecnologías, capa por capa", true);
[["Monitor", "Pantallas", "Lo que ve el usuario", TEAL, [["React", "las pantallas"], ["Chart.js", "los gráficos"], ["Axios", "lleva los pedidos al servidor"]]],
 ["Server", "Servidor", "Las reglas del sistema", TEAL, [["Python · FastAPI", "recibe cada pedido"], ["Pydantic", "valida lo que entra"], ["pandas · openpyxl", "leen los extractos"], ["ReportLab", "arma el reporte PDF"]]],
 ["Brain", "Inteligencia", "Clasifica y proyecta", MINT, [["scikit-learn", "el clasificador de gastos"], ["Prophet", "la proyección de ingresos"], ["Groq", "redacta el resumen del mes"]]],
 ["Database", "Datos", "La base y la seguridad", TEAL, [["PostgreSQL", "la base de datos"], ["SQLAlchemy · Alembic", "las tablas y sus cambios"], ["bcrypt", "el hash de la contraseña"], ["JWT", "el pase de la sesión"]]],
].forEach((c, i) => {
  const x = 0.6 + i * 3.08, y = 1.8;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:2.85, h:4.1, fill:{color:NAVY2}, line:{color: c[3], width:1}, rectRadius:0.1 });
  icono(s, c[0], x + 0.2, y + 0.22, 0.62, c[3]);
  s.addText(c[1], { x:x+0.95, y:y+0.18, w:1.8, h:0.38, fontFace:FH, fontSize:16, bold:true, color:WHITE, margin:0, isTextBox:true });
  texto(s, c[2], { x:x+0.95, y:y+0.55, w:1.85, h:0.3, fontSize:11, color:TEAL_L });
  s.addShape(pptx.ShapeType.line, { x:x+0.2, y:y+1.05, w:2.45, h:0, line:{color:"2A4D6E", width:1} });
  c[4].forEach((t, k) => {
    const ty = y + 1.2 + k * 0.7;
    s.addText(t[0], { x:x+0.2, y:ty, w:2.5, h:0.32, fontFace:FB, fontSize:14, bold:true, color:WHITE, margin:0, isTextBox:true });
    texto(s, t[1], { x:x+0.2, y:ty + 0.31, w:2.5, h:0.3, fontSize:11.5, color:ICE });
  });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:6.1, w:12.1, h:0.62, fill:{color:NAVY3}, line:{color:"23415F", width:1}, rectRadius:0.1 });
icono(s, "Layers", 0.75, 6.16, 0.5, TEAL);
s.addText([{ text:"Docker Compose  ", options:{ bold:true, color:WHITE } }, { text:"levanta la base, el servidor y las pantallas juntos", options:{ color:ICE } }], {
  x:1.35, y:6.1, w:5.6, h:0.62, fontFace:FB, fontSize:13, valign:"middle", margin:0, isTextBox:true });
icono(s, "ListChecks", 7.05, 6.16, 0.5, TEAL);
s.addText([{ text:"pytest · Testing Library  ", options:{ bold:true, color:WHITE } }, { text:"las pruebas automáticas", options:{ color:ICE } }], {
  x:7.65, y:6.1, w:5.0, h:0.62, fontFace:FB, fontSize:13, valign:"middle", margin:0, isTextBox:true });

// ── La frase de alcance ─────────────────────────────────────────────────────
s = slide(true, `RELOJ 5:15 · 1:05. LO PIDIÓ LA CÁTEDRA: decí la frase TAL CUAL, despacio.
Después, los tres ejemplos de abajo.
Y cerrá con el aviso: "Esta frase no es una nota al pie: está en el producto. Aparece en seis pantallas —Panel, Monotributo, Proyecciones, Recomendaciones, Resumen y Auditoría— y al pie del reporte PDF, que es lo único que sale de la aplicación. Lo van a ver en la demo."`);
kicker(s, "Hasta dónde llega", MINT);
titulo(s, "Informa, proyecta y alerta. No asesora.", true);
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:1.8, w:12.1, h:1.95, fill:{color:NAVY2}, line:{color:MINT, width:1.5}, rectRadius:0.12 });
s.addText("“FreelanceControl informa, proyecta y alerta sobre la base de los datos que el usuario carga. No constituye asesoramiento contable, fiscal ni financiero, y no reemplaza la intervención de un profesional matriculado.”", {
  x:1.0, y:1.8, w:11.3, h:1.95, fontFace:FH, fontSize:19.5, italic:true, color:WHITE, valign:"middle", margin:0, isTextBox:true });
[["Gauge", "Te dice que, a este ritmo, te pasarías del tope", "No te dice qué hacer"],
 ["Copy", "Te marca dos gastos iguales", "No decide que uno sea un error"],
 ["TrendingUp", "Te proyecta lo que podrías cobrar, con un rango", "No lo garantiza"]].forEach((e, i) => {
  const x = 0.6 + i * 4.1;
  s.addShape(pptx.ShapeType.roundRect, { x, y:4.15, w:3.85, h:2.25, fill:{color:NAVY}, line:{color:TEAL, width:1}, rectRadius:0.1 });
  icono(s, e[0], x + 0.3, 4.4, 0.65, TEAL);
  texto(s, e[1], { x:x+1.1, y:4.38, w:2.55, h:1.0, fontSize:14.5, color:ICE });
  s.addShape(pptx.ShapeType.line, { x:x+0.3, y:5.5, w:3.25, h:0, line:{color:"2A4D6E", width:1} });
  s.addText(e[2], { x:x+0.3, y:5.62, w:3.3, h:0.55, fontFace:FH, fontSize:16, bold:true, color:MINT, margin:0, isTextBox:true });
});

// ── Lo que quedó afuera ─────────────────────────────────────────────────────
// Los cuatro límites de la tesis ("Límites del prototipo"), cada uno con lo que
// el sistema no hace y lo que hace en su lugar.
s = slide(false, `RELOJ 6:20 · 30 s.
DECÍ: "Esto es lo que el sistema no hace, a propósito, y qué hace en su lugar."
· "No emite facturas: eso se sigue haciendo en ARCA. Lo que hace es registrar la factura y seguir su cobro y su vencimiento; por eso la auditoría avisa cuando una vence sin cobrar."
· "No entra al homebanking ni pide la clave del banco: el usuario baja el archivo de movimientos y lo sube. Lo van a ver en la demo." (El porqué está en el anexo, por si preguntan.)
· "No tiene una agenda de clientes aparte: el cliente se carga en cada factura y en cada ingreso."
· "No es para quien vende productos: no maneja stock. Está pensado para quien presta servicios."
Cierre: "Quedaron afuera para que el alcance entrara en el tiempo del proyecto. Facturar desde el sistema y conectarse con el banco quedan como trabajo futuro."
Respaldo: la tesis los fija en "Límites del prototipo": la integración con la facturación electrónica del organismo recaudador, la conciliación bancaria automatizada con cuentas reales, la gestión de clientes como entidad independiente y la venta de productos.`);
kicker(s, "Hasta dónde llega");
titulo(s, "Lo que quedó afuera, a propósito");
texto(s, "Lo que el sistema no hace, y qué hace en su lugar.", { x:0.6, y:1.55, w:12, h:0.4, fontSize:15, italic:true });
[["Receipt", "Facturación electrónica de ARCA", "No emite facturas.", "Registra las que hacés en ARCA y sigue su cobro y su vencimiento."],
 ["Landmark", "Conexión directa con el banco", "No entra al homebanking ni pide tu clave.", "Subís el archivo de movimientos que te da el banco."],
 ["Users", "Gestión de clientes aparte", "No tiene una agenda de clientes.", "El cliente se carga en cada factura y en cada ingreso."],
 ["Package", "Venta de productos", "No maneja stock ni mercadería.", "Está pensado para quien presta servicios."],
].forEach((f, i) => {
  const x = 0.6 + i * 3.08, y = 2.1;
  card(s, x, y, 2.85, 3.85);
  icono(s, f[0], x + 0.2, y + 0.25, 0.7, GREY);
  s.addText(f[1], { x:x+1.05, y:y+0.2, w:1.7, h:0.8, fontFace:FH, fontSize:14.5, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addShape(pptx.ShapeType.line, { x:x+0.2, y:y+1.18, w:2.45, h:0, line:{color:BORDE, width:1} });
  s.addText("NO HACE", { x:x+0.2, y:y+1.32, w:2.45, h:0.28, fontFace:FB, fontSize:10.5, bold:true, color:ROJO, charSpacing:2, margin:0, isTextBox:true });
  texto(s, f[2], { x:x+0.2, y:y+1.6, w:2.45, h:0.75, fontSize:13.5, color:INK });
  s.addText("EN SU LUGAR", { x:x+0.2, y:y+2.4, w:2.45, h:0.28, fontFace:FB, fontSize:10.5, bold:true, color:VERDE, charSpacing:2, margin:0, isTextBox:true });
  texto(s, f[3], { x:x+0.2, y:y+2.68, w:2.45, h:1.05, fontSize:13.5 });
});
card(s, 0.6, 6.12, 12.1, 0.62, { fill:NAVY, line:NAVY, sombra:false });
icono(s, "Route", 0.75, 6.18, 0.5, MINT, "n");
texto(s, "Quedaron afuera para que el alcance entrara en el tiempo del proyecto. Facturar y conectarse con el banco son trabajo futuro.", {
  x:1.4, y:6.12, w:11.1, h:0.62, fontSize:13.5, color:WHITE, valign:"middle" });

// =============================================================================
// 3 · EL PROTOTIPO FUNCIONANDO                                  (6:50 – 32:00)
// =============================================================================

// ── El recorrido ────────────────────────────────────────────────────────────
s = slide(true, `RELOJ 6:50 · 20 s.
"Lo que pidió la cátedra ver funcionando, en este orden. El clasificador lo van a ver trabajar en la importación, y les explico cómo funciona con capturas. Y en cada parte, sus límites. Antes, un video corto con el problema y la propuesta."
El mapa (guion): cuatro tramos en vivo, con filminas en el medio. La filmina anterior a cada tramo lo anuncia abajo a la derecha.
· Tramo 1 (9:20 – 13:30): entrar (el hash, en palabras) → importar (dos rechazos y el extracto) → panel.
· Filminas del clasificador (13:30 – 19:45).
· Tramo 2 (20:15 – 21:30): auditoría → facturas, de pasada.
· Tramo 3 (22:30 – 24:00): monotributo → proyecciones. Lo pidió el profesor: no se recorta nunca.
· Tramo 4 (27:45 – 29:15): recomendaciones → reporte PDF.`);
kicker(s, "El prototipo funcionando", MINT);
titulo(s, "Lo que van a ver funcionando", true);
[["Upload", "Importación", "en vivo"], ["Brain", "Clasificador", "en vivo + capturas"], ["ScanSearch", "Auditoría", "en vivo"],
 ["Gauge", "Estado fiscal", "en vivo"], ["TrendingUp", "Proyección", "en vivo"], ["FileText", "Reporte PDF", "en vivo"]].forEach((p, i) => {
  const x = 0.6 + i * 2.05;
  icono(s, p[0], x + 0.42, 2.25, 1.05, i === 1 ? MINT : TEAL);
  s.addText(p[1], { x:x-0.1, y:3.5, w:2.1, h:0.45, fontFace:FH, fontSize:17, bold:true, color:WHITE, align:"center", margin:0, isTextBox:true });
  chip(s, p[2], x + 0.08, 4.05, 1.75, { fill:NAVY2, line: i === 1 ? MINT : TEAL, color: i === 1 ? MINT : ICE, size:11.5, h:0.38 });
  if (i < 5) flecha(s, x + 1.62, 2.6, 0.3, "2A4D6E");
});
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:5.05, w:12.1, h:1.15, fill:{color:NAVY2}, line:{color:TEAL, width:1}, rectRadius:0.1 });
texto(s, "Y en cada parte, hasta dónde llega: los límites del clasificador, del motor predictivo y de las recomendaciones.", {
  x:0.95, y:5.05, w:11.4, h:1.15, fontSize:17, color:ICE, valign:"middle" });

// ── Video ───────────────────────────────────────────────────────────────────
// El video va adentro de la filmina, a pantalla completa. Es una copia en H.264
// (la que reproducen Keynote y PowerPoint) que no se versiona en git; si falta,
// queda la filmina que lo anuncia y el video se pasa aparte.
const VIDEO = path.join(RAIZ, "video", "FreelanceControl_Institucional.mp4");
s = slide(true, `RELOJ 7:10 · VIDEO (1:43) → termina 8:53.
"Antes de verlo funcionando, un video corto con el problema y la propuesta."
El video está adentro de esta filmina, a pantalla completa. Si no arranca solo al llegar, un clic sobre el video. NO hables durante el video.
Al terminar: "Ahora, el sistema funcionando." y avanzá.
Si el video no arranca: está también en Escritorio → Defensa_FreelanceControl → 3_Video (FreelanceControl_Institucional.mp4).`);
if (fs.existsSync(VIDEO)) {
  s.background = { color:"000000" };
  const portada = "data:image/png;base64," + fs.readFileSync(path.join(CAP, "video_portada.png")).toString("base64");
  s.addMedia({ type:"video", path:VIDEO, x:0, y:0, w:13.333, h:7.5, cover:portada });
} else {
  icono(s, "Play", 0.7, 2.35, 1.3, MINT, "n");
  s.addText("VIDEO", { x:2.35, y:2.45, w:9, h:0.4, fontFace:FB, fontSize:13, bold:true, color:MINT, charSpacing:3, margin:0, isTextBox:true });
  s.addText("El problema y la propuesta, en video", { x:2.35, y:2.85, w:10.2, h:1.0, fontFace:FH, fontSize:36, bold:true, color:WHITE, margin:0, isTextBox:true });
  texto(s, "Después, el sistema funcionando.", { x:2.35, y:4.0, w:9, h:0.5, fontSize:19, color:ICE });
}

// ── Lo que trae el extracto ─────────────────────────────────────────────────
s = slide(true, `RELOJ 9:00 · 20 s, y pasás al navegador.
EN VIVO (9:20 – 13:30). Los dos rechazos suman unos 25 s: si vas atrasado, hacé solo el PDF.
· Entrar: demo@freelancecontrol.com / demo1234 → Ingresar. Mientras entrás, el hash en palabras (unos 40 s): "La base no guarda mi contraseña: guarda su hash. El hash sale de pasar la contraseña por una fórmula que va en un solo sentido: de la contraseña se llega al hash, pero del hash no se puede volver. Antes de calcularlo le suma una sal al azar, distinta para cada usuario, así dos personas con la misma contraseña quedan con hashes distintos. Para dejarme entrar, calcula el hash de lo que escribí y lo compara con el guardado. Y al entrar, me da un pase firmado que vence solo." Si piden verlo en la base: primera filmina del anexo (la terminal con los dos hashes y el comando).
· Rechazo 1: Importar CSV → recuadro → Escritorio → Defensa_FreelanceControl → 4_Demo → resumen_banco.pdf. Si el Mac lo muestra en gris, ese ya es el rechazo; si no, aparece en rojo "Solo se aceptan archivos .csv o .xlsx". "Un PDF no trae los datos en columnas."
· Rechazo 2: planilla_vacia.xlsx → Analizar archivo → "El archivo no tiene movimientos: solo se encontró el encabezado." "No guarda nada."
· El extracto: extracto_28sep_14oct.csv → Analizar archivo. "En vez de tipear gasto por gasto, lo subo. Reconoce solo cuál columna es la fecha, la descripción y el monto. Y antes de guardar me muestra qué va a hacer. Lo armamos con seis casos difíciles a propósito."
Los seis casos, una frase cada uno, de arriba abajo (la vista previa muestra solo las primeras 20 filas):
1. Lo que ya estaba (cartel amarillo, Rappi, Uber y SUBE en gris): "Los reconoce y no los guarda de nuevo: si no, septiembre quedaría inflado." No carga dos veces.
2. La plata que va y vuelve (cartel ⇄, los $ 200.000): "Me mandé plata a mi propia cuenta y volvió. Eso no es un cobro: inflaría lo facturado y me podría cambiar la categoría." Transferencia propia no es ingreso.
3. La fecha imposible (recuadro rojo, fila 22, 31/09): "No la adivina ni la corrige: deja la fila afuera y me dice por qué." No inventa datos.
4. Lo que no reconoce (coworking fila 5 y Telecentro fila 17: "Otros", lo señalás vos): "Cada gasto ya trae su categoría: es el clasificador. Los que no reconoce los manda a 'Otros' para que yo los revise." Ante la duda, Otros.
→ Confirmar.
5. Dos gastos iguales (cartel de abajo: los dos Figma, 2 y 4 de octubre): "Son nuevos, así que los guardó, pero los marcó como posible repetido. El sistema avisa; decide el usuario."
"Guardó solo lo que corresponde y me dice qué dejó afuera y por qué. Guarda todo junto o nada. Y el archivo nunca salió de esta computadora."
6. Panel (Dashboard): "Abre siempre en el mes actual. Antes de importar, octubre estaba vacío. La cuarta tarjeta es cuánto espero cobrar el mes que viene; a la derecha, la recomendación más urgente; y abajo, el aviso de alcance." En "Últimos movimientos": Grupo Delta, + $ 1.850.000 (venía con punto de miles y lo leyó bien) y el pago de la Visa, que también fue a "Otros". Dato: ingresos de octubre $ 3.460.000 = 980.000 + 630.000 + 1.850.000.
Volvé a las filminas.
Si te preguntan: ¿por qué no directo al banco? → anexo · ¿qué bancos? nueve: Galicia, Santander, BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago y Naranja X · ¿el mismo archivo dos veces? la segunda vez no entra nada nuevo · ¿un PDF renombrado a .csv? lo rechaza igual: intenta leerlo · ¿los cobros dicen "Otros"? el clasificador es de gastos; el rubro se pone en Ingresos · ¿solo 20 filas? es la muestra que pide la tesis: al confirmar se guardan todas · ¿octubre muestra un gasto menos? la comisión es del 30/09: cada movimiento va al mes de su fecha.`);
kicker(s, "Importar el extracto", MINT);
titulo(s, "Lo que trae el extracto, a propósito", true);
// Primero, los dos archivos que no son extractos (HU-07).
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:1.8, w:12.1, h:0.8, fill:{color:NAVY}, line:{color:ROJO, width:1.25}, rectRadius:0.1 });
icono(s, "FileX", 0.8, 1.9, 0.6, ROJO);
s.addText([{ text:"Antes, dos archivos que no son extractos: ", options:{ bold:true, color:WHITE } },
           { text:"un PDF y una planilla vacía. Los rechaza sin guardar nada.", options:{ color:ICE } }], {
  x:1.6, y:1.8, w:10.9, h:0.8, fontFace:FB, fontSize:15.5, valign:"middle", margin:0, isTextBox:true });
// Los seis casos, en el orden en que aparecen en la demo, y dónde se ve cada uno.
[["Copy", "Movimientos que ya estaban cargados", "vista previa"], ["ArrowLeftRight", "Plata que va y vuelve entre cuentas propias", "vista previa"],
 ["CalendarX", "Una fila con una fecha que no existe", "vista previa"], ["CircleHelp", "Gastos que el modelo no reconoce", "vista previa"],
 ["Split", "Dos gastos iguales que son nuevos", "al confirmar"], ["Calculator", "Un cobro con punto de miles", "en el panel"]].forEach((c, i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 2.85 + Math.floor(i / 2) * 1.07;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.95, h:0.9, fill:{color:NAVY2}, line:{color:TEAL, width:1}, rectRadius:0.1 });
  icono(s, c[0], x + 0.2, y + 0.14, 0.62, TEAL);
  texto(s, c[1], { x:x+1.0, y, w:3.3, h:0.9, fontSize:15, color:WHITE, valign:"middle" });
  chip(s, c[2], x + 4.4, y + 0.27, 1.37, { fill:NAVY, line:TEAL_L, color:TEAL_L, size:10.5, h:0.36 });
});
texto(s, "Antes de guardar, el sistema muestra cada caso y qué va a hacer con él.", {
  x:0.6, y:6.12, w:7.5, h:0.4, fontSize:14, italic:true, color:ICE });
enVivo(s, "entrar e importar");

// ── El clasificador ya trabajó ──────────────────────────────────────────────
// Vista previa real: la columna "Categoría" es el clasificador.
s = slide(false, `RELOJ 13:30 · 30 s. (Volviste del navegador.) Paso 1 de 6 del clasificador: el punto más importante de la tesis, acá no apures.
EL HILO: lo vieron trabajar → aprende de ejemplos → una planilla de puntos → si duda, pregunta → aprende de tus correcciones → hasta dónde llega.
SI TE QUEDÁS EN BLANCO: "Aprende de ejemplos; si duda, pregunta; y aprende de tus correcciones."
DECÍ: "Cuando importé el extracto, cada gasto llegó con su categoría y nadie la eligió: la puso el clasificador, leyendo la descripción. Los que no reconoció, como el coworking o Telecentro, no los inventó: los mandó a 'Otros' para que yo los revise. Ahora les cuento cómo lo hace."
Qué hace: lee la descripción de cada gasto y le pone la categoría solo, entre 12 posibles.
Los que no reconoce (el coworking, Telecentro, la tarjeta) los mandó a "Otros" para revisar: no inventa una categoría.
Y corre acá: "¿Por qué no ChatGPT? Habría que mandarle la descripción de cada gasto a una empresa de afuera, y ahí están los clientes, los proveedores y los hábitos del usuario."
Respaldo: de los 26 gastos nuevos del extracto, a 23 les puso categoría y 3 fueron a "Otros".`);
kicker(s, "El clasificador");
titulo(s, "El clasificador ya trabajó en la importación");
const vp = ventana(s, "importacion_vista_previa", 0.6, 1.8, 7.9);
// La columna "Categoría" de la captura (medida sobre la imagen recortada).
s.addShape(pptx.ShapeType.roundRect, { x: vp.ix + vp.iw * 0.655, y: vp.iy + vp.ih * 0.335, w: vp.iw * 0.13, h: vp.ih * 0.655,
  fill:{color:MINT, transparency:100}, line:{color:MINT, width:2.5}, rectRadius:0.06 });
[["Tags", "Cada gasto llegó con su categoría", "Nadie la eligió: la sugirió el clasificador leyendo la descripción.", MINT],
 ["CircleHelp", "Si no la reconoce, va a «Otros»", "Para que el usuario la revise. No inventa una categoría.", AMARILLO],
 ["Lock", "Corre en esta computadora", "Las descripciones de los gastos no salen a ningún servicio externo.", TEAL]].forEach((c, i) => {
  const y = 1.9 + i * 1.6;
  icono(s, c[0], 8.85, y, 0.7, c[3]);
  s.addText(c[1], { x:9.7, y:y-0.04, w:3.05, h:0.65, fontFace:FH, fontSize:15, bold:true, color:INK, margin:0, valign:"top", isTextBox:true });
  texto(s, c[2], { x:9.7, y:y + (c[1].length > 26 ? 0.66 : 0.42), w:3.05, h:0.85, fontSize:12.5 });
});

// ── Qué es un SVM ───────────────────────────────────────────────────────────
s = slide(false, `RELOJ 14:00 · 45 s. (Lo pidió el profesor: explicar bien el SVM.) Paso 2: aprende de ejemplos, no de reglas.
DECÍ: "Es aprendizaje automático. Nosotros no le escribimos reglas del tipo 'si dice Uber, es Transporte'. Le dimos 600 gastos ya clasificados, 50 de cada una de las 12 categorías, y él solo aprendió a separarlos. El algoritmo se llama SVM, máquina de vectores de soporte: los vectores de soporte son los ejemplos más difíciles, los que quedan pegados a la frontera entre dos categorías, y son los que la definen. La tesis prevé dos algoritmos: Naive Bayes para cuando hay pocos ejemplos y SVM desde cien. Como siempre arranca con esos 600, usa el SVM."
PUENTE a la que sigue: "¿Y cómo aprende a separarlos?"
· SVM = Support Vector Machine, "máquina de vectores de soporte".
· Lo que dice la tesis aprobada: meta de 70 % o más sobre 12 categorías; se logró 76 %. El código hace exactamente lo que prevé: Naive Bayes con menos de 100 ejemplos, SVM desde 100.
· ¿Qué es Naive Bayes? Cuenta qué tan seguido aparece cada palabra en cada categoría y multiplica esas probabilidades como si las palabras no tuvieran relación entre sí (por eso "ingenuo"). Anda bien con pocos datos; el SVM busca la frontera que mejor separa y con más datos gana: 76 contra 74 con los mismos 600.`);
kicker(s, "El clasificador · qué es");
titulo(s, "Un SVM aprende de ejemplos, no de reglas");
texto(s, "Ejemplos ya clasificados", { x:0.6, y:1.85, w:3.6, h:0.4, fontSize:13, bold:true, color:TEAL });
[["uber viaje a reunión", "Transporte"], ["licencia adobe mensual", "Software"], ["almuerzo con cliente", "Alimentación"], ["hosting del servidor", "Infraestructura"]].forEach((e, i) => {
  const y = 2.35 + i * 0.78;
  chip(s, e[0], 0.6, y, 2.55, { mono:true, size:11.5 });
  texto(s, "→", { x:3.2, y:y+0.02, w:0.3, h:0.4, fontSize:15, color:GREY });
  chip(s, e[1], 3.5, y, 1.6, { fill:TEAL, line:TEAL, color:WHITE, bold:true, size:11.5 });
});
flecha(s, 5.3, 3.35, 0.55);
icono(s, "Brain", 6.05, 2.75, 1.5, MINT);
s.addText("SVM", { x:5.85, y:4.35, w:1.9, h:0.45, fontFace:FH, fontSize:20, bold:true, color:INK, align:"center", margin:0, isTextBox:true });
texto(s, "máquina de vectores de soporte: aprende a separar las categorías", { x:5.45, y:4.8, w:2.7, h:0.6, fontSize:11.5, align:"center" });
flecha(s, 7.85, 3.35, 0.55);
texto(s, "Un gasto nuevo", { x:8.6, y:1.85, w:4.1, h:0.4, fontSize:13, bold:true, color:TEAL });
chip(s, "licencia jetbrains anual", 8.6, 2.75, 3.2, { mono:true, size:12 });
s.addShape(pptx.ShapeType.downArrow, { x:10.0, y:3.35, w:0.4, h:0.5, fill:{color:TEAL_L}, line:{color:TEAL_L, width:0} });
chip(s, "Software", 9.35, 4.0, 1.7, { fill:MINT, line:MINT, color:NAVY, bold:true, size:13 });
texto(s, "nadie le dijo que «jetbrains» es Software: lo dedujo de los ejemplos", { x:8.6, y:4.6, w:3.6, h:0.7, fontSize:12, italic:true, color:GREY, align:"center" });
// Qué quiere decir el nombre, y los dos algoritmos que prevé la tesis.
[["Target", "¿Por qué «vectores de soporte»?", "Son los ejemplos más difíciles, los que quedan pegados a la frontera entre dos categorías: son los que la definen."],
 ["Split", "Dos algoritmos", "La tesis prevé Naive Bayes con pocos ejemplos y SVM con muchos. Como siempre parte de la base completa, corre el SVM."]].forEach((c, i) => {
  const x = 0.6 + i * 6.15;
  card(s, x, 5.5, 5.95, 1.15, { sombra:false });
  icono(s, c[0], x + 0.22, 5.75, 0.62, TEAL);
  s.addText(c[1], { x:x+1.0, y:5.58, w:4.8, h:0.34, fontFace:FH, fontSize:14, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, c[2], { x:x+1.0, y:5.93, w:4.8, h:0.66, fontSize:12 });
});

// ── Cómo aprende: un peso por palabra y una planilla de puntos ──────────────
// Pesos TF-IDF reales de "licencia jetbrains anual" y palabras reales que más
// suman y más restan a Transporte en el modelo base.
s = slide(false, `RELOJ 14:45 · 1:00. Paso 3: cómo aprendió a separarlas. El corazón de la explicación: despacio.
DECÍ: "La computadora no entiende palabras, entiende números. Entonces hace dos cosas. Primero, le da un peso a cada palabra: pesa más una rara, como 'jetbrains', que una que aparece en todos lados, como 'pago'. Segundo, para cada categoría arma una planilla de puntos: palabras que suman y palabras que restan. En la de Transporte suman 'viaje', 'vuelo' o 'peaje', y restan 'compra' o 'impuesto'. Esos puntos no los escribió nadie: el SVM los fue ajustando mirando los 600 ejemplos, hasta que cada uno sumara más en su categoría correcta, y con la mayor ventaja posible. Cuando llega un gasto nuevo, suma sus palabras en las doce planillas, y gana la que más suma. Es como alguien nuevo en el correo: nadie le explica las reglas, pero mirando muchas cartas ya separadas aprende qué palabras van a cada caja."
PUENTE a la que sigue: "Pero ganar no alcanza: también tiene que saber si ganó con seguridad."
¿Por qué ejemplos parejos? "Si una categoría tuviera 300 ejemplos y las demás 25, el modelo aprendería a decir siempre esa, y el porcentaje mentiría."
Respaldo (modelo base):
· Pesos: licencia jetbrains 0,60 · jetbrains 0,57 · licencia 0,42 · anual 0,37. "jetbrains" pesa más que "pago" porque aparece en muchos menos ejemplos.
· Transporte suma con auto, viaje, vuelo, abono, estación (y peaje) y resta con compra, monotributo, impuesto.
· Software: licencia, antivirus, plugin, photoshop · Infraestructura: hosting, aws, servidor, ssl, cloud · Marketing: ads, seo, agencia, campaña, publicidad.
· "uber viaje": Transporte suma +0,68 y la segunda, Hardware, −0,93. Gana Transporte.`);
kicker(s, "El clasificador · cómo aprende");
titulo(s, "Cada categoría tiene su planilla de puntos");
card(s, 0.6, 1.8, 4.95, 3.95);
icono(s, "Calculator", 0.85, 2.0, 0.6, TEAL);
s.addText("1 · Cada palabra, un peso", { x:1.6, y:2.05, w:3.8, h:0.5, fontFace:FH, fontSize:17, bold:true, color:INK, margin:0, isTextBox:true });
texto(s, "La computadora entiende números. Pesa más la palabra rara, como «jetbrains», que la que aparece en todos lados.", {
  x:0.85, y:2.75, w:4.5, h:0.85, fontSize:13 });
[["licencia jetbrains", 0.60], ["jetbrains", 0.57], ["licencia", 0.42], ["anual", 0.37]].forEach((p, i) => {
  const y = 3.72 + i * 0.48;
  s.addText(p[0], { x:0.85, y, w:1.85, h:0.38, fontFace:FM, fontSize:11, color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addShape(pptx.ShapeType.rect, { x:2.75, y:y+0.06, w:2.55, h:0.26, fill:{color:PISTA}, line:{color:PISTA, width:0} });
  s.addShape(pptx.ShapeType.rect, { x:2.75, y:y+0.06, w:2.55 * p[1] / 0.62, h:0.26, fill:{color: i < 2 ? MINT : TEAL_L}, line:{color: i < 2 ? MINT : TEAL_L, width:0} });
});
card(s, 5.8, 1.8, 6.9, 3.95);
icono(s, "ClipboardList", 6.05, 2.0, 0.6, MINT);
s.addText("2 · Una planilla de puntos por categoría", { x:6.8, y:2.05, w:5.8, h:0.5, fontFace:FH, fontSize:17, bold:true, color:INK, margin:0, isTextBox:true });
texto(s, "Arranca en cero y, mirando los ejemplos, ajusta qué palabras suman y cuáles restan: que cada uno gane en su categoría, con la mayor ventaja posible.", {
  x:6.05, y:2.58, w:6.45, h:0.74, fontSize:12.5 });
// La planilla de Transporte: dos columnas, lo que suma y lo que resta.
s.addShape(pptx.ShapeType.roundRect, { x:6.05, y:3.35, w:3.75, h:2.2, fill:{color:"F7FAFD"}, line:{color:BORDE, width:1}, rectRadius:0.06 });
texto(s, "Transporte", { x:6.25, y:3.45, w:3.4, h:0.35, fontSize:14, bold:true, color:INK, fontFace:FH });
linea(s, 6.25, 3.85, 9.6, 3.85, { color:BORDE, width:1 });
texto(s, "suman", { x:6.25, y:3.92, w:1.6, h:0.28, fontSize:11, bold:true, color:VERDE });
texto(s, "restan", { x:8.05, y:3.92, w:1.6, h:0.28, fontSize:11, bold:true, color:ROJO });
["viaje", "vuelo", "auto", "abono", "peaje"].forEach((p, i) =>
  s.addText([{ text:"+ ", options:{ bold:true, color:VERDE } }, { text:p, options:{ color:INK } }], {
    x:6.25, y:4.22 + i * 0.255, w:1.6, h:0.255, fontFace:FB, fontSize:12, margin:0, valign:"middle", isTextBox:true }));
["compra", "impuesto", "monotributo"].forEach((p, i) =>
  s.addText([{ text:"− ", options:{ bold:true, color:ROJO } }, { text:p, options:{ color:INK } }], {
    x:8.05, y:4.22 + i * 0.255, w:1.6, h:0.255, fontFace:FB, fontSize:12, margin:0, valign:"middle", isTextBox:true }));
// Un gasto nuevo: suma sus palabras en cada planilla y gana la que más suma.
texto(s, "Un gasto nuevo", { x:10.1, y:3.38, w:2.4, h:0.3, fontSize:12, bold:true, color:TEAL, align:"center" });
chip(s, "uber viaje", 10.2, 3.72, 2.2, { mono:true, size:12, h:0.4 });
s.addShape(pptx.ShapeType.downArrow, { x:11.12, y:4.2, w:0.36, h:0.4, fill:{color:TEAL_L}, line:{color:TEAL_L, width:0} });
chip(s, "Transporte", 10.3, 4.68, 2.0, { fill:MINT, line:MINT, color:NAVY, bold:true, size:12.5, h:0.4 });
texto(s, "suma sus palabras en cada planilla: gana la que más suma", { x:9.95, y:5.12, w:2.7, h:0.45, fontSize:10.5, italic:true, color:GREY, align:"center" });
// La analogía del correo.
card(s, 0.6, 5.95, 12.1, 0.75, { fill:NAVY, line:NAVY, sombra:false });
icono(s, "Mail", 0.8, 6.04, 0.56, MINT, "n");
texto(s, "Como alguien nuevo en el correo: nadie le da reglas; mirando muchas cartas ya separadas, aprende qué palabras van a cada caja.", {
  x:1.6, y:5.95, w:10.9, h:0.75, fontSize:14, color:WHITE, valign:"middle" });

// ── Cuándo duda: por cuánto le ganó a la segunda ───────────────────────────
// Puntajes reales (decision_function) del modelo base, desplazados para dibujarlos.
// "telecentro internet fibra" es el Telecentro que en la importación fue a "Otros".
s = slide(false, `RELOJ 15:45 · 45 s. Paso 4: cuándo duda. Si casi empatan, va a "Otros".
DECÍ: "La seguridad la medimos como en una elección: no importa cuántos votos sacó el ganador, importa por cuánto le ganó al segundo. En 'uber viaje', Transporte le gana por mucho a la segunda: está seguro y lo guarda. En 'telecentro internet fibra' no conoce ninguna de esas palabras y las dos primeras casi empatan: entonces no adivina, lo manda a 'Otros' para revisar. Es el Telecentro que vieron en la importación. Preferimos una revisión antes que una categoría equivocada."
PUENTE a la que sigue: "Y cuando el usuario corrige, el sistema aprende."
Los números, si los piden (modelo base): "uber viaje": Transporte +0,68 le gana lejos a Hardware −0,93 → 80 % de seguridad. "telecentro internet fibra": Hardware −0,77 y Transporte −0,79 → empate técnico, 2 %, va a "Otros". La vara está en 30 %.`);
kicker(s, "El clasificador · cuándo duda");
titulo(s, "La seguridad: por cuánto le ganó a la segunda");
icono(s, "Vote", 0.6, 1.62, 0.42, TEAL);
texto(s, "Como en una elección: importa por cuánto le ganó al segundo. Si gana por poco, no adivina: pide revisión.", {
  x:1.15, y:1.62, w:11.5, h:0.42, fontSize:14.5, italic:true, valign:"middle" });
const casos = [["uber viaje", [["Transporte", 0.68], ["Hardware", -0.93], ["Marketing", -0.94], ["Infraestructura", -0.94], ["Capacitación", -0.95]],
                "Ganó por mucho: está seguro", "Transporte", MINT],
               ["telecentro internet fibra", [["Hardware", -0.77], ["Transporte", -0.79], ["Servicios", -0.80], ["Otros", -0.82], ["Infraestructura", -0.82]],
                "Casi empatan: se recuenta", "«Otros», a revisión", AMARILLO]];
casos.forEach((c, k) => {
  const x0 = 0.6 + k * 6.2;
  card(s, x0, 2.2, 5.9, 4.4);
  chip(s, c[0], x0 + 0.3, 2.38, 3.4, { mono:true, size:12 });
  const base = 3.1, alto = 1.95, ancho = 0.72;
  c[1].forEach((b, i) => {
    const h = alto * (b[1] + 1.2) / 2.05, x = x0 + 0.45 + i * 1.05, y = base + alto - h;
    const col = i === 0 ? c[4] : (i === 1 ? TEAL_L : PISTA);
    s.addShape(pptx.ShapeType.rect, { x, y, w:ancho, h, fill:{color:col}, line:{color:col, width:0} });
    s.addText(b[0], { x:x-0.2, y:base+alto+0.07, w:ancho+0.4, h:0.32, fontFace:FB, fontSize:9.5, color:TEXTO, align:"center", margin:0, isTextBox:true });
  });
  // La distancia entre la primera y la segunda.
  const h1 = alto * (c[1][0][1] + 1.2) / 2.05, h2 = alto * (c[1][1][1] + 1.2) / 2.05;
  const xb = x0 + 0.45 + ancho + 0.08, yTop = base + alto - h1;
  linea(s, x0 + 0.45, yTop, x0 + 0.45 + 2 * 1.05 - 0.05, yTop, { color:INK, width:1, dashType:"dash" });
  if (k === 0) {
    linea(s, xb + 0.2, yTop, xb + 0.2, base + alto - h2, { color:ROJO, width:2.5 });
    texto(s, "le ganó por mucho", { x:xb + 0.32, y:yTop + (h1 - h2) / 2 - 0.14, w:1.7, h:0.28, fontSize:10.5, bold:true, color:ROJO });
  } else {
    texto(s, "casi la misma altura", { x:x0 + 0.45, y:yTop - 0.36, w:2.4, h:0.28, fontSize:10.5, bold:true, color:ROJO });
  }
  s.addText(c[2], { x:x0 + 0.3, y:5.55, w:5.3, h:0.42, fontFace:FH, fontSize:16, bold:true, color:INK, margin:0, isTextBox:true });
  s.addText([{ text:"Resultado: ", options:{ color:TEXTO } }, { text:c[3], options:{ bold:true, color: k ? "9A6B00" : VERDE } }], {
    x:x0 + 0.3, y:6.0, w:5.3, h:0.4, fontFace:FB, fontSize:14, margin:0, isTextBox:true });
});

// ── Aprende de las correcciones ─────────────────────────────────────────────
// Capturas del 14/10 simulado (después de importar, con el modelo propio):
// "mostaza" → Otros 1 %; se corrige a Alimentación; "mostaza palermo", que nunca
// se le enseñó, da Alimentación 73 % después del reentrenamiento de fondo.
s = slide(false, `RELOJ 16:30 · 45 s. Paso 5: cómo aprende, de tus correcciones.
DECÍ: "En el extracto, muchos gastos vienen solo con el nombre del comercio. 'Mostaza' el modelo nunca la vio, así que la manda a 'Otros'. La corrijo a Alimentación, y la corrección vale al instante. Además, de fondo y sin trabar la pantalla, el modelo se vuelve a entrenar. Por eso 'mostaza palermo', que nunca le enseñé, ahora va sola a Alimentación: aprendió la palabra, no solo la frase. Y cada usuario tiene su propio modelo: la base más sus gastos."
PUENTE a la que sigue: "Y, como pidió la cátedra, hasta dónde llega."
1. "mostaza" → Otros, 1 %: ninguna de sus palabras estaba en lo que aprendió.
2. La corregís a Alimentación: desde ese momento, esa descripción da Alimentación ("Corrección tuya", 100 %), aunque la escribas con mayúsculas o espacios de más.
3. El reentrenamiento de fondo: "mostaza palermo" pasó de Otros (1 %) a Alimentación (73 %). Supera la vara del 30 %: se guarda sin pedir revisión.
Si te preguntan "¿por qué 73 y no 100?": "Es una sola corrección contra casi setecientos ejemplos: el modelo no se da vuelta por un solo dato, y eso es sano. La frase exacta que corregí sí da 100 %. Y sube con cada gasto de Mostaza que cargue: con uno más, 78 %; con dos, 81 %."
El modelo propio: todos arrancan con el de base (600 ejemplos). A los 20 gastos, el sistema le entrena uno propio: los 600 más los suyos; después se reentrena cada 10 gastos nuevos o con cada corrección, de a uno por usuario. Los datos de cada usuario entrenan solo su modelo: nunca se mezclan.
OJO: por eso, después de importar, la pantalla del Clasificador dice 78 % y no 76. La usuaria pasó los 20 gastos y tiene su modelo propio (600 de base + sus 91 gastos). El 76 es el modelo de base, el de la tesis.
Si te preguntan: ¿un usuario nuevo tiene que entrenarlo? "No. Desde el primer día usa el modelo de 600 ejemplos; lo único que hace es corregir lo que cae en 'Otros'."`);
kicker(s, "El clasificador · en la aplicación");
titulo(s, "Aprende de las correcciones del usuario");
texto(s, "En el extracto, muchos gastos vienen solo con el nombre del comercio.", { x:0.6, y:1.55, w:12.1, h:0.38, fontSize:14.5, italic:true });
[["clasif_mostaza", "1 · Duda", "«mostaza» va a «Otros»: nunca vio esa palabra."],
 ["clasif_mostaza_corregido", "2 · La corregís", "La pasás a «Alimentación». Vale al instante."],
 ["clasif_mostaza_palermo_despues", "3 · Aprendió", "«mostaza palermo», que nunca le enseñaste, ya va a «Alimentación»."]].forEach((c, i) => {
  const x = 0.6 + i * 4.18;
  ventana(s, c[0], x, 2.0, 3.75);
  s.addText(c[1], { x, y:4.65, w:3.75, h:0.45, fontFace:FH, fontSize:18, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, c[2], { x, y:5.12, w:3.75, h:0.7, fontSize:14 });
  if (i < 2) flecha(s, x + 3.8, 3.05, 0.33);
});
card(s, 0.6, 5.9, 12.1, 0.8, { fill:NAVY, line:NAVY, sombra:false });
icono(s, "RefreshCw", 0.8, 6.03, 0.54, MINT, "n");
texto(s, "La corrección vale al instante. Y de fondo, sin trabar la pantalla, el modelo propio del usuario se vuelve a entrenar con ella: aprende la palabra, no solo la frase.", {
  x:1.55, y:5.9, w:10.95, h:0.8, fontSize:14, color:WHITE, valign:"middle" });

// ── Los límites del clasificador ────────────────────────────────────────────
s = slide(true, `RELOJ 17:15 · 45 s (más 15 s por los desafíos y 20 s por la frase del examen, si las decís). LO PIDIÓ LA CÁTEDRA: límites del clasificador. Cierra el clasificador: terminás entre 18:00 y 18:35, y vas a la auditoría con tiempo de sobra (no lo llenes).
SI QUERÉS NOMBRAR LOS DESAFÍOS (15 s; los pidió el profesor en la 3.ª entrega, la filmina está en el anexo): "Llegar a esto costó: pocos ejemplos de base, que supiera cuándo duda y reentrenar sin trabar la pantalla. Si quieren, los tengo en el anexo."
SI QUERÉS DECIR CÓMO SE MIDIÓ EL 76 % (20 s; si piden verlo, anexo, filmina 36, con el comando): "¿Cómo sabemos que acierta el 76 %? No lo medimos con los gastos con los que aprendió, porque esos se los sabe de memoria. Sería como un examen con las mismas preguntas que se dieron en clase: todos se sacan 10. Por eso lo probamos con gastos que nunca había visto. Y para que no fuera suerte, lo hicimos cinco veces, cada vez con otros gastos, y sacamos el promedio. Dio 76 %, y la meta era 70."
DECÍ: "No acierta siempre: tres de cada cuatro. Por eso la revisión es parte del diseño, no un parche. Entiende palabras, no contexto: 'diseño de logo' puede ser Marketing o Servicios, y el modelo no sabe para qué fue el logo. Las doce categorías son fijas: lo que no encaja va a 'Otros'. Y los ejemplos de base los armamos nosotros: sumar datos reales de usuarios es trabajo futuro."
PUENTE a la que sigue: "Del clasificador paso a la auditoría, que revisa los registros sola."
· Acierta 3 de cada 4 (medido con validación cruzada). Por eso existe la revisión: no es un parche, es parte del diseño. Y se puede probar: está en el anexo (filmina 36), con el comando para correrlo.
· Entiende palabras, no contexto: "diseño de logo" puede ser Marketing o Servicios; comparten vocabulario y ahí es donde más se confunde (Marketing es la categoría más floja).
· Las 12 categorías son fijas: lo que no encaja va a "Otros". (Software, Hardware, Infraestructura, Marketing, Servicios, Capacitación, Suscripciones, Transporte, Alimentación, Impuestos, Monotributo y Otros.)
· Los ejemplos de base los armamos nosotros: sumar datos reales de usuarios es trabajo futuro.
Límite honesto si preguntan: un gasto importado que quedó en "Otros" y nadie revisó entra al reentrenamiento como "Otros".`);
kicker(s, "El clasificador · hasta dónde llega", MINT);
titulo(s, "Los límites del clasificador", true);
[["Target", "No acierta siempre", "Por eso existe la revisión: es parte del diseño. Y se puede probar."],
 ["MessageSquare", "Entiende palabras, no contexto", "Si dos categorías comparten vocabulario, puede confundirlas."],
 ["List", "Las categorías son fijas", "Lo que no encaja en ninguna va a «Otros»."],
 ["Hand", "Los ejemplos de base los armamos nosotros", "Sumar datos reales de usuarios es trabajo futuro."]].forEach((l, i) => {
  const y = 1.9 + i * 1.18;
  icono(s, l[0], 0.6, y, 0.78, TEAL);
  s.addText(l[1], { x:1.6, y:y-0.02, w:5.8, h:0.42, fontFace:FH, fontSize:17, bold:true, color:WHITE, margin:0, isTextBox:true });
  texto(s, l[2], { x:1.6, y:y+0.42, w:5.8, h:0.5, fontSize:13.5, color:ICE });
});
s.addShape(pptx.ShapeType.roundRect, { x:7.9, y:1.9, w:4.8, h:4.5, fill:{color:NAVY2}, line:{color:TEAL, width:1}, rectRadius:0.12 });
texto(s, "Un ejemplo de contexto", { x:8.2, y:2.1, w:4.2, h:0.4, fontSize:13, bold:true, color:TEAL_L });
chip(s, "diseño de logo", 8.95, 2.75, 2.7, { mono:true, size:13, fill:WHITE });
linea(s, 10.3, 3.2, 9.15, 4.25, { color:TEAL_L, width:2 });
linea(s, 10.3, 3.2, 11.45, 4.25, { color:TEAL_L, width:2 });
chip(s, "¿Marketing?", 8.15, 4.3, 2.0, { fill:NAVY, line:AMARILLO, color:AMARILLO, bold:true, size:13 });
chip(s, "¿Servicios?", 10.45, 4.3, 2.0, { fill:NAVY, line:AMARILLO, color:AMARILLO, bold:true, size:13 });
texto(s, "Las dos categorías usan las mismas palabras. El modelo no sabe para qué fue el logo.", {
  x:8.2, y:5.05, w:4.2, h:1.1, fontSize:13, color:ICE });

// ── La auditoría ────────────────────────────────────────────────────────────
s = slide(false, `RELOJ 19:45 · 30 s, y pasás al navegador.
Qué hace: revisa todos tus registros con cinco controles y te avisa lo que parece raro. Avisa, no corrige sola.
Los cinco, de corrido: gastos repetidos, gastos irregulares, facturas vencidas, cuota del monotributo sin pagar y transferencias entre cuentas propias.
EN VIVO (20:15 – 21:30): Auditoría → Ejecutar auditoría → 5 alertas. "La auditoría es la que revisa por mí lo que nadie revisa. No corre sola: corre cuando aprieto este botón. Encontró cinco cosas."
1. Figma repetido: "Mismo monto, misma categoría y pocos días de diferencia. Puedo eliminar el repetido o, si fueron dos compras de verdad, marcarlo como resuelto, y no vuelve a aparecer."
2. Adobe repetido: "Este es de junio. Lo encuentra aunque sea viejo."
3. El servidor de julio: "Un gasto irregular: mucho más alto de lo que esa categoría suele gastar. En la filmina que sigue les explico cómo lo mide."
4. Dos facturas vencidas (Consultora Aurora y Brand Studio): "Brand Studio en realidad pagó, y vino en el extracto. Pero cruzar los cobros del banco con las facturas quedó fuera del alcance: la marca pagada el usuario. Es un límite, y lo digo."
5. Lo que no aparece: "No aparece la cuota del monotributo porque vino pagada en el extracto. Ni la transferencia a mi propia cuenta, porque la frenó la importación. Los módulos se hablan entre sí."
Bajá un poco y señalá el aviso de alcance al pie.
FACTURAS, de pasada (15 s): menú Facturas. Señalá verde (pagadas), amarillo (Tienda Sur y Acme) y rojo (Consultora Aurora y Brand Studio). "Las facturas las cargo a mano: cliente, monto, emisión y vencimiento. Amarilla mientras está en plazo; roja si venció sin cobrarse, y eso lo cambia el sistema solo; verde cuando la marco pagada. Las rojas son las que acaba de encontrar la auditoría."
NO toques Resolver, Eliminar ni "Marcar pagada": cambia lo que después muestran las Recomendaciones.
Si te preguntan: ¿marcarla pagada crea un ingreso? No, a propósito: el cobro ya entra con el extracto y se contaría dos veces · ¿se puede editar una pagada? No: ni se edita ni se borra (lo pide la tesis).
Volvé a las filminas.`);
kicker(s, "Auditoría");
titulo(s, "La auditoría revisa los registros sola, y avisa");
[["Copy", "Gastos repetidos", "Mismo monto y categoría, con pocos días de diferencia."],
 ["Activity", "Gastos irregulares", "Mucho más altos de lo que su categoría suele moverse."],
 ["CalendarX", "Facturas vencidas", "Emitidas y sin cobrar después del vencimiento."],
 ["BadgeDollarSign", "Cuota del monotributo", "El mes sin la cuota cubierta."],
 ["ArrowLeftRight", "Transferencias propias", "Plata que fue y volvió entre cuentas del usuario."]].forEach((c, i) => {
  const x = 0.6 + i * 2.45;
  card(s, x, 1.95, 2.25, 3.0);
  icono(s, c[0], x + 0.68, 2.2, 0.9, [AMARILLO, ROJO, ROJO, TEAL, TEAL_L][i], i === 0 ? "n" : "b");
  s.addText(c[1], { x:x+0.12, y:3.25, w:2.0, h:0.62, fontFace:FH, fontSize:14.5, bold:true, color:INK, align:"center", valign:"top", margin:0, isTextBox:true });
  texto(s, c[2], { x:x+0.15, y:3.9, w:1.95, h:1.0, fontSize:11.5, align:"center" });
});
card(s, 0.6, 5.25, 7.5, 1.15, { fill:NAVY, line:NAVY });
icono(s, "Hand", 0.85, 5.48, 0.7, MINT, "n");
texto(s, "Avisa, no corrige: cada alerta la resuelve el usuario. El sistema no decide que algo sea un error.", {
  x:1.75, y:5.25, w:6.15, h:1.15, fontSize:14.5, color:WHITE, valign:"middle" });
enVivo(s, "la auditoría y las facturas");

// ── ¿Qué es un gasto irregular? ─────────────────────────────────────────────
// Los gastos de Infraestructura de los últimos seis meses (datos de la demo):
// la forma es real, sin cifras. Promedio y vara calculados como la auditoría.
s = slide(false, `RELOJ 21:30 · 1:00. (Volviste del navegador.)
DECÍ: "El sistema compara cada gasto con los de su misma categoría de los últimos seis meses. Saca el promedio y cuánto se suelen mover esos gastos alrededor del promedio, que se llama desvío. Si un gasto se pasa del promedio por más de dos desvíos, lo marca como irregular."
La boleta de luz (panel de la derecha): "Si tu boleta siempre viene parecida, una un poco más alta te llama la atención. Si tu boleta varía mucho entre invierno y verano, esa misma boleta es normal. Por eso la vara no es fija: se ajusta sola a cada categoría."
Para cerrar: "Solo marca gastos más altos de lo normal, y necesita historia: al menos seis gastos de esa categoría. Y en esa alerta no hay botón de borrar, a propósito: un gasto alto puede ser real, como comprar un servidor caro."
Palabras clave: se compara con su propia categoría · la vara se ajusta sola · boleta de luz · señal, no acusación.
Respaldo: 10 gastos de Infraestructura; promedio $ 170.100; desvío $ 258.358; vara $ 686.816 (2 desvíos, no "2,8 veces"); el servidor de $ 900.000 quedó 2,8 desvíos arriba. Por qué 2 desvíos: cuando los gastos se comportan normal, casi todos (unos 95 de cada 100) caen dentro.
EN VIVO (22:30 – 24:00). Lo pidió el profesor en la 4.ª entrega: NO se recorta nunca.
· MONOTRIBUTO, de arriba abajo: la franja verde (cuota de octubre pagada) · la barra roja (lo facturado hasta hoy contra el tope de la G) · la tarjeta Diciembre 2026 · el recuadro rojo ("superarías el límite en diciembre", categoría H) · el aviso al pie.
"El sistema no mira solo lo que ya cobré: suma lo cobrado más lo que espera cobrar hasta diciembre, y lo compara con el tope de mi categoría. A este ritmo me pasaría en diciembre, y la categoría que cubriría esa facturación es la H. No dice 'te pasaste': dice cuándo te pasarías. Esa es la respuesta a la pregunta del trabajo: anticipar el riesgo, no solo registrarlo."
"La cuota de octubre figura pagada porque vino en el extracto. Y el aviso lo deja claro: la categoría la define ARCA, y la decisión es del usuario con su contador."
· PROYECCIONES: esperá unos 2 s a que se anime el gráfico. Señalá el punto hueco de octubre y la franja de noviembre.
"El sistema mira lo que cobré cada mes cerrado, la línea blanca, y estima los próximos seis, la línea azul. La azul no es el promedio: es hacia dónde vienen yendo mis cobros. No da un solo número: da un rango, entre un escenario pesimista, en rojo, y uno optimista, en verde."
"Octubre aparece hueco porque el mes no terminó: si lo usara por la mitad, tiraría la proyección para abajo. Y el rango es ancho porque esta freelancer alterna meses muy buenos con meses flojos. El sistema no lo esconde: lo muestra."
Volvé a las filminas.`);
kicker(s, "Auditoría · el control más fino");
titulo(s, "¿Qué es un gasto irregular?");
card(s, 0.6, 1.85, 7.2, 4.6);
texto(s, "Los gastos de una categoría en los últimos meses", { x:0.9, y:2.0, w:6.6, h:0.35, fontSize:13, bold:true, color:INK });
const infra = [101, 72, 104, 108, 900, 112, 115, 35, 118, 36];
const prom = 170.1, vara = 686.8, tope = 960;
const gx = 1.0, gy = 2.55, gw = 6.0, gh = 3.5, bw = gw / infra.length;
infra.forEach((v, i) => {
  const h = gh * v / tope, col = v > vara ? ROJO : TEAL_L;
  s.addShape(pptx.ShapeType.rect, { x:gx + i * bw + 0.08, y:gy + gh - h, w:bw - 0.16, h, fill:{color:col}, line:{color:col, width:0} });
});
const yProm = gy + gh - gh * prom / tope, yVara = gy + gh - gh * vara / tope;
linea(s, gx, yProm, gx + gw, yProm, { color:INK, width:1.5 });
linea(s, gx, yVara, gx + gw, yVara, { color:ROJO, width:2, dashType:"dash" });
linea(s, gx, gy + gh, gx + gw, gy + gh, { color:GREY, width:1 });
texto(s, "el promedio", { x:gx + 5.0, y:yProm - 0.32, w:1.1, h:0.28, fontSize:11, bold:true, color:INK, align:"right" });
texto(s, "la vara: promedio + dos desvíos", { x:gx + gw - 2.85, y:yVara - 0.34, w:2.85, h:0.3, fontSize:11, bold:true, color:ROJO, align:"right" });
texto(s, "un servidor de julio", { x:gx + 5 * bw - 0.02, y:gy + 0.05, w:1.8, h:0.3, fontSize:11, bold:true, color:ROJO });
// La boleta de luz: la misma boleta, dos historias.
card(s, 8.1, 1.85, 4.6, 4.6, { fill:NAVY, line:NAVY });
texto(s, "La boleta de luz", { x:8.4, y:2.0, w:4.0, h:0.4, fontSize:16, bold:true, color:WHITE, fontFace:FH });
[["Si siempre viene parecida…", [30, 32, 35, 31, 33, 34], 36.3, "…una más alta llama la atención"],
 ["Si cambia mucho mes a mes…", [10, 60, 15, 55, 20, 40], 75.5, "…la misma boleta es normal"]].forEach((b, k) => {
  const y0 = 2.5 + k * 2.0, bx = 8.4, bh = 1.05, max = 80;
  texto(s, b[0], { x:bx, y:y0, w:4.0, h:0.3, fontSize:12, color:ICE });
  b[1].concat([50]).forEach((v, i) => {
    const h = bh * v / max, nueva = i === 6, col = nueva ? (k === 0 ? ROJO : MINT) : "4F7393";
    s.addShape(pptx.ShapeType.rect, { x:bx + 0.15 + i * 0.55, y:y0 + 0.35 + bh - h, w:0.38, h, fill:{color:col}, line:{color:col, width:0} });
  });
  const yv = y0 + 0.35 + bh - bh * Math.min(b[2], max) / max;
  linea(s, bx + 0.05, yv, bx + 3.95, yv, { color:AMARILLO, width:1.5, dashType:"dash" });
  texto(s, b[3], { x:bx, y:y0 + 1.45, w:4.1, h:0.3, fontSize:12, bold:true, color: k === 0 ? "F08A8A" : MINT });
});
s.addText([{ text:"Una señal para revisar, no una acusación: ", options:{ bold:true, color:INK } },
           { text:"un gasto alto puede ser real.", options:{ color:TEXTO } }], {
  x:0.6, y:6.62, w:7.6, h:0.42, fontFace:FB, fontSize:13.5, valign:"middle", margin:0, isTextBox:true });
enVivo(s, "monotributo y proyecciones");

// ── El semáforo del monotributo ─────────────────────────────────────────────
// Proporciones reales del 14/10: lo cobrado en el año (incluido octubre) y lo
// que se espera hasta diciembre, contra el tope de la categoría G.
s = slide(false, `RELOJ 24:00 · 1:15. (Volviste del navegador. LO PIDIÓ EL PROFESOR: topes del monotributo.)
DECÍ: "El semáforo responde una sola pregunta: ¿cuánto voy a haber facturado el 31 de diciembre? Es como un viaje de Córdoba a Rosario: el largo del viaje es lo que voy a haber facturado a fin de año; lo recorrido es lo que ya cobré. La barra muestra lo recorrido; el semáforo mira el viaje entero."
· Lo que vas a haber facturado = lo que ya cobraste + lo que se espera cobrar hasta diciembre (lo estima la proyección). Se compara con el tope de tu categoría.
· El semáforo, en criollo: verde, lejos del tope · amarillo, cerca · rojo, a este ritmo te pasarías.
· No dice "te pasaste": dice CUÁNDO te pasarías (diciembre) y qué categoría cubriría esa facturación (la H).
Respaldo: facturado real 75,5 %; con lo esperado hasta diciembre, 109,4 % → rojo; verde < 70 %, amarillo 70–90 %, rojo > 90 %. Anual = cobrado + lo que falta de lo esperado en octubre + noviembre + diciembre = 59,09 M contra un tope de 54,0 M.
Si te preguntan:
· ¿Por qué no se movió el porcentaje al importar? "Lo que cobré en octubre ya estaba previsto. Al importar, esa plata pasó de 'esperada' a 'cobrada', y el total del año quedó igual. Se movió lo recorrido, no el largo del viaje." (anexo)
· ¿La escala de ARCA se actualiza sola? "No, pero tampoco hay que tocar el cálculo: la escala es un dato con su fecha. ARCA no ofrece una forma oficial de leerla con un programa, y cambia dos veces por año. Cargarla lleva minutos, y la de agosto entró así." (anexo)`);
kicker(s, "Estado fiscal");
titulo(s, "El semáforo mide el largo del viaje, no lo recorrido");
// La barra del año: cobrado (recorrido) + esperado (lo que falta), contra el tope.
const tramos = [[37.3 + 3.46, TEAL, "lo que ya cobraste"], [3.64 + 7.10 + 7.59, TEAL_L, "lo que se espera hasta diciembre"]];
const total = 59.09, topeG = 54.0, ax = 0.9, aw = 11.3, ay = 2.35, ah = 0.75;
let acc = 0;
tramos.forEach(t => {
  const w = aw * t[0] / total;
  s.addShape(pptx.ShapeType.rect, { x:ax + aw * acc / total, y:ay, w, h:ah, fill:{color:t[1]}, line:{color:WHITE, width:1.5} });
  texto(s, t[2], { x:ax + aw * acc / total, y:ay + ah + 0.1, w, h:0.35, fontSize:13, bold:true, color:t[1] === TEAL ? TEAL : "3D8FA0", align:"center" });
  acc += t[0];
});
icono(s, "Car", ax + aw * (37.3 + 3.46) / total - 0.31, ay + 0.065, 0.62, NAVY);
const xTope = ax + aw * topeG / total;
linea(s, xTope, ay - 0.35, xTope, ay + ah, { color:ROJO, width:2.5 });
texto(s, "el tope de tu categoría", { x:xTope - 3.0, y:ay - 0.42, w:2.9, h:0.3, fontSize:12, bold:true, color:ROJO, align:"right" });
texto(s, "lo que vas a haber facturado el 31 de diciembre", { x:ax, y:ay - 0.42, w:5.0, h:0.3, fontSize:12, bold:true, color:INK });
ventana(s, "monotributo_semaforo", 0.6, 3.75, 6.6);
[["Verde", "lejos del tope", VERDE], ["Amarillo", "cerca del tope", AMARILLO], ["Rojo", "a este ritmo te pasarías", ROJO]].forEach((c, i) => {
  const y = 3.8 + i * 0.62;
  s.addShape(pptx.ShapeType.ellipse, { x:7.6, y:y + 0.04, w:0.38, h:0.38, fill:{color:c[2]}, line:{color:c[2], width:0} });
  s.addText([{ text:c[0] + "  ", options:{ bold:true, color:INK } }, { text:c[1], options:{ color:TEXTO } }], {
    x:8.15, y, w:4.5, h:0.46, fontFace:FB, fontSize:14.5, valign:"middle", margin:0, isTextBox:true });
});
card(s, 7.6, 5.75, 5.1, 0.85, { fill:NAVY, line:NAVY, sombra:false });
texto(s, "No dice «te pasaste»: dice cuándo te pasarías. Qué hacer lo decide el usuario con su contador.", {
  x:7.85, y:5.75, w:4.7, h:0.85, fontSize:13, color:WHITE, valign:"middle" });

// ── Prophet, en criollo ─────────────────────────────────────────────────────
s = slide(false, `RELOJ 25:15 · 45 s. (LO PIDIÓ EL PROFESOR: reportes predictivos.)
EL HILO: separa la historia en capas → con eso arma tres escenarios → y tiene límites claros.
SI TE QUEDÁS EN BLANCO: "Mira hacia dónde van mis cobros y me da un rango, no un número."
DECÍ: "La proyección que vieron en vivo la hace Prophet, una herramienta gratuita de Meta, la empresa de Facebook, pensada para pronosticar números que cambian con el tiempo. Separa la historia en capas, como los instrumentos de una canción: la tendencia, hacia dónde van mis cobros; la estacionalidad, lo que se repite cada año; y el ruido, el sube y baja sin patrón. La estacionalidad Prophet la enciende solo cuando hay dos años de historia; esta freelancer tiene nueve meses, así que trabaja con la tendencia y el ruido. No viene entrenado: cada vez que cambian los cobros, se ajusta con los de esta usuaria. Usa un solo dato: cuánto cobró en cada mes cerrado. El mes en curso no entra, porque todavía no terminó."
PUENTE a la que sigue: "Con esas capas arma los tres escenarios."
Si lo entrenamos: "No viene entrenado de fábrica y no le dimos datos nuestros. Cada vez que cambian los cobros, o empieza un mes, toma los cobros de esta usuaria y se ajusta en el momento, en un segundo, en la computadora. Usa un solo dato: el total cobrado en cada mes cerrado. Nada de gastos, ni inflación, ni datos de otras personas, ni internet."
Cuánta historia necesita: "Con poca historia, menos de diez cobros o menos de tres meses cerrados, no usa Prophet: proyecta el promedio de los últimos tres meses, una línea plana, y la pantalla lo dice. Esta freelancer tiene 27 cobros en nueve meses, así que corre Prophet."
Si te preguntan "¿nunca mide la estacionalidad?": "Con esta historia, no. Prophet la enciende solo cuando los datos cubren dos años: el código no la apaga, la decide Prophet. Con nueve meses, la proyección es tendencia más vaivén. Lo probamos: con 24 meses todavía no la usa; con 25, sí."
Respaldo: Taylor y Letham (2018). Con los mismos datos da siempre lo mismo (el azar va con semilla fija). La tesis describe Prophet con sus tres capas (tendencia, estacionalidad y ruido).`);
kicker(s, "Proyección · cómo funciona");
titulo(s, "Prophet separa tu historia en capas");
texto(s, "Prophet, de Meta: pronostica números que cambian con el tiempo.", { x:0.6, y:1.58, w:7.3, h:0.34, fontSize:14, bold:true, color:INK });
texto(s, "Separa tu historia como una canción en sus instrumentos:", { x:0.6, y:1.92, w:7.3, h:0.32, fontSize:13.5, italic:true });
const capas = [["TrendingUp", "Tendencia", "Hacia dónde va: sube, baja o se frena.", TEAL, "recta"],
               ["Repeat", "Estacionalidad (apagada)", "Lo que se repite cada año. Prophet la enciende solo con dos años de historia; acá, todavía no.", GREY, "onda"],
               ["AudioWaveform", "Ruido", "El sube y baja que no sigue ningún patrón.", AMARILLO, "ruido"]];
capas.forEach((c, i) => {
  const y = 2.3 + i * 1.45, tenue = i === 1;
  card(s, 0.6, y, 7.2, 1.25, { fill: tenue ? "EEF2F6" : WHITE, sombra:!tenue });
  icono(s, c[0], 0.85, y + 0.25, 0.75, c[3], c[3] === AMARILLO ? "n" : "b");
  s.addText(c[1], { x:1.8, y:y + 0.15, w:3.2, h:0.42, fontFace:FH, fontSize:16, bold:true, color: tenue ? GREY : INK, margin:0, isTextBox:true });
  texto(s, c[2], { x:1.8, y:y + 0.58, w:3.0, h:0.62, fontSize:11.5, color: tenue ? GREY : TEXTO });
  const px = 5.05, pw = 2.5, py = y + 0.2, ph = 0.85;
  let pts;
  if (c[4] === "recta") pts = [{ x:0, y:ph }, { x:pw, y:0.05 }];
  else if (c[4] === "onda") pts = Array.from({ length:25 }, (_, k) => ({ x:pw * k / 24, y:ph / 2 - 0.35 * Math.sin(k / 24 * Math.PI * 4) }));
  else pts = [0.5, 0.15, 0.7, 0.25, 0.8, 0.1, 0.6, 0.3, 0.75, 0.2, 0.55].map((v, k) => ({ x:pw * k / 10, y:ph * v }));
  trazo(s, px, py, pw, ph, pts, { line:{ color:c[3], width:2.5, dashType: tenue ? "dash" : "solid" } });
});
card(s, 8.15, 1.85, 4.55, 4.75, { fill:NAVY, line:NAVY });
texto(s, "Qué usa", { x:8.45, y:2.05, w:4, h:0.4, fontSize:15, bold:true, color:MINT, fontFace:FH });
texto(s, "Solo lo que cobraste en cada mes cerrado. El mes en curso no entra: todavía no terminó.", { x:8.45, y:2.5, w:4.0, h:1.0, fontSize:13, color:WHITE });
texto(s, "Qué no usa", { x:8.45, y:3.6, w:4, h:0.4, fontSize:15, bold:true, color:AMARILLO, fontFace:FH });
texto(s, "Gastos, facturas, inflación, datos de otras personas ni nada de internet.", { x:8.45, y:4.05, w:4.0, h:0.8, fontSize:13, color:WHITE });
texto(s, "No viene entrenado: se ajusta en el momento con tus cobros, en tu computadora. Con los mismos datos, siempre da lo mismo.", {
  x:8.45, y:5.0, w:4.0, h:1.4, fontSize:13, color:ICE, italic:true });

// ── De dónde salen los tres escenarios ──────────────────────────────────────
// Forma real de la demo: los nueve meses cerrados, la tendencia de Prophet
// estirada y la banda de noviembre a abril. Sin cifras en la filmina.
s = slide(false, `RELOJ 26:00 · 1:00. Los tres escenarios, en criollo:
DECÍ: "Son los cuatro pasos de la derecha. Uno: traza la línea que mejor pasa por el medio de mis meses. Dos: la estira hacia adelante, y ese es el esperado: 'si sigo como vengo'. No es el promedio: el año arrancó flojo y septiembre fue el mejor mes, así que la línea viene subiendo. Tres: mira cuánto se apartó cada mes de esa línea, e imagina mil futuros posibles, cada uno con sacudones de ese tamaño. Cuatro: los ordena de peor a mejor. El pesimista deja solo uno de cada diez futuros por debajo; el optimista, solo uno de cada diez por encima. Es como el pronóstico del tiempo: no te dice '22 grados', te dice 'entre 18 y 26'. Y lo ancho de la franja es qué tan irregular fui."
PUENTE a la que sigue: "Y los límites, que también pidió la cátedra."
· Esperado (azul): "La línea que mejor pasa por el medio de mis meses, estirada seis meses: es 'si sigo como vengo'. No es el promedio. El promedio del año es 4,1 millones, pero el esperado de noviembre es 7,1, porque el año arrancó con dos meses flojos y septiembre fue el mejor: la línea viene subiendo."
· Para los otros dos: "Mide cuánto se apartó cada mes de esa línea: acá, hasta cuatro millones para arriba o para abajo. Después imagina mil futuros posibles, cada uno con la línea más sacudones del mismo tamaño, y los ordena de peor a mejor."
· Pesimista (rojo): "Solo uno de cada diez futuros quedó por debajo. En nueve de cada diez cobro más que esto: sirve para planificar los gastos fijos." Noviembre: 3,6 millones.
· Optimista (verde): "Solo uno de cada diez futuros lo supera: no conviene gastar contando con eso." Noviembre: 10,7 millones.
· El ancho de la franja: "Es qué tan irregular fui. Un sueldo parejo da una franja finita; esta freelancer, ancha. Es como el pronóstico del tiempo: 'mañana, entre 18 y 26 grados'."
Palabras clave: la línea, no el promedio · mil futuros · 1 de cada 10 · pronóstico del tiempo.
De dónde salen los datos de la demo (si lo preguntan): "Los cobros de enero a septiembre son ficticios: los armamos nosotros, alternando meses buenos, de 5 a 10 millones, con meses flojos, de 1 a 2, como cobra un freelancer por proyecto. A Prophet no le tocamos ninguna perilla: usa sus valores de fábrica. Lo que fijamos nosotros es usar solo meses cerrados, seis meses, nunca menos de cero, y el azar con semilla fija."
Si te preguntan:
· ¿Por qué espera 7 millones si el promedio es 4? "Prophet no mira el promedio, mira hacia dónde va: el año arrancó flojo y septiembre fue el mejor mes, así que la línea sube."
· ¿Por qué el pesimista de abril da 6,2 millones si los meses flojos son de 1,5? "El pesimista se mide alrededor de la línea, y la línea viene subiendo. Con nueve meses, Prophet no sabe que los meses flojos se repiten: los toma como vaivén. Por eso proyectamos seis meses y no más, y la decisión es del usuario."
· ¿Sabe que diciembre es temporada alta? "Todavía no: para aprender lo que se repite cada año necesita dos años de historia."
Respaldo: tendencia +$ 490.000 por mes; vaivén típico ~2,7 M; pesimista = percentil 10, optimista = percentil 90, con 1000 simulaciones.`);
kicker(s, "Proyección · cómo funciona");
titulo(s, "De dónde salen los tres escenarios");
card(s, 0.6, 1.85, 7.9, 4.75);
const meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic", "ene", "feb", "mar", "abr"];
const reales = [1.4, 1.9, 6.3, 1.6, 8.1, 1.2, 5.7, 1.8, 9.3];
const tend = meses.map((_, i) => i <= 11 ? 2.2 + 0.4875 * i : [8.09, 8.59, 9.04, 9.54][i - 12]);
const bajo = [3.64, 4.15, 4.85, 5.42, 5.74, 6.23], alto = [10.74, 11.17, 11.69, 12.01, 12.49, 13.31];
const cx = 0.95, cy = 2.15, cw = 7.25, ch = 3.65, ymax = 14, paso = cw / meses.length;
const X = i => cx + paso * (i + 0.5), Y = v => cy + ch - ch * v / ymax;
// Banda: desde septiembre (sobre la tendencia) hasta abril.
const banda = [{ x:X(8), y:Y(tend[8]) }].concat(alto.map((v, k) => ({ x:X(10 + k), y:Y(v) })))
  .concat(bajo.slice().reverse().map((v, k) => ({ x:X(15 - k), y:Y(v) })));
const bx0 = Math.min(...banda.map(p => p.x)), by0 = Math.min(...banda.map(p => p.y));
trazo(s, bx0, by0, Math.max(...banda.map(p => p.x)) - bx0, Math.max(...banda.map(p => p.y)) - by0,
  banda.map(p => ({ x:p.x - bx0, y:p.y - by0 })).concat([{ close:true }]), { fill:{color:TEAL_L, transparency:72}, line:{color:TEAL_L, width:0.75} });
reales.forEach((v, i) => {
  const h = ch * v / ymax;
  s.addShape(pptx.ShapeType.rect, { x:X(i) - paso * 0.32, y:cy + ch - h, w:paso * 0.64, h, fill:{color:"B9C7D6"}, line:{color:"B9C7D6", width:0} });
});
const tPts = tend.map((v, i) => ({ x:X(i), y:Y(v) }));
const t0x = tPts[0].x, t0y = Math.min(...tPts.map(p => p.y));
trazo(s, t0x, t0y, tPts[8].x - t0x, Math.max(...tPts.slice(0, 9).map(p => p.y)) - t0y, tPts.slice(0, 9).map(p => ({ x:p.x - t0x, y:p.y - t0y })), { line:{ color:TEAL, width:2.5 } });
trazo(s, tPts[8].x, tPts[15].y, tPts[15].x - tPts[8].x, tPts[8].y - tPts[15].y, tPts.slice(8).map(p => ({ x:p.x - tPts[8].x, y:p.y - tPts[15].y })), { line:{ color:TEAL, width:2.5, dashType:"dash" } });
s.addShape(pptx.ShapeType.ellipse, { x:X(9) - 0.1, y:Y(3.46) - 0.1, w:0.2, h:0.2, fill:{color:WHITE}, line:{color:GREY, width:2} });
linea(s, cx, cy + ch, cx + cw, cy + ch, { color:GREY, width:1 });
meses.forEach((m, i) => texto(s, m, { x:X(i) - 0.25, y:cy + ch + 0.05, w:0.5, h:0.25, fontSize:9, color:GREY, align:"center" }));
texto(s, "lo que cobró cada mes", { x:X(0) - 0.2, y:Y(9.3) - 0.05, w:2.2, h:0.3, fontSize:10.5, color:"6B7F93" });
texto(s, "octubre no entra:\nno terminó", { x:X(9) - 0.6, y:Y(3.46) + 0.15, w:1.25, h:0.45, fontSize:9.5, color:GREY, align:"center" });
texto(s, "optimista", { x:X(15) - 1.0, y:Y(13.31) - 0.32, w:1.2, h:0.28, fontSize:10.5, bold:true, color:"3D8FA0", align:"right" });
texto(s, "esperado", { x:X(15) - 1.0, y:Y(9.54) - 0.33, w:1.2, h:0.28, fontSize:10.5, bold:true, color:TEAL, align:"right" });
texto(s, "pesimista", { x:X(15) - 1.0, y:Y(6.23) + 0.05, w:1.2, h:0.28, fontSize:10.5, bold:true, color:"3D8FA0", align:"right" });
[["Traza la línea que mejor pasa por el medio de tus meses", TEAL], ["La estira hacia adelante: el esperado. Es hacia dónde vas, no el promedio", TEAL],
 ["Imagina muchos futuros, con sacudones del tamaño de los tuyos", TEAL_L], ["Pesimista: casi todos los futuros quedan por encima. Optimista: casi ninguno lo supera", TEAL_L]].forEach((p, i) => {
  const y = 1.9 + i * 0.95;
  s.addShape(pptx.ShapeType.ellipse, { x:8.85, y, w:0.48, h:0.48, fill:{color:p[1]}, line:{color:p[1], width:0} });
  s.addText(String(i + 1), { x:8.85, y, w:0.48, h:0.48, fontFace:FH, fontSize:15, bold:true, color:WHITE, align:"center", valign:"middle", margin:0, isTextBox:true });
  texto(s, p[0], { x:9.5, y:y - 0.02, w:3.2, h:0.85, fontSize:13.5, color:INK });
});
card(s, 8.85, 5.75, 3.85, 0.85, { fill:NAVY, line:NAVY, sombra:false });
icono(s, "CloudSun", 9.0, 5.89, 0.56, AMARILLO, "n");
texto(s, "Como el pronóstico del tiempo: un rango. Lo ancho es qué tan irregular fuiste.", { x:9.7, y:5.75, w:2.9, h:0.85, fontSize:12, color:WHITE, valign:"middle" });

// ── Los límites del motor predictivo ────────────────────────────────────────
s = slide(true, `RELOJ 27:00 · 45 s, y pasás al navegador. LO PIDIÓ LA CÁTEDRA: límites del motor predictivo.
DECÍ: "Si los ingresos son irregulares, el rango sale ancho: no inventa una certeza que no tiene. Son montos sin inflación. Necesita historia: con poca, usa el promedio de los últimos meses y lo avisa en pantalla. Mira seis meses y no más, porque más lejos el error pesa más que la estimación. Y no sabe lo que no está en tu historia: un contrato que firmaste ayer, para el modelo, no existe."
· El rango es ancho cuando los ingresos son irregulares: esta freelancer alterna meses grandes y flojos; ese vaivén no es estacionalidad, no lo predice: lo refleja en lo ancho de la banda.
· Son montos nominales: no contempla la inflación.
· Necesita historia (10 cobros y 3 meses cerrados); si no, usa el promedio y lo dice.
· Proyecta 6 meses y no más: más lejos, el error domina.
· No sabe lo que no está en tu historia: si ayer firmaste un contrato grande, no lo sabe.
Si preguntan "¿por qué Prophet y no otro?": "Porque da el rango además del número, se ajusta solo a cada usuario, se puede explicar y corre en la computadora sin mandar los ingresos afuera." (anexo)
EN VIVO (27:45 – 29:15):
· RECOMENDACIONES: leé la primera y señalá su renglón "Por qué"; bajá a la segunda y a la tercera. "Las recomendaciones no usan inteligencia artificial: son reglas fijas, ordenadas por urgencia. Y cada una muestra su 'Por qué': el dato exacto del que sale, para que el usuario pueda verificarlo." "La primera son las dos facturas vencidas. La segunda es el tope del monotributo, y sugiere consultarlo con el contador. La tercera, las alertas de la auditoría que todavía no revisé. Fíjense cómo están escritas: 'te sugerimos'. Son sugerencias, no órdenes."
· REPORTE PDF: menú Dashboard → el selector ya dice Septiembre 2026 → Descargar reporte PDF → abrí el archivo → bajá hasta el pie. "Este es el reporte de septiembre, el último mes cerrado. Tiene cuánto entró y salió comparado con el mes anterior, el estado del monotributo, los gastos por categoría, las facturas y las alertas pendientes. Es lo único que sale de la aplicación, y por eso lleva el aviso adentro: no reemplaza el asesoramiento de un contador matriculado."
Si te preguntan "¿es para el contador?": "No es un documento contable: es el resumen del mes cerrado, para archivarlo o compartirlo si el usuario quiere (HU-13)."
Volvé a las filminas.`);
kicker(s, "Proyección · hasta dónde llega", MINT);
titulo(s, "Los límites del motor predictivo", true);
[["Waves", "El rango es ancho si los ingresos son irregulares", "No inventa certeza: muestra cuánto se puede equivocar."],
 ["Calculator", "Son montos nominales", "No contempla la inflación."],
 ["Hourglass", "Necesita historia", "Con poca, proyecta con el promedio y lo dice en pantalla."],
 ["Eye", "Mira pocos meses hacia adelante", "Más lejos, el error pasa a dominar la estimación."],
 ["CalendarClock", "No sabe lo que no está en tu historia", "Un contrato que firmaste ayer, para el modelo, no existe."]].forEach((l, i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.9 + Math.floor(i / 2) * 1.45;
  icono(s, l[0], x, y, 0.78, TEAL);
  s.addText(l[1], { x:x+1.0, y:y-0.02, w:4.95, h:0.72, fontFace:FH, fontSize:16, bold:true, color:WHITE, margin:0, valign:"top", isTextBox:true });
  texto(s, l[2], { x:x+1.0, y:y+0.72, w:4.95, h:0.6, fontSize:13, color:ICE });
});
enVivo(s, "recomendaciones y reporte PDF");

// ── Las recomendaciones ─────────────────────────────────────────────────────
s = slide(false, `RELOJ 29:15 · 1:00. (Volviste del navegador. LO PIDIÓ LA CÁTEDRA: límites de las recomendaciones.)
DECÍ: "Las recomendaciones solo ven lo que cargó el usuario: no conocen su situación personal, sus deudas ni cuánto riesgo quiere correr. Si sugieren hacer algo con un excedente, el instrumento lo elige el usuario: el sistema no dice en qué invertir."
El Resumen del mes, en una frase (no se abre en vivo): "El único lugar que usa una inteligencia artificial de afuera es el Resumen del mes, que escribe en castellano cómo te fue. Recibe solo totales, nunca descripciones, clientes ni el correo. Si inventa una cifra, se descarta; y sin internet, usa una plantilla local."
Palabras clave: reglas, no IA · cada una con su porqué · sugiere, no ordena · ordenadas por urgencia.
Respaldo: el Resumen usa Groq; sin internet o si el texto trae una cifra que no le mandamos, usa la plantilla y lo dice con la etiqueta "Sin IA".`);
kicker(s, "Recomendaciones · hasta dónde llegan");
titulo(s, "Las recomendaciones sugieren; decide el usuario");
const rv = ventana(s, "recomendaciones_dos", 0.6, 1.8, 6.6);
texto(s, "Cada recomendación muestra su «por qué»: el dato que la disparó.", { x:0.6, y:1.8 + rv.h + 0.1, w:6.6, h:0.4, fontSize:13, italic:true, color:GREY });
[["ListChecks", "Reglas fijas, no IA", "Ordenadas por urgencia. Se puede ver de dónde sale cada una."],
 ["UserCheck", "Sugieren, no ordenan", "Si hay un excedente, en qué destinarlo lo elige el usuario."],
 ["EyeOff", "Solo ven lo que cargaste", "No conocen tu situación personal, tus deudas ni cuánto riesgo querés correr."]].forEach((r, i) => {
  const y = 1.9 + i * 1.18;
  icono(s, r[0], 7.6, y, 0.68, [TEAL, MINT, AMARILLO][i], i === 2 ? "n" : "b");
  s.addText(r[1], { x:8.45, y:y-0.03, w:4.25, h:0.4, fontFace:FH, fontSize:15.5, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, r[2], { x:8.45, y:y+0.38, w:4.25, h:0.75, fontSize:12.5 });
});
card(s, 7.6, 5.55, 5.1, 1.05, { fill:NAVY, line:NAVY, sombra:false });
icono(s, "Sparkles", 7.8, 5.75, 0.62, AMARILLO, "n");
texto(s, "La única IA de afuera es el Resumen del mes: recibe solo totales. Si inventa una cifra, se descarta; sin internet, usa una plantilla local.", {
  x:8.55, y:5.55, w:4.05, h:1.05, fontSize:11.5, color:WHITE, valign:"middle" });

// =============================================================================
// 4 · CIERRE                                                    (30:15 – 32:00)
// =============================================================================

// ── Objetivos cumplidos ─────────────────────────────────────────────────────
// Los límites de cada parte ya se dijeron en su lugar (clasificador, motor
// predictivo y recomendaciones): el cierre no los repite.
s = slide(false, `RELOJ 30:15 · 45 s.
1. Objetivos cumplidos: "Clasificar, proyectar, controlar el monotributo y auditar, con el prototipo funcionando. El clasificador superó la meta."
2. Cómo se hizo: "Con Scrum, en etapas cortas, cada una con algo funcionando para revisar."
Respaldo: meta 70 %, logrado 76 %. 17 historias de usuario, 8 sprints, 4 meses.`);
kicker(s, "Resultados");
titulo(s, "Lo que se propuso, funcionando");
[["Tags", "Clasificar", "Los gastos se clasifican solos, aprenden de las correcciones y el modelo superó la meta."],
 ["TrendingUp", "Proyectar", "Los ingresos que vienen, con escenario pesimista y optimista, y su reporte."],
 ["Gauge", "Controlar", "La categoría del monotributo, con el mes en que te pasarías."],
 ["ScanSearch", "Auditar", "Gastos repetidos e irregulares, facturas vencidas, cuota y transferencias propias."]].forEach((o, i) => {
  const x = 0.6 + i * 3.08;
  card(s, x, 1.95, 2.85, 3.65);
  icono(s, o[0], x + 0.3, 2.25, 0.8, TEAL);
  icono(s, "Check", x + 2.0, 2.33, 0.6, MINT, "n");
  s.addText(o[1], { x:x+0.3, y:3.25, w:2.3, h:0.5, fontFace:FH, fontSize:19, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, o[2], { x:x+0.3, y:3.8, w:2.3, h:1.7, fontSize:13 });
});
card(s, 0.6, 5.85, 12.1, 0.75, { sombra:false });
icono(s, "Route", 0.8, 5.95, 0.55, TEAL);
texto(s, "Construido con Scrum, en etapas cortas, cada una con algo funcionando para revisar.", {
  x:1.55, y:5.85, w:11, h:0.75, fontSize:14.5, color:INK, valign:"middle" });

// ── Trabajo futuro ──────────────────────────────────────────────────────────
s = slide(false, `RELOJ 31:00 · 30 s.
3. Trabajo futuro: "Facturación electrónica de ARCA, conectar el banco cuando haya reglas para eso, datos reales para el clasificador y más seguridad para producción."
· La escala del monotributo también, si ARCA ofrece una forma oficial de leerla.
· Producción: base cifrada en disco, HTTPS, sesiones más cortas, anular un pase antes de que venza y límite de intentos de inicio de sesión.`);
kicker(s, "Hacia adelante");
titulo(s, "Trabajo futuro");
[["Receipt", "Facturación electrónica de ARCA", "Emitir desde el sistema y tomar la escala del régimen."],
 ["Landmark", "Conexión con el banco", "Cuando finanzas abiertas tenga sus reglas técnicas."],
 ["Database", "Datos reales para el clasificador", "Ampliar los ejemplos con gastos reales de usuarios."],
 ["Shield", "Llevarlo a producción", "Base cifrada, HTTPS y sesiones más cortas."]].forEach((f, i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.95 + Math.floor(i / 2) * 2.2;
  card(s, x, y, 5.95, 1.95);
  icono(s, f[0], x + 0.3, y + 0.5, 0.95, [TEAL, TEAL, MINT, AMARILLO][i], i === 3 ? "n" : "b");
  s.addText(f[1], { x:x+1.5, y:y+0.38, w:4.25, h:0.5, fontFace:FH, fontSize:17, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, f[2], { x:x+1.5, y:y+0.95, w:4.25, h:0.8, fontSize:14 });
});

// ── Gracias ─────────────────────────────────────────────────────────────────
s = slide(true, `RELOJ 31:30 · 30 s.
4. La frase de alcance, otra vez (la de la franja), despacio: "El sistema informa, proyecta y alerta. La decisión y el asesoramiento siguen siendo del usuario y de su contador."
5. "Muchas gracias. Quedo a disposición para las preguntas."
RELOJ 32:00. Del 32:00 al 35:00 es colchón: si sobra tiempo, no lo llenes. Esta filmina queda de fondo durante las preguntas.`);
s.addText("Muchas gracias", { x:0.7, y:1.55, w:7.5, h:1.2, fontFace:FH, fontSize:52, bold:true, color:WHITE, margin:0, isTextBox:true });
texto(s, "Quedo a disposición para las preguntas.", { x:0.7, y:2.85, w:7, h:0.5, fontSize:20, color:ICE });
ventana(s, "proyecciones_grafico", 8.1, 1.45, 4.6);
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:4.15, w:12.1, h:1.05, fill:{color:MINT}, rectRadius:0.12, line:{color:MINT, width:0} });
s.addText("Informa, proyecta y alerta. La decisión y el asesoramiento siguen siendo del usuario y de su contador.", {
  x:0.9, y:4.15, w:11.5, h:1.05, fontFace:FH, fontSize:18.5, bold:true, color:NAVY, valign:"middle", margin:0, isTextBox:true });
texto(s, "Marcos Gamaliel Joaquín  ·  Legajo SOF02218", { x:0.7, y:5.75, w:7, h:0.4, fontSize:15, color:WHITE });
texto(s, "Ingeniería de Software · Universidad Siglo 21", { x:0.7, y:6.15, w:7, h:0.4, fontSize:13, color:GREY });

// =============================================================================
// ANEXO · PARA LAS PREGUNTAS (no se muestra en la exposición)
// =============================================================================

s = slide(true, "Anexo: no se muestra en la exposición. Respaldo para la ronda de preguntas y plan B si falla algo en vivo.");
kicker(s, "Anexo", MINT);
s.addText("Para las preguntas", { x:0.6, y:2.6, w:12, h:1.0, fontFace:FH, fontSize:44, bold:true, color:WHITE, margin:0, isTextBox:true });
texto(s, "La contraseña en la base · por qué archivo y no conexión con el banco · la escala de ARCA · el semáforo al importar · por qué Prophet · por qué SVM · los desafíos del entrenamiento · la prueba del 76 % · las pruebas automáticas · seguridad · y la demo en capturas, por si algo falla en vivo.", {
  x:0.6, y:3.8, w:11.5, h:1.0, fontSize:16, color:ICE });

// ── Anexo · la contraseña en la base ────────────────────────────────────────
// Salida real y completa de `sh defensa_final/demo/ver_usuarios.sh` sobre la base
// de la defensa (tfg_db, 10/10): las dos cuentas tienen la misma contraseña y la
// base guarda dos hashes distintos. Se puede correr en vivo y da lo mismo: la
// siembra conserva el hash de la cuenta demo y la del tribunal no se borra.
const HASHES = [["demo@freelancecontrol.com", "$2b$12$2ywjtsYRN0kRv3xdX1dQ2.L0lZJR5Pfllwhsq8OpEaY6mW4eLT4Ny"],
                ["tribunal@freelancecontrol.com", "$2b$12$1LV63ca2SQx1bUjkl6KTRenaxi7SOMg8ulFv9z3P1TVThZB8tOizC"]];
s = slide(false, `Anexo, primera filmina: si preguntan por la contraseña o por la seguridad al entrar. En la exposición, el hash se cuenta en palabras mientras entrás en vivo; esta filmina es para mostrarlo en la base.
Lo que se dice con ella: "La base no guarda mi contraseña: guarda su hash. El hash sale de pasar la contraseña por una fórmula que va en una sola dirección: de la contraseña se llega al hash, pero del hash no se puede volver a la contraseña. Antes de calcularlo, el sistema le agrega una sal: caracteres al azar, distintos para cada usuario. Por eso estas dos cuentas, que tienen la misma contraseña, quedan con hashes distintos. Para dejarme entrar, calcula el hash de lo que escribí con la misma sal y lo compara con el guardado. Si alguien se roba la base, se lleva hashes, no contraseñas. Y al entrar, el sistema me da un pase firmado que vence solo."
Palabras clave: hash, no contraseña · una sola dirección · sal distinta por usuario · pase firmado.
El recuadro "¿Qué es un hash?" es para el que no programa: si ves caras de duda, señalalo y leé las tres propiedades. Si roban la base, se llevan hashes, no contraseñas: eso se dice, no está escrito.
OJO: decí "hasheada", nunca "encriptada". Encriptar se deshace con una llave; el hash no se deshace nunca.
Cómo se lee el hash: "$2b$" es la versión de bcrypt; "12" es el costo; después, los 22 caracteres de la sal; el resto, el hash.
EN VIVO, si lo piden: terminal "1 · La contraseña en la base" → clic en la ventana → Enter (el comando ya está escrito; también está en la filmina, para copiarlo: sh defensa_final/demo/ver_usuarios.sh). Da exactamente lo que se ve acá: la siembra conserva el hash de la cuenta demo y la cuenta del tribunal no se borra. Solo lee la base: no cambia nada.
Si te preguntan:
· ¿La sal? Veintidós caracteres al azar, distintos por usuario, guardados junto al hash: no son secretos, su trabajo es que dos contraseñas iguales no den el mismo hash.
· ¿No se puede adivinar probando? bcrypt repite el cálculo 4.096 veces a propósito (el costo 12): entrar lleva una fracción de segundo; probar millones de contraseñas se vuelve lentísimo.
· ¿Un correo que no existe? Contesta el mismo mensaje y tarda lo mismo (compara contra un hash de relleno): nadie puede averiguar qué correos están registrados.
· ¿El pase? Un token firmado con una clave que solo tiene el servidor. Se puede leer; si lo modifican, la firma no coincide. Vence a los siete días.`);
kicker(s, "Anexo · la contraseña en la base");
titulo(s, "La contraseña no se guarda: se guarda su hash");
// La terminal, con la salida completa del script.
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:1.8, w:7.6, h:4.15, fill:{color:NAVY3}, line:{color:"23415F", width:1},
  rectRadius:0.07, shadow:{ type:"outer", color:"0A1622", blur:10, offset:3, angle:90, opacity:0.35 } });
["FF5F57", "FEBC2E", "28C840"].forEach((c, i) =>
  s.addShape(pptx.ShapeType.ellipse, { x:0.72 + i * 0.15, y:1.88, w:0.09, h:0.09, fill:{color:c}, line:{color:c, width:0} }));
// El comando va en su propio cuadro, sin el "$", para poder copiarlo desde la filmina.
s.addText("$", { x:0.85, y:2.12, w:0.2, h:0.27, fontFace:FM, fontSize:10.5, color:GREY, margin:0, valign:"middle", isTextBox:true });
s.addText("sh defensa_final/demo/ver_usuarios.sh", { x:1.05, y:2.12, w:6.9, h:0.27, fontFace:FM, fontSize:10.5, color:MINT, margin:0, valign:"middle", isTextBox:true });
const filasHash = [];
HASHES.forEach((h, i) => {
  const [v, sal, resto] = [h[1].slice(0, 7), h[1].slice(7, 29), h[1].slice(29)];
  filasHash.push([[`-[ RECORD ${i + 1} ]-----+` + "-".repeat(61), GREY]],
    [["email             | ", GREY], [h[0], WHITE]],
    [["password_hash     | ", GREY], [v, AMARILLO], [sal, MINT], [resto, ICE]],
    [["  versión y costo | ", GREY], [v, AMARILLO]],
    [["  sal             | ", GREY], [sal, MINT]],
    [["  hash            | ", GREY], [resto, ICE]]);
});
filasHash.forEach((l, i) => s.addText(l.map(t => ({ text:t[0], options:{ color:t[1] } })), {
  x:0.85, y:2.5 + i * 0.27, w:7.25, h:0.27, fontFace:FM, fontSize:10.5, margin:0, valign:"middle", isTextBox:true }));
card(s, 0.6, 6.1, 7.6, 0.68, { fill:"FFF6E0", line:"F1D9A0", sombra:false });
texto(s, "Las dos cuentas tienen la misma contraseña, y en la base quedan dos hashes distintos: eso hace la sal.", {
  x:0.85, y:6.1, w:7.2, h:0.68, fontSize:13.5, color:INK, bold:true, valign:"middle" });
// Qué es un hash, para quien no programa: las tres propiedades y para qué sirve.
card(s, 8.45, 1.8, 4.25, 2.62, { line:TEAL_L, lw:1.25 });
icono(s, "Lock", 8.68, 1.97, 0.5, TEAL);
s.addText("¿Qué es un hash?", { x:9.3, y:1.98, w:3.25, h:0.48, fontFace:FH, fontSize:16, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
s.addText([
  { text:"Es el resultado de pasar un texto por una fórmula que va en un solo sentido:", options:{ breakLine:true } },
  { text:"El mismo texto da siempre el mismo hash.", options:{ bullet:{ indent:13 }, breakLine:true } },
  { text:"Si cambiás una sola letra, el hash sale completamente distinto.", options:{ bullet:{ indent:13 }, breakLine:true } },
  { text:"Del hash no se puede volver al texto.", options:{ bullet:{ indent:13 }, breakLine:true } },
  { text:"Por eso sirve para comprobar tu contraseña sin guardarla.", options:{ bold:true, color:INK } },
], { x:8.68, y:2.56, w:3.85, h:1.78, fontFace:FB, fontSize:12, color:TEXTO, valign:"top", margin:0, paraSpaceAfter:2, isTextBox:true });
[["Scale", "Para entrar, compara hashes", "Calcula el hash de lo que escribiste, con la misma sal, y lo compara con el guardado."],
 ["Signature", "La sesión es un pase firmado", "Se puede leer, pero si alguien lo modifica la firma no coincide y deja de servir. Vence solo."]].forEach((p, i) => {
  const y = 4.62 + i * 1.12;
  icono(s, p[0], 8.5, y, 0.6, [MINT, AMARILLO][i], i === 1 ? "n" : "b");
  s.addText(p[1], { x:9.28, y:y-0.03, w:3.45, h:0.38, fontFace:FH, fontSize:14, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, p[2], { x:9.28, y:y+0.36, w:3.45, h:0.7, fontSize:12 });
});

// ── ¿Por qué archivo y no conexión directa? ─────────────────────────────────
s = slide(false, `Respuesta corta: "Hoy en Argentina no hay una forma estándar y segura de que una aplicación lea las cuentas de todos los bancos. Lo único que dan todos es el archivo de movimientos, y para eso no hace falta pedirle ninguna clave al usuario. La conexión directa quedó fuera del alcance y es trabajo futuro; el sistema ya está preparado."
· Finanzas abiertas: creada por el Decreto 353/2025, pero el BCRA no publicó las reglas técnicas: los bancos no están obligados a ofrecerla.
· La tesis (proceso P3): los bancos entregan los movimientos "exclusivamente en archivos exportados".
· Homebanking con clave del usuario: obligaría a guardar la llave de su cuenta. El sistema no guarda ni su propia contraseña.
· Mercado Pago: cubre 1 de las 9 entidades, exige guardar un permiso sobre una cuenta con plata, y sus reportes igual son archivos.
· Cierre: "No fue por no saber conectar una API: el sistema ya usa una, la del Resumen. Fue una decisión de seguridad y de alcance."`);
kicker(s, "Anexo · importación");
titulo(s, "¿Por qué el archivo y no la conexión directa?");
[["Landmark", "Los bancos no abren una ventanilla común", "Finanzas abiertas existe por decreto, pero todavía no tiene sus reglas técnicas."],
 ["KeyRound", "La otra opción es pedir la clave del banco", "Guardar la llave de la cuenta del usuario va contra todo el diseño de seguridad."],
 ["Wallet", "Una billetera sola no alcanza", "Cubriría una entidad y las demás seguirían con archivo."]].forEach((r, i) => {
  const y = 1.9 + i * 1.4;
  icono(s, r[0], 0.6, y, 0.78, [TEAL, ROJO, AMARILLO][i], i === 2 ? "n" : "b");
  s.addText(r[1], { x:1.6, y:y-0.03, w:5.2, h:0.45, fontFace:FH, fontSize:16, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, r[2], { x:1.6, y:y+0.45, w:5.2, h:0.85, fontSize:13 });
});
card(s, 7.2, 1.85, 5.5, 4.75, { fill:NAVY, line:NAVY });
texto(s, "Un solo molde para todos", { x:7.5, y:2.05, w:5, h:0.4, fontSize:16, bold:true, color:MINT, fontFace:FH });
["Galicia", "Santander", "BBVA", "Macro", "Nación", "Brubank", "ICBC", "Mercado Pago", "Naranja X"].forEach((b, i) => {
  chip(s, b, 7.5 + (i % 3) * 1.68, 2.6 + Math.floor(i / 3) * 0.5, 1.55, { fill:NAVY2, line:TEAL, color:ICE, size:10.5, h:0.38 });
});
s.addShape(pptx.ShapeType.downArrow, { x:9.75, y:4.15, w:0.4, h:0.38, fill:{color:TEAL_L}, line:{color:TEAL_L, width:0} });
chip(s, "fecha · descripción · monto · tipo", 7.75, 4.65, 4.4, { fill:MINT, line:MINT, color:NAVY, bold:true, size:12.5 });
texto(s, "Duplicados, transferencias propias, clasificador y auditoría trabajan sobre el molde. Una conexión futura sería otra entrada al mismo molde.", {
  x:7.5, y:5.25, w:5.0, h:1.2, fontSize:12.5, color:WHITE });

// ── ¿Cómo se actualiza la escala de ARCA? ───────────────────────────────────
s = slide(false, `· ¿Se actualiza sola? No. Pero tampoco hay que tocar el cálculo: la escala es un dato (catálogo con tope y cuota de cada categoría y la fecha desde la que rige).
· La tesis (riesgo R2): "catálogo de categorías versionado en la base de datos con fecha de vigencia, actualizable por carga de datos sin modificar el código". La escala de agosto se cargó así: el riesgo ocurrió y se resolvió sin tocar el cálculo.
· Por qué no sola: ARCA no tiene un servicio web que entregue la escala (sus servicios son para operar con un CUIT y certificado); la publica como página para personas (arca.gob.ar/monotributo/categorias.asp). Leer la página con un programa (scraping) es frágil: un tope mal leído da verde cuando es rojo, sin que nadie se entere. Cambia dos veces por año (Ley 27.743: 1/2 y 1/8).
· Tres pasos: copiar los topes y cuotas con su fecha; docker compose exec api python seed_categorias_monotributo.py; verificar en Monotributo.
· No se actualiza en vivo: la próxima escala real (febrero 2027) no existe todavía.`);
kicker(s, "Anexo · monotributo");
titulo(s, "¿Cómo se actualiza la escala de ARCA?");
[["Ban", "No hay un servicio de ARCA que la entregue", "Se publica como una página web pensada para personas."],
 ["TriangleAlert", "Leer la página con un programa es frágil", "Si cambia el diseño, un tope mal leído pasa sin aviso: el semáforo diría verde cuando es rojo."],
 ["CalendarClock", "Cambia dos veces por año, en fechas conocidas", "Cargarla y verificarla lleva minutos."]].forEach((r, i) => {
  const y = 1.9 + i * 1.4;
  icono(s, r[0], 0.6, y, 0.78, [GREY, ROJO, TEAL][i]);
  s.addText(r[1], { x:1.6, y:y-0.03, w:5.3, h:0.45, fontFace:FH, fontSize:15.5, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, r[2], { x:1.6, y:y+0.45, w:5.3, h:0.85, fontSize:13 });
});
card(s, 7.3, 1.85, 5.4, 2.7);
texto(s, "Tres pasos, sin tocar el cálculo", { x:7.6, y:2.0, w:4.9, h:0.4, fontSize:15.5, bold:true, color:INK, fontFace:FH });
["Cargar los topes y cuotas nuevos, con la fecha desde la que rigen", "Correr el comando que guarda la escala", "Verificar el tope en la pantalla de Monotributo"].forEach((p, i) => {
  const y = 2.55 + i * 0.62;
  s.addShape(pptx.ShapeType.ellipse, { x:7.6, y, w:0.42, h:0.42, fill:{color:TEAL}, line:{color:TEAL, width:0} });
  s.addText(String(i + 1), { x:7.6, y, w:0.42, h:0.42, fontFace:FH, fontSize:13, bold:true, color:WHITE, align:"center", valign:"middle", margin:0, isTextBox:true });
  texto(s, p, { x:8.15, y:y - 0.02, w:4.4, h:0.55, fontSize:12.5, color:INK, valign:"middle" });
});
card(s, 7.3, 4.75, 5.4, 1.85, { fill:NAVY, line:NAVY });
texto(s, "Cada escala queda guardada con su fecha", { x:7.6, y:4.9, w:4.9, h:0.4, fontSize:14, bold:true, color:MINT });
chip(s, "escala de febrero · histórica", 7.6, 5.4, 2.4, { fill:NAVY2, line:GREY, color:GREY, size:11 });
chip(s, "escala de agosto · vigente", 10.15, 5.4, 2.35, { fill:NAVY2, line:MINT, color:MINT, size:11, bold:true });
texto(s, "Un reporte de mayo se sigue calculando con la escala de mayo.", { x:7.6, y:5.95, w:4.9, h:0.5, fontSize:12, color:ICE });

// ── ¿Por qué no se movió el semáforo al importar? ───────────────────────────
// Antes y después de importar: el largo del viaje es el mismo; cambia lo recorrido.
s = slide(false, `Respuesta corta: "No se suma de más porque ya estaba prevista. El sistema esperaba cobrar unos 7,1 millones en octubre. Al importar, 3,46 pasaron de 'esperado' a 'cobrado', y el total del año quedó igual. Lo que sí subió es lo facturado real, de 69 a 75 %."
· Analogía: Córdoba–Rosario, 400 km. A mitad de camino el viaje sigue midiendo 400: cambió cuánto recorriste.
· Cuándo se mueve: si en octubre cobrás más de lo esperado, o el 1 de noviembre, cuando octubre se cierra y entra con lo realmente cobrado.
· Por qué así: si contara solo lo cobrado del mes en curso, cada día 1 el riesgo "bajaría" y volvería a subir a fin de mes: falsa tranquilidad en el dato fiscal.`);
kicker(s, "Anexo · monotributo");
titulo(s, "¿Por qué el semáforo no cambia al importar?");
const filas = [["Antes de importar", [[37.3, TEAL], [7.10, TEAL_L], [7.10, TEAL_L], [7.59, TEAL_L]]],
               ["Después de importar", [[37.3, TEAL], [3.46, TEAL], [3.64, TEAL_L], [7.10, TEAL_L], [7.59, TEAL_L]]]];
filas.forEach((f, k) => {
  const y = 2.3 + k * 1.45, x0 = 3.2, w0 = 9.0;
  texto(s, f[0], { x:0.6, y:y + 0.12, w:2.5, h:0.45, fontSize:15, bold:true, color:INK });
  let a = 0;
  f[1].forEach(t => {
    s.addShape(pptx.ShapeType.rect, { x:x0 + w0 * a / total, y, w:w0 * t[0] / total, h:0.7, fill:{color:t[1]}, line:{color:WHITE, width:1.5} });
    a += t[0];
  });
  const xt = x0 + w0 * topeG / total;
  linea(s, xt, y - 0.12, xt, y + 0.82, { color:ROJO, width:2.5 });
});
[["ya cobrado", TEAL], ["esperado hasta diciembre", TEAL_L], ["tope de la categoría", ROJO]].forEach((l, i) => {
  const x = 3.2 + i * 3.0;
  s.addShape(pptx.ShapeType.rect, { x, y:5.05, w:0.3, h:0.22, fill:{color:l[1]}, line:{color:l[1], width:0} });
  texto(s, l[0], { x:x + 0.42, y:4.98, w:2.5, h:0.35, fontSize:12.5 });
});
card(s, 0.6, 5.6, 12.1, 1.0, { fill:NAVY, line:NAVY, sombra:false });
texto(s, "Lo importado ya estaba previsto: pasó de «esperado» a «cobrado». El largo del viaje es el mismo; cambió lo recorrido.", {
  x:0.9, y:5.6, w:11.5, h:1.0, fontSize:15, color:WHITE, valign:"middle" });

// ── ¿Por qué Prophet y no otro? ─────────────────────────────────────────────
s = slide(false, `Respuesta corta: "Porque da el rango además del número, se ajusta solo a la historia de cada usuario, se puede explicar y corre en la computadora sin mandar los ingresos afuera. Con poca historia se comporta como una línea con su banda; con dos años, suma solo lo que se repite cada año, sin tocar el código."
Si dicen "entonces es una regresión lineal": "Hoy, con nueve meses, se comporta como una. La diferencia es que trae la banda calculada de forma estándar, detecta si la tendencia dobla y, con dos años, suma la estacionalidad sola. Elegimos una herramienta que crece con el usuario."`);
kicker(s, "Anexo · proyección");
titulo(s, "¿Por qué Prophet y no otro modelo?");
const th = t => ({ text:t, options:{ bold:true, color:WHITE, fill:{color:NAVY}, fontSize:13 } });
const td = (t, o) => ({ text:t, options:Object.assign({ color:INK, fill:{color:WHITE} }, o || {}) });
s.addTable([
  [th("Opción"), th("Qué haría con esta usuaria"), th("Por qué no")],
  [td("El promedio de los meses", { bold:true }), td("El mismo número para todos los meses"), td("No ve que viene creciendo. Es el plan B para usuarios nuevos.")],
  [td("Una recta común", { bold:true }), td("Hoy, algo parecido a Prophet"), td("Se queda recta para siempre y la banda hay que armarla aparte.")],
  [td("ARIMA", { bold:true }), td("Podría andar"), td("Hay que elegir parámetros para cada serie y pide una historia larga y pareja.")],
  [td("Redes neuronales o una IA", { bold:true }), td("Con pocos datos, se aprende el ruido de memoria"), td("No se puede explicar el resultado y una IA externa recibiría los ingresos.")],
], { x:0.6, y:1.9, w:12.1, colW:[2.9, 3.9, 5.3], rowH:0.72, fontFace:FB, fontSize:13, border:{ type:"solid", color:BORDE, pt:1 }, valign:"middle" });
card(s, 0.6, 5.75, 12.1, 0.85, { fill:NAVY, line:NAVY, sombra:false });
texto(s, "Prophet: da un rango, se ajusta solo a cada usuario, se puede explicar y corre en la computadora.", {
  x:0.9, y:5.75, w:11.5, h:0.85, fontSize:15, color:WHITE, valign:"middle" });

// ── ¿Por qué SVM? ───────────────────────────────────────────────────────────
s = slide(false, `· SVM es de los métodos clásicos que mejor funcionan con textos cortos y muchas palabras distintas, y entrena en segundos en la propia computadora.
· La tesis planteó Naive Bayes con menos de 100 ejemplos y SVM desde 100 (patrón Strategy: el resto del código no sabe cuál le tocó). Medidos sobre los mismos 600 ejemplos: SVM 76 %, Naive Bayes 74 %. Con 96 ejemplos, en 50 sorteos: SVM 46 %, NB 44 %. Como el modelo siempre parte de los 600 de base, en la práctica corre SVM.
· Un modelo tipo ChatGPT obligaría a mandar la descripción de cada gasto a una empresa externa: clientes, proveedores y hábitos del usuario.`);
kicker(s, "Anexo · clasificador");
titulo(s, "¿Por qué SVM y no otro modelo?");
[["Brain", "SVM", "Lo elegido", "Muy bueno con textos cortos y muchas palabras distintas. Entrena en segundos en la computadora del usuario.", MINT],
 ["Calculator", "Naive Bayes", "Para pocos ejemplos", "Cuenta qué tan seguido aparece cada palabra en cada categoría. Anda bien con pocos datos: la tesis lo prevé para eso y está implementado. Con la base completa, gana el SVM.", TEAL],
 ["Sparkles", "Un modelo tipo ChatGPT", "Lo descartamos", "Habría que mandar la descripción de cada gasto a una empresa externa: ahí están los clientes y los hábitos del usuario.", ROJO]].forEach((m, i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 1.95, 3.85, 4.25);
  icono(s, m[0], x + 0.3, 2.25, 0.85, m[4], "b");
  s.addText(m[1], { x:x+1.35, y:2.25, w:2.35, h:0.5, fontFace:FH, fontSize:17, bold:true, color:INK, margin:0, isTextBox:true });
  s.addText(m[2], { x:x+1.35, y:2.75, w:2.35, h:0.35, fontFace:FB, fontSize:12.5, bold:true, color:m[4], margin:0, isTextBox:true });
  texto(s, m[3], { x:x+0.3, y:3.45, w:3.25, h:2.6, fontSize:13.5 });
});

// ── Los desafíos del entrenamiento ──────────────────────────────────────────
// A la izquierda, tres desafíos; a la derecha, el que más cuesta entender
// (medirlo de forma honesta), con el problema, la solución y las cinco vueltas.
s = slide(false, `Anexo: si preguntan por los desafíos del entrenamiento (los pidió el profesor en la 3.ª entrega). En la exposición se nombran en una frase, con los límites del clasificador.
Lo que se dice con ella: "Fueron cuatro. Pocos datos: con los primeros ejemplos no llegaba a la meta; armamos más, la misma cantidad para cada categoría, y llegó. Medirlo de forma honesta: no lo medimos con los gastos con los que aprendió, porque se los sabe de memoria; sería como un examen con las mismas preguntas de la clase. Lo probamos con gastos que nunca había visto, cinco veces, cada vez con otros, y promediamos: 76 %, y la meta era 70 (las cinco vueltas están en la filmina que sigue). Saber cuándo duda: la fórmula estándar repartía la seguridad entre las doce categorías y hasta los aciertos obvios parecían dudosos; lo resolvimos con la elección que les mostré. Y reentrenar sin trabar la pantalla: se hace de fondo, de a uno por usuario."
1. Pocos datos, nuestros, no del usuario: con 216 ejemplos (18 por categoría) acertaba el 57 %. Lo ampliamos a 600, 50 por categoría, y llegó al 76 %. Un usuario nuevo no entrena nada: desde el primer día usa ese modelo de 600, y a los 20 gastos recibe uno propio que es 600 más los suyos. Nunca arranca de cero.
2. Medirlo honesto, la validación cruzada: "Es como un profesor con 600 preguntas. Si toma el examen con las mismas preguntas que dio en clase, el alumno las sabe de memoria: medido así, el modelo saca 100 %, un número mentiroso. Entonces separa 120 que el modelo nunca vio, le enseña con las otras 480 y le toma esas 120. Lo repite cinco veces, cambiando cuáles quedan afuera. Las cinco notas fueron 84, 78, 76, 70 y 72. El promedio es 76."
Cómo se lee el dibujo: cada fila es una vuelta; la celda amarilla es la parte que se aparta para el examen, y en cada vuelta es otra.
3. Saber cuándo duda: "El primer intento usó una fórmula estándar que reparte 100 % entre las doce categorías. Aunque una gane clarísimo, las otras once se llevan su parte: 'Uber viaje', un acierto obvio, sacaba 32 %, y algo dudoso como Telecentro, 9 %. Todo quedaba amontonado abajo y casi todo iba a revisión. La solución fue medir por cuánto le gana la primera a la segunda: el recuento de la elección."
4. Reentrenar sin trabar: de fondo y de a uno por usuario, para que nunca queden dos modelos activos.`);
kicker(s, "Anexo · clasificador · desafíos");
titulo(s, "Los desafíos del entrenamiento");
[["Database", "Pocos datos", "Con pocos ejemplos por categoría no llegaba a la meta. Armamos más, la misma cantidad para cada una. Un usuario nuevo no entrena nada: arranca con esa base.", TEAL],
 ["CircleHelp", "Que supiera cuándo duda", "La fórmula estándar reparte la seguridad entre todas las categorías: hasta un acierto obvio salía dudoso. La solución: medir por cuánto le gana la primera a la segunda.", AMARILLO],
 ["Timer", "Reentrenar sin trabar la pantalla", "Entrenar lleva unos segundos. Corre de fondo, mientras el usuario sigue usando la aplicación, y de a uno por usuario: nunca quedan dos modelos activos.", TEAL_L]].forEach((d, i) => {
  const y = 1.85 + i * 1.6;
  card(s, 0.6, y, 6.2, 1.45);
  icono(s, d[0], 0.85, y + 0.33, 0.78, d[3], d[3] === AMARILLO ? "n" : "b");
  s.addText(d[1], { x:1.85, y:y+0.14, w:4.8, h:0.42, fontFace:FH, fontSize:16.5, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, d[2], { x:1.85, y:y+0.56, w:4.8, h:0.82, fontSize:12.5 });
});
card(s, 7.05, 1.85, 5.65, 4.65);
icono(s, "Scale", 7.3, 2.05, 0.78, MINT);
s.addText("Medirlo de forma honesta", { x:8.25, y:2.2, w:4.3, h:0.48, fontFace:FH, fontSize:18, bold:true, color:INK, margin:0, isTextBox:true });
texto(s, [{ text:"El problema: ", options:{ bold:true, color:INK } },
          { text:"si se lo evalúa con los mismos ejemplos con los que aprendió, se los sabe de memoria. La nota sale perfecta y no dice nada." }], {
  x:7.35, y:3.0, w:5.1, h:0.85, fontSize:12.5 });
texto(s, [{ text:"La solución: ", options:{ bold:true, color:INK } },
          { text:"se aparta una parte que el modelo no ve, se lo entrena con el resto y se lo evalúa con lo apartado. Se repite cambiando la parte apartada, y se promedia." }], {
  x:7.35, y:3.92, w:5.1, h:0.85, fontSize:12.5 });
// Las cinco vueltas: cada fila es una vuelta; la celda amarilla es el examen.
for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) {
  const col = r === c ? AMARILLO : TEAL_L;
  s.addShape(pptx.ShapeType.rect, { x:7.4 + c * 0.55, y:4.85 + r * 0.22, w:0.5, h:0.17, fill:{color:col}, line:{color:col, width:0} });
}
[[AMARILLO, "examen: no lo vio"], [TEAL_L, "estudio: aprende con esto"]].forEach((l, i) => {
  s.addShape(pptx.ShapeType.rect, { x:10.3, y:4.9 + i * 0.36, w:0.18, h:0.18, fill:{color:l[0]}, line:{color:l[0], width:0} });
  texto(s, l[1], { x:10.58, y:4.84 + i * 0.36, w:2.05, h:0.3, fontSize:11.5, color:INK });
});
texto(s, "cada fila, una vuelta", { x:10.3, y:5.58, w:2.3, h:0.3, fontSize:11, italic:true, color:GREY });
texto(s, "Como un profesor que no toma en el examen las mismas preguntas que dio en clase.", {
  x:7.35, y:5.97, w:5.15, h:0.42, fontSize:11.5, italic:true, color:TEAL });

// ── Anexo · se puede probar: las cinco vueltas y los errores ────────────────
// Salida real de evaluar_modelo.py (validación cruzada sobre los 600 ejemplos de
// base, las mismas cinco particiones): con las cinco vueltas desde el 11/10, da lo mismo en vivo. El
// mosaico tiene las proporciones reales: el ancho de cada columna y el alto de
// cada bloque salen de esos cuatro conteos.
s = slide(false, `Anexo: si preguntan cómo se midió el 76 % o piden ver la prueba funcionando. En la exposición, la frase del examen se puede decir con los límites del clasificador.
Lo que se dice con ella: "¿Cómo sabemos que acierta el 76 %? No lo medimos con los gastos con los que aprendió, porque esos se los sabe de memoria. Sería como un examen con las mismas preguntas que se dieron en clase: todos se sacan 10. Por eso lo probamos con gastos que nunca había visto. Y para que no fuera suerte, lo hicimos cinco veces, cada vez con otros gastos, y sacamos el promedio. Dio 76 %, y la meta era 70. Son las cinco vueltas que imprime el script, con su promedio. Y miren los errores, la columna de la derecha: es casi toda amarilla. De cada tres errores, dos no se guardan callados: van a revisión. Y cuando pone una categoría sin dudar, acierta casi nueve de cada diez. Lo que no sabe, lo pregunta."
EN VIVO, si lo piden: "Lo corro acá." Terminal "2 · Las cinco vueltas" → clic en la ventana → Enter (el comando ya está escrito; también está en la filmina, para copiarlo). Tarda menos de un segundo y no cambia nada. Las últimas líneas son las de la filmina: las cinco vueltas y los errores (más arriba quedan las métricas por categoría y la matriz). Si vas atrasado, no lo corras: la filmina es la misma salida. Ojo: necesita el contenedor api corriendo (docker compose up -d).
Las cinco vueltas (StratifiedKFold, las mismas particiones de la tesis): 84,2 · 78,3 · 75,8 · 70,0 · 71,7 → promedio 76,0. Cada vuelta, 120 gastos que no vio.
Cómo leer el mosaico, en criollo: la columna de la izquierda son los aciertos y la de la derecha, los errores (el ancho es cuántos). Arriba, lo que guardó sin preguntar; abajo, lo que mandó a revisión. Lo que importa es la columna de los errores: casi toda amarilla, o sea, casi todos los errores se atajan.
Respaldo (de 600 que el modelo no había visto): acertó y estaba seguro 378 · acertó, pero pidió revisión 78 · se equivocó y pidió revisión 93 · se equivocó estando seguro 51. SVM 76 % · Naive Bayes 74 %.
Y en la demo ya se vio: de los 26 gastos nuevos del extracto, a 23 les puso categoría y 3 los mandó a "Otros" (el coworking, Telecentro y la Visa).
¿Lo de los errores está en la tesis? "No: es una medición extra sobre los mismos 600 ejemplos y las mismas cinco vueltas. El script la imprime al final."`);
kicker(s, "Anexo · clasificador · se puede probar");
titulo(s, "Cuando se equivoca, la mayoría de las veces avisa");
texto(s, "El examen: gastos que el modelo no había visto, en cinco vueltas. Para cada uno: ¿acertó? ¿pidió revisión?", {
  x:0.6, y:1.55, w:12.1, h:0.4, fontSize:14.5, italic:true });
// La terminal, con la salida real del script (recortada: sin métricas por categoría ni matriz).
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:2.1, w:6.95, h:4.72, fill:{color:NAVY3}, line:{color:"23415F", width:1},
  rectRadius:0.07, shadow:{ type:"outer", color:"0A1622", blur:10, offset:3, angle:90, opacity:0.35 } });
["FF5F57", "FEBC2E", "28C840"].forEach((c, i) =>
  s.addShape(pptx.ShapeType.ellipse, { x:0.72 + i * 0.15, y:2.18, w:0.09, h:0.09, fill:{color:c}, line:{color:c, width:0} }));
// El comando va en su propio cuadro, sin el "$", para poder copiarlo desde la filmina.
s.addText("$", { x:0.85, y:2.4, w:0.2, h:0.25, fontFace:FM, fontSize:10.5, color:GREY, margin:0, valign:"middle", isTextBox:true });
s.addText("docker compose exec -T api python - < evaluar_modelo.py", { x:1.05, y:2.4, w:6.4, h:0.25, fontFace:FM, fontSize:10.5, color:MINT, margin:0, valign:"middle", isTextBox:true });
const salida = [
  [[["EVALUACIÓN DEL MODELO BASE — algoritmo: svm", WHITE]]],
  [[["Accuracy global: 0.7600  (76.00%)", WHITE]]],
  [[["…", GREY]]],
  [[["── Las cinco vueltas: cada una, un examen con gastos que no vio ──", TEAL_L]]],
  [[["Vuelta 1    84.2 %   (120 gastos)", ICE]]],
  [[["Vuelta 2    78.3 %   (120 gastos)", ICE]]],
  [[["Vuelta 3    75.8 %   (120 gastos)", ICE]]],
  [[["Vuelta 4    70.0 %   (120 gastos)", ICE]]],
  [[["Vuelta 5    71.7 %   (120 gastos)", ICE]]],
  [[["Promedio    76.0 %", MINT]]],
  [[["── Qué pasa con los errores (vara de confianza 30%) ──", TEAL_L]]],
  [[["Acertó y estaba seguro          378", ICE]], MINT],
  [[["Acertó, pero pidió revisión      78", ICE]], TEAL_L],
  [[["Se equivocó y pidió revisión     93", ICE]], AMARILLO],
  [[["Se equivocó estando seguro       51", ICE]], ROJO],
  [[["De los 144 errores, 93 (65%) van a revisión en vez de guardarse mal.", "F2C26B"]]],
  [[["Cuando pone una categoría sin dudar, acierta el 88%.", MINT]]],
];
salida.forEach((l, i) => {
  const y = 2.72 + i * 0.232;
  s.addText(l[0].map(t => ({ text:t[0], options:{ color:t[1] } })), {
    x:1.05, y, w:6.4, h:0.232, fontFace:FM, fontSize:10, margin:0, valign:"middle", isTextBox:true });
  if (l[1]) s.addShape(pptx.ShapeType.rect, { x:0.8, y:y + 0.05, w:0.13, h:0.13, fill:{color:l[1]}, line:{color:l[1], width:0} });
});
// El mosaico: columnas = acertó / se equivocó; bloques = seguro (arriba) / a revisión (abajo).
const mxo = 7.85, myo = 2.5, mwo = 4.85, mho = 2.2, gap = 0.05;
const anchoA = (mwo - gap) * 456 / 600, anchoE = (mwo - gap) * 144 / 600, xE = mxo + anchoA + gap;
texto(s, "Acertó", { x:mxo, y:2.12, w:anchoA, h:0.32, fontSize:13, bold:true, color:INK, align:"center" });
texto(s, "Se equivocó", { x:xE - 0.2, y:2.12, w:anchoE + 0.4, h:0.32, fontSize:13, bold:true, color:INK, align:"center" });
[[mxo, anchoA, 378 / 456, 78 / 456, MINT, TEAL_L], [xE, anchoE, 51 / 144, 93 / 144, ROJO, AMARILLO]].forEach(c => {
  const hA = (mho - gap) * c[2], hB = (mho - gap) * c[3];
  s.addShape(pptx.ShapeType.rect, { x:c[0], y:myo, w:c[1], h:hA, fill:{color:c[4]}, line:{color:c[4], width:0} });
  s.addShape(pptx.ShapeType.rect, { x:c[0], y:myo + hA + gap, w:c[1], h:hB, fill:{color:c[5]}, line:{color:c[5], width:0} });
});
// Qué quiere decir cada color.
[[MINT, "Acertó y estaba seguro:", "se guarda bien."],
 [TEAL_L, "Acertó, pero preguntó:", "un clic de más."],
 [AMARILLO, "Se equivocó, pero preguntó:", "el error se ataja."],
 [ROJO, "Se equivocó sin preguntar:", "el error se cuela."]].forEach((t, i) => {
  const y = 4.92 + i * 0.44;
  s.addShape(pptx.ShapeType.rect, { x:7.85, y:y + 0.1, w:0.22, h:0.22, fill:{color:t[0]}, line:{color:t[0], width:0} });
  s.addText([{ text:t[1] + " ", options:{ bold:true, color:INK } }, { text:t[2], options:{ color:TEXTO } }], {
    x:8.22, y, w:4.5, h:0.42, fontFace:FB, fontSize:13, valign:"middle", margin:0, isTextBox:true });
});

// ── Anexo · las pruebas automáticas (HU-16) ─────────────────────────────────
// Salida real de la suite del servidor (12/10, sin las tres líneas de versiones
// del encabezado). En vivo, la terminal 4 de abrir_terminales.sh la corre entera
// (unos dos minutos) y la 3, solo las de seguridad con el nombre de cada caso.
const PYTEST = `=========================== test session starts ============================
collected 447 items
tests/test_auditoria.py ........................                         [  5%]
tests/test_auth.py .....................                                 [ 10%]
tests/test_estado_fiscal.py ...............................              [ 17%]
tests/test_facturas.py .............................                     [ 23%]
tests/test_gastos.py .............................                       [ 29%]
tests/test_ia.py ..........                                              [ 32%]
tests/test_importar.py ................................................. [ 43%]
.......................................................                  [ 55%]
tests/test_ingresos.py .........................................         [ 64%]
tests/test_migraciones.py ..                                             [ 65%]
tests/test_ml.py ...................                                     [ 69%]
tests/test_monotributo.py ...........                                    [ 71%]
tests/test_proyecciones.py ..................................            [ 79%]
tests/test_recomendaciones.py ...............................            [ 86%]
tests/test_reportes.py ..........................                        [ 92%]
tests/test_resumen_ia.py ..................................              [ 99%]
tests/test_seed_demo.py .                                                [100%]
======================= 447 passed in 136.71s (0:02:16) ========================`.split("\n");
s = slide(false, `Anexo: si preguntan cómo se verificó que el sistema funciona, o por las pruebas. En la tesis es la HU-16 ("Suite automatizada de pruebas") y la mitigación del riesgo R4.
Lo que se dice con ella: "Además de probarlo a mano, el sistema tiene pruebas automáticas: pequeños programas que lo usan como lo usaría una persona y revisan el resultado. Por ejemplo, uno entra con una contraseña equivocada y comprueba que no lo deje pasar; otro importa dos extractos que se pisan y comprueba que no guarde dos veces lo repetido. Cada línea es un módulo: auditoría, autenticación, estado fiscal, facturas, gastos, importación… Y cada punto es una prueba que pasó. Corren sobre una base aparte, en memoria, que se crea y se borra en cada prueba: no tocan los datos de la demo. Si una falla, dice el archivo y el nombre del caso. Así, cada vez que cambiaba algo, comprobaba que no se rompiera lo que ya andaba."
EN VIVO, si lo piden: terminal "4 · Todas las pruebas automáticas" → clic en la ventana → Enter (el comando ya está escrito). Tarda unos dos minutos: hablá mientras corre (lo de arriba alcanza). Si vas justo de tiempo: terminal "3 · Las pruebas de seguridad" → Enter: unos segundos, y se lee el nombre de cada caso. Las terminales se abren con: sh defensa_final/demo/terminales/abrir_terminales.sh (también están los dos comandos en la filmina, para copiarlos).
Cómo leer los nombres de la terminal 3, en criollo: register_exitoso = registrarse bien · email_duplicado = un correo ya usado · login_password_incorrecto = contraseña equivocada · ruta_privada_sin_token = entrar a una pantalla sin iniciar sesión · token_manipulado = un pase adulterado · aislamiento_entre_usuarios = nadie ve lo de otro · clave_de_firma_insegura_frena_el_arranque = con una clave del servidor débil, el sistema no arranca · login_con_correo_inexistente_tambien_verifica_la_contrasena = un correo que no existe tarda lo mismo.
Respaldo: 447 pruebas del servidor en 17 archivos (12/10: 2 min 16 s), más 16 de las pantallas, aparte. "-p no:warnings" apaga los avisos de las bibliotecas (Pydantic, httpx, scikit-learn) que anuncian cambios de versiones futuras; sin eso, el resumen suma 638 avisos. Si preguntan: "Son avisos de que algunas bibliotecas van a cambiar en versiones futuras, no fallas. Los apago para que se lea el resultado."`);
kicker(s, "Anexo · pruebas automáticas");
titulo(s, "Todo el sistema se prueba con un comando");
// La terminal, con la salida real de la suite.
s.addShape(pptx.ShapeType.roundRect, { x:0.6, y:1.8, w:7.6, h:4.98, fill:{color:NAVY3}, line:{color:"23415F", width:1},
  rectRadius:0.07, shadow:{ type:"outer", color:"0A1622", blur:10, offset:3, angle:90, opacity:0.35 } });
["FF5F57", "FEBC2E", "28C840"].forEach((c, i) =>
  s.addShape(pptx.ShapeType.ellipse, { x:0.72 + i * 0.15, y:1.88, w:0.09, h:0.09, fill:{color:c}, line:{color:c, width:0} }));
// El comando va en su propio cuadro, sin el "$", para poder copiarlo desde la filmina.
s.addText("$", { x:0.85, y:2.1, w:0.2, h:0.27, fontFace:FM, fontSize:10.5, color:GREY, margin:0, valign:"middle", isTextBox:true });
s.addText("docker compose exec api python -m pytest -p no:warnings", { x:1.05, y:2.1, w:6.9, h:0.27, fontFace:FM, fontSize:10.5, color:MINT, margin:0, valign:"middle", isTextBox:true });
PYTEST.forEach((l, i) => {
  const m = l.match(/^(tests\/\S+ )?(\.+)(\s+\[[ \d]+%\])$/);
  const partes = m ? [[m[1] || "", ICE], [m[2], MINT], [m[3], GREY]]
               : [[l, l.includes("passed") ? MINT : (l.startsWith("=") ? GREY : WHITE)]];
  s.addText(partes.filter(p => p[0]).map(p => ({ text:p[0], options:{ color:p[1], bold: l.includes("passed") } })), {
    x:0.85, y:2.45 + i * 0.2, w:7.25, h:0.2, fontFace:FM, fontSize:9.5, margin:0, valign:"middle", isTextBox:true });
});
// Qué es una prueba automática, para quien no programa.
card(s, 8.45, 1.8, 4.25, 2.2, { line:TEAL_L, lw:1.25 });
icono(s, "ListChecks", 8.68, 1.97, 0.5, TEAL);
s.addText("¿Qué es una prueba automática?", { x:9.3, y:1.98, w:3.3, h:0.48, fontFace:FH, fontSize:15, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
s.addText([
  { text:"Un pequeño programa que usa el sistema como lo usaría una persona y revisa el resultado.", options:{ breakLine:true } },
  { text:"Por ejemplo: entra con una contraseña equivocada y comprueba que no lo deje pasar.", options:{ bullet:{ indent:13 }, breakLine:true } },
  { text:"Cada punto de la terminal es una prueba que pasó.", options:{ bold:true, color:INK } },
], { x:8.68, y:2.56, w:3.85, h:1.38, fontFace:FB, fontSize:12, color:TEXTO, valign:"top", margin:0, paraSpaceAfter:3, isTextBox:true });
[["Database", "Usan una base aparte", "Se crea en memoria para cada prueba y se borra al terminar: no tocan los datos de la demo."],
 ["FileX", "Si una falla, dice cuál", "Muestra el archivo y el nombre del caso."]].forEach((p, i) => {
  const y = 4.18 + i * 0.86;
  icono(s, p[0], 8.5, y, 0.56, [MINT, AMARILLO][i], i === 1 ? "n" : "b");
  s.addText(p[1], { x:9.24, y:y-0.04, w:3.5, h:0.34, fontFace:FH, fontSize:13.5, bold:true, color:INK, margin:0, isTextBox:true });
  texto(s, p[2], { x:9.24, y:y+0.3, w:3.5, h:0.5, fontSize:11.5 });
});
// La versión corta, para correr en segundos: las de seguridad, con el nombre de cada caso.
texto(s, "En segundos: solo las de seguridad, con el nombre de cada caso", { x:8.45, y:5.86, w:4.25, h:0.25, fontSize:10.5, italic:true, color:TEAL });
s.addShape(pptx.ShapeType.roundRect, { x:8.45, y:6.13, w:4.25, h:0.65, fill:{color:NAVY3}, line:{color:"23415F", width:1}, rectRadius:0.07 });
s.addText("$", { x:8.58, y:6.2, w:0.2, h:0.25, fontFace:FM, fontSize:10, color:GREY, margin:0, valign:"middle", isTextBox:true });
s.addText("docker compose exec api python -m pytest tests/test_auth.py -v -p no:warnings", { x:8.78, y:6.2, w:3.85, h:0.52, fontFace:FM, fontSize:10, color:MINT, margin:0, valign:"top", isTextBox:true });

// ── Seguridad, ampliada ─────────────────────────────────────────────────────
s = slide(false, `· Hashear (contraseña, bcrypt con sal): una sola vía.
· Firmar (pase de sesión, HMAC-SHA256 con una clave que solo tiene el servidor; vence a los 7 días): se lee, pero no se falsifica.
· Cifrar (HTTPS hacia el único servicio externo, que recibe solo totales): se abre con la llave.
· El usuario sale siempre del pase firmado, nunca de lo que manda el navegador: lo ajeno responde igual que lo inexistente.
· Base, servidor y aplicación atienden solo en esta computadora.
· Lo que no hace (para producción): base cifrada en disco, anular un pase antes de que venza, límite de intentos de inicio de sesión.`);
kicker(s, "Anexo · seguridad");
titulo(s, "Hashear, firmar y cifrar no son lo mismo");
[["Shield", "Hashear", "No vuelve", "La contraseña: ni el sistema puede recuperarla.", TEAL],
 ["Signature", "Firmar", "No se falsifica", "El pase de sesión: se puede leer, pero si lo tocan deja de servir.", MINT],
 ["Lock", "Cifrar", "Vuelve, con la llave", "Lo que viaja al único servicio externo, que recibe solo totales.", AMARILLO]].forEach((v, i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 1.95, 3.85, 2.75);
  icono(s, v[0], x + 0.3, 2.2, 0.8, v[4], v[4] === AMARILLO ? "n" : "b");
  s.addText(v[1], { x:x+1.3, y:2.2, w:2.4, h:0.5, fontFace:FH, fontSize:21, bold:true, color:INK, margin:0, isTextBox:true });
  s.addText(v[2], { x:x+1.3, y:2.7, w:2.4, h:0.35, fontFace:FB, fontSize:13, italic:true, color:TEAL, margin:0, isTextBox:true });
  texto(s, v[3], { x:x+0.3, y:3.3, w:3.25, h:1.3, fontSize:13.5 });
});
card(s, 0.6, 4.95, 12.1, 1.65, { fill:NAVY, line:NAVY });
texto(s, "Lo que el prototipo no hace (es lo primero para producción)", { x:0.9, y:5.1, w:11.5, h:0.4, fontSize:14, bold:true, color:AMARILLO });
texto(s, "La base no está cifrada en disco  ·  un pase no se puede anular antes de que venza  ·  no hay límite de intentos de inicio de sesión", {
  x:0.9, y:5.6, w:11.5, h:0.8, fontSize:14, color:WHITE });

// ── Plan B: la demo en capturas ─────────────────────────────────────────────
// Si algo falla en vivo: recargar (Cmd + R); si no vuelve, "Tengo un problema de
// entorno. Les muestro la misma pantalla en captura, y si da el tiempo vuelvo al final."
const planB = [["importacion_vista_previa", "Importación: la vista previa con los avisos", "Plan B si falla en vivo: 3 repetidos, 2 de transferencia propia, 1 fila con fecha inexistente; cada gasto con su categoría (coworking a «Otros»)."],
               ["importacion_resultado", "Importación: lo que guardó y lo que dejó afuera", "Plan B: guardó solo lo que corresponde; omitió los repetidos y la transferencia propia, y marcó los dos Figma como posible repetido."],
               ["dashboard", "Panel: octubre, ya cargado", "Plan B: abre en el mes actual; en «Últimos movimientos», Grupo Delta (+ $ 1.850.000, punto de miles) y la Visa; abajo, el aviso de alcance."],
               ["auditoria", "Auditoría: las alertas", "Plan B: Figma duplicado, Adobe duplicado de junio, el servidor irregular y las dos facturas vencidas."],
               ["monotributo", "Estado fiscal: el semáforo", "Plan B: rojo, te pasarías en diciembre; la categoría que cubriría esa facturación es la H; cuota de octubre pagada."],
               ["proyecciones", "Proyección: los tres escenarios", "Plan B: Prophet con los meses cerrados; octubre hueco; banda pesimista–optimista."],
               ["recomendaciones", "Recomendaciones: cada una con su «por qué»", "Plan B: reglas fijas, ordenadas por urgencia."]];
planB.forEach(p => {
  s = slide(false, p[2]);
  kicker(s, "Anexo · plan B · la demo en capturas");
  titulo(s, p[1], false, 26);
  const t = pngSize(path.join(CAP, p[0] + ".png")), alto = 5.3;
  const ancho = (alto - 0.29) * t.w / t.h + 0.1;      // el mismo cálculo que hace ventana()
  ventana(s, p[0], (13.333 - ancho) / 2, 1.6, 0, { alto });
});
// El reporte: las dos hojas, una al lado de la otra.
s = slide(false, "Plan B: el reporte de septiembre, dos hojas. Al pie: «no reemplaza el asesoramiento de un contador matriculado».");
kicker(s, "Anexo · plan B · la demo en capturas");
titulo(s, "Reporte PDF: el resumen del mes cerrado", false, 26);
["reporte_pdf_1", "reporte_pdf_2"].forEach((h, i) => {
  const t = pngSize(path.join(CAP, h + ".png")), alto = 5.25, ancho = alto * t.w / t.h;
  s.addShape(pptx.ShapeType.rect, { x:3.0 + i * 3.9, y:1.6, w:ancho, h:alto, fill:{color:WHITE}, line:{color:BORDE, width:1},
    shadow:{ type:"outer", color:"9AA9B8", blur:8, offset:2, angle:90, opacity:0.3 } });
  s.addImage({ path:path.join(CAP, h + ".png"), x:3.0 + i * 3.9, y:1.6, w:ancho, h:alto });
});

pptx.writeFile({ fileName: SALIDA }).then(f => console.log("OK:", f, "·", n, "filminas"));
