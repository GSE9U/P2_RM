######################
#	servidorTrenContinuo.py  #
#	Prácticas RM - Versión que maneja múltiples trenes #
######################


import sys
import socket
import struct
import time
import statistics
import json

MAX_ETHERNET_DATA=1500
MIN_ETHERNET_DATA=46
ETH_HDR_SIZE=14+4+8+12 # Cabecera Ethernet + CRC + Preambulo + Interframe gap
IP_HDR_SIZE=20
UDP_HDR_SIZE=8
RTP_HDR_SIZE=12

MAX_WAIT_TIME=8
MAX_BUFFER=100000000

B_MASK=0xFFFFFFFF
DECENASMICROSECS=100000

def process_train(packet_list, ipListen, portListen, is_loopback, link_hdr_size, summary_target):
	"""Procesa un tren de paquetes y devuelve las métricas"""
	if len(packet_list) == 0:
		return None

	# Parseo de paquetes recibidos
	parsed=[]
	for raw, recv_time in packet_list:
		header=struct.unpack('!HHII',raw[0:12])
		seq_number=header[1]
		send_time_trunc=header[2]
		trainLength=header[3]
		reception_time_trunc=int(recv_time*DECENASMICROSECS)&B_MASK
		payload_len = max(0, len(raw) - RTP_HDR_SIZE)
		parsed.append({
			'seq': seq_number,
			'send_time_trunc': send_time_trunc,
			'recv_time': recv_time,
			'recv_time_trunc': reception_time_trunc,
			'train_len': trainLength,
			'payload_len': payload_len
		})

	# Ordenación por número de secuencia
	parsed.sort(key=lambda p: p['seq'])

	# Esperado (según SSRC: longitud del tren)
	expected = parsed[-1]['train_len']
	received = len(parsed)

	# Cálculo de retardos OWD con corrección de wrap de 32 bits
	owd_seconds=[]
	for p in parsed:
		delta_trunc = p['recv_time_trunc'] - p['send_time_trunc']
		if delta_trunc < 0:
			delta_trunc += (1<<32)
		owd_seconds.append(delta_trunc / DECENASMICROSECS)

	owd_min = min(owd_seconds)
	owd_max = max(owd_seconds)
	owd_mean = sum(owd_seconds)/len(owd_seconds)
	jitter = statistics.pstdev(owd_seconds) if len(owd_seconds) > 1 else 0.0

	# Cálculo de pérdidas (en base a expected)
	lost = max(0, expected - received)
	loss_pct = (lost/expected)*100.0 if expected > 0 else 0.0

	# Cálculo de anchos de banda
	# Tamaño efectivo por paquete para BW = link + IP + UDP + RTP + payload
	per_packet_bytes = [
		link_hdr_size + IP_HDR_SIZE + UDP_HDR_SIZE + RTP_HDR_SIZE + p['payload_len'] for p in parsed
	]
	per_packet_bits = [b*8 for b in per_packet_bytes]

	# Instantáneo: usar intervalos de llegada consecutivos
	inst_bw_bps=[]
	for i in range(1, len(parsed)):
		dt = parsed[i]['recv_time'] - parsed[i-1]['recv_time']
		if dt > 0:
			inst_bw_bps.append(per_packet_bits[i] / dt)
	# Métricas de BW
	if len(inst_bw_bps) > 0:
		bw_min = min(inst_bw_bps)
		bw_max = max(inst_bw_bps)
		bw_mean_inst = sum(inst_bw_bps) / len(inst_bw_bps)
	else:
		bw_min = bw_max = bw_mean_inst = 0.0

	# Media global: total bits / duración del tren recibido (primer a último)
	duration = parsed[-1]['recv_time'] - parsed[0]['recv_time']
	total_bits = sum(per_packet_bits)
	bw_mean_global = (total_bits / duration) if duration > 0 else 0.0

	# Impresión de métricas finales
	print('\n=== Instantáneos ===')
	for idx, p in enumerate(parsed):
		print(f'Paquete seq={p["seq"]} OWD={owd_seconds[idx]:.6f}s')
	for i in range(1, len(parsed)):
		dt = parsed[i]['recv_time'] - parsed[i-1]['recv_time']
		if dt > 0:
			bw_i = per_packet_bits[i] / dt
			print(f'Intervalo {parsed[i-1]["seq"]}->{parsed[i]["seq"]} Δt={dt:.6f}s BW={int(bw_i)} bit/s')

	print('=== Resultados ===')
	print(f'Escucha: {ipListen}:{portListen}  loopback={is_loopback}')
	print(f'Paquetes esperados: {expected}  recibidos: {received}  perdidos: {lost}  pérdida: {loss_pct:.2f}%')
	print(f'OWD (s): min={owd_min:.6f}  max={owd_max:.6f}  media={owd_mean:.6f}  jitter(pstdev)={jitter:.6f}')
	print(f'BW instantáneo (bit/s): min={int(bw_min)}  max={int(bw_max)}  media={int(bw_mean_inst)}')
	print(f'BW medio global (bit/s): {int(bw_mean_global)}')

	# Envío opcional de resumen por UDP a quien lo solicite (para automatización remota)
	if summary_target is not None:
		try:
			summary = {
				'ipListen': ipListen,
				'portListen': portListen,
				'loopback': is_loopback,
				'expected': expected,
				'received': received,
				'lost': lost,
				'loss_pct': loss_pct,
				'owd_min_s': owd_min,
				'owd_max_s': owd_max,
				'owd_mean_s': owd_mean,
				'jitter_s': jitter,
				'bw_min_bps': bw_min,
				'bw_max_bps': bw_max,
				'bw_mean_inst_bps': bw_mean_inst,
				'bw_mean_global_bps': bw_mean_global,
			}
			payload = json.dumps(summary).encode('utf-8')
			sock_summary = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock_summary.sendto(payload, summary_target)
		except Exception as e:
			# Evitar romper salida normal si el envío del resumen falla
			pass

	return bw_mean_global

if __name__ == "__main__":
	if len(sys.argv) not in (3,5):
		print ('Error en los argumentos:\npython servidorTrenContinuo.py ip_escucha puerto_escucha [summary_ip summary_port]\n')
		exit(-1)

	ipListen=sys.argv[1]
	portListen=int(sys.argv[2])
	summary_target = None
	if len(sys.argv) == 5:
		summary_target = (sys.argv[3], int(sys.argv[4]))

	sock_listen = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
	sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,MAX_BUFFER)
	sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock_listen.bind((ipListen,portListen))
	sock_listen.settimeout(MAX_WAIT_TIME)

	# Detección de entorno: si el servidor escucha en loopback, no sumamos Ethernet
	resolved_listen_ip = socket.gethostbyname(ipListen)
	is_loopback = resolved_listen_ip == '127.0.0.1'
	link_hdr_size = 0 if is_loopback else ETH_HDR_SIZE

	print(f'Servidor iniciado en {ipListen}:{portListen} (loopback={is_loopback})')
	print('Esperando trenes de paquetes... (Ctrl+C para terminar)\n')

	train_count = 0
	
	# Bucle infinito para recibir múltiples trenes
	while True:
		try:
			packet_list = []
			
			# Recibimos los paquetes y salimos del bucle cuando no se reciban paquetes en MAX_WAIT_TIME segundos
			while True:
				try:
					data, addr = sock_listen.recvfrom(2048)
					# Para cada paquete recibido añadimos a la lista de paquetes
					# una tupla que contiene los datos del paquete y el tiempo en que 
					# se recibió dicho paquete
					packet_list.append((data,time.time()))

				except socket.timeout:
					break

			# Procesar el tren si se recibieron paquetes
			if len(packet_list) > 0:
				train_count += 1
				print(f'\n{"="*60}')
				print(f'TREN #{train_count} - Procesando {len(packet_list)} paquetes...')
				print(f'{"="*60}')
				process_train(packet_list, ipListen, portListen, is_loopback, link_hdr_size, summary_target)
				print(f'\nEsperando siguiente tren...\n')
			else:
				print('Timeout sin paquetes, esperando...')

		except KeyboardInterrupt:
			print(f'\n\nServidor detenido. Total de trenes procesados: {train_count}')
			break

