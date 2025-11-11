######################
#	clienteTren2.py  #
#	Prácticas RM     #
######################

import sys
import socket
import struct
import time

MAX_ETHERNET_DATA=1500
MIN_ETHERNET_DATA=46
ETH_HDR_SIZE=14+4+8+12 # Cabecera Ethernet + CRC + Preámbulo + InterFrame gap
IP_HDR_SIZE=20
UDP_HDR_SIZE=8
RTP_HDR_SIZE=12

B_MASK=0xFFFFFFFF
DECENASMICROSECS=100000

# Activar/desactivar logs de depuración
DEBUG=True

if __name__ == "__main__":
	# Uso:
	#   python3 clienteTren2.py ip_destino puerto_destino longitud_tren longitud_datos [tasa_bit_s]
	if len(sys.argv) not in (5,6):
		print ('Error en los argumentos:\npython3 clienteTren2.py ip_destino puerto_destino longitud_tren longitud_datos [tasa_bit_s]\n')
		exit(-1)

	dstIP=socket.gethostbyname(sys.argv[1])
	dstPort=int(sys.argv[2])
	addr=(dstIP,dstPort)
	trainLength=int(sys.argv[3])
	dataLength=int(sys.argv[4])
	bitrate_bps=int(sys.argv[5]) if len(sys.argv)==6 else 0

	is_loopback = dstIP == '127.0.0.1'
	link_hdr_size = 0 if is_loopback else ETH_HDR_SIZE

	# Comprobaciones de tamaño (ver comentarios en clienteTren.py)
	ip_udp_rtp_and_payload = IP_HDR_SIZE + UDP_HDR_SIZE + RTP_HDR_SIZE + dataLength
	if not is_loopback:
		if ip_udp_rtp_and_payload > MAX_ETHERNET_DATA or ip_udp_rtp_and_payload < MIN_ETHERNET_DATA:
			print('Tamaño de datos incorrecto para red real (viola límites de trama Ethernet)')
			exit(0)
	else:
		if dataLength < 0:
			print('Tamaño de datos incorrecto (negativo)')
			exit(0)

	sock_send= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	data=('0'*(dataLength)).encode()
	seq_number=0

	# Tamaño total por paquete efectivo para control de tasa
	packet_bytes = link_hdr_size + IP_HDR_SIZE + UDP_HDR_SIZE + RTP_HDR_SIZE + dataLength
	packet_bits = packet_bytes * 8

	if DEBUG:
		print(f'Destino: {dstIP}:{dstPort}  loopback={is_loopback}')
		print(f'Longitud tren: {trainLength}  Datos: {dataLength} bytes')
		if bitrate_bps > 0:
			print(f'Tasa objetivo: {bitrate_bps} bit/s  Paquete: {packet_bytes} bytes ({packet_bits} bits)')

	for i in range(0,trainLength):
		# Timestamp RTP simplificado: segundos*1e5 (decenas de microsegundos) truncado a 32 bits
		message=struct.pack('!HHII',0x8014,seq_number, int(time.time()*DECENASMICROSECS)&B_MASK,trainLength)+data

		send_t0 = time.time()
		sock_send.sendto(message,addr)
		seq_number+=1
		send_t1 = time.time()

		# Control de tasa binaria si se especifica
		if bitrate_bps > 0:
			# Intervalo teórico entre paquetes
			interval_s = packet_bits / float(bitrate_bps)
			# Considerar el tiempo ya empleado en el envío
			elapsed = send_t1 - send_t0
			sleep_time = interval_s - elapsed
			if sleep_time > 0:
				time.sleep(sleep_time)
			if DEBUG:
				actual_elapsed = (time.time() - send_t0)
				# bps aproximada alcanzada en este intervalo
				actual_bps = packet_bits / actual_elapsed if actual_elapsed > 0 else 0
				print(f'[{i+1}/{trainLength}] Δt={actual_elapsed:.6f}s  tasa≈{int(actual_bps)} bit/s')


