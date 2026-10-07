import argparse
import json
import mimetypes
import os
import socket
import unicodedata
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from openpyxl import load_workbook


APP_DIR = Path(__file__).resolve().parent
ARQUIVOS_DIR = APP_DIR / "arquivos"
ICONES_DIR = APP_DIR / "icones"
ICONES2_DIR = APP_DIR / "icones2"
INDEX_FILE = APP_DIR / "index.html"

# Informacoes mostradas no rodape. Edite aqui quando revisar as bases.
APP_NOME = "Código de Eventos"
APP_VERSAO = "2.0"
DADOS_REVISADOS_EM = "outubro/2026"

CODE_KEY = "CODIGO"
DESCRIPTION_KEY = "DESCRICAO"
COMPONENT_KEY = "COMPONENTE"

# Sistemas cujos codigos numericos sao exibidos com zeros a esquerda (ex.: 300 -> 0300).
NUMERIC_PADDING = {"FREIO KNORR 3000 4000 E 5000.xlsm": 4}

SYSTEM_DISPLAY_ORDER = [
    "APU 2005 E 3000",
    "CVS 4000 E 5000",
    "EIMS 2005",
    "FREIO KNORR 3000 4000 E 5000",
    "VVVF 2005 E 3000",
    "INVERSOR DE TRACAO 4000 E 5000",
    "TMS 3000",
    "EVR 4000 E 5000",
    "PERFORMANCE 3000",
]
ICON_EXTENSIONS = (".svg", ".png")


def normalize_code(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def normalize_key(value):
    text = normalize_code(value).upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def compare_key(value):
    """Chave de comparacao: sem acentos/maiusculas e, se for numero, sem zeros a esquerda."""
    key = normalize_key(value)
    if key.isdigit():
        return key.lstrip("0") or "0"
    return key


def format_visible_code(code, filename):
    width = NUMERIC_PADDING.get(filename)
    if width and code.isdigit():
        return code.zfill(width)
    return code


def code_type(code):
    return "numerico" if code.isdigit() else "alfabetico"


def get_system_filename(system_name):
    filename = f"{system_name}.xlsm"
    path = ARQUIVOS_DIR / filename
    if not path.is_file():
        raise ValueError("Sistema nao encontrado.")
    return filename


@lru_cache(maxsize=64)
def read_event_rows(filename):
    workbook_path = ARQUIVOS_DIR / filename
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    sheet = workbook.active
    headers = [normalize_key(cell.value) for cell in sheet[1]]
    rows = []
    for values in sheet.iter_rows(min_row=2, values_only=True):
        item = dict(zip(headers, values))
        code = normalize_code(item.get(CODE_KEY))
        if not code:
            continue
        rows.append({
            "codigo": code,
            "visivel": format_visible_code(code, filename),
            "tipo": code_type(code),
            "descricao": normalize_code(item.get(DESCRIPTION_KEY)),
            "componente": normalize_code(item.get(COMPONENT_KEY)),
        })
    workbook.close()
    return rows


def find_event(rows, code):
    wanted = compare_key(code)
    for row in rows:
        if compare_key(row["codigo"]) == wanted:
            return row
    return None


def system_kind(rows):
    kinds = {row["tipo"] for row in rows}
    if kinds == {"numerico"}:
        return "numerico"
    if kinds == {"alfabetico"} or not kinds:
        return "alfabetico"
    return "misto"


def list_systems():
    order_map = {normalize_key(name): index for index, name in enumerate(SYSTEM_DISPLAY_ORDER)}
    icon_paths = sorted(
        (p for p in ICONES_DIR.iterdir() if p.suffix.lower() in ICON_EXTENSIONS),
        key=lambda path: (order_map.get(normalize_key(path.stem), len(order_map)), path.name.casefold()),
    )
    systems = []
    seen = set()
    for icon_path in icon_paths:
        name = icon_path.stem
        filename = f"{name}.xlsm"
        if name in seen or not (ARQUIVOS_DIR / filename).is_file():
            continue
        seen.add(name)
        systems.append({
            "name": name,
            "icon": "/static/icones/" + quote(icon_path.name),
            "filename": filename,
            "kind": system_kind(read_event_rows(filename)),
        })
    return systems


def app_info():
    return {"nome": APP_NOME, "versao": APP_VERSAO, "dados": DADOS_REVISADOS_EM}


def json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def safe_static_path(base_dir, relative_path):
    decoded = unquote(relative_path).replace("\\", "/").lstrip("/")
    path = (base_dir / decoded).resolve()
    base = base_dir.resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/":
                self.send_html(INDEX_FILE.read_text(encoding="utf-8"))
            elif path == "/api/systems":
                self.send_json({"systems": list_systems(), "app": app_info()})
            elif path == "/api/events":
                self.handle_events(query)
            elif path == "/api/codes":
                self.handle_codes(query)
            elif path == "/api/search":
                self.handle_search(query)
            elif path.startswith("/static/icones/"):
                self.send_static(ICONES_DIR, path.removeprefix("/static/icones/"))
            elif path.startswith("/static/icones2/"):
                self.send_static(ICONES2_DIR, path.removeprefix("/static/icones2/"))
            else:
                self.send_error_json(HTTPStatus.NOT_FOUND, "Rota nao encontrada.")
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Erro interno: {exc}")

    def handle_events(self, query):
        system = query.get("system", [""])[0]
        if not system:
            raise ValueError("Informe o sistema.")
        rows = read_event_rows(get_system_filename(system))
        self.send_json({
            "system": system,
            "kind": system_kind(rows),
            "events": [
                {k: row[k] for k in ("codigo", "visivel", "tipo", "componente", "descricao")}
                for row in rows
            ],
        })

    # Rotas antigas, mantidas por compatibilidade.
    def handle_codes(self, query):
        system = query.get("system", [""])[0]
        if not system:
            raise ValueError("Informe o sistema.")
        rows = read_event_rows(get_system_filename(system))
        self.send_json({"system": system, "codes": [row["visivel"] for row in rows]})

    def handle_search(self, query):
        system = query.get("system", [""])[0]
        code = query.get("code", [""])[0]
        if not system:
            raise ValueError("Informe o sistema.")
        if not code:
            raise ValueError("Informe o codigo.")
        filename = get_system_filename(system)
        event = find_event(read_event_rows(filename), code)
        if event is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Codigo nao encontrado.")
            return
        self.send_json({
            "codigo": event["visivel"],
            "componente": event["componente"],
            "descricao": event["descricao"],
        })

    def send_html(self, html):
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload, status=HTTPStatus.OK):
        data = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, status, message):
        self.send_json({"error": message}, status)

    def send_static(self, base_dir, relative_path):
        path = safe_static_path(base_dir, relative_path)
        if path is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Arquivo nao encontrado.")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Codigo de Eventos para acesso web.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8000")), type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), WebAppHandler)
    lan_ip = get_lan_ip()
    print("Codigo de Eventos Web em execucao.")
    print(f"No computador: http://127.0.0.1:{args.port}")
    print(f"No celular:    http://{lan_ip}:{args.port}")
    print("Use Ctrl+C para parar.")
    server.serve_forever()


if __name__ == "__main__":
    main()
