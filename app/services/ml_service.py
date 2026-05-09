import base64
import logging
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

    if existente and existente.n_ejemplos >= 200:
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


def _softmax(x: np.ndarray) -> np.ndarray:
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def clasificar_gasto(descripcion: str, db: Session, usuario_id: int) -> dict:
    try:
        pipeline, algoritmo = obtener_o_crear_modelo(db, usuario_id)
        clases = pipeline.classes_

        if algoritmo == "svm":
            scores = pipeline.decision_function([descripcion])[0]
            probas = _softmax(np.array(scores, dtype=float))
        else:
            probas = pipeline.predict_proba([descripcion])[0]

        idx = int(np.argmax(probas))
        categoria = clases[idx]
        confianza = float(probas[idx])

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


def registrar_ejemplo(descripcion: str, categoria: str, db: Session, usuario_id: int) -> None:
    try:
        descripcion_norm = descripcion.strip().lower()
        existente = db.query(CacheClasificacion).filter(
            CacheClasificacion.descripcion_normalizada == descripcion_norm
        ).first()
        if existente:
            existente.categoria = categoria
        else:
            db.add(CacheClasificacion(
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

    X_base = [desc for desc, _ in DATASET_BASE]
    y_base = [cat for _, cat in DATASET_BASE]

    X = X_base + X_usuario
    y = y_base + y_usuario
    n = len(X_usuario)

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
