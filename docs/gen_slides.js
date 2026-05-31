// Slides de defensa — TFG FreelanceControl
// Reproducible: node docs/gen_slides.js   (requiere pptxgenjs global)
// Las imágenes de métricas conservan su aspect ratio real para no deformarse:
//   metricas_f1_por_categoria.png  1744x1261  (h/w = 0.7231)
//   metricas_matriz_confusion.png  1744x1504  (h/w = 0.8624)
const PptxGenJS = require("/opt/homebrew/lib/node_modules/pptxgenjs");
const pptx = new PptxGenJS();
pptx.defineLayout({ name: "W", width: 13.33, height: 7.5 });
pptx.layout = "W";
pptx.author = "TFG FreelanceControl";
pptx.title = "FreelanceControl — Defensa";

const NAVY = "0D2B45", NAVY2 = "14395E", TEAL = "1C7293", TEAL_L = "5BB3C4";
const MINT = "02C39A", ICE = "CADCFC", WHITE = "FFFFFF", GREY = "8FA3B5";
const VERDE = "2E9E5B", AMARILLO = "E0A82E", ROJO = "D14D4D";
const CREAM = "F4F7FB", INK = "16222E";
const DOCS = "/Users/marcosjoaquin/proyecto-tfg/docs";
const FH = "Georgia", FB = "Calibri";

function bgDark(s){ s.background = { color: NAVY }; }
function bgLight(s){ s.background = { color: CREAM }; }
function kicker(s, txt, color){
  s.addText(txt.toUpperCase(), { x:0.7, y:0.55, w:11.9, h:0.35, fontFace:FB, fontSize:13,
    color: color||MINT, bold:true, charSpacing:3 });
}
function title(s, txt, color){
  s.addText(txt, { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:32, bold:true, color: color||INK });
}
function footer(s, n){
  s.addText("FreelanceControl · Defensa TFG", { x:0.7, y:7.08, w:7, h:0.3, fontFace:FB, fontSize:9, color: GREY });
  s.addText(String(n), { x:12.4, y:7.08, w:0.5, h:0.3, fontFace:FB, fontSize:9, color: GREY, align:"right" });
}

// ── SLIDE 1 — Portada ──
let s = pptx.addSlide(); bgDark(s);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:7.5, fill:{color:MINT} });
s.addText("TRABAJO FINAL DE GRADO · INGENIERÍA EN SISTEMAS DE INFORMACIÓN", {
  x:0.9, y:1.7, w:11.5, h:0.4, fontFace:FB, fontSize:13, color:TEAL_L, bold:true, charSpacing:2 });
s.addText("FreelanceControl", { x:0.85, y:2.2, w:11.7, h:1.4, fontFace:FH, fontSize:60, bold:true, color:WHITE });
s.addText("Gestión financiera y fiscal inteligente para monotributistas argentinos", {
  x:0.9, y:3.65, w:10.8, h:0.7, fontFace:FB, fontSize:20, color:ICE });
const chips = ["Clasificación ML local", "Proyección Prophet", "Semáforo Monotributo", "Auditoría automática"];
let cx = 0.9;
chips.forEach(c=>{
  const w = 0.4 + c.length*0.108;
  s.addShape(pptx.ShapeType.roundRect, { x:cx, y:4.75, w:w, h:0.5, fill:{color:NAVY2}, line:{color:TEAL, width:1}, rectRadius:0.1 });
  s.addText(c, { x:cx, y:4.75, w:w, h:0.5, fontFace:FB, fontSize:12.5, color:ICE, align:"center", valign:"middle" });
  cx += w + 0.25;
});
s.addText("Defensa · Mayo 2026", { x:0.9, y:6.4, w:6, h:0.4, fontFace:FB, fontSize:14, color:GREY });

// ── SLIDE 2 — El problema ──
s = pptx.addSlide(); bgLight(s);
kicker(s, "El punto de partida", TEAL);
title(s, "Cuatro problemas concretos del monotributista");
const probs = [
  ["Flujo de caja variable", "Ingresos dependientes de entregables y plazos de cada cliente. Las herramientas registran, pero no proyectan."],
  ["Riesgo fiscal silencioso", "El límite de la categoría se descubre superado recién al cierre del año. No hay anticipación."],
  ["Inconsistencias no detectadas", "Duplicados, facturas vencidas y cuotas impagas que solo se cruzan manualmente al cierre."],
  ["Fragmentación documental", "Planillas, apps, correos y CSV de homebanking dispersos, sin consulta consolidada."],
];
probs.forEach((p,i)=>{
  const col = i%2, row = Math.floor(i/2);
  const x = 0.7 + col*6.1, y = 2.2 + row*2.35;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.75, h:2.05, fill:{color:WHITE}, line:{color:"DCE4EC", width:1}, rectRadius:0.08,
    shadow:{type:"outer", color:"AAB7C4", blur:6, offset:2, angle:90, opacity:0.3} });
  s.addShape(pptx.ShapeType.roundRect, { x:x+0.3, y:y+0.32, w:0.55, h:0.55, fill:{color:TEAL}, rectRadius:0.27 });
  s.addText(String(i+1), { x:x+0.3, y:y+0.32, w:0.55, h:0.55, fontFace:FH, fontSize:22, bold:true, color:WHITE, align:"center", valign:"middle" });
  s.addText(p[0], { x:x+1.05, y:y+0.3, w:4.5, h:0.55, fontFace:FH, fontSize:17, bold:true, color:INK, valign:"middle" });
  s.addText(p[1], { x:x+0.32, y:y+1.0, w:5.2, h:0.95, fontFace:FB, fontSize:13, color:"4A5A68" });
});
footer(s,2);

// ── SLIDE 3 — La propuesta ──
s = pptx.addSlide(); bgDark(s);
kicker(s, "La propuesta", MINT);
s.addText("Un sistema que centraliza, clasifica y anticipa", { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:32, bold:true, color:WHITE });
const sol = [
  ["Centraliza", "Ingresos, gastos y facturas en una base relacional con aislamiento por usuario.", TEAL_L],
  ["Clasifica", "Cada gasto recibe categoría automática vía PLN local; el modelo aprende de tus correcciones.", MINT],
  ["Anticipa", "Proyecta el flujo a 6 meses y avisa el riesgo de recategorización antes del cierre fiscal.", AMARILLO],
];
sol.forEach((c,i)=>{
  const x = 0.7 + i*4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.4, w:3.8, h:3.4, fill:{color:NAVY2}, line:{color:c[2], width:1.5}, rectRadius:0.1 });
  s.addText(c[0], { x:x+0.35, y:2.85, w:3.1, h:0.7, fontFace:FH, fontSize:26, bold:true, color:c[2] });
  s.addText(c[1], { x:x+0.35, y:3.75, w:3.15, h:1.9, fontFace:FB, fontSize:15, color:ICE });
});
s.addText("Núcleo de procesamiento local · soberanía de datos · IA externa solo sobre agregados numéricos", {
  x:0.7, y:6.25, w:11.9, h:0.5, fontFace:FB, fontSize:14, italic:true, color:GREY, align:"center" });
footer(s,3);

// ── SLIDE 4 — Arquitectura ──
s = pptx.addSlide(); bgLight(s);
kicker(s, "Arquitectura", TEAL);
title(s, "Tres capas contenedorizadas");
const capas = [
  ["Presentación", "React · 13 pantallas · tema oscuro", "Puerto 3000", TEAL],
  ["API REST", "FastAPI · Python 3.11 · JWT · ML · Prophet", "Puerto 8000", MINT],
  ["Persistencia", "PostgreSQL 15 · 9 tablas · 5 migraciones Alembic", "Puerto 5432", NAVY2],
];
capas.forEach((c,i)=>{
  const y = 2.25 + i*1.35;
  s.addShape(pptx.ShapeType.roundRect, { x:0.7, y, w:8.3, h:1.15, fill:{color:WHITE}, line:{color:"DCE4EC",width:1}, rectRadius:0.08 });
  s.addShape(pptx.ShapeType.roundRect, { x:0.7, y, w:0.16, h:1.15, fill:{color:c[3]}, rectRadius:0.04 });
  s.addText(c[0], { x:1.05, y:y+0.18, w:3, h:0.5, fontFace:FH, fontSize:19, bold:true, color:INK });
  s.addText(c[1], { x:1.05, y:y+0.65, w:6, h:0.4, fontFace:FB, fontSize:13.5, color:"4A5A68" });
  s.addShape(pptx.ShapeType.roundRect, { x:7.4, y:y+0.35, w:1.45, h:0.45, fill:{color:c[3]}, rectRadius:0.1 });
  s.addText(c[2], { x:7.4, y:y+0.35, w:1.45, h:0.45, fontFace:FB, fontSize:11, color:WHITE, align:"center", valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:9.35, y:2.25, w:3.25, h:4.05, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("STACK CLAVE", { x:9.6, y:2.47, w:2.8, h:0.4, fontFace:FB, fontSize:12, bold:true, color:MINT, charSpacing:2 });
const stack = ["scikit-learn — SVM + TF-IDF","Prophet — series temporales","Groq llama-3.3 — solo agregados","ReportLab — PDF","Docker Compose","pytest — 97 tests"];
stack.forEach((t,i)=>{
  s.addText("›", { x:9.6, y:3.0+i*0.52, w:0.3, h:0.4, fontFace:FB, fontSize:15, color:MINT, bold:true });
  s.addText(t, { x:9.9, y:3.0+i*0.52, w:2.6, h:0.45, fontFace:FB, fontSize:12, color:ICE, valign:"middle" });
});
footer(s,4);

// ── SLIDE 5 — ML local ──
s = pptx.addSlide(); bgDark(s);
kicker(s, "Decisión de diseño central", MINT);
s.addText("¿Por qué la clasificación corre 100% local?", { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:31, bold:true, color:WHITE });
s.addText("La descripción de un gasto es información financiera sensible. Enviarla a un servicio externo significaría ceder el historial de consumo del usuario a un tercero.", {
  x:0.7, y:2.05, w:7.4, h:1.2, fontFace:FB, fontSize:17, color:ICE });
const facts = [
  ["SVM + TF-IDF","Modelo entrenado sobre 600 ejemplos en 12 categorías"],
  ["Cortocircuito","Las correcciones del usuario responden al instante con confianza 1.0"],
  ["Umbral 0.30","Bajo confianza → 'Otros' + revisión manual, en vez de adivinar"],
  ["Groq acotado","Solo resúmenes y recomendaciones, sobre datos numéricos agregados"],
];
facts.forEach((f,i)=>{
  const y = 3.5 + i*0.82;
  s.addShape(pptx.ShapeType.roundRect, { x:0.7, y, w:7.4, h:0.7, fill:{color:NAVY2}, rectRadius:0.06 });
  s.addText(f[0], { x:0.95, y, w:2.2, h:0.7, fontFace:FH, fontSize:14, bold:true, color:MINT, valign:"middle" });
  s.addText(f[1], { x:3.2, y, w:4.75, h:0.7, fontFace:FB, fontSize:12, color:ICE, valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:8.45, y:2.05, w:4.15, h:4.65, fill:{color:MINT}, rectRadius:0.12 });
s.addText("Soberanía\nde datos", { x:8.7, y:2.4, w:3.7, h:1.3, fontFace:FH, fontSize:30, bold:true, color:NAVY });
s.addText("La información sensible nunca abandona la infraestructura del usuario.", {
  x:8.7, y:3.8, w:3.7, h:1.4, fontFace:FB, fontSize:16, color:NAVY });
s.addText("Valor diferencial del proyecto", { x:8.7, y:6.05, w:3.7, h:0.5, fontFace:FB, fontSize:12.5, italic:true, color:NAVY2 });
footer(s,5);

// ── SLIDE 6 — Métricas ──  (imagen ratio h/w 0.7231 → 6.78 x 4.9)
s = pptx.addSlide(); bgLight(s);
kicker(s, "Resultados medidos", TEAL);
title(s, "Desempeño del clasificador");
s.addImage({ path:`${DOCS}/metricas_f1_por_categoria.png`, x:0.75, y:2.15, w:6.78, h:4.9 });
s.addShape(pptx.ShapeType.roundRect, { x:8.0, y:2.15, w:4.65, h:4.9, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("76%", { x:8.25, y:2.4, w:4.2, h:1.0, fontFace:FH, fontSize:54, bold:true, color:MINT });
s.addText("accuracy global · cross-validation 5-fold", { x:8.3, y:3.45, w:4.1, h:0.5, fontFace:FB, fontSize:13, color:ICE });
s.addShape(pptx.ShapeType.line, { x:8.3, y:4.05, w:4.0, h:0, line:{color:TEAL, width:1} });
s.addText("Mejores categorías", { x:8.3, y:4.18, w:4.1, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:TEAL_L, charSpacing:1 });
s.addText("Monotributo  F1 0.96\nImpuestos  F1 0.91\nTransporte  F1 0.88", { x:8.3, y:4.55, w:4.1, h:1.0, fontFace:FB, fontSize:13, color:ICE });
s.addText("A mejorar", { x:8.3, y:5.65, w:4.1, h:0.35, fontFace:FB, fontSize:11.5, bold:true, color:AMARILLO, charSpacing:1 });
s.addText("Marketing  F1 0.58\nServicios  F1 0.63", { x:8.3, y:6.0, w:4.1, h:0.8, fontFace:FB, fontSize:13, color:ICE });
footer(s,6);

// ── SLIDE 7 — Matriz de confusión ──  (imagen ratio h/w 0.8624 → 5.80 x 5.0)
s = pptx.addSlide(); bgLight(s);
kicker(s, "Resultados medidos", TEAL);
title(s, "Matriz de confusión");
s.addImage({ path:`${DOCS}/metricas_matriz_confusion.png`, x:0.7, y:2.0, w:5.80, h:5.0 });
s.addShape(pptx.ShapeType.roundRect, { x:6.95, y:2.05, w:5.7, h:4.95, fill:{color:WHITE}, line:{color:"DCE4EC",width:1}, rectRadius:0.1 });
s.addText("Cómo leerla", { x:7.2, y:2.25, w:5.2, h:0.5, fontFace:FH, fontSize:18, bold:true, color:INK });
const reads = [
  "La diagonal verde son los aciertos: concentra la mayoría de los casos.",
  "Las confusiones son coherentes: categorías de vocabulario afín se solapan.",
  "Software, Infraestructura y Capacitación derivan parte a Suscripciones (todo es SaaS hoy).",
  "'Otros' no es un vertedero: F1 0.76, distingue lo genuinamente inclasificable.",
];
reads.forEach((r,i)=>{
  const y = 2.95 + i*1.0;
  s.addShape(pptx.ShapeType.roundRect, { x:7.2, y:y+0.05, w:0.14, h:0.78, fill:{color:MINT}, rectRadius:0.04 });
  s.addText(r, { x:7.5, y, w:4.9, h:0.92, fontFace:FB, fontSize:12.5, color:"3A4A58", valign:"middle" });
});
footer(s,7);

// ── SLIDE 8 — Prophet→Monotributo ──
s = pptx.addSlide(); bgDark(s);
kicker(s, "El diferencial", MINT);
s.addText("Del dato histórico al aviso fiscal anticipado", { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:31, bold:true, color:WHITE });
const flow = [["Ingresos\nhistóricos","Lo ya facturado en el año"],["Proyección\nProphet","Estima hasta el 31/12 con IC"],["Semáforo\nfiscal","% proyectado sobre el límite"]];
flow.forEach((f,i)=>{
  const x = 0.7 + i*3.3;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.2, w:2.85, h:1.6, fill:{color:NAVY2}, line:{color:TEAL,width:1}, rectRadius:0.1 });
  s.addText(f[0], { x:x+0.2, y:2.38, w:2.45, h:0.85, fontFace:FH, fontSize:17, bold:true, color:WHITE, align:"center" });
  s.addText(f[1], { x:x+0.2, y:3.2, w:2.45, h:0.5, fontFace:FB, fontSize:11.5, color:ICE, align:"center" });
  if(i<2) s.addText("→", { x:x+2.92, y:2.55, w:0.5, h:0.9, fontFace:FB, fontSize:28, bold:true, color:MINT, align:"center", valign:"middle" });
});
s.addText("El semáforo decide por la PROYECCIÓN, no por lo ya facturado:", { x:0.7, y:4.3, w:11.5, h:0.5, fontFace:FB, fontSize:16, color:ICE });
const sem = [["VERDE","< 70%","Sin riesgo",VERDE],["AMARILLO","70 – 90%","Precaución",AMARILLO],["ROJO","> 90%","Recategorizar",ROJO]];
sem.forEach((c,i)=>{
  const x=0.7+i*4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:5.0, w:3.8, h:1.55, fill:{color:NAVY2}, line:{color:c[3],width:2}, rectRadius:0.1 });
  s.addShape(pptx.ShapeType.ellipse, { x:x+0.3, y:5.3, w:0.6, h:0.6, fill:{color:c[3]} });
  s.addText(c[0], { x:x+1.05, y:5.25, w:2.6, h:0.45, fontFace:FH, fontSize:18, bold:true, color:c[3] });
  s.addText(c[1]+"  ·  "+c[2], { x:x+1.05, y:5.72, w:2.6, h:0.4, fontFace:FB, fontSize:13, color:ICE });
  s.addText("del límite anual", { x:x+0.3, y:6.08, w:3.3, h:0.35, fontFace:FB, fontSize:11, italic:true, color:GREY });
});
footer(s,8);

// ── SLIDE 9 — Auditoría ──
s = pptx.addSlide(); bgLight(s);
kicker(s, "Módulo de auditoría", TEAL);
title(s, "Cuatro detectores automáticos");
const det = [
  ["Gastos duplicados","Mismo monto, categoría y descripción en una ventana de 3 días.", TEAL],
  ["Anomalías estadísticas","z-score > 2σ respecto de la media de la categoría (mín. 5 gastos).", MINT],
  ["Facturas vencidas","Facturas pendientes cuya fecha de vencimiento ya pasó.", AMARILLO],
  ["Monotributo impago","Ausencia del pago de la cuota en el mes en curso.", ROJO],
];
det.forEach((d,i)=>{
  const col=i%2, row=Math.floor(i/2);
  const x=0.7+col*6.1, y=2.2+row*2.0;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.75, h:1.75, fill:{color:WHITE}, line:{color:"DCE4EC",width:1}, rectRadius:0.08 });
  s.addShape(pptx.ShapeType.roundRect, { x:x+0.25, y:y+0.32, w:0.6, h:0.6, fill:{color:d[2]}, rectRadius:0.3 });
  s.addText(String(i+1), { x:x+0.25, y:y+0.32, w:0.6, h:0.6, fontFace:FH, fontSize:22, bold:true, color:WHITE, align:"center", valign:"middle" });
  s.addText(d[0], { x:x+1.0, y:y+0.32, w:4.55, h:0.55, fontFace:FH, fontSize:17, bold:true, color:INK, valign:"middle" });
  s.addText(d[1], { x:x+1.0, y:y+0.95, w:4.6, h:0.7, fontFace:FB, fontSize:13, color:"4A5A68" });
});
s.addText("Regenera las alertas no resueltas y conserva las resueltas como historial auditable.", {
  x:0.7, y:6.4, w:11.9, h:0.45, fontFace:FB, fontSize:13.5, italic:true, color:TEAL, align:"center" });
footer(s,9);

// ── SLIDE 10 — Demo ──
s = pptx.addSlide(); bgDark(s);
kicker(s, "Demostración en vivo", MINT);
s.addText("Recorrido del prototipo", { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:32, bold:true, color:WHITE });
const demo = [
  ["1","Clasificar un gasto","El ML sugiere categoría y confianza"],
  ["2","Corregir y aprender","La corrección responde al instante la próxima vez"],
  ["3","Importar extracto","CSV de banco con detección automática de columnas"],
  ["4","Ejecutar auditoría","Las 4 alertas, una de cada tipo"],
  ["5","Estado Monotributo","Semáforo en rojo: proyección supera el límite"],
  ["6","Descargar PDF","Reporte mensual consolidado"],
];
demo.forEach((d,i)=>{
  const col=i%2, row=Math.floor(i/2);
  const x=0.7+col*6.05, y=2.2+row*1.45;
  s.addShape(pptx.ShapeType.roundRect, { x, y, w:5.7, h:1.25, fill:{color:NAVY2}, rectRadius:0.08 });
  s.addShape(pptx.ShapeType.ellipse, { x:x+0.28, y:y+0.32, w:0.6, h:0.6, fill:{color:MINT} });
  s.addText(d[0], { x:x+0.28, y:y+0.32, w:0.6, h:0.6, fontFace:FH, fontSize:22, bold:true, color:NAVY, align:"center", valign:"middle" });
  s.addText(d[1], { x:x+1.05, y:y+0.24, w:4.4, h:0.5, fontFace:FH, fontSize:16, bold:true, color:WHITE });
  s.addText(d[2], { x:x+1.05, y:y+0.72, w:4.5, h:0.45, fontFace:FB, fontSize:12, color:ICE });
});
s.addText("Usuario demo:  demo@freelancecontrol.com / demo1234", {
  x:0.7, y:6.8, w:11.9, h:0.4, fontFace:FB, fontSize:13, italic:true, color:TEAL_L, align:"center" });
footer(s,10);

// ── SLIDE 11 — Verificación ──
s = pptx.addSlide(); bgLight(s);
kicker(s, "Verificación", TEAL);
title(s, "Cómo sabemos que funciona");
const stats = [["97","tests automatizados\n11 módulos, todos verdes",MINT],["5","niveles de smoke E2E\nsobre PostgreSQL real",TEAL],["13/13","historias de usuario\nimplementadas y verificadas",NAVY2]];
stats.forEach((st,i)=>{
  const x=0.7+i*4.05;
  s.addShape(pptx.ShapeType.roundRect, { x, y:2.25, w:3.8, h:2.2, fill:{color:WHITE}, line:{color:"DCE4EC",width:1}, rectRadius:0.1 });
  s.addText(st[0], { x:x+0.2, y:2.45, w:3.4, h:1.0, fontFace:FH, fontSize:44, bold:true, color:st[2], align:"center" });
  s.addText(st[1], { x:x+0.25, y:3.55, w:3.3, h:0.8, fontFace:FB, fontSize:13, color:"4A5A68", align:"center" });
});
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:4.75, w:11.9, h:1.95, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("El valor del smoke E2E", { x:1.0, y:4.95, w:6, h:0.5, fontFace:FH, fontSize:18, bold:true, color:MINT });
s.addText("Los tests corren sobre SQLite; las pruebas de humo sobre PostgreSQL real expusieron defectos invisibles en el otro entorno: un enum incompatible que rompía la auditoría, el separador ';' no detectado en CSV de Galicia y un formato de moneda inconsistente. Todos corregidos y verificados.", {
  x:1.0, y:5.45, w:11.3, h:1.1, fontFace:FB, fontSize:13.5, color:ICE });
footer(s,11);

// ── SLIDE 12 — Cumplimiento ──
s = pptx.addSlide(); bgLight(s);
kicker(s, "Cumplimiento del Entregable 2", TEAL);
title(s, "Alcance cubierto y límite respetado");
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.15, w:6.0, h:4.55, fill:{color:WHITE}, line:{color:VERDE,width:1.5}, rectRadius:0.1 });
s.addText("Los 10 alcances declarados", { x:1.25, y:2.35, w:5.2, h:0.5, fontFace:FH, fontSize:17, bold:true, color:VERDE });
const alc = ["Auth con aislamiento por usuario","CRUD ingresos/gastos/facturas + estados","Clasificación PLN local","Reentrenamiento por correcciones","Importación CSV/Excel multibanco","Auditoría automatizada","Semáforo de Monotributo","Proyección 6 meses con IC","Resúmenes y recomendaciones IA","Reporte PDF mensual"];
alc.forEach((a,i)=>{
  s.addText("✓", { x:0.95, y:2.98+i*0.36, w:0.3, h:0.35, fontFace:FB, fontSize:13, bold:true, color:VERDE });
  s.addText(a, { x:1.3, y:2.98+i*0.36, w:5.2, h:0.35, fontFace:FB, fontSize:12.5, color:INK, valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:6.95, y:2.15, w:5.65, h:4.55, fill:{color:NAVY}, rectRadius:0.1 });
s.addText("Límite respetado", { x:7.2, y:2.35, w:5.2, h:0.5, fontFace:FH, fontSize:17, bold:true, color:TEAL_L });
s.addText("Fuera de alcance por diseño — no implementarlo es cumplir el Entregable 2:", { x:7.2, y:2.9, w:5.15, h:0.7, fontFace:FB, fontSize:13, italic:true, color:ICE });
const lim = ["Integración con facturación electrónica de AFIP","Conciliación bancaria con cuentas reales","Gestión de clientes como entidad propia"];
lim.forEach((l,i)=>{
  s.addShape(pptx.ShapeType.roundRect, { x:7.2, y:3.75+i*0.78, w:5.15, h:0.65, fill:{color:NAVY2}, rectRadius:0.06 });
  s.addText("—", { x:7.4, y:3.75+i*0.78, w:0.35, h:0.65, fontFace:FB, fontSize:16, bold:true, color:AMARILLO, valign:"middle" });
  s.addText(l, { x:7.8, y:3.75+i*0.78, w:4.45, h:0.65, fontFace:FB, fontSize:12.5, color:ICE, valign:"middle" });
});
s.addText("17/17 PB · 13/13 HU · artefactos Scrum completos", { x:7.2, y:6.2, w:5.2, h:0.35, fontFace:FB, fontSize:12, bold:true, color:MINT });
footer(s,12);

// ── SLIDE 13 — Conclusiones ──
s = pptx.addSlide(); bgDark(s);
kicker(s, "Conclusiones", MINT);
s.addText("Qué se logró y qué sigue", { x:0.7, y:0.95, w:11.9, h:1.0, fontFace:FH, fontSize:32, bold:true, color:WHITE });
s.addShape(pptx.ShapeType.roundRect, { x:0.7, y:2.2, w:5.85, h:4.35, fill:{color:NAVY2}, rectRadius:0.1 });
s.addText("Logros", { x:1.0, y:2.4, w:5, h:0.5, fontFace:FH, fontSize:19, bold:true, color:MINT });
["Prototipo funcional sobre los 6 objetivos","Clasificador local con 76% de exactitud","Cruce Prophet → semáforo fiscal operativo","Auditoría con 4 detectores","13 HU verificadas, 97 tests verdes"].forEach((t,i)=>{
  s.addText("›", { x:1.0, y:3.05+i*0.66, w:0.3, h:0.45, fontFace:FB, fontSize:15, bold:true, color:MINT });
  s.addText(t, { x:1.3, y:3.05+i*0.66, w:5.1, h:0.6, fontFace:FB, fontSize:14, color:ICE, valign:"middle" });
});
s.addShape(pptx.ShapeType.roundRect, { x:6.75, y:2.2, w:5.85, h:4.35, fill:{color:NAVY2}, line:{color:AMARILLO,width:1}, rectRadius:0.1 });
s.addText("Trabajos futuros", { x:7.05, y:2.4, w:5, h:0.5, fontFace:FH, fontSize:19, bold:true, color:AMARILLO });
["Ampliar y balancear el dataset base","Cubrir el régimen de venta de bienes","Integrar facturación electrónica de AFIP","Migrar los tests a PostgreSQL","Gestión de clientes y notificaciones"].forEach((t,i)=>{
  s.addText("›", { x:7.05, y:3.05+i*0.66, w:0.3, h:0.45, fontFace:FB, fontSize:15, bold:true, color:AMARILLO });
  s.addText(t, { x:7.35, y:3.05+i*0.66, w:5.1, h:0.6, fontFace:FB, fontSize:14, color:ICE, valign:"middle" });
});
footer(s,13);

// ── SLIDE 14 — Cierre ──
s = pptx.addSlide(); bgDark(s);
s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:13.33, h:0.28, fill:{color:MINT} });
s.addShape(pptx.ShapeType.rect, { x:0, y:7.22, w:13.33, h:0.28, fill:{color:MINT} });
s.addText("FreelanceControl", { x:0.7, y:2.5, w:11.9, h:1.3, fontFace:FH, fontSize:54, bold:true, color:WHITE, align:"center" });
s.addText("Aprendizaje automático con soberanía de datos al servicio del monotributista argentino", {
  x:1.5, y:3.9, w:10.3, h:0.9, fontFace:FB, fontSize:19, color:ICE, align:"center" });
s.addText("Gracias.  ¿Preguntas?", { x:0.7, y:5.1, w:11.9, h:0.7, fontFace:FH, fontSize:24, bold:true, color:MINT, align:"center" });

pptx.writeFile({ fileName: "/Users/marcosjoaquin/proyecto-tfg/docs/FreelanceControl_Defensa.pptx" })
  .then(f => console.log("OK:", f));
