"""Gera o arquivo HTML unico (offline) do Codigo de Eventos.

O arquivo resultante tem a mesma interface do site, com as bases, os icones e o logo
embutidos. Abre direto no navegador do computador ou do celular, sem internet e sem instalar nada.

Uso:
    python gerar_offline.py                       # cria Codigo_de_Eventos_offline.html
    python gerar_offline.py --saida pasta/app.html
"""
import argparse
import base64
import json
import mimetypes
from datetime import date
from pathlib import Path

import web_app


def data_uri(path):
    tipo = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{tipo};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def montar_dados():
    app = web_app.app_info()
    app["versao"] = f'{app["versao"]} · arquivo offline gerado em {date.today():%d/%m/%Y}'
    sistemas, eventos = [], {}
    for sistema in web_app.list_systems():
        icone = next(p for p in web_app.ICONES_DIR.iterdir() if p.stem == sistema["name"])
        sistemas.append({**sistema, "icon": data_uri(icone)})
        linhas = web_app.read_event_rows(sistema["filename"])
        eventos[sistema["name"]] = {
            "system": sistema["name"],
            "kind": web_app.system_kind(linhas),
            "events": [{k: l[k] for k in ("codigo", "visivel", "tipo", "componente", "descricao")} for l in linhas],
        }
    return {"systems": sistemas, "app": app}, eventos


def gerar(saida):
    html = web_app.INDEX_FILE.read_text(encoding="utf-8")
    logo = data_uri(web_app.ICONES2_DIR / "logo_trensrj.png")
    html = html.replace('src="/static/icones2/logo_trensrj.png"', f'src="{logo}"')
    lista, eventos = montar_dados()
    dados = json.dumps({"lista": lista, "eventos": eventos}, ensure_ascii=False).replace("</", "<\\/")
    gancho = (
        "<script>\n"
        f"  const __DADOS = {dados};\n"
        "  window.__localApi = function (url) {\n"
        "    if (url === '/api/systems') return __DADOS.lista;\n"
        "    const m = url.match(/^\\/api\\/events\\?system=(.*)$/);\n"
        "    if (m) { const d = __DADOS.eventos[decodeURIComponent(m[1])]; if (d) return d; }\n"
        "    return null;\n"
        "  };\n"
        "</script>\n"
    )
    marca = "  <script>\n    /* ícone padrão"
    assert marca in html, "Trecho esperado do index.html nao encontrado."
    html = html.replace(marca, gancho + marca, 1)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(html, encoding="utf-8")
    total = sum(len(v["events"]) for v in eventos.values())
    print(f"{saida} ({saida.stat().st_size / 1024:.0f} KB): {len(eventos)} sistemas, {total} codigos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera o HTML offline do Codigo de Eventos.")
    parser.add_argument("--saida", default="Codigo_de_Eventos_offline.html", type=Path)
    gerar(parser.parse_args().saida)
