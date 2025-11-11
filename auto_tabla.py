######################
#	auto_tabla.py    #
#	Prácticas RM     #
######################

import argparse
import os
import re
import subprocess
import sys
import time
from typing import List, Dict, Tuple

PYTHON = sys.executable

BW_GLOBAL_RE = re.compile(r'BW medio global \(bit/s\):\s+(\d+)', re.IGNORECASE)
JSON_SUMMARY_KEY = 'bw_mean_global_bps'


def find_free_port() -> int:
	import socket
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
		s.bind(('127.0.0.1', 0))
		return s.getsockname()[1]


def run_single_measure_local(server_ip: str, server_port: int, train_len: int, data_len: int, client: str) -> Tuple[int, str]:
	"""
	Lanza el servidor en local (loopback), ejecuta el cliente y devuelve
	(BW_medio_global_bit_s, salida_servidor_completa).
	"""
	is_loopback = server_ip == '127.0.0.1'
	server_proc = None
	server_out = ""

	try:
		if is_loopback:
			server_cmd = [PYTHON, 'servidorTren.py', server_ip, str(server_port)]
			server_proc = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
			# Dar tiempo a que el servidor empiece a escuchar
			time.sleep(0.3)

		client_cmd = [PYTHON, client, server_ip, str(server_port), str(train_len), str(data_len)]
		subprocess.run(client_cmd, check=True)

		if is_loopback and server_proc:
			try:
				server_out = server_proc.communicate(timeout=15)[0]
			except subprocess.TimeoutExpired:
				server_proc.kill()
				server_out = server_proc.communicate()[0]
		else:
			# En remoto, no tenemos salida del servidor
			server_out = ""

		# Parseo de BW medio global
		bw = 0
		if server_out:
			m = BW_GLOBAL_RE.search(server_out)
			if m:
				bw = int(m.group(1))
		return bw, server_out

	finally:
		if server_proc and server_proc.poll() is None:
			server_proc.kill()


def listen_summary(summary_ip: str, summary_port: int, timeout_s: float = 20.0) -> Tuple[int, str]:
	"""
	Escucha un datagrama UDP JSON de servidorTren.py con el resumen.
	Devuelve (bw_mean_global_bps, json_str) o (0, '') en caso de timeout.
	"""
	import socket, json
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		sock.bind((summary_ip, summary_port))
		sock.settimeout(timeout_s)
		data, _ = sock.recvfrom(65535)
		txt = data.decode('utf-8', errors='replace')
		try:
			obj = json.loads(txt)
			bw = int(obj.get(JSON_SUMMARY_KEY, 0))
		except Exception:
			bw = 0
		return bw, txt
	except socket.timeout:
		return 0, ''
	finally:
		sock.close()


def build_table(train_lengths: List[int], data_lengths: List[int], results: Dict[Tuple[int, int], int]) -> str:
	"""
	Construye una tabla Markdown con BW medio global (bit/s).
	"""
	header = "| Tamaño Tren/Tamaño Paquete | " + " | ".join(f"{d}B" for d in data_lengths) + " |\n"
	sep = "|" + "---|" * (len(data_lengths) + 1) + "\n"
	rows = []
	for t in train_lengths:
		cells = [str(t)]
		for d in data_lengths:
			val = results.get((t, d), 0)
			cells.append(str(val) if val else "-")
		rows.append("| " + " | ".join(cells) + " |")
	return header + sep + "\n".join(rows) + "\n"


def main():
	parser = argparse.ArgumentParser(description="Ejecuta medidas y genera tabla de BW medio global (bit/s).")
	parser.add_argument("--ip", default="127.0.0.1", help="IP del servidor (por defecto 127.0.0.1)")
	parser.add_argument("--port", type=int, default=0, help="Puerto del servidor (0=auto)")
	parser.add_argument("--trenes", default="2,50,100,1000", help="Lista de longitudes de tren separadas por comas")
	parser.add_argument("--datos", default="60,200,600,1400", help="Lista de longitudes de datos (bytes) separadas por comas")
	parser.add_argument("--cliente", default="clienteTren.py", help="Script de cliente a usar (clienteTren.py o clienteTren2.py)")
	parser.add_argument("--out", default="RESULTADOS_AUTO.md", help="Archivo de salida con la tabla")
	parser.add_argument("--summary-ip", default="", help="IP local donde escucharemos el resumen UDP del servidor (modo remoto)")
	parser.add_argument("--summary-port", type=int, default=55055, help="Puerto local para el resumen UDP")
	parser.add_argument("--pause-ms", type=int, default=300, help="Pausa entre combinaciones (ms)")
	args = parser.parse_args()

	server_ip = args.ip
	server_port = args.port if args.port != 0 else find_free_port()
	train_lengths = [int(x) for x in args.trenes.split(",") if x.strip()]
	data_lengths = [int(x) for x in args.datos.split(",") if x.strip()]
	client_script = args.cliente
	pause_s = max(0, args.pause_ms) / 1000.0

	results: Dict[Tuple[int, int], int] = {}

	is_loopback = server_ip == '127.0.0.1'
	if not is_loopback:
		if not args.summary_ip:
			print("Modo remoto: especifica --summary-ip con la IP del portátil para recibir el resumen UDP del servidor.")
			print("En el PC servidor ejecuta: python3 servidorTren.py 0.0.0.0 {port} {summary_ip} {summary_port}")
			return

	for t in train_lengths:
		for d in data_lengths:
			print(f"Midiendo tren={t}, datos={d}B en {server_ip}:{server_port} ...")
			if is_loopback:
				bw, srv_out = run_single_measure_local(server_ip, server_port, t, d, client_script)
			else:
				# Modo remoto: escuchar resumen del servidor por UDP
				# 1) Lanzar cliente
				client_cmd = [PYTHON, client_script, server_ip, str(server_port), str(t), str(d)]
				subprocess.run(client_cmd, check=True)
				# 2) Esperar resumen
				bw, srv_out = listen_summary(args.summary_ip, args.summary_port, timeout_s=20.0)
			if bw:
				print(f"  BW medio global: {bw} bit/s")
			else:
				print("  No se pudo extraer BW (revisa salida del servidor).")
			results[(t, d)] = bw
			if pause_s > 0:
				time.sleep(pause_s)

	table_md = build_table(train_lengths, data_lengths, results)
	with open(args.out, "w", encoding="utf-8") as f:
		f.write("# Tabla de velocidades (BW medio global)\n\n")
		f.write(table_md)
	print("\nTabla generada en:", args.out)
	print("\nResumen:\n")
	print(table_md)


if __name__ == "__main__":
	main()


