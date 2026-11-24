
import socket
import json
import time
import os

from datetime import datetime, timezone

HOST = "192.168.10.254"
PORT = 2528
BISTOS_IP = "192.168.10.4"

CAPTURE_SECONDS = 60

os.umask(0o077)

folder = datetime.now().strftime("capture_%Y%m%d_%H%M%S")
os.makedirs(folder, exist_ok=True)

binary_path = os.path.join(folder, "cms_raw.bin")
json_path = os.path.join(folder, "cms_raw.txt")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Listening: {HOST}:{PORT}", flush=True)

    while True:
        conn, addr = server.accept()

        if addr[0] == BISTOS_IP:
            break

        conn.close()

    print(f"BISTOS connected: {addr}", flush=True)

    start_time = time.monotonic()
    packet_count = 0
    total_bytes = 0

    conn.settimeout(1)

    with conn, \
         open(binary_path, "wb") as binary_file, \
         open(json_path, "w") as json_file:

        try:
            while time.monotonic() - start_time < CAPTURE_SECONDS:

                try:
                    data = conn.recv(65535)
                except socket.timeout:
                    continue

                if not data:
                    print("Connection closed.")
                    break

                timestamp = datetime.now(
                    timezone.utc
                ).isoformat()

                packet_count += 1

                record = {
                    "timestamp": timestamp,
                    "chunk_index": packet_count,
                    "byte_offset": total_bytes,
                    "length": len(data),
                    "hex": data.hex()
                }

                binary_file.write(data)

                json_file.write(
                    json.dumps(record) + "\n"
                )

                binary_file.flush()
                json_file.flush()

                total_bytes += len(data)

                print(
                    f"Chunk: {packet_count} | "
                    f"Bytes: {len(data)} | "
                    f"Total: {total_bytes}",
                    flush=True
                )

        except KeyboardInterrupt:
            print("Capture stopped.")

print("\nCapture completed.")
print(f"Total chunks: {packet_count}")
print(f"Total bytes: {total_bytes}")
print(f"Folder: {folder}")