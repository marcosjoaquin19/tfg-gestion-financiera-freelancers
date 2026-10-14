"""API con el reloj en el 14/10/2026 12:00 (hora AR), para las capturas de las filminas.
Primero se importa la app (pydantic no tolera la fecha falsa al definir sus clases)."""
import uvicorn
from app.main import app
from freezegun import freeze_time
freeze_time("2026-10-14 15:00:00", tick=True).start()
uvicorn.run(app, host="0.0.0.0", port=8000)
