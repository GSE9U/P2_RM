######################
#	clienteTren.py   #
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

if __name__ == "__main__":
	if len(sys.argv)!=5:
		print ('Error en los argumentos:\npython3 clienteTren.py ip_destino puerto_destino longitud_tren longitud_datos\n')
		exit(-1)

	# Resolución de IP destino (portabilidad: admite nombre o IP)
	dstIP=socket.gethostbyname(sys.argv[1])
	dstPort=int(sys.argv[2])
	addr=(dstIP,dstPort)
	trainLength=int(sys.argv[3])
	dataLength=int(sys.argv[4])

	# Detección de localhost: si es loopback no hay cabecera Ethernet
	is_loopback = dstIP == '127.0.0.1'
	link_hdr_size = 0 if is_loopback else ETH_HDR_SIZE

	# Comprobaciones de tamaño:
	# - En red real (no localhost), el payload Ethernet debe estar entre [MIN_ETHERNET_DATA, MAX_ETHERNET_DATA]
	#   considerando IP+UDP+RTP+datos, pues es lo que viaja dentro de la trama.
	# - En localhost, no aplican restricciones de Ethernet; solo aseguramos longitud no negativa.
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
	#generar un array de datos de longitud dataLength con el caracter 0 
	data=('0'*(dataLength)).encode()
	seq_number=0


	for i in range(0,trainLength):
		#usamos la longitud del tren como identificador de fuente. De esta manera en destino podemos saber la
		#longitud original del tren. En el campo timestamp (32bits) sólo podemos enviar segundos y 
		#centésimas de milisegundos (o decenas de microsegundos, según se quiera ver) truncados a 32bits.
		#El timestamp se obtiene de time.time() (segundos en coma flotante) multiplicado por DECENASMICROSECS
		#y enmascarado a 32 bits, emulando el campo timestamp de un encabezado RTP simplificado.
		message=struct.pack('!HHII',0x8014,seq_number, int(time.time()*DECENASMICROSECS)&B_MASK,trainLength)+data
		sock_send.sendto(message,addr)
		seq_number+=1

