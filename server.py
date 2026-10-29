
import queue
import random
import threading
import time
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

#HOST, PORT = "localhost", 8000
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

INDEX = Path(__file__).parent / "index.html"

clients = []              # una cola por cada navegador conectado
clients_lock = threading.Lock()


def generar_numeros():
    """Hilo que produce un número por segundo y lo reparte a todos los clientes."""
    while True:
        numero = random.randint(0, 100)
        print(f"Número: {numero}", flush=True)
        with clients_lock:
            for q in clients:
                q.put(numero)
        time.sleep(1)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            data = INDEX.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q = queue.Queue()
            with clients_lock:
                clients.append(q)
            try:
                while True:
                    numero = q.get()
                    self.wfile.write(f"data: {numero}\n\n".encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    clients.remove(q)
        else:
            self.send_error(404)

    def log_message(self, *args):  # silencia el log HTTP para que solo veas los números
        pass


if __name__ == "__main__":
    threading.Thread(target=generar_numeros, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    #print(f"Servidor listo en http://{HOST}:{PORT}  (Ctrl+C para salir)")
    print(f"Servidor listo en el puerto {PORT}  (Ctrl+C para salir)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
