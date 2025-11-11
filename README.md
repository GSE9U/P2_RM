# Práctica 2 – Redes y Medidas de Tráfico (RM_P2)

Este proyecto implementa un sistema cliente-servidor UDP con una cabecera RTP simplificada para medir retardo en un sentido (OWD), jitter, ancho de banda y pérdidas de paquetes. Es multiplataforma y no depende de librerías externas.

## Requisitos
- Python 3.8+
- Bibliotecas estándar: `socket`, `struct`, `time`, `statistics`, `sys`

## Archivos
- `clienteTren.py`: Cliente base que envía un tren de paquetes RTP simplificados.
- `clienteTren2.py`: Cliente con control de tasa binaria opcional.
- `servidorTren.py`: Servidor que recibe paquetes y calcula métricas.
- `instructions.md`: Guía y tareas de la práctica.

## Uso

### Servidor
```bash
python3 servidorTren.py 127.0.0.1 5000
```
Notas:
- Si el servidor escucha en `127.0.0.1` (loopback), no se suma la cabecera Ethernet al cálculo del ancho de banda.
- En redes reales (no loopback) se incluye la sobrecarga de `ETH_HDR_SIZE = 14+4+8+12` bytes (cabecera Ethernet + CRC + preámbulo + IFG).

### Cliente base
```bash
python3 clienteTren.py ip_destino puerto_destino longitud_tren longitud_datos
```
- Resuelve `ip_destino` con `socket.gethostbyname()`.
- En localhost no aplica restricciones de Ethernet (solo que la longitud no sea negativa).
- En red real se comprueba que `IP+UDP+RTP+datos` está en el rango `[46, 1500]` bytes (payload Ethernet).

Ejemplo (localhost):
```bash
python3 clienteTren.py 127.0.0.1 5000 100 200
```

### Cliente con tasa binaria
```bash
python3 clienteTren2.py ip_destino puerto_destino longitud_tren longitud_datos [tasa_bit_s]
```
- Si se especifica `tasa_bit_s` (bits/s), se calcula el intervalo entre paquetes como:
  - `t = L_bits / tasa_bit_s`, donde `L_bits = (ETH/IP/UDP/RTP + carga) * 8`
  - En localhost no se suma Ethernet; en red real sí.
- Incluye logs de depuración (DEBUG activado por defecto) indicando el ritmo logrado.

Ejemplo con tasa (red real):
```bash
python3 clienteTren2.py 192.168.1.50 5000 200 300 1000000
```

## Métricas calculadas por el servidor
- OWD (s): mínimo, máximo, media.
- Jitter: `statistics.pstdev` del OWD.
- Pérdida de paquetes: basada en `trainLength` (SSRC) incluido en cada paquete.
- Ancho de banda:
  - Instantáneo (entre llegadas sucesivas): mínimo, máximo, media.
  - Media global: `bits_totales / (t_último - t_primero)`.
- Detección de entorno:
  - Loopback: no se suma Ethernet.
  - Red real: se suma `ETH_HDR_SIZE`.
 - Salida instantánea adicional:
   - Por paquete: `seq` y `OWD`.
   - Por intervalo: `Δt` y `BW` entre paquetes consecutivos.

## Origen del timestamp RTP simplificado
El timestamp que va en la cabecera RTP se calcula como:
- `int(time.time() * 100000) & 0xFFFFFFFF`
- Esto equivale a truncar a 32 bits el tiempo en decenas de microsegundos. En destino se trunca igual el tiempo de recepción para calcular OWD en la misma base, corrigiendo el posible wrap de 32 bits.

## Pruebas sugeridas
1. Localhost (127.0.0.1):
   - `python3 servidorTren.py 127.0.0.1 5000`
   - `python3 clienteTren.py 127.0.0.1 5000 100 200`
2. Red doméstica (Ethernet ↔ Wi‑Fi): ajustar `ip_destino`.
3. Con emulador: ejecutar con distintos retardos/pérdidas/MTU para observar efectos.

## Guía para completar los apartados 3–8

### 3) Pruebas en localhost y LAN
- Ejecuta varias combinaciones de `longitud_tren` y `longitud_datos` y registra resultados en `RESULTADOS.md`.
- 3.1 Cabeceras empleadas:
  - Ethernet: `14 (MACs y tipo) + 4 (FCS) + 8 (preámbulo) + 12 (IFG) = 38 bytes` de sobrecarga fuera del payload
  - IP: 20 bytes; UDP: 8 bytes; RTP: 12 bytes
- 3.2 Longitud mínima de trama enviada:
  - Payload Ethernet mínimo 46 bytes. Por tanto, en red real: `IP+UDP+RTP+datos ≥ 46` → `datos ≥ 46 - 20 - 8 - 12 = 6 bytes`.
- 3.3 Longitud máxima de datos con sentido:
  - Para evitar fragmentación: `IP+UDP+RTP+datos ≤ 1500` → `datos ≤ 1500 - 20 - 8 - 12 = 1460 bytes`.
- 3.4 Mejores resultados:
  - Usa tren suficientemente largo para estabilidad (p.ej., 200–1000 paquetes) y datos dentro de 200–800 bytes para observar retardo/jitter sin estar cerca de MTU. Ajusta según tus medidas.

### 5) Uso del emulador
- Sintaxis: `emulador.exe ip_escucha puerto_escucha ip_destino puerto_destino DNI`
- Flujo típico (Windows):
  1. Servidor: `python3 servidorTren.py 0.0.0.0 5001`
  2. Emulador: `emulador\emulador.exe 127.0.0.1 5000 127.0.0.1 5001 12345678`
  3. Cliente hacia el emulador: `python3 clienteTren2.py 127.0.0.1 5000 500 300 800000`
- Deduce BW, retardo, jitter y pérdidas a partir de las métricas del servidor (media global ~ BW del canal; OWD medio ~ retardo; pstdev ~ jitter; % pérdidas directo).

### 6) Captura y análisis con Wireshark
- Filtro: `udp.port == 5000 or udp.port == 5001`
- Compara BW medido (sumando cabeceras en red real), OWD/Jitter (desde timestamps) y pérdidas con los cálculos del servidor.

### 7) VoIP sobre el canal del emulador
- Con la tabla de Cisco, selecciona códec según BW disponible (p.ej., G.711, G.729, Opus) y fija tiempos de paquetización (10/20/30 ms) para latencia/jitter.
- Llamadas simultáneas ≈ `BW_disponible / BW_por_llamada` (full‑duplex).
- Buffer de jitter ≈ `k * jitter` (p.ej., 1.5–2× desviación estándar) equilibrando latencia y pérdidas.

### 8) Simulación del servicio
- Genera trenes con `clienteTren2.py` imitando carga de VoIP: `longitud_datos` coherente con códec y paquetización, `tasa_binaria` ≈ tasa por llamada × nº de llamadas.
- Valida si los resultados (BW, OWD, jitter, pérdidas) concuerdan con la predicción del apartado 7.

## Referencias
- Tabla Cisco de consumo de ancho de banda VoIP: https://www.cisco.com/c/en/us/support/docs/voice/voice-quality/7934-bwidth-consume.html


