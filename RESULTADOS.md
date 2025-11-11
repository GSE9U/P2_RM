# RESULTADOS – Práctica RM_P2

Rellene este documento con sus medidas. Deje constancia de las versiones de Python y SO.

## Entorno
- SO / versión:
- Python:
- Interfaces usadas (loopback, Ethernet, Wi‑Fi):

## Parámetros utilizados
- Longitudes de tren probadas:
- Longitudes de datos probadas:
- Puertos usados:

## 3) Pruebas en localhost y LAN
### 3.1 Cabeceras empleadas
- Ethernet: 14 + 4 + 8 + 12 = 38 bytes (cabecera + FCS + preámbulo + IFG)
- IP: 20, UDP: 8, RTP: 12

### 3.2 Longitud mínima de trama y motivo
- Mínimo payload Ethernet 46 → datos ≥ 46 - 20 - 8 - 12 = 6 bytes (en red real). En el medio físico: 64 B por trama (14 + 46 + 4); considerando preámbulo (8) e IFG (12), 84 B a nivel de línea.
- En localhost no aplica Ethernet; no hay padding.

### 3.3 Longitud máxima de datos con sentido y motivo
- Evitar fragmentación: datos ≤ 1500 - 20 - 8 - 12 = 1460 bytes (asumiendo MTU 1500). Valores superiores causarían fragmentación IP y sesgarían las medidas.

### 3.4 Mejores combinaciones (según medidas)
- Para medir ancho de banda: tren largo (≥ 1000) y datos cercanos a 1400 B maximizan rendimiento por menor sobrecarga por paquete y mejor estabilización temporal.
- Para medir retardo/jitter: tren medio‑largo (200–1000) y datos moderados (200–600 B) con `clienteTren2.py` limitando la tasa por debajo del enlace para evitar colas.
- Justificación: tamaños grandes reducen overhead relativo y la varianza; limitar tasa elimina cuellos de botella y refleja condiciones de red sin congestión.

### Tabla automática de velocidad media
Ejecuta en localhost:
```bash
python3 auto_tabla.py --ip 127.0.0.1 --trenes 2,50,100,1000 --datos 60,200,600,1400
```
Esto generará `RESULTADOS_AUTO.md` con una tabla Markdown. Puedes cambiar `--cliente clienteTren2.py` para enviar con control de tasa si lo deseas.

## 5) Medidas con emulador
- Comando emulador usado:
- DNI: 55242328P
- Resultados deducidos:
  - Ancho de banda:
  - Retardo medio:
  - Jitter (pstdev):
  - Pérdidas (%):

## 6) Comparación con Wireshark
- Observaciones:
- Coincidencias / discrepancias con el servidor:

## 7) Diseño VoIP para el canal del emulador
- Códec elegido:
- Paquetización (ms):
- BW por llamada (incl. cabeceras):
- Nº máximo de llamadas (aprox.):
- Buffer de jitter recomendado:
- Justificación:

## 8) Simulación del servicio
- Parámetros de `clienteTren2.py` (tren, datos, tasa):
- Medidas obtenidas:
- ¿Concuerdan con lo predicho en 7?:

