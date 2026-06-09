import base64
import logging
import re
import unicodedata
from io import BytesIO
from typing import Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sqlalchemy.orm import Session

from app.models.modelo_clasificador import ModeloClasificador
from app.models.cache_clasificacion import CacheClasificacion
from app.models.gasto import Gasto

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = [
    "Software", "Hardware", "Infraestructura", "Marketing", "Servicios",
    "Capacitación", "Suscripciones", "Transporte", "Alimentación",
    "Impuestos", "Monotributo", "Otros",
]

# 216 ejemplos base (18 por categoría)
DATASET_BASE = [
    # ── Software ───────────────────────────────────────────────────────────
    ("licencia windows", "Software"),
    ("adobe photoshop", "Software"),
    ("antivirus kaspersky", "Software"),
    ("office 365 anual", "Software"),
    ("licencia autocad", "Software"),
    ("jetbrains intellij", "Software"),
    ("sublime text licencia", "Software"),
    ("github pro mensual", "Software"),
    ("figma professional", "Software"),
    ("notion premium", "Software"),
    ("microsoft teams licencia", "Software"),
    ("zoom pro plan", "Software"),
    ("licencia affinity designer", "Software"),
    ("vmware workstation", "Software"),
    ("parallels desktop mac", "Software"),
    ("software contable tango", "Software"),
    ("visual studio enterprise", "Software"),
    ("licencia windows server", "Software"),
    # ── Hardware ───────────────────────────────────────────────────────────
    ("monitor lg 27 pulgadas", "Hardware"),
    ("teclado mecanico logitech", "Hardware"),
    ("disco rigido externo seagate", "Hardware"),
    ("mouse inalambrico microsoft", "Hardware"),
    ("impresora epson multifuncion", "Hardware"),
    ("webcam logitech hd", "Hardware"),
    ("auriculares sony bluetooth", "Hardware"),
    ("tablet wacom grafica", "Hardware"),
    ("router wifi tp link", "Hardware"),
    ("memoria ram ddr4 16gb", "Hardware"),
    ("ssd samsung 500gb", "Hardware"),
    ("placa de video rtx", "Hardware"),
    ("procesador intel core i7", "Hardware"),
    ("fuente de poder corsair", "Hardware"),
    ("parlantes pc creative", "Hardware"),
    ("microfono blue yeti usb", "Hardware"),
    ("ups estabilizador de tension", "Hardware"),
    ("notebook dell latitude", "Hardware"),
    # ── Infraestructura ────────────────────────────────────────────────────
    ("hosting servidor web", "Infraestructura"),
    ("dominio web godaddy", "Infraestructura"),
    ("aws ec2 instancia", "Infraestructura"),
    ("google cloud storage", "Infraestructura"),
    ("azure virtual machine", "Infraestructura"),
    ("certificado ssl comodo", "Infraestructura"),
    ("cdn cloudflare pro", "Infraestructura"),
    ("vps digitalocean droplet", "Infraestructura"),
    ("servidor dedicado datacenter", "Infraestructura"),
    ("hosting wordpress siteground", "Infraestructura"),
    ("email corporativo gsuite", "Infraestructura"),
    ("backup nube backblaze", "Infraestructura"),
    ("linode servidor linux", "Infraestructura"),
    ("heroku plan standard", "Infraestructura"),
    ("firebase plan blaze", "Infraestructura"),
    ("s3 bucket almacenamiento aws", "Infraestructura"),
    ("ip fija dedicada isp", "Infraestructura"),
    ("colocation servidor datacenter", "Infraestructura"),
    # ── Marketing ──────────────────────────────────────────────────────────
    ("publicidad facebook ads", "Marketing"),
    ("google ads campana", "Marketing"),
    ("diseno logo empresa", "Marketing"),
    ("folletos imprenta diseno", "Marketing"),
    ("banner publicitario web", "Marketing"),
    ("instagram ads pauta", "Marketing"),
    ("linkedin ads campana", "Marketing"),
    ("seo posicionamiento organico", "Marketing"),
    ("email marketing mailchimp", "Marketing"),
    ("diseno flyer evento", "Marketing"),
    ("video promocional produccion", "Marketing"),
    ("fotografia producto comercial", "Marketing"),
    ("contenido redes sociales", "Marketing"),
    ("agencia publicidad honorarios", "Marketing"),
    ("tiktok ads publicidad", "Marketing"),
    ("landing page diseno web", "Marketing"),
    ("branding identidad visual", "Marketing"),
    ("campana remarketing google", "Marketing"),
    # ── Servicios ──────────────────────────────────────────────────────────
    ("contador honorarios mensuales", "Servicios"),
    ("abogado consulta legal", "Servicios"),
    ("freelancer diseno grafico", "Servicios"),
    ("consultor marketing digital", "Servicios"),
    ("estudio juridico honorarios", "Servicios"),
    ("servicio limpieza oficina", "Servicios"),
    ("seguridad informatica consultoria", "Servicios"),
    ("soporte tecnico informatico", "Servicios"),
    ("desarrollo software externo", "Servicios"),
    ("disenador grafico externo", "Servicios"),
    ("traductor documentos tecnicos", "Servicios"),
    ("asesor impositivo mensual", "Servicios"),
    ("notario escritura publica", "Servicios"),
    ("arquitecto planos oficina", "Servicios"),
    ("medico laboral empresa", "Servicios"),
    ("honorarios profesionales varios", "Servicios"),
    ("consultor rrhh recursos humanos", "Servicios"),
    ("ingeniero consulta tecnica", "Servicios"),
    # ── Capacitación ───────────────────────────────────────────────────────
    ("curso udemy python programacion", "Capacitación"),
    ("libro programacion javascript", "Capacitación"),
    ("workshop react avanzado", "Capacitación"),
    ("certificacion aws solutions architect", "Capacitación"),
    ("bootcamp fullstack desarrollo", "Capacitación"),
    ("masterclass diseno ux ui", "Capacitación"),
    ("curso linkedin learning mensual", "Capacitación"),
    ("capacitacion excel avanzado", "Capacitación"),
    ("conferencia tecnologia devconf", "Capacitación"),
    ("webinar marketing digital", "Capacitación"),
    ("diplomado gestion proyectos", "Capacitación"),
    ("curso ingles online", "Capacitación"),
    ("certificacion google analytics", "Capacitación"),
    ("training metodologia agile", "Capacitación"),
    ("curso fotografia profesional", "Capacitación"),
    ("seminario finanzas personales", "Capacitación"),
    ("libro contabilidad basica", "Capacitación"),
    ("taller escritura tecnica", "Capacitación"),
    # ── Suscripciones ──────────────────────────────────────────────────────
    ("netflix mensual", "Suscripciones"),
    ("spotify premium mensual", "Suscripciones"),
    ("adobe creative cloud mensual", "Suscripciones"),
    ("amazon prime membresia", "Suscripciones"),
    ("hbo max suscripcion", "Suscripciones"),
    ("disney plus plan mensual", "Suscripciones"),
    ("youtube premium mensual", "Suscripciones"),
    ("apple music suscripcion", "Suscripciones"),
    ("dropbox plus mensual", "Suscripciones"),
    ("evernote premium anual", "Suscripciones"),
    ("canva pro mensual", "Suscripciones"),
    ("grammarly premium suscripcion", "Suscripciones"),
    ("expressvpn suscripcion mensual", "Suscripciones"),
    ("nordvpn plan anual", "Suscripciones"),
    ("1password suscripcion", "Suscripciones"),
    ("monday com pro", "Suscripciones"),
    ("chatgpt plus openai mensual", "Suscripciones"),
    ("midjourney suscripcion ia", "Suscripciones"),
    # ── Transporte ─────────────────────────────────────────────────────────
    ("uber viaje cliente", "Transporte"),
    ("nafta combustible auto", "Transporte"),
    ("estacionamiento zona paga", "Transporte"),
    ("taxi visita cliente", "Transporte"),
    ("tren mensual abono", "Transporte"),
    ("colectivo pasaje boletera", "Transporte"),
    ("remis aeropuerto viaje", "Transporte"),
    ("vuelo congreso conferencia", "Transporte"),
    ("peaje autopista viaje", "Transporte"),
    ("alquiler auto negocio", "Transporte"),
    ("bici compartida ecobici", "Transporte"),
    ("combustible moto trabajo", "Transporte"),
    ("transfer aeropuerto hotel", "Transporte"),
    ("micro larga distancia viaje", "Transporte"),
    ("seguro vehiculo anual", "Transporte"),
    ("parking mensual edificio", "Transporte"),
    ("patente auto anual", "Transporte"),
    ("gasolina viaje laboral", "Transporte"),
    # ── Alimentación ───────────────────────────────────────────────────────
    ("almuerzo reunion cliente", "Alimentación"),
    ("cafe coworking diario", "Alimentación"),
    ("delivery comida trabajo", "Alimentación"),
    ("desayuno reunion negocio", "Alimentación"),
    ("cena cliente restaurante", "Alimentación"),
    ("almuerzo oficina comedor", "Alimentación"),
    ("merienda reunion equipo", "Alimentación"),
    ("catering evento empresa", "Alimentación"),
    ("lunch trabajo remoto", "Alimentación"),
    ("cafe mientras trabajo", "Alimentación"),
    ("vianda oficina tupper", "Alimentación"),
    ("snacks oficina varios", "Alimentación"),
    ("bebidas reunion equipo", "Alimentación"),
    ("restaurante almuerzo negocio", "Alimentación"),
    ("brunch trabajo matutino", "Alimentación"),
    ("comida rapida viaje laboral", "Alimentación"),
    ("almuerzo capacitacion jornada", "Alimentación"),
    ("cena equipo celebracion", "Alimentación"),
    # ── Impuestos ──────────────────────────────────────────────────────────
    ("ingresos brutos declaracion", "Impuestos"),
    ("iva declaracion jurada", "Impuestos"),
    ("sellos provincia contrato", "Impuestos"),
    ("impuesto automotor patente", "Impuestos"),
    ("bienes personales declaracion", "Impuestos"),
    ("ganancias persona fisica", "Impuestos"),
    ("tasa municipal habilitacion", "Impuestos"),
    ("contribucion especial municipal", "Impuestos"),
    ("impuesto inmobiliario", "Impuestos"),
    ("derecho de registro", "Impuestos"),
    ("timbrado provincial", "Impuestos"),
    ("retencion ganancias cobro", "Impuestos"),
    ("percepcion iva factura", "Impuestos"),
    ("impuesto pais compra", "Impuestos"),
    ("impuesto transferencia inmueble", "Impuestos"),
    ("tasa judicial expediente", "Impuestos"),
    ("impuesto cheque banco", "Impuestos"),
    ("impuesto sellos contrato", "Impuestos"),
    # ── Monotributo ────────────────────────────────────────────────────────
    ("pago monotributo afip", "Monotributo"),
    ("cuota monotributo marzo", "Monotributo"),
    ("arca monotributo mensual", "Monotributo"),
    ("monotributo categoria b", "Monotributo"),
    ("pago mensual afip freelancer", "Monotributo"),
    ("recategorizacion monotributo anual", "Monotributo"),
    ("monotributo cuota anual", "Monotributo"),
    ("cuota afip febrero pago", "Monotributo"),
    ("pago arca digital mensual", "Monotributo"),
    ("monotributo digital categoria", "Monotributo"),
    ("baja monotributo afip", "Monotributo"),
    ("alta monotributo inscripcion", "Monotributo"),
    ("modificacion datos monotributo", "Monotributo"),
    ("adhesion al monotributo", "Monotributo"),
    ("declaracion jurada monotributo", "Monotributo"),
    ("constancia monotributo afip", "Monotributo"),
    ("formulario f960 monotributo", "Monotributo"),
    ("vencimiento cuota monotributo", "Monotributo"),
    # ── Otros ──────────────────────────────────────────────────────────────
    ("papeleria oficina insumos", "Otros"),
    ("limpieza insumos generales", "Otros"),
    ("gastos generales varios", "Otros"),
    ("miscelaneos varios", "Otros"),
    ("materiales oficina varios", "Otros"),
    ("elementos limpieza oficina", "Otros"),
    ("articulos escritorio varios", "Otros"),
    ("cuaderno agenda planificador", "Otros"),
    ("toner impresora recarga", "Otros"),
    ("resma papel impresion", "Otros"),
    ("carpetas archivos varios", "Otros"),
    ("cinta adhesiva sobres", "Otros"),
    ("sello empresa goma", "Otros"),
    ("lapiceras marcadores varios", "Otros"),
    ("agua bidones oficina", "Otros"),
    ("flores decoracion oficina", "Otros"),
    ("pilas baterias electrodomesticos", "Otros"),
    ("regalo cliente navidad", "Otros"),

    # ── Ampliación: 32 ejemplos adicionales por categoría ─────────────────
    # El dataset original (18 por categoría) daba 57% en cross-validation.
    # Ampliamos a 50 por categoría con foco en diversidad léxica: cómo
    # describiría el gasto un usuario real, cómo lo escribe un banco
    # (abreviaturas, mayúsculas), cómo aparece en distintos contextos.

    # ── Software ──
    ("compra licencia jetbrains pycharm", "Software"),
    ("pago anual office hogar y empresas", "Software"),
    ("dbeaver pro renovacion", "Software"),
    ("renovacion antivirus eset nod32", "Software"),
    ("compra adobe acrobat dc", "Software"),
    ("pago anual sketch app mac", "Software"),
    ("ms project licencia anual", "Software"),
    ("nitro pdf compra", "Software"),
    ("autodesk maya licencia mensual", "Software"),
    ("tableau desktop personal", "Software"),
    ("matlab licencia academica", "Software"),
    ("compra plugin wordpress yoast", "Software"),
    ("xero plan starter", "Software"),
    ("plan webex pro", "Software"),
    ("datagrip suscripcion anual", "Software"),
    ("compra pinegrow editor html", "Software"),
    ("postman team plan", "Software"),
    ("compra software contable bejerman", "Software"),
    ("docker desktop business", "Software"),
    ("vscode extension pack pago", "Software"),
    ("compra plan teamviewer", "Software"),
    ("pago anydesk profesional", "Software"),
    ("compra licencia camtasia", "Software"),
    ("compra obs studio plugin", "Software"),
    ("pago wordpress plugin elementor pro", "Software"),
    ("compra photoshop plan fotografia", "Software"),
    ("renovacion sublime text 4", "Software"),
    ("compra licencia coreldraw graphics", "Software"),
    ("pago licencia fl studio producer", "Software"),
    ("compra plan navicat premium", "Software"),
    ("renovacion atom one editor", "Software"),
    ("paragon ntfs mac compra", "Software"),

    # ── Hardware ──
    ("compra notebook lenovo thinkpad", "Hardware"),
    ("teclado logitech mx keys mini", "Hardware"),
    ("mouse logitech mx master 3", "Hardware"),
    ("compra mac mini m2", "Hardware"),
    ("auriculares airpods pro segunda gen", "Hardware"),
    ("compra ipad pro 11 pulgadas", "Hardware"),
    ("disco ssd nvme samsung 1tb", "Hardware"),
    ("compra dock thunderbolt 4 caldigit", "Hardware"),
    ("hub usb c anker 7 puertos", "Hardware"),
    ("monitor secundario samsung 24", "Hardware"),
    ("kit memoria ddr5 32gb crucial", "Hardware"),
    ("compra impresora hp laserjet pro", "Hardware"),
    ("scanner epson workforce", "Hardware"),
    ("router mesh asus zenwifi", "Hardware"),
    ("switch tp-link 8 puertos gigabit", "Hardware"),
    ("compra pendrive sandisk 256gb", "Hardware"),
    ("microfono shure mv7 podcast", "Hardware"),
    ("luz aro ring light fotografia", "Hardware"),
    ("trípode manfrotto compacto", "Hardware"),
    ("compra silla gamer dxracer", "Hardware"),
    ("escritorio regulable altura", "Hardware"),
    ("compra notebook macbook air m3", "Hardware"),
    ("teclado magic apple", "Hardware"),
    ("compra placa madre asus prime", "Hardware"),
    ("ventilador noctua nh-d15", "Hardware"),
    ("compra gabinete corsair 4000d", "Hardware"),
    ("disco externo wd elements 4tb", "Hardware"),
    ("compra cable hdmi 2.1 ugreen", "Hardware"),
    ("monitor curvo lg ultragear", "Hardware"),
    ("compra adaptador usb c hdmi", "Hardware"),
    ("camara sony zv-1 vlogging", "Hardware"),
    ("kit limpieza pantalla notebook", "Hardware"),

    # ── Infraestructura ──
    ("renovacion dominio nic.ar", "Infraestructura"),
    ("compra dominio dot com namecheap", "Infraestructura"),
    ("aws lambda funciones serverless", "Infraestructura"),
    ("digitalocean droplet 4gb mensual", "Infraestructura"),
    ("vultr instancia compute", "Infraestructura"),
    ("hetzner cloud server", "Infraestructura"),
    ("railway plan starter", "Infraestructura"),
    ("render plan pro web service", "Infraestructura"),
    ("netlify plan pro mensual", "Infraestructura"),
    ("vercel plan pro hobby", "Infraestructura"),
    ("supabase plan team", "Infraestructura"),
    ("planetscale base de datos mysql", "Infraestructura"),
    ("mongodb atlas cluster m10", "Infraestructura"),
    ("redis cloud plan fixed", "Infraestructura"),
    ("upstash redis serverless", "Infraestructura"),
    ("compra ssl certificate digicert", "Infraestructura"),
    ("namecheap renovacion ssl wildcard", "Infraestructura"),
    ("hostinger hosting compartido", "Infraestructura"),
    ("dreamhost plan unlimited", "Infraestructura"),
    ("a2 hosting reseller", "Infraestructura"),
    ("compra ip dedicada hosting", "Infraestructura"),
    ("aws route53 hosted zone", "Infraestructura"),
    ("aws s3 storage mensual", "Infraestructura"),
    ("aws cloudfront cdn distribucion", "Infraestructura"),
    ("gitlab plan premium hosting", "Infraestructura"),
    ("bitbucket cloud premium", "Infraestructura"),
    ("docker hub plan team", "Infraestructura"),
    ("compra google workspace plan business", "Infraestructura"),
    ("microsoft 365 business standard", "Infraestructura"),
    ("compra zoho workplace anual", "Infraestructura"),
    ("compra rackspace email hosting", "Infraestructura"),
    ("compra storage glacier deep archive", "Infraestructura"),

    # ── Marketing ──
    ("pauta google ads campana brand", "Marketing"),
    ("inversion meta ads facebook instagram", "Marketing"),
    ("twitter ads pauta promocional", "Marketing"),
    ("youtube ads campana video", "Marketing"),
    ("disenador freelance logo identidad", "Marketing"),
    ("redaccion contenidos blog seo", "Marketing"),
    ("contratacion influencer instagram", "Marketing"),
    ("agencia comunicacion mensual", "Marketing"),
    ("disenadora ux ui contratada", "Marketing"),
    ("estudio grafico folleteria", "Marketing"),
    ("imprenta tarjetas personales", "Marketing"),
    ("merchandising remeras empresa", "Marketing"),
    ("compra dominio publicitario brand", "Marketing"),
    ("plan email marketing sendgrid", "Marketing"),
    ("hubspot starter marketing", "Marketing"),
    ("pago activecampaign anual", "Marketing"),
    ("klaviyo ecommerce email plan", "Marketing"),
    ("hootsuite professional plan", "Marketing"),
    ("compra plan buffer pro social", "Marketing"),
    ("semrush plan pro herramientas seo", "Marketing"),
    ("ahrefs plan lite mensual", "Marketing"),
    ("ubersuggest premium licencia", "Marketing"),
    ("clickup plan business plus", "Marketing"),
    ("seguidor ig services pago", "Marketing"),
    ("video productora corporativo", "Marketing"),
    ("fotografo producto pack", "Marketing"),
    ("locutor jingle radio", "Marketing"),
    ("disenador plantilla pitch deck", "Marketing"),
    ("compra stock footage shutterstock", "Marketing"),
    ("compra pack iconos premium", "Marketing"),
    ("agencia seo posicionamiento mensual", "Marketing"),
    ("contratacion copywriter ventas", "Marketing"),

    # ── Servicios ──
    ("honorarios contadora marzo", "Servicios"),
    ("estudio contable mensualidad", "Servicios"),
    ("abogada laboral consulta", "Servicios"),
    ("consultor tributario afip", "Servicios"),
    ("desarrollador externo proyecto", "Servicios"),
    ("contratacion fullstack freelance", "Servicios"),
    ("ux researcher por hora", "Servicios"),
    ("traductor ingles tecnico", "Servicios"),
    ("editor video freelance", "Servicios"),
    ("escribiente notarial documento", "Servicios"),
    ("ingeniero electricista oficina", "Servicios"),
    ("plomero arreglos sanitarios", "Servicios"),
    ("electricista mantenimiento estudio", "Servicios"),
    ("cerrajero cambio cerradura", "Servicios"),
    ("contratacion virtual assistant remoto", "Servicios"),
    ("community manager mensual", "Servicios"),
    ("editor podcast por episodio", "Servicios"),
    ("gestoria automotor patente", "Servicios"),
    ("contratacion data scientist freelance", "Servicios"),
    ("arquitecta consultoria diseno oficina", "Servicios"),
    ("psicologa laboral empresa", "Servicios"),
    ("nutricionista equipo trabajo", "Servicios"),
    ("entrenador personal mensual", "Servicios"),
    ("masajista oficina semanal", "Servicios"),
    ("seguridad alarma monitoreo abono", "Servicios"),
    ("limpieza profunda oficina trimestral", "Servicios"),
    ("jardineria mantenimiento mensual", "Servicios"),
    ("contratacion qa tester freelance", "Servicios"),
    ("growth hacker consultoria", "Servicios"),
    ("product manager fraccional", "Servicios"),
    ("scrum master por hora", "Servicios"),
    ("devops freelance infraestructura", "Servicios"),

    # ── Capacitación ──
    ("compra curso platzi escuela datos", "Capacitación"),
    ("inscripcion bootcamp henry", "Capacitación"),
    ("compra curso coderhouse react", "Capacitación"),
    ("ada tech curso fullstack", "Capacitación"),
    ("frontend masters suscripcion anual", "Capacitación"),
    ("egghead io plan pro", "Capacitación"),
    ("compra curso pluralsight", "Capacitación"),
    ("safari oreilly plan individual", "Capacitación"),
    ("compra libro clean code amazon", "Capacitación"),
    ("compra libro pragmatic programmer", "Capacitación"),
    ("conferencia react latina entrada", "Capacitación"),
    ("entrada nerdearla evento", "Capacitación"),
    ("entrada pyday argentina", "Capacitación"),
    ("entrada devfest cordoba", "Capacitación"),
    ("compra curso udemy javascript", "Capacitación"),
    ("compra curso domestika ilustracion", "Capacitación"),
    ("workshop figma avanzado online", "Capacitación"),
    ("certificacion azure az900", "Capacitación"),
    ("certificacion aws cloud practitioner", "Capacitación"),
    ("certificacion gcp professional", "Capacitación"),
    ("scrum master psm1 examen", "Capacitación"),
    ("inscripcion charla tedx local", "Capacitación"),
    ("masterclass startup founder", "Capacitación"),
    ("curso diseno ux google certificado", "Capacitación"),
    ("compra coursera plus anual", "Capacitación"),
    ("inscripcion mentoria producto", "Capacitación"),
    ("compra libro sapiens harari", "Capacitación"),
    ("compra audible suscripcion anual", "Capacitación"),
    ("blinkist premium libros resumen", "Capacitación"),
    ("inscripcion clase clubhouse digital", "Capacitación"),
    ("compra curso freelance roadmap", "Capacitación"),
    ("compra ebook arquitectura software", "Capacitación"),

    # ── Suscripciones ──
    ("renovacion icloud 200gb mensual", "Suscripciones"),
    ("google one 2tb mensual", "Suscripciones"),
    ("microsoft 365 personal mensual", "Suscripciones"),
    ("renovacion hbo max anual", "Suscripciones"),
    ("paramount plus suscripcion", "Suscripciones"),
    ("star plus mensual", "Suscripciones"),
    ("crunchyroll premium mensual", "Suscripciones"),
    ("plex pass anual", "Suscripciones"),
    ("tidal hifi suscripcion mensual", "Suscripciones"),
    ("deezer premium mensual", "Suscripciones"),
    ("setapp suite apps mac", "Suscripciones"),
    ("renovacion bitwarden premium", "Suscripciones"),
    ("nordpass premium anual", "Suscripciones"),
    ("dashlane suscripcion premium", "Suscripciones"),
    ("malwarebytes premium suscripcion", "Suscripciones"),
    ("renovacion cleanmymac plus", "Suscripciones"),
    ("ccleaner pro anual", "Suscripciones"),
    ("renovacion duolingo plus", "Suscripciones"),
    ("babbel suscripcion idiomas", "Suscripciones"),
    ("calm meditacion app anual", "Suscripciones"),
    ("headspace mensual", "Suscripciones"),
    ("strava summit anual", "Suscripciones"),
    ("nike training club premium", "Suscripciones"),
    ("renovacion descript pro", "Suscripciones"),
    ("loom business plan", "Suscripciones"),
    ("rev pro transcripcion mensual", "Suscripciones"),
    ("otter ai pro mensual", "Suscripciones"),
    ("grammarly business mensual", "Suscripciones"),
    ("languagetool premium anual", "Suscripciones"),
    ("readwise reader plus", "Suscripciones"),
    ("medium membership mensual", "Suscripciones"),
    ("substack pago suscripcion newsletter", "Suscripciones"),

    # ── Transporte ──
    ("uber moto trayecto cliente", "Transporte"),
    ("cabify viaje aeropuerto", "Transporte"),
    ("didi viaje a reunion", "Transporte"),
    ("nafta ypf full estacion", "Transporte"),
    ("axion cargas combustible", "Transporte"),
    ("shell estacion servicio nafta", "Transporte"),
    ("vuelo aerolineas argentinas", "Transporte"),
    ("vuelo flybondi cordoba", "Transporte"),
    ("vuelo jetsmart neuquen", "Transporte"),
    ("micro andesmar larga distancia", "Transporte"),
    ("micro via bariloche", "Transporte"),
    ("subte sube carga", "Transporte"),
    ("recarga sube transporte", "Transporte"),
    ("peaje autopista panamericana", "Transporte"),
    ("peaje acceso oeste", "Transporte"),
    ("estacionamiento bairesparking", "Transporte"),
    ("estacion saba microcentro", "Transporte"),
    ("alquiler avis auto fin de semana", "Transporte"),
    ("hertz alquiler vehiculo", "Transporte"),
    ("localiza renta auto", "Transporte"),
    ("scooter electrica grin minutos", "Transporte"),
    ("ecobici abono mensual", "Transporte"),
    ("revision tecnica vtv vehicular", "Transporte"),
    ("seguro auto la caja anual", "Transporte"),
    ("seguro federacion patronal anual", "Transporte"),
    ("patente automotor cuota", "Transporte"),
    ("aerolineas plus pasaje promocional", "Transporte"),
    ("expreso linea 152 abono", "Transporte"),
    ("taxi radio call center", "Transporte"),
    ("transfer privado ezeiza", "Transporte"),
    ("uber black ejecutivo cliente", "Transporte"),
    ("compra cubiertas auto firestone", "Transporte"),

    # ── Alimentación ──
    ("compra pedidos ya delivery cena", "Alimentación"),
    ("rappi almuerzo oficina", "Alimentación"),
    ("uber eats sushi reunion", "Alimentación"),
    ("starbucks cafe manana", "Alimentación"),
    ("havanna medialunas oficina", "Alimentación"),
    ("mcdonalds combo cliente", "Alimentación"),
    ("burger king almuerzo rapido", "Alimentación"),
    ("kentucky pizza equipo viernes", "Alimentación"),
    ("don julio cena cliente", "Alimentación"),
    ("la cabrera asado reunion", "Alimentación"),
    ("compra coca cola six pack", "Alimentación"),
    ("agua mineral villavicencio caja", "Alimentación"),
    ("compra cafe nespresso capsulas", "Alimentación"),
    ("cafe la virginia molido", "Alimentación"),
    ("supermercado compra oficina semanal", "Alimentación"),
    ("disco compra galletitas snacks", "Alimentación"),
    ("compra fruta verduleria semanal", "Alimentación"),
    ("almuerzo bistro mediodia", "Alimentación"),
    ("desayuno reunion socios cafeteria", "Alimentación"),
    ("merienda meeting equipo", "Alimentación"),
    ("vianda ofyou semanal", "Alimentación"),
    ("compra catering presentacion proyecto", "Alimentación"),
    ("delivery sushi oferta noche", "Alimentación"),
    ("delivery pizza muzzarella", "Alimentación"),
    ("freshly oficina almuerzo", "Alimentación"),
    ("compra empanadas caceros docena", "Alimentación"),
    ("almuerzo japonesa cliente importante", "Alimentación"),
    ("cafe martinez encuentro mensual", "Alimentación"),
    ("happiness cake bday equipo", "Alimentación"),
    ("brunch mexicano cliente domingo", "Alimentación"),
    ("milanesa restaurante porteno", "Alimentación"),
    ("comida saludable healthy rapido", "Alimentación"),

    # ── Impuestos ──
    ("ingresos brutos caba mensual", "Impuestos"),
    ("ingresos brutos provincia bsas", "Impuestos"),
    ("retencion ganancias 4ta categoria", "Impuestos"),
    ("declaracion jurada iva mensual", "Impuestos"),
    ("anticipo ganancias persona fisica", "Impuestos"),
    ("convenio multilateral declaracion", "Impuestos"),
    ("impuesto debitos creditos bancarios", "Impuestos"),
    ("ley 25413 cheques", "Impuestos"),
    ("impuesto sello contrato locacion", "Impuestos"),
    ("tasa abl ciudad buenos aires", "Impuestos"),
    ("tasa municipal seguridad", "Impuestos"),
    ("contribucion mejoras municipalidad", "Impuestos"),
    ("rentas provincia caba", "Impuestos"),
    ("arba inmobiliario rural", "Impuestos"),
    ("impuesto automotor cuota anual", "Impuestos"),
    ("vtv habilitacion vehicular tasa", "Impuestos"),
    ("impuesto pais compra dolares", "Impuestos"),
    ("retencion 35 percepcion ganancias", "Impuestos"),
    ("retencion suss seguridad social", "Impuestos"),
    ("ley pyme retencion impuesto", "Impuestos"),
    ("declaracion patrimonial bienes", "Impuestos"),
    ("impuesto solidario riqueza", "Impuestos"),
    ("retencion iva cliente factura", "Impuestos"),
    ("retencion iibb chaco", "Impuestos"),
    ("retencion iibb mendoza", "Impuestos"),
    ("retencion iibb cordoba", "Impuestos"),
    ("retencion arba bs as", "Impuestos"),
    ("retencion agip caba", "Impuestos"),
    ("siper sicore declaracion", "Impuestos"),
    ("formulario 931 cargas sociales", "Impuestos"),
    ("rentas santa fe iibb", "Impuestos"),
    ("tasa habilitacion comercial municipal", "Impuestos"),

    # ── Monotributo ──
    ("arca pago mensual cuota", "Monotributo"),
    ("monotributo categoria a febrero", "Monotributo"),
    ("monotributo categoria d marzo", "Monotributo"),
    ("monotributo categoria e abril", "Monotributo"),
    ("monotributo categoria f mayo", "Monotributo"),
    ("monotributo cuota junio", "Monotributo"),
    ("monotributo julio pago vencimiento", "Monotributo"),
    ("recategorizacion semestral monotributo", "Monotributo"),
    ("monotributo cuota agosto adhesion", "Monotributo"),
    ("monotributo deuda atrasada cancelacion", "Monotributo"),
    ("monotributo aporte obra social", "Monotributo"),
    ("componente impositivo monotributo", "Monotributo"),
    ("componente jubilatorio monotributo", "Monotributo"),
    ("aportes osde monotributo", "Monotributo"),
    ("aportes obra social swiss medical", "Monotributo"),
    ("monotributo aporte autonomos", "Monotributo"),
    ("baja temporal monotributo arca", "Monotributo"),
    ("alta nueva categoria monotributo", "Monotributo"),
    ("monotributo unificado cuota", "Monotributo"),
    ("vep generado monotributo", "Monotributo"),
    ("debito automatico monotributo", "Monotributo"),
    ("vencimiento monotributo dia 20", "Monotributo"),
    ("pago monotributo banco galicia", "Monotributo"),
    ("pago monotributo rapipago link", "Monotributo"),
    ("pago monotributo pagomiscuentas", "Monotributo"),
    ("pago monotributo home banking", "Monotributo"),
    ("constancia monotributo digital trámite", "Monotributo"),
    ("recategorizacion enero arca", "Monotributo"),
    ("recategorizacion julio monotributo", "Monotributo"),
    ("modificacion datos arca personal", "Monotributo"),
    ("clave fiscal arca renovacion", "Monotributo"),
    ("pago monotributo modo qr", "Monotributo"),

    # ── Otros ──
    ("compra resmas papel a4 oficina", "Otros"),
    ("compra biromes bic varios colores", "Otros"),
    ("compra carpetas archivos oficina", "Otros"),
    ("compra sobres x100 manila", "Otros"),
    ("compra etiquetas adhesivas oficina", "Otros"),
    ("compra calculadora casio cientifica", "Otros"),
    ("compra agenda 2026 organizador", "Otros"),
    ("compra cuaderno moleskine clasico", "Otros"),
    ("post-it varios bloques colores", "Otros"),
    ("compra clips broches metalicos", "Otros"),
    ("compra cinta scotch transparente", "Otros"),
    ("trapos rejilla limpieza oficina", "Otros"),
    ("detergente concentrado limpieza", "Otros"),
    ("lavandina cif limpieza profunda", "Otros"),
    ("papel higienico oficina pack", "Otros"),
    ("rollos cocina oficina cinco", "Otros"),
    ("desinfectante alcohol gel", "Otros"),
    ("ambientador habitaciones oficina", "Otros"),
    ("flores cumpleanos colaborador", "Otros"),
    ("regalo aniversario socio", "Otros"),
    ("souvenir cliente fin ano", "Otros"),
    ("compra batería pilas aa duracell", "Otros"),
    ("foco led oficina led", "Otros"),
    ("regleta enchufes multiple", "Otros"),
    ("toner brother impresora", "Otros"),
    ("compra cartucho hp 21 negro", "Otros"),
    ("regalo navidad equipo", "Otros"),
    ("compra adornos decoracion fiesta", "Otros"),
    ("compra cajas mudanza estudio", "Otros"),
    ("etiquetas cajas almacenamiento", "Otros"),
    ("compra calefactor electrico oficina", "Otros"),
    ("ventilador pie verano oficina", "Otros"),
]


def _crear_pipeline(algoritmo: str) -> Pipeline:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        strip_accents="unicode",
        lowercase=True,
        min_df=1,
    )
    if algoritmo == "svm":
        clasificador = LinearSVC(max_iter=2000)
    else:
        clasificador = MultinomialNB()
    return Pipeline([("tfidf", vectorizer), ("clf", clasificador)])


def _serializar_modelo(pipeline: Pipeline) -> str:
    # joblib es la biblioteca recomendada por scikit-learn para persistir modelos:
    # comprime arrays NumPy de manera más eficiente que pickle estándar.
    # Envolvemos el binario en base64 para almacenarlo como texto en la columna
    # modelo_serializado de la tabla modelos_clasificador.
    buffer = BytesIO()
    joblib.dump(pipeline, buffer)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _deserializar_modelo(texto: str) -> Pipeline:
    datos = base64.b64decode(texto)
    return joblib.load(BytesIO(datos))


def _elegir_algoritmo(n_ejemplos: int) -> str:
    return "svm" if n_ejemplos >= 100 else "naive_bayes"


def _calcular_precision(pipeline: Pipeline, X: list, y: list, cv: int = 5) -> Optional[float]:
    try:
        import pandas as pd
        conteos = pd.Series(y).value_counts()
        min_clase = int(conteos.min())
        cv_real = min(cv, min_clase)
        if cv_real < 2 or len(X) < cv_real:
            return None
        scores = cross_val_score(pipeline, X, y, cv=cv_real, scoring="accuracy")
        return float(scores.mean())
    except Exception as e:
        logger.warning(f"No se pudo calcular precisión CV: {e}")
        return None


def entrenar_modelo_base(db: Session) -> ModeloClasificador:
    existente = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id.is_(None),
        ModeloClasificador.activo == True,
    ).first()

    # Solo saltamos el reentrenamiento si ya está entrenado con TODOS los
    # ejemplos disponibles. Si el dataset creció (ej: ampliación del corpus),
    # forzamos un fit nuevo para que el modelo persistido refleje la realidad.
    if existente and existente.n_ejemplos >= len(DATASET_BASE):
        return existente

    X = [desc for desc, _ in DATASET_BASE]
    y = [cat for _, cat in DATASET_BASE]
    n = len(X)

    algoritmo = _elegir_algoritmo(n)
    pipeline = _crear_pipeline(algoritmo)
    pipeline.fit(X, y)

    precision = _calcular_precision(pipeline, X, y, cv=5)
    modelo_str = _serializar_modelo(pipeline)

    if existente:
        existente.modelo_serializado = modelo_str
        existente.algoritmo = algoritmo
        existente.precision = precision
        existente.n_ejemplos = n
        existente.activo = True
        db.commit()
        db.refresh(existente)
        return existente

    nuevo = ModeloClasificador(
        usuario_id=None,
        modelo_serializado=modelo_str,
        algoritmo=algoritmo,
        precision=precision,
        n_ejemplos=n,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_o_crear_modelo(db: Session, usuario_id: int) -> tuple[Pipeline, str]:
    """Retorna (pipeline, algoritmo)."""
    modelo_usuario = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id == usuario_id,
        ModeloClasificador.activo == True,
    ).first()

    if modelo_usuario:
        try:
            pipeline = _deserializar_modelo(modelo_usuario.modelo_serializado)
            return pipeline, modelo_usuario.algoritmo
        except Exception as e:
            logger.error(f"Error deserializando modelo usuario {usuario_id}, reentrenando base: {e}")

    modelo_base = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id.is_(None),
        ModeloClasificador.activo == True,
    ).first()

    if not modelo_base:
        modelo_base = entrenar_modelo_base(db)

    try:
        pipeline = _deserializar_modelo(modelo_base.modelo_serializado)
        return pipeline, modelo_base.algoritmo
    except Exception as e:
        logger.error(f"Error deserializando modelo base, reentrenando: {e}")
        modelo_base = entrenar_modelo_base(db)
        pipeline = _deserializar_modelo(modelo_base.modelo_serializado)
        return pipeline, modelo_base.algoritmo


def _confianza_svm(scores: np.ndarray) -> tuple[int, float]:
    """Confianza para LinearSVC a partir del margen entre las dos mejores clases.

    El softmax directo sobre decision_function() no sirve como confianza: con
    12 clases reparte densidad entre todas y hasta los aciertos claros quedan
    en ~0.20, por debajo de cualquier umbral razonable. En cambio, la brecha
    top1 - top2 sí refleja la duda del modelo: 0 ante un empate (dos clases
    compiten cabeza a cabeza) y crece cuando hay una dominante. La mapeamos a
    [0, 1) con 1 - e^(-brecha), monótona y acotada.
    """
    if len(scores) == 1:
        # Caso binario: decision_function devuelve un único margen con signo.
        idx = 1 if scores[0] > 0 else 0
        return idx, float(1.0 - np.exp(-abs(float(scores[0]))))
    orden = np.argsort(scores)[::-1]
    brecha = float(scores[orden[0]] - scores[orden[1]])
    return int(orden[0]), float(1.0 - np.exp(-brecha))


def clasificar_gasto(descripcion: str, db: Session, usuario_id: int) -> dict:
    try:
        pipeline, algoritmo = obtener_o_crear_modelo(db, usuario_id)
        clases = pipeline.classes_

        if algoritmo == "svm":
            scores = np.array(pipeline.decision_function([descripcion])[0], dtype=float).ravel()
            idx, confianza = _confianza_svm(scores)
        else:
            probas = pipeline.predict_proba([descripcion])[0]
            idx = int(np.argmax(probas))
            confianza = float(probas[idx])

        categoria = clases[idx]

        return {
            "categoria": categoria,
            "confianza": confianza,
            "fuente": "ml_propio",
            "algoritmo": algoritmo,
        }
    except Exception as e:
        logger.error(f"Error ML clasificar_gasto usuario {usuario_id}: {e}")
        return {
            "categoria": "Otros",
            "confianza": 0.0,
            "fuente": "ml_propio",
            "algoritmo": "naive_bayes",
        }


def normalizar_descripcion(descripcion: str) -> str:
    """Forma canónica para comparar descripciones de gastos.

    Insensible a mayúsculas, tildes y espacios múltiples: el usuario debería
    poder corregir "Adobe Photoshop" una vez y que la corrección se aplique
    también a "adobe  photoshop" o "ADOBE PHOTOSHOP". Es la misma estrategia
    que csv_service usa para detectar duplicados en importaciones bancarias.
    """
    if not descripcion:
        return ""
    nfkd = unicodedata.normalize("NFKD", descripcion)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes.lower().strip())


def registrar_ejemplo(descripcion: str, categoria: str, db: Session, usuario_id: int) -> None:
    """Persiste una corrección explícita aportada por el usuario desde el
    playground del clasificador (POST /ml/corregir). La corrección se usa
    como ejemplo de entrenamiento adicional en el próximo reentrenamiento."""
    try:
        descripcion_norm = normalizar_descripcion(descripcion)
        existente = db.query(CacheClasificacion).filter(
            CacheClasificacion.usuario_id == usuario_id,
            CacheClasificacion.descripcion_normalizada == descripcion_norm,
        ).first()
        if existente:
            existente.categoria = categoria
        else:
            db.add(CacheClasificacion(
                usuario_id=usuario_id,
                descripcion_normalizada=descripcion_norm,
                categoria=categoria,
            ))
        db.commit()
    except Exception as e:
        logger.error(f"Error registrar_ejemplo: {e}")
        db.rollback()


def reentrenar_modelo_usuario(db: Session, usuario_id: int) -> dict:
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.descripcion.isnot(None),
        Gasto.categoria.isnot(None),
    ).all()

    X_usuario = [g.descripcion.strip().lower() for g in gastos if g.descripcion and g.categoria]
    y_usuario = [g.categoria for g in gastos if g.descripcion and g.categoria]

    # Correcciones explícitas del usuario desde el playground (/ml/corregir).
    # No dependen de que existan gastos reales asociados: son enseñanza directa
    # al modelo. Por eso entran como ejemplos de entrenamiento del usuario.
    correcciones = db.query(CacheClasificacion).filter(
        CacheClasificacion.usuario_id == usuario_id,
    ).all()
    X_correcciones = [c.descripcion_normalizada for c in correcciones]
    y_correcciones = [c.categoria for c in correcciones]

    X_base = [desc for desc, _ in DATASET_BASE]
    y_base = [cat for _, cat in DATASET_BASE]

    X = X_base + X_usuario + X_correcciones
    y = y_base + y_usuario + y_correcciones
    n = len(X_usuario) + len(X_correcciones)

    if n < 20:
        modelo_base = db.query(ModeloClasificador).filter(
            ModeloClasificador.usuario_id.is_(None),
            ModeloClasificador.activo == True,
        ).first()
        if not modelo_base:
            modelo_base = entrenar_modelo_base(db)
        return {
            "n_ejemplos": n,
            "precision": modelo_base.precision,
            "algoritmo": modelo_base.algoritmo,
            "mensaje": "Pocos ejemplos propios, usando modelo base. Clasificá más gastos para personalizar.",
        }

    algoritmo = _elegir_algoritmo(len(X))
    pipeline = _crear_pipeline(algoritmo)
    pipeline.fit(X, y)

    precision = _calcular_precision(pipeline, X, y, cv=3)
    modelo_str = _serializar_modelo(pipeline)

    db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id == usuario_id,
        ModeloClasificador.activo == True,
    ).update({"activo": False})
    db.commit()

    nuevo = ModeloClasificador(
        usuario_id=usuario_id,
        modelo_serializado=modelo_str,
        algoritmo=algoritmo,
        precision=precision,
        n_ejemplos=len(X),
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {
        "n_ejemplos": len(X),
        "precision": precision,
        "algoritmo": algoritmo,
        "mensaje": f"Modelo personalizado entrenado con {len(X)} ejemplos ({n} propios + {len(X_base)} base).",
    }


# ── Política de reentrenamiento automático ──────────────────────────────────
# La tesis declara que el clasificador "aprende de las correcciones del usuario
# mediante reentrenamiento automático". Estos dos parámetros definen cuándo se
# dispara ese reentrenamiento sin intervención manual.

UMBRAL_MINIMO_REENTRENAMIENTO = 20
# Por debajo de este número de gastos clasificados, no entrenamos un modelo
# personalizado: el sample sería demasiado chico para que el SVM/Naive Bayes
# generalice algo útil contra las 12 categorías. Mismo umbral que ya usa
# reentrenar_modelo_usuario() para no entrar en contradicción.

INTERVALO_REENTRENAMIENTO_NUEVOS = 10
# Cantidad de gastos nuevos que se acumulan antes de reentrenar por creación.
# Buscamos un balance: si reentrenamos en cada gasto, gastamos CPU al pedo;
# si esperamos demasiado, el modelo queda viejo. Diez es razonable para un
# freelancer típico que carga ~30-60 gastos al mes.


def evaluar_reentrenamiento_automatico(db: Session, usuario_id: int, motivo: str = "creacion") -> dict:
    """Evalúa la política de reentrenamiento y dispara el fit si corresponde.

    motivo: "creacion"   → gasto nuevo, reentrena cada INTERVALO_REENTRENAMIENTO_NUEVOS.
            "correccion" → el usuario cambió la categoría de un gasto existente.
                           Esa es la señal más informativa que tenemos, así que
                           reentrenamos siempre que se haya superado el umbral.
    """
    n_actuales = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.descripcion.isnot(None),
        Gasto.categoria.isnot(None),
    ).count()

    if n_actuales < UMBRAL_MINIMO_REENTRENAMIENTO:
        return {
            "reentrenado": False,
            "razon": "umbral_no_alcanzado",
            "n_actuales": n_actuales,
            "umbral": UMBRAL_MINIMO_REENTRENAMIENTO,
        }

    modelo_actual = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id == usuario_id,
        ModeloClasificador.activo == True,
    ).first()

    if modelo_actual is None:
        # El usuario recién cruzó el umbral: primer entrenamiento personalizado.
        resultado = reentrenar_modelo_usuario(db, usuario_id)
        return {"reentrenado": True, "razon": "primer_entrenamiento", **resultado}

    # n_ejemplos guardado = DATASET_BASE + propios al momento del último fit.
    # Restando el tamaño del base obtenemos cuántos propios había entonces.
    n_propios_anterior = max(0, modelo_actual.n_ejemplos - len(DATASET_BASE))
    nuevos_desde_ultimo = n_actuales - n_propios_anterior

    if motivo == "correccion":
        resultado = reentrenar_modelo_usuario(db, usuario_id)
        return {"reentrenado": True, "razon": "correccion_usuario", **resultado}

    if nuevos_desde_ultimo >= INTERVALO_REENTRENAMIENTO_NUEVOS:
        resultado = reentrenar_modelo_usuario(db, usuario_id)
        return {"reentrenado": True, "razon": "intervalo_alcanzado", **resultado}

    return {
        "reentrenado": False,
        "razon": "intervalo_no_alcanzado",
        "n_actuales": n_actuales,
        "nuevos_desde_ultimo": nuevos_desde_ultimo,
        "intervalo": INTERVALO_REENTRENAMIENTO_NUEVOS,
    }


def evaluar_modelo_base(db: Session) -> dict:
    """Mide la performance del modelo base con cross-validation 5-fold.

    Devuelve accuracy global, métricas por categoría (precision, recall, f1)
    y matriz de confusión. Se usa antes de ampliar el dataset para diagnosticar
    qué categorías están fallando, y después para validar la mejora.

    Cross-validation 5-fold significa que cada ejemplo se predice cinco veces
    (entrenando con el resto del dataset cada vez) y se promedia. Es una
    métrica más honesta que evaluar sobre el mismo dataset de entrenamiento.
    """
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

    X = [desc for desc, _ in DATASET_BASE]
    y = [cat for _, cat in DATASET_BASE]
    n = len(X)

    algoritmo = _elegir_algoritmo(n)
    pipeline = _crear_pipeline(algoritmo)

    # cross_val_predict da la predicción de cada ejemplo cuando NO formó parte
    # del fold de entrenamiento. Esa es la métrica que reportamos.
    y_pred = cross_val_predict(pipeline, X, y, cv=5)

    accuracy = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)
    matriz = confusion_matrix(y, y_pred, labels=CATEGORIAS_VALIDAS)

    return {
        "accuracy_global": float(accuracy),
        "por_categoria": {
            cat: {
                "precision": float(report[cat]["precision"]),
                "recall": float(report[cat]["recall"]),
                "f1": float(report[cat]["f1-score"]),
                "support": int(report[cat]["support"]),
            }
            for cat in CATEGORIAS_VALIDAS if cat in report
        },
        "matriz_confusion": {
            "labels": list(CATEGORIAS_VALIDAS),
            "matriz": matriz.tolist(),
        },
        "n_ejemplos_total": n,
        "algoritmo": algoritmo,
    }


def obtener_estado_modelo(db: Session, usuario_id: int) -> dict:
    modelo_usuario = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id == usuario_id,
        ModeloClasificador.activo == True,
    ).first()

    if modelo_usuario:
        return {
            "tiene_modelo_propio": True,
            "algoritmo": modelo_usuario.algoritmo,
            "precision": modelo_usuario.precision,
            "n_ejemplos": modelo_usuario.n_ejemplos,
            "fecha_entrenamiento": modelo_usuario.fecha_entrenamiento,
            "usa_modelo_base": False,
        }

    modelo_base = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id.is_(None),
        ModeloClasificador.activo == True,
    ).first()

    if modelo_base:
        return {
            "tiene_modelo_propio": False,
            "algoritmo": modelo_base.algoritmo,
            "precision": modelo_base.precision,
            "n_ejemplos": modelo_base.n_ejemplos,
            "fecha_entrenamiento": modelo_base.fecha_entrenamiento,
            "usa_modelo_base": True,
        }

    return {
        "tiene_modelo_propio": False,
        "algoritmo": None,
        "precision": None,
        "n_ejemplos": 0,
        "fecha_entrenamiento": None,
        "usa_modelo_base": True,
    }
