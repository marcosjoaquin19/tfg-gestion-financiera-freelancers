"""
Servicio de Machine Learning — clasificador de gastos por texto.

Núcleo del clasificador NLP que asigna una categoría a un gasto según su
descripción. Entrena modelos de scikit-learn (Naive Bayes o SVM lineal sobre
features TF-IDF) usando un dataset base más los gastos y correcciones del
usuario. El entrenamiento corre 100% local (soberanía de datos); el modelo se
serializa y se guarda en la BD para reutilizarlo sin reentrenar cada vez.

Funciones clave: clasificar_gasto(), reentrenar_modelo_usuario(), registrar_ejemplo()
y obtener_estado_modelo().

Cómo leer este archivo (recorrido de un gasto):
  1. Clasificar: ia_service.clasificar_gasto() llama a clasificar_gasto() de
     acá, que pide el modelo a obtener_o_crear_modelo() (el propio del usuario
     si ya lo tiene, si no el modelo base) y devuelve categoría + confianza.
  2. Aprender: cada gasto cargado o corregido pasa por
     evaluar_reentrenamiento_automatico(), que decide si conviene reentrenar;
     las correcciones del Clasificador se guardan con registrar_ejemplo().
  3. Reentrenar: _reentrenar_modelo_usuario() junta los 600 ejemplos base con
     los gastos y correcciones del usuario y entrena su modelo propio.

Vocabulario mínimo:
  - TF-IDF: forma de convertir un texto en números. Cada palabra recibe un peso
    alto si aparece en esa descripción y es rara en el resto (distingue), y
    bajo si aparece en casi todas (no aporta).
  - Naive Bayes y SVM: los dos algoritmos que aprenden a ir de esos números a
    una categoría. Naive Bayes calcula probabilidades por palabra; SVM busca la
    frontera que mejor separa una categoría de otra.
  - Validación cruzada: forma honesta de medir la exactitud. Se prueba al modelo
    con ejemplos que no vio al entrenar (como tomar examen con preguntas nuevas).
"""

# PATRÓN: Strategy — _elegir_algoritmo() selecciona Naive Bayes o SVM según el volumen de datos.
# PATRÓN: Pipeline — TF-IDF y clasificador encadenados en un solo objeto entrenable.
# PATRÓN: Memento — el modelo entrenado se convierte a texto (joblib + base64) y se guarda en la BD.
# PATRÓN: carga diferida con respaldo — obtener_o_crear_modelo() busca el modelo
#         recién cuando se necesita: el del usuario → si no, el base → si no, lo entrena.
# Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md

import base64
import logging
import re
import threading
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
from app.services.categorias_gasto import CATEGORIAS_GASTO

logger = logging.getLogger(__name__)

# Alias histórico: el resto del módulo y los tests usan este nombre.
CATEGORIAS_VALIDAS = CATEGORIAS_GASTO

# Dataset base: 600 ejemplos, 50 por cada una de las 12 categorías.
# El balanceo es deliberado: con clases desbalanceadas la exactitud global
# se vuelve engañosa (el modelo acierta prediciendo siempre la clase mayoritaria).
# Con 50 por categoría, el 76 % de exactitud (aciertos sobre el total) medido por
# validación cruzada de 5 particiones es una medida honesta. Ver Anexo A de la tesis.
# Son descripciones cortas y en minúscula, como las que escribe un freelancer
# argentino o las que trae un extracto bancario. Las tildes no importan: el
# TF-IDF las quita antes de aprender (ver _crear_pipeline).
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
    """Arma el modelo vacío: un "Pipeline" de dos pasos, todavía sin entrenar.

    Pipeline es como una línea de montaje: el texto entra por un extremo, pasa
    por el TF-IDF (texto → números) y después por el clasificador (números →
    categoría). Se entrena y se usa como una sola pieza, así nunca puede pasar
    que se entrene con una conversión y se prediga con otra.
    """
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),       # mira palabras sueltas y pares de palabras seguidas:
                                  # "mercado libre" dice más que "mercado" y "libre" por separado
        strip_accents="unicode",  # "batería" y "bateria" cuentan como la misma palabra
        lowercase=True,           # "ADOBE" y "adobe" también
        min_df=1,                 # alcanza con que una palabra aparezca una vez para
                                  # tenerla en cuenta (el dataset es chico: 50 por categoría)
    )
    if algoritmo == "svm":
        # LinearSVC = SVM lineal. max_iter es el tope de vueltas que puede dar el
        # cálculo hasta encontrar la frontera entre categorías.
        #
        # random_state=0 fija la "semilla" del azar que usa el algoritmo por dentro.
        # El resultado es el mismo (medido: igual exactitud y confianzas), pero sin
        # semilla propia LinearSVC sacaba números del generador de azar compartido
        # de numpy, el mismo que usa Prophet para calcular la banda (el rango
        # mínimo-máximo) de la proyección. Como el reentrenamiento corre de fondo
        # justo después de importar un extracto, le cambiaba la banda a la
        # proyección que se calculaba al mismo tiempo.
        clasificador = LinearSVC(max_iter=2000, random_state=0)
    else:
        # Naive Bayes "multinomial": el que se usa para contar palabras en textos.
        clasificador = MultinomialNB()
    return Pipeline([("tfidf", vectorizer), ("clf", clasificador)])


def _serializar_modelo(pipeline: Pipeline) -> str:
    """Convierte el modelo entrenado en texto para poder guardarlo en la base.

    Serializar = pasar un objeto que vive en memoria a un formato que se puede
    guardar y después reconstruir (como "congelar" el modelo).
    """
    # joblib es la biblioteca que recomienda scikit-learn para guardar modelos:
    # guarda las tablas de números (arrays de NumPy) de forma más eficiente que
    # pickle, el formato estándar de Python. El resultado son bytes; base64 los
    # pasa a letras y números para poder guardarlos como texto en la columna
    # modelo_serializado de la tabla modelos_clasificador.
    buffer = BytesIO()
    joblib.dump(pipeline, buffer)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _deserializar_modelo(texto: str) -> Pipeline:
    """Lo inverso: a partir del texto guardado reconstruye el modelo listo para usar.

    Por eso no hace falta reentrenar en cada clasificación: se "descongela".
    """
    datos = base64.b64decode(texto)
    return joblib.load(BytesIO(datos))


def _elegir_algoritmo(n_ejemplos: int) -> str:
    """Strategy: Naive Bayes con menos de 100 ejemplos, SVM desde 100.

    Es la regla que define la tesis (pág. 14): Naive Bayes se comporta mejor con
    pocos datos y SVM aprovecha mejor el volumen. Medido con los 600 ejemplos:
    SVM 76 %, Naive Bayes 74 %. Como todo modelo (base o del usuario) incluye
    siempre los 600 ejemplos base, en la práctica se usa SVM; Naive Bayes queda
    para conjuntos chicos.
    """
    return "svm" if n_ejemplos >= 100 else "naive_bayes"


def _calcular_precision(pipeline: Pipeline, X: list, y: list, cv: int = 5) -> Optional[float]:
    """Mide la exactitud del modelo con validación cruzada (porcentaje de aciertos).

    Cómo funciona, con cv=5: se parten los ejemplos en 5 grupos; se entrena con
    4 y se toma "examen" con el quinto, que el modelo no vio. Se repite 5 veces
    rotando el grupo de examen y se promedian las 5 notas. Así no se mide al
    modelo con las mismas preguntas que estudió (eso daría casi 100 % y mentiría).

    Ojo con el nombre: la función y la columna de la base se llaman "precision"
    por el diseño original, pero lo que se mide es la exactitud (scoring=
    "accuracy": aciertos / total). En aprendizaje automático, "precision" es otra
    métrica: de los gastos que el modelo dijo que eran "Software", cuántos lo eran.

    X son las descripciones y y las categorías correctas (los nombres X/y son la
    convención de scikit-learn: entrada y respuesta esperada).

    Devuelve None si no hay datos suficientes para medir.
    """
    try:
        import pandas as pd
        conteos = pd.Series(y).value_counts()   # cuántos ejemplos tiene cada categoría
        min_clase = int(conteos.min())
        # Cada grupo de examen necesita al menos un ejemplo de cada categoría: si
        # una categoría tiene solo 3 ejemplos, no se la puede repartir en 5 grupos.
        # Por eso se usan como mucho tantos grupos como ejemplos tenga la
        # categoría más chica.
        cv_real = min(cv, min_clase)
        if cv_real < 2 or len(X) < cv_real:
            # Con menos de 2 grupos no hay forma de entrenar con uno y probar con otro.
            return None
        scores = cross_val_score(pipeline, X, y, cv=cv_real, scoring="accuracy")
        return float(scores.mean())   # promedio de las notas de cada vuelta
    except Exception as e:
        # Si la medición falla, el modelo igual se guarda; solo queda sin el dato.
        logger.warning(f"No se pudo calcular precisión CV: {e}")
        return None


def entrenar_modelo_base(db: Session) -> ModeloClasificador:
    """Entrena y guarda el modelo base: el que comparten todos los usuarios nuevos.

    Se entrena solo con los 600 ejemplos de DATASET_BASE y se guarda con
    usuario_id vacío (None), que es la marca de "no es de nadie en particular".
    Cada usuario lo usa hasta juntar 20 gastos propios; desde ahí tiene su
    modelo personal (ver _reentrenar_modelo_usuario).

    La exactitud se mide con validación cruzada de 5 partes: es el 76 % que
    informa la tesis y que muestra la pantalla Clasificador.
    """
    # Buscamos el modelo base activo. En SQLAlchemy (la biblioteca que traduce
    # estas consultas a SQL) se escribe "== True" e ".is_(None)" para que la
    # comparación se haga en la base de datos y no en Python.
    existente = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id.is_(None),
        ModeloClasificador.activo == True,
    ).first()

    # Solo nos salteamos el entrenamiento si el modelo guardado ya usó TODOS los
    # ejemplos disponibles. Si al dataset se le sumaron ejemplos, se entrena de
    # nuevo para que el modelo guardado refleje el dataset actual.
    if existente and existente.n_ejemplos >= len(DATASET_BASE):
        return existente

    X = [desc for desc, _ in DATASET_BASE]   # entradas: las descripciones
    y = [cat for _, cat in DATASET_BASE]     # respuestas correctas: las categorías
    n = len(X)

    algoritmo = _elegir_algoritmo(n)
    pipeline = _crear_pipeline(algoritmo)
    pipeline.fit(X, y)   # fit = entrenar: el modelo aprende de los ejemplos

    precision = _calcular_precision(pipeline, X, y, cv=5)
    modelo_str = _serializar_modelo(pipeline)

    # Si ya había un modelo base (con menos ejemplos), se lo actualiza en el
    # mismo registro; si no había ninguno, se crea. db.commit() es el momento
    # en que los cambios quedan guardados de verdad en la base de datos.
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


def obtener_o_crear_modelo(db: Session, usuario_id: int) -> tuple[Pipeline, str, bool]:
    """Devuelve el modelo con el que hay que clasificar a este usuario.

    Orden de búsqueda (patrón "carga diferida con respaldo"):
      1. El modelo propio y activo del usuario, si ya tiene uno.
      2. Si no tiene, o si el suyo no se puede leer: el modelo base compartido.
      3. Si todavía no existe el modelo base (base de datos recién creada), lo
         entrena en el momento.

    Retorna (pipeline, algoritmo, es_modelo_propio). El tercer elemento
    distingue si el modelo devuelto es el personal del usuario o el base. Sin
    ese dato la respuesta de clasificación no puede decir con honestidad de
    dónde salió la predicción, y se contradice con lo que informa GET /ml/estado.
    """
    # 1. ¿El usuario ya tiene modelo propio?
    modelo_usuario = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id == usuario_id,
        ModeloClasificador.activo == True,
    ).first()

    if modelo_usuario:
        try:
            pipeline = _deserializar_modelo(modelo_usuario.modelo_serializado)
            return pipeline, modelo_usuario.algoritmo, True
        except Exception as e:
            # Si el modelo propio está dañado no cortamos la clasificación:
            # seguimos con el modelo base (paso 2).
            logger.error(f"Error deserializando modelo usuario {usuario_id}, reentrenando base: {e}")

    # 2. Modelo base compartido.
    modelo_base = db.query(ModeloClasificador).filter(
        ModeloClasificador.usuario_id.is_(None),
        ModeloClasificador.activo == True,
    ).first()

    # 3. Si no existe, se entrena ahora (pasa una sola vez, con la base vacía).
    if not modelo_base:
        modelo_base = entrenar_modelo_base(db)

    try:
        pipeline = _deserializar_modelo(modelo_base.modelo_serializado)
        return pipeline, modelo_base.algoritmo, False
    except Exception as e:
        # Último intento si el modelo base guardado no se puede leer. Ojo:
        # entrenar_modelo_base() solo vuelve a entrenar si el guardado tiene menos
        # ejemplos que el dataset; si tiene todos, devuelve el mismo registro, la
        # lectura vuelve a fallar y clasificar_gasto() responde "Otros" con
        # confianza 0 (el gasto queda marcado para revisión, no se rompe nada).
        logger.error(f"Error deserializando modelo base, reentrenando: {e}")
        modelo_base = entrenar_modelo_base(db)
        pipeline = _deserializar_modelo(modelo_base.modelo_serializado)
        return pipeline, modelo_base.algoritmo, False


def _confianza_svm(scores: np.ndarray) -> tuple[int, float]:
    """Calcula qué tan seguro está el SVM, a partir de la distancia entre sus dos mejores opciones.

    El SVM no da probabilidades: decision_function() devuelve un puntaje por
    categoría ("scores": cuánto se inclina el modelo hacia cada una). Para
    convertirlos en una confianza entre 0 y 1 probamos primero lo habitual,
    repartir los puntajes como porcentajes entre las 12 categorías (lo que se
    llama softmax), y no sirvió: aun en los aciertos claros la ganadora quedaba
    cerca de 0,20, por debajo de cualquier umbral razonable.

    Lo que sí refleja la duda del modelo es la brecha entre la mejor categoría y
    la segunda: 0 si empatan (el modelo duda entre dos) y más grande cuanto más
    se despega la ganadora. La llevamos a un número entre 0 y 1 con
    1 - e^(-brecha), que siempre crece con la brecha y nunca pasa de 1:
        brecha 0    → confianza 0 %
        brecha 0,36 → 30 % (el umbral de revisión, ver ia_service.UMBRAL_CONFIANZA_ML)
        brecha 1    → 63 %
        brecha 2    → 86 %

    Devuelve (posición de la categoría ganadora, confianza).
    """
    if len(scores) == 1:
        # Caso de solo dos categorías (no pasa con las 12 reales, pero
        # scikit-learn lo devuelve distinto): llega un único puntaje con signo;
        # positivo = segunda categoría, negativo = primera.
        idx = 1 if scores[0] > 0 else 0
        return idx, float(1.0 - np.exp(-abs(float(scores[0]))))
    orden = np.argsort(scores)[::-1]                      # posiciones de mayor a menor puntaje
    brecha = float(scores[orden[0]] - scores[orden[1]])   # mejor menos segunda
    return int(orden[0]), float(1.0 - np.exp(-brecha))


def clasificar_gasto(descripcion: str, db: Session, usuario_id: int) -> dict:
    """Predice la categoría de una descripción y cuánta confianza tiene el modelo.

    Es la predicción "pura" del modelo. Quien la llama, ia_service.clasificar_gasto(),
    agrega dos cosas antes: si el usuario ya corrigió esa misma descripción, usa
    la corrección; y si la confianza queda por debajo del 30 %, sugiere "Otros"
    y marca el gasto para revisión.

    Todo corre en el servidor propio: la descripción del gasto no sale a ningún
    servicio externo (soberanía de datos; se descartó clasificar con Groq por eso).

    Devuelve un diccionario con categoria, confianza (0 a 1), fuente ("ml_propio"
    o "ml_base") y algoritmo.
    """
    try:
        pipeline, algoritmo, es_propio = obtener_o_crear_modelo(db, usuario_id)
        clases = pipeline.classes_   # las 12 categorías, en el orden interno del modelo

        if algoritmo == "svm":
            # Un puntaje por categoría → confianza por brecha (ver _confianza_svm).
            scores = np.array(pipeline.decision_function([descripcion])[0], dtype=float).ravel()
            idx, confianza = _confianza_svm(scores)
        else:
            # Naive Bayes sí da probabilidades: la más alta es la categoría elegida
            # y su probabilidad es la confianza.
            probas = pipeline.predict_proba([descripcion])[0]
            idx = int(np.argmax(probas))
            confianza = float(probas[idx])

        categoria = clases[idx]

        return {
            "categoria": categoria,
            "confianza": confianza,
            # "ml_propio" solo si el pipeline es el modelo reentrenado del
            # usuario; si todavía no cruzó el umbral, es el modelo base.
            "fuente": "ml_propio" if es_propio else "ml_base",
            "algoritmo": algoritmo,
        }
    except Exception as e:
        # Si algo falla, el alta del gasto no se corta: va a "Otros" con
        # confianza 0, y por estar debajo del umbral queda marcado para revisión.
        logger.error(f"Error ML clasificar_gasto usuario {usuario_id}: {e}")
        return {
            "categoria": "Otros",
            "confianza": 0.0,
            "fuente": "ml_base",
            "algoritmo": "naive_bayes",
        }


def normalizar_descripcion(descripcion: str) -> str:
    """Lleva una descripción a una forma única para poder compararla con otras.

    No le importan las mayúsculas, las tildes ni los espacios repetidos: el
    usuario corrige "Adobe Photoshop" una vez y la corrección se aplica también
    a "adobe  photoshop" o "ADOBE PHOTOSHOP". Ejemplo: "  Café   Martínez " →
    "cafe martinez".
    """
    if not descripcion:
        return ""
    # NFKD separa cada letra de su tilde ("é" pasa a ser "e" + "´")...
    nfkd = unicodedata.normalize("NFKD", descripcion)
    # ...y acá se descartan las tildes sueltas (los caracteres "combinables").
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Minúsculas, sin espacios en los bordes y los espacios repetidos se vuelven uno.
    return re.sub(r"\s+", " ", sin_tildes.lower().strip())


def registrar_ejemplo(descripcion: str, categoria: str, db: Session, usuario_id: int) -> None:
    """Guarda una corrección que el usuario hizo en la pantalla Clasificador (POST /ml/corregir).

    Se guarda en la tabla cache_clasificacion y sirve para dos cosas:
      - la próxima vez que aparezca esa misma descripción, ia_service la usa
        directo, sin preguntarle al modelo (confianza 100 %);
      - entra como ejemplo de entrenamiento en el próximo reentrenamiento.
    Si esa descripción ya estaba corregida, se pisa con la categoría nueva: la
    última corrección del usuario es la que vale.
    """
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
        db.commit()   # guardar los cambios en la base
    except Exception as e:
        logger.error(f"Error registrar_ejemplo: {e}")
        db.rollback()   # deshacer lo que quedó a medias para no dejar la sesión rota


# Un reentrenamiento a la vez por usuario. Las correcciones y los gastos nuevos
# disparan reentrenamientos en segundo plano; si dos corrían a la vez, cada uno
# desactivaba el modelo anterior e insertaba el suyo, y el usuario quedaba con
# varios modelos "activos". La API corre en un solo proceso, así que un candado
# en memoria alcanza para ordenarlos.
#
# Un candado (threading.Lock) funciona como la llave del baño de una estación de
# servicio: el que la tiene entra, y el que llega después espera a que la devuelvan.
# Hay un candado por usuario, así el reentrenamiento de uno no frena al de otro.
_candados_reentrenamiento: dict[int, threading.Lock] = {}
# Este segundo candado cuida el diccionario de arriba: evita que dos pedidos
# simultáneos le creen dos candados distintos al mismo usuario.
_candado_registro = threading.Lock()


def _candado_de(usuario_id: int) -> threading.Lock:
    """Devuelve el candado del usuario; la primera vez lo crea."""
    with _candado_registro:
        return _candados_reentrenamiento.setdefault(usuario_id, threading.Lock())


def reentrenar_modelo_usuario(db: Session, usuario_id: int) -> dict:
    """Reentrena el modelo del usuario, esperando su turno si ya hay uno en curso.

    Es la función que llaman las rutas (POST /ml/reentrenar) y la política
    automática. El trabajo real está en _reentrenar_modelo_usuario().
    """
    with _candado_de(usuario_id):   # "with" toma el candado y lo suelta al terminar, aunque falle
        return _reentrenar_modelo_usuario(db, usuario_id)


def _reentrenar_modelo_usuario(db: Session, usuario_id: int) -> dict:
    """Entrena el modelo personal del usuario.

    Pasos:
      1. Junta tres fuentes de ejemplos: los 600 del dataset base, los gastos
         del usuario (descripción + categoría que quedó guardada) y sus
         correcciones del Clasificador.
      2. Si entre gastos y correcciones tiene menos de 20 propios, no entrena:
         todavía no hay suficiente información suya y sigue con el modelo base.
      3. Si tiene 20 o más, entrena, mide la exactitud, desactiva el modelo
         anterior y guarda el nuevo como activo. Los anteriores quedan en la
         tabla con activo=False (historial).

    Los 600 ejemplos base siempre se incluyen: así el modelo personal nunca
    "olvida" las categorías para las que el usuario todavía no cargó gastos.
    """
    # Paso 1a: los gastos del usuario que tienen descripción y categoría.
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.descripcion.isnot(None),
        Gasto.categoria.isnot(None),
    ).all()

    X_usuario = [g.descripcion.strip().lower() for g in gastos if g.descripcion and g.categoria]
    y_usuario = [g.categoria for g in gastos if g.descripcion and g.categoria]

    # Paso 1b: correcciones explícitas del usuario desde el Clasificador (/ml/corregir).
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
    n = len(X_usuario) + len(X_correcciones)   # cuántos ejemplos son del usuario

    # Paso 2: con menos de 20 propios no vale la pena un modelo personal
    # (mismo valor que UMBRAL_MINIMO_REENTRENAMIENTO, más abajo).
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

    # Paso 3: entrenar el modelo personal.
    algoritmo = _elegir_algoritmo(len(X))
    pipeline = _crear_pipeline(algoritmo)
    pipeline.fit(X, y)   # fit = entrenar

    # Se mide con 3 partes y no con 5 como el modelo base: esto corre en segundo
    # plano cada vez que el usuario corrige o carga gastos, y 3 partes son 3
    # entrenamientos de prueba en lugar de 5 (más rápido). La cifra de
    # referencia de la tesis (76 %) es la del modelo base, medida con 5.
    precision = _calcular_precision(pipeline, X, y, cv=3)
    modelo_str = _serializar_modelo(pipeline)

    # El modelo anterior del usuario se desactiva (no se borra) y el nuevo pasa
    # a ser el activo: siempre hay uno solo activo por usuario.
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
# personal: la muestra sería demasiado chica para que el modelo aprenda algo
# que sirva con descripciones nuevas en las 12 categorías. Es el mismo umbral
# que usa _reentrenar_modelo_usuario(), para que las dos no se contradigan.

INTERVALO_REENTRENAMIENTO_NUEVOS = 10
# Cantidad de gastos nuevos que se acumulan antes de reentrenar por carga.
# Buscamos un equilibrio: si reentrenáramos con cada gasto, el servidor
# trabajaría de más sin necesidad; si esperáramos demasiado, el modelo quedaría
# desactualizado. Diez es un punto medio: con un uso típico de algunas decenas
# de gastos por mes (estimación de diseño, no medición), el modelo se actualiza
# unas pocas veces por mes.


def evaluar_reentrenamiento_automatico(db: Session, usuario_id: int, motivo: str = "creacion") -> dict:
    """Decide si corresponde reentrenar el modelo del usuario y, si corresponde, lo hace.

    Corre en segundo plano (routers/gastos.py, _reentrenar_en_background):
    después de cada alta de gasto, cuando el usuario le cambia la categoría a
    uno, y al confirmar una importación. El usuario no espera: su gasto ya quedó
    guardado.

    motivo: "creacion"   → gasto nuevo: se reentrena cada 10 gastos nuevos
                           (INTERVALO_REENTRENAMIENTO_NUEVOS).
            "correccion" → el usuario cambió la categoría de un gasto existente.
                           Es la señal más valiosa que tenemos (nos dice
                           exactamente en qué se equivocó el modelo), así que
                           se reentrena siempre que se haya superado el umbral.

    Devuelve un diccionario que dice si reentrenó y por qué ("razon"), útil
    para las pruebas y para los registros del servidor.
    """
    # Cuántos gastos con descripción y categoría tiene hoy el usuario.
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

    # El modelo guardado recuerda con cuántos ejemplos se entrenó (n_ejemplos =
    # 600 base + los propios de ese momento). Restando los 600 base sabemos
    # cuántos propios había, y por diferencia cuántos gastos nuevos llegaron desde
    # el último entrenamiento.
    n_propios_anterior = max(0, modelo_actual.n_ejemplos - len(DATASET_BASE))
    nuevos_desde_ultimo = n_actuales - n_propios_anterior

    # Una corrección reentrena siempre; un gasto nuevo, solo cada 10.
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
    """Evaluación completa del modelo base con validación cruzada de 5 partes.

    No la usa la aplicación: la usa el script evaluar_modelo.py, que genera las
    cifras del Anexo A de la tesis. Sirvió para ver qué categorías fallaban antes
    de ampliar el dataset y para confirmar después que había mejorado.

    Validación cruzada de 5 partes: los 600 ejemplos se parten en 5 grupos de
    120. Cada grupo, por turno, queda afuera del entrenamiento y el modelo lo
    predice "a ciegas". Al final, cada ejemplo se predijo una sola vez y siempre
    por un modelo que no lo había visto. Es una medida más honesta que evaluar
    con los mismos ejemplos con los que se entrenó.

    Devuelve:
      - exactitud global: aciertos / total (el 76 %);
      - por categoría:
          precision = de los gastos que el modelo dijo "Software", cuántos lo eran;
          recall    = de los gastos que eran "Software", cuántos encontró;
          f1        = un promedio de las dos (si una es baja, el f1 también);
          support   = cuántos ejemplos de esa categoría había (50);
      - matriz de confusión: tabla de "categoría real" contra "categoría predicha".
        La diagonal son los aciertos; lo que queda fuera muestra con qué se confunde
        cada categoría.
    """
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

    X = [desc for desc, _ in DATASET_BASE]
    y = [cat for _, cat in DATASET_BASE]
    n = len(X)

    algoritmo = _elegir_algoritmo(n)
    pipeline = _crear_pipeline(algoritmo)

    # cross_val_predict devuelve, para cada ejemplo, lo que predijo el modelo
    # entrenado SIN ese ejemplo (cuando su grupo quedó afuera). Con esas
    # predicciones "a ciegas" se calculan todas las métricas de abajo.
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
    """Datos del modelo que está usando el usuario (GET /ml/estado).

    Es lo que muestra el recuadro de arriba de la pantalla Clasificador:
    algoritmo, exactitud, cantidad de ejemplos y fecha del último entrenamiento.
    Tres casos: el usuario tiene modelo propio; usa el modelo base; o todavía
    no existe ningún modelo (base de datos recién creada, sin sembrar).
    """
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
