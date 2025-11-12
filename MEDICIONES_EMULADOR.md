MEDICIONES CON EL EMULADOR, clienteTren2.py y servidorTren.py

Objetivo

Documentar y automatizar el procedimiento para medir: ancho de banda, retardo (OWD), desviación estándar del retardo (jitter) y pérdidas usando el ejecutable `emulador`, `clienteTren2.py` y `servidorTren.py`.

Resumen rápido de configuración (ejemplos)

- servidor escucha: 127.0.0.1:5000
- emulador escucha: 127.0.0.1:4000 (reenvía a 127.0.0.1:5000)
- cliente apunta a emulador: 127.0.0.1:4000
- Parámetros ejemplo de cliente: `trainLength=1000`, `dataLength=1000`

Pasos (repetir para cada DNI)

1) Iniciar el servidor de métricas

   En una terminal:
   ```bash
   python3 servidorTren.py 127.0.0.1 5000
   ```
   El servidor imprimirá las métricas al terminar cada tren (timeout 8 s sin paquetes).

2) Iniciar el emulador con el DNI correspondiente

   En otra terminal (mantener activo):
   ```bash
   ./emulador 127.0.0.1 4000 127.0.0.1 5000 DNI
   ```
   Sustituye DNI por 55242328 o 02349187 según el caso.

3) Medida primaria: ancho de banda y pérdidas (envío a máxima velocidad)

   En otra terminal lanza el cliente sin control de tasa:
   ```bash
   python3 clienteTren2.py 127.0.0.1 4000 1000 1000 0
   ```
   - El `servidorTren.py` mostrará: BW medio global, BW instantáneo (min/max/media), paquetes esperados/recibidos/pérdida%.
   - Ancho de banda estimado ≈ `BW medio global`.
   - Porcentaje de pérdidas ≈ `pérdida`.
   Repite 3 veces y toma la mediana o media para estabilidad.

4) Medir retardo (OWD) y desviación (jitter)

   - Para medir OWD correctamente hay que no saturar el enlace. Usa el BW estimado del paso 3 y fija `bitrate_bps` en `clienteTren2.py` a un valor ≤ 90% del BW estimado.
   - Ejemplo: si BW_est = 2_000_000 bps entonces `bitrate_bps = 1800000`:
     ```bash
     python3 clienteTren2.py 127.0.0.1 4000 1000 1000 1800000
     ```
   - Observa en `servidorTren.py` la salida:
     - `OWD (s): media=...` => retardo estimado
     - `jitter(pstdev)=...` => desviación estándar del retardo
   - Repite 3–5 veces y promedia los resultados.

5) Afinar la estimación de ancho de banda (opcional)

   - Ejecuta pruebas con `bitrate_bps` fijos (1 Mbps, 2 Mbps, 4 Mbps, ...) y observa si el `BW medio global` real se sitúa en el límite impuesto por el emulador.
   - También puedes enviar a `bitrate_bps=0` (envío lo más rápido posible) y usar la `BW medio global` resultante como referencia del límite.

6) Registro y reporte

   - Guarda la salida del servidor en ficheros para análisis posterior:
     ```bash
     python3 clienteTren2.py 127.0.0.1 4000 1000 1000 0   > out_bw_DNI.txt
     python3 clienteTren2.py 127.0.0.1 4000 1000 1000 1800000 > out_delay_DNI.txt
     ```
   - Extrae los valores de interés (`bw_mean_global`, `loss_pct`, `owd_mean_s`, `jitter_s`).

7) Repetir para el compañero

   - Para el DNI del compañero repite los pasos 1–6 cambiando el DNI en el comando del emulador.

Comandos concretos para tus DNIs

- Para DNI 55242328:
  1. `python3 servidorTren.py 127.0.0.1 5000`
  2. `./emulador 127.0.0.1 4000 127.0.0.1 5000 55242328`
  3. `python3 clienteTren2.py 127.0.0.1 4000 1000 1000 0`  # medir BW y pérdidas
  4. Tras estimar BW_est, `python3 clienteTren2.py 127.0.0.1 4000 1000 1000 <0.9*BW_est>`  # medir OWD/jitter

- Para DNI 02349187: repetir los mismos pasos sustituyendo el DNI en el comando del emulador.

Consejos prácticos

- Usa `trainLength` entre 500 y 2000 para mayor estabilidad.
- `dataLength` entre 500 y 1200 bytes. Evita >1400 en red real (no loopback).
- Repite varias veces y usa la mediana para resultados robustos.
- Si trabajas en máquinas diferentes, usa IPs reales y asegúrate de conectividad entre emulador y servidor.

Análisis final

- Ancho de banda estimado: `bw_mean_global` (bit/s)
- Retardo estimado: `owd_mean_s` (s)
- Desviación estándar del retardo: `jitter_s` (s)
- Porcentaje de pérdidas: `loss_pct` (%)

Si quieres, puedo crear un script que automatice las 3 repeticiones y guarde los resultados en ficheros para cada DNI.
