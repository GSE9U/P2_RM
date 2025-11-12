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

MEDICIONES ENTRE DOS ORDENADORES (NO localhost)

Prefacio

Las instrucciones anteriores asumían localhost. A continuación se describen los pasos para realizar las mismas mediciones entre dos ordenadores (PC_A y PC_B). En esta configuración: el servidor (`servidorTren.py`) se ejecuta en PC_A; el emulador y el cliente (`clienteTren2.py`) se ejecutan en PC_B. Capture con Wireshark (o tshark) en ambos equipos en cada experimento y guarde los pcap para análisis.

Nombres y variables (sustituir por IPs reales)

- PC_A_IP: dirección IP de la máquina que ejecuta `servidorTren.py` (ej. 192.168.1.10)
- PC_B_IP: dirección IP de la máquina que ejecuta `emulador` y `clienteTren2.py` (ej. 192.168.1.20)
- Puerto servidor: 5000 (ejemplo)
- Puerto emulador (escucha): 4000 (ejemplo)

Pasos detallados (para cada DNI)

1) En PC_A (servidor + captura Wireshark)

- Iniciar `servidorTren.py` escuchando en la IP de PC_A:
  ```bash
  python3 servidorTren.py PC_A_IP 5000
  ```
- Iniciar captura de paquetes en la interfaz que conecta con PC_B (Wireshark GUI) o con tshark:
  ```bash
  sudo tshark -i <iface> -w captura_PC_A_DNI.pcap
  ```
  Mantener la captura hasta que termine el experimento.

2) En PC_B (emulador + cliente + captura Wireshark)

- Iniciar captura en la interfaz que conecta con PC_A:
  ```bash
  sudo tshark -i <iface> -w captura_PC_B_DNI.pcap
  ```
- In otra terminal de PC_B iniciar el emulador (reenvía a PC_A_IP:5000):
  ```bash
  ./emulador PC_B_IP 4000 PC_A_IP 5000 DNI
  ```
  Sustituye `DNI` por 55242328 o 02349187.

- En otra terminal de PC_B lanza `clienteTren2.py` apuntando al emulador (primer experimento: sin control de tasa):
  ```bash
  python3 clienteTren2.py PC_B_IP 4000 1000 1000 0
  ```
  Nota: el primer envío es a máxima velocidad.

3) Qué observar y cómo proceder tras la primera ejecución

- En PC_A el `servidorTren.py` imprimirá las métricas. Anota o guarda la salida (especialmente `bw_mean_global` y `loss_pct`).
- Detén las capturas pcap en ambos equipos cuando termine el tren y guarda los ficheros.

4) Cálculo del bitrate para medir OWD/jitter

- Usa la `bw_mean_global` obtenida en la ejecución rápida como estimación del ancho de banda impuesto por el emulador.
- Fija el bitrate objetivo al 90% de ese valor: bitrate_bps = int(0.9 * bw_mean_global).

5) Medición con tasa limitada (medir OWD y jitter)

- En PC_A reinicia/asegura que `servidorTren.py` sigue activo (o vuelve a arrancarlo si hace falta) y prepara captura nueva: `captura_PC_A_DNI_rate.pcap`.
- En PC_B reinicia captura `captura_PC_B_DNI_rate.pcap`, y lanza de nuevo:
  ```bash
  python3 clienteTren2.py PC_B_IP 4000 1000 1000 <bitrate_bps>
  ```
- En PC_A recoge la salida del servidor y extrae `owd_mean_s` y `jitter_s`.
- Guarda las capturas pcap de ambos equipos.

6) Repeticiones y registro (Wireshark obligatorio según tu comentario)

- Para cada DNI realiza:
  - Una ejecución inicial sin tasa (bitrate 0) y captura pcap en ambos equipos.
  - Cálculo de bitrate_bps = 0.9 * bw_mean_global.
  - 3 ejecuciones con ese bitrate (cada una con capturas pcap en ambos equipos).
- Guarda la salida del servidor (puedes redirigirla a ficheros) y los pcap para análisis posterior.

Ejemplo de comandos concretos (sustituye IPs e iface):

PC_A (servidor):
```bash
python3 servidorTren.py 192.168.1.10 5000 > resultado_servidor_DNI.txt
sudo tshark -i eth0 -w captura_PC_A_DNI.pcap
```

PC_B (emulador+cliente):
```bash
sudo tshark -i eth0 -w captura_PC_B_DNI.pcap &
./emulador 192.168.1.20 4000 192.168.1.10 5000 55242328
python3 clienteTren2.py 192.168.1.20 4000 1000 1000 0
```
Después de la primera ejecución calcular `bitrate_bps` y repetir:
```bash
python3 clienteTren2.py 192.168.1.20 4000 1000 1000 1800000
```
(Ajusta `1800000` por el 90% del `bw_mean_global` que obtuviste.)

Notas y consejos prácticos para la medición en dos máquinas

- Asegúrate de usar la interfaz correcta en tshark/wireshark (la que conecta ambos equipos).
- Si hay firewalls, habilita el tráfico UDP en los puertos usados (4000 y 5000) o desactiva temporalmente el firewall para la prueba.
- Usar ficheros pcap recolectados en ambos extremos permite verificar pérdidas (comparando secuencias) y analizar latencias desde la perspectiva del emisor y receptor.
- Si la latencia entre los equipos es alta por la red local, aumenta `trainLength` para obtener medidas más estables.

Actualiza los placeholders `PC_A_IP`, `PC_B_IP` e `iface` por los valores reales de vuestra red antes de ejecutar.
