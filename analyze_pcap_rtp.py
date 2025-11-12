#!/usr/bin/env python3
"""
analyze_pcap_rtp.py
-------------------
Analiza capturas PCAP/PCAPNG con tráfico UDP/RTP generado por clienteTren/servidorTren.
Requisitos: tener instalado 'tshark' (parte de Wireshark).
Uso:
    python3 analyze_pcap_rtp.py --pcap /ruta/a/archivo.pcapng --server-ip 10.250.6.24 --server-port 5003 --gap 1.0
Puedes pasar múltiples --pcap para procesar varias capturas.
Qué calcula por cada segmento (secuencia continua separada por 'gap' segundos):
- Paquetes recibidos
- % pérdidas (a partir de la secuencia RTP)
- OWD medio (s) y jitter (desv. típica)
- BW instantáneo min/med/max (bit/s) y BW medio global (bit/s)
La separación en segmentos permite tener una sola captura con varios experimentos; cualquier hueco > 'gap' s separa un experimento del siguiente.
"""
import argparse
import math
import shutil
import subprocess
import sys
from statistics import pstdev, mean

MOD32 = 2**32
DECENAS_MICROS = 100000  # 1e5
MOD16 = 2**16

def have_tshark():
    return shutil.which("tshark") is not None

def run_tshark(pcap, server_ip, server_port):
    # Fuerza decodificación RTP en ese puerto y extrae campos necesarios
    # Campos: tiempo_epoch, tamaño_frame, rtp.seq, rtp.timestamp
    cmd = [
        "tshark", "-r", pcap,
        "-d", f"udp.port=={server_port},rtp",
        "-Y", f"udp && ip.dst=={server_ip} && udp.dstport=={server_port}",
        "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "frame.len",
        "-e", "rtp.seq",
        "-e", "rtp.timestamp"
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("ERROR al invocar tshark:\n", e.output)
        sys.exit(2)
    rows = []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            # Puede que no haya RTP si tshark no lo detecta; intenta sin RTP para tamaño/tiempo
            continue
        try:
            t = float(parts[0])
            frame_len = int(parts[1])
            seq = int(parts[2])
            ts = int(parts[3])
            rows.append((t, frame_len, seq, ts))
        except ValueError:
            continue
    return rows

def split_segments(rows, gap):
    if not rows:
        return []
    rows.sort(key=lambda x: x[0])
    segs = []
    current = [rows[0]]
    for a, b in zip(rows, rows[1:]):
        if (b[0] - a[0]) > gap:
            segs.append(current)
            current = [b]
        else:
            current.append(b)
    if current:
        segs.append(current)
    return segs

def seq_distance(start, end):
    # número de valores desde start hasta end inclusivo en aritmética módulo 2^16
    # p.ej: start=65530, end=2 -> distancia 9 (65530..65535,0..2)
    if start is None or end is None:
        return 0
    return ((end - start) % MOD16) + 1

def compute_metrics(seg):
    # seg: lista de tuplas (time_epoch, frame_len, rtp_seq, rtp_ts)
    times = [t for t,_,_,_ in seg]
    sizes = [l for _,l,_,_ in seg]
    seqs  = [s for *_,s,_ in seg]
    rtpts = [ts for *_,ts in seg]

    # BW medio global
    duration = max(times) - min(times) if len(times) > 1 else 0.0
    total_bits = sum(sizes) * 8
    bw_global = (total_bits / duration) if duration > 0 else float('nan')

    # BW instantáneo para dt <= 1s (se filtra fuera por segmentación)
    inst = []
    for i in range(1, len(seg)):
        dt = times[i] - times[i-1]
        if dt > 0:
            bits = sizes[i] * 8
            inst.append(bits / dt)
    bw_inst_min = min(inst) if inst else float('nan')
    bw_inst_max = max(inst) if inst else float('nan')
    bw_inst_mean = mean(inst) if inst else float('nan')

    # Pérdidas a partir de RTP seq (únicos dentro del segmento)
    uniq = sorted(set(seqs), key=lambda x: (x - seqs[0]) % MOD16) if seqs else []
    received = len(uniq)
    expected = seq_distance(seqs[0], seqs[-1]) if seqs else 0
    loss_pct = ((expected - received) / expected * 100.0) if expected > 0 else float('nan')

    # OWD usando RTP timestamp frente a llegada truncada (mismo método que el servidor)
    owd = []
    for t, _, _, ts in seg:
        recv_trunc = (int(t * DECENAS_MICROS)) & (MOD32 - 1)
        # diferencia módulo 2^32 para gestionar wrap
        diff = (recv_trunc - ts) % MOD32
        # preferimos el representativo más pequeño (si es > 2^31, interpretamos como negativo y sumamos -2^32)
        if diff > (MOD32 // 2):
            diff = diff - MOD32
        owd.append(diff / DECENAS_MICROS)
    owd_mean = mean(owd) if owd else float('nan')
    owd_min = min(owd) if owd else float('nan')
    owd_max = max(owd) if owd else float('nan')
    owd_jitter = pstdev(owd) if len(owd) > 1 else float('nan')

    return {
        "pkts": len(seg),
        "duration_s": duration,
        "bw_global_bps": bw_global,
        "bw_inst_min_bps": bw_inst_min,
        "bw_inst_mean_bps": bw_inst_mean,
        "bw_inst_max_bps": bw_inst_max,
        "loss_pct": loss_pct,
        "owd_mean_s": owd_mean,
        "owd_min_s": owd_min,
        "owd_max_s": owd_max,
        "jitter_s": owd_jitter,
    }

def format_bps(x):
    if math.isnan(x):
        return "nan"
    return f"{x:.0f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcap", nargs="+", required=True, help="Rutas a .pcap/.pcapng")
    ap.add_argument("--server-ip", required=True, help="IP destino (servidor) en la captura")
    ap.add_argument("--server-port", type=int, required=True, help="Puerto UDP destino (servidor)")
    ap.add_argument("--gap", type=float, default=1.0, help="Umbral (s) para separar experimentos")
    args = ap.parse_args()

    if not have_tshark():
        print("ERROR: se requiere 'tshark' instalado (Wireshark).")
        sys.exit(1)

    for pcap in args.pcap:
        print(f"\n=== Archivo: {pcap} ===")
        rows = run_tshark(pcap, args.server_ip, args.server_port)
        if not rows:
            print("No se encontraron paquetes UDP->RTP hacia el servidor con esos filtros.")
            continue
        segs = split_segments(rows, args.gap)
        for idx, seg in enumerate(segs, 1):
            m = compute_metrics(seg)
            print(f"\n--- Segmento {idx} (pkts={m['pkts']}, dur={m['duration_s']:.3f}s) ---")
            print(f"Pérdidas estimadas (%): {m['loss_pct']:.2f}")
            print(f"OWD (s): media={m['owd_mean_s']:.6f}  min={m['owd_min_s']:.6f}  max={m['owd_max_s']:.6f}  jitter(pstdev)={m['jitter_s']:.6f}")
            print(f"BW inst (bit/s): min={format_bps(m['bw_inst_min_bps'])}  max={format_bps(m['bw_inst_max_bps'])}  media={format_bps(m['bw_inst_mean_bps'])}")
            print(f"BW global (bit/s): {format_bps(m['bw_global_bps'])}")

if __name__ == "__main__":
    main()
