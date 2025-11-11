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
- Mínimo payload Ethernet 46 → datos ≥ 46 - 20 - 8 - 12 = 6 bytes (en red real).
- En localhost no aplica Ethernet.

### 3.3 Longitud máxima de datos con sentido y motivo
- Evitar fragmentación: datos ≤ 1500 - 20 - 8 - 12 = 1460 bytes.

### 3.4 Mejores combinaciones (según medidas)
- Mejor tren:
- Mejor longitud de datos:
- Justificación:

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

