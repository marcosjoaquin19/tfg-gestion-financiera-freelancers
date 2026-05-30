# Extractos bancarios de ejemplo

Archivos para demostrar la importación masiva (HU-07) durante la defensa.
Cada uno reproduce el formato real de exportación de un banco argentino
distinto, para mostrar que la detección heurística de columnas y separador
funciona sin configuración manual.

| Archivo | Banco | Separador | Formato fecha | Montos |
|---|---|---|---|---|
| `galicia.csv` | Galicia | `;` (punto y coma) | `dd/mm/yyyy` | Débito/Crédito en columnas separadas |
| `santander.csv` | Santander | `,` (coma) | `yyyy-mm-dd` | Importe único con signo |
| `brubank.csv` | Brubank | `,` (coma) | `yyyy-mm-dd` | Monto único con signo |

## Cómo usarlos

1. Iniciar sesión en `http://localhost:3000`.
2. Ir a **Importar**.
3. Subir cualquiera de estos archivos.
4. Revisar la vista previa: columnas detectadas, tipos (ingreso/gasto) y
   posibles duplicados.
5. Confirmar la importación.

> Para mostrar la **detección de duplicados**, importar el mismo archivo dos
> veces: la segunda vez todos los movimientos aparecen marcados como ya
> existentes.
