import csv
import io
import json
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pandas as pd

import analisis_desercion


HOST = "127.0.0.1"
PORT = 8765
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_UPLOAD_ROWS = 100_000


class DashboardHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"error": "Ruta de API no encontrada."})

    def do_POST(self):
        if self.path != "/api/analyze":
            self.send_json(404, {"error": "Ruta de API no encontrada."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "El tamaño del archivo no es válido."})
            return

        if length <= 0:
            self.send_json(400, {"error": "Selecciona un archivo CSV para analizar."})
            return
        if length > MAX_UPLOAD_BYTES:
            self.send_json(413, {"error": "El archivo supera el límite de 25 MB."})
            return

        try:
            nombre_archivo, contenido = self.read_uploaded_file(length)
            if Path(nombre_archivo).suffix.lower() != ".csv":
                raise ValueError("El archivo debe tener extensión .csv.")
            if not contenido:
                raise ValueError("El archivo CSV está vacío.")

            try:
                texto = contenido.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = contenido.decode("cp1252")
            try:
                delimitador = csv.Sniffer().sniff(
                    texto[:4096], delimiters=",;\t"
                ).delimiter
            except csv.Error:
                delimitador = ","
            original = pd.read_csv(
                io.StringIO(texto),
                sep=delimitador,
                decimal="," if delimitador == ";" else ".",
            )
            if len(original) > MAX_UPLOAD_ROWS:
                raise ValueError("El archivo supera el límite de 100.000 filas.")

            dashboard = analisis_desercion.analizar_dataset(
                original,
                origen=nombre_archivo,
                salida_graficos=analisis_desercion.DASHBOARD_GRAFICOS,
                verboso=False,
            )
        except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
            self.send_json(
                400,
                {"error": f"No se pudo leer el CSV: {error}"},
            )
            return
        except ValueError as error:
            self.send_json(422, {"error": str(error)})
            return
        except IndexError as error:
            self.send_json(
                422,
                {"error": f"No fue posible formar los grupos de análisis: {error}"},
            )
            return
        except (OSError, KeyError, TypeError):
            self.log_error("Error preparando o guardando los resultados del CSV.")
            self.send_json(
                500,
                {"error": "No se pudieron guardar los resultados del análisis en el dashboard."},
            )
            return

        self.send_json(200, dashboard)

    def read_uploaded_file(self, length):
        content_type = self.headers.get("Content-Type", "")
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: "
            + content_type.encode("ascii", errors="ignore")
            + b"\r\nMIME-Version: 1.0\r\n\r\n"
            + self.rfile.read(length)
        )
        if not message.is_multipart():
            raise ValueError("Selecciona un archivo CSV con el botón de carga.")

        for part in message.iter_parts():
            filename = part.get_filename()
            if filename:
                contenido = part.get_payload(decode=True)
                return Path(filename.replace("\\", "/")).name, contenido or b""

        raise ValueError("No se encontró un archivo en la solicitud.")

    def log_error(self, message):
        self.log_message("%s", message)


def main():
    server = HTTPServer((HOST, PORT), DashboardHandler)
    print(f"API del dashboard disponible en http://{HOST}:{PORT}/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor del dashboard detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
