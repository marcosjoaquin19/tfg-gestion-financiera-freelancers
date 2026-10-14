// Íconos de las filminas (Lucide, vía react-icons) a PNG, en blanco y en azul noche.
const React = require("react"), { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp"), lu = require("react-icons/lu");
const DST = "/Users/marcosjoaquin/proyecto-tfg/defensa_final/slides/iconos";
const NOMBRES = ["Palette","Code","Presentation","ChartSpline","Gauge","EyeOff","Files","Layers","Tags","Tag",
  "TrendingUp","ShieldCheck","ScanSearch","FileText","Receipt","Landmark","Users","Package","Lock","KeyRound",
  "Fingerprint","Signature","Brain","GraduationCap","CircleHelp","Pencil","RefreshCw","User","Database","Scale",
  "Timer","Target","MessageSquare","List","Hand","Copy","TriangleAlert","Activity","CalendarX","BadgeDollarSign",
  "ArrowLeftRight","Repeat","AudioWaveform","ListChecks","Sparkles","WifiOff","Play","Monitor","Server","Laptop",
  "Check","CircleCheck","X","Blend","Route","FileSpreadsheet","Upload","Calculator","CloudSun","Car","Lightbulb",
  "Eye","Hourglass","Split","Map","Shield","Wallet","UserCheck","Waves","Ban","CalendarClock","Ruler","Layers3",
  "Mail","FileX","Vote","SquareTerminal","ClipboardList"];
(async () => {
  for (const n of NOMBRES) {
    const C = lu["Lu" + n]; if (!C) { console.log("falta", n); continue; }
    for (const [suf, color] of [["b", "#FFFFFF"], ["n", "#0D2B45"], ["t", "#1C7293"]]) {
      const svg = renderToStaticMarkup(React.createElement(C, { size: 256, color, strokeWidth: 2 }));
      await sharp(Buffer.from(svg)).png().toFile(`${DST}/${n}_${suf}.png`);
    }
  }
  console.log("listo");
})();
