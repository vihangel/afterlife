# from seleniumwire import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from seleniumwire.webdriver import Chrome
# from seleniumwire.request import Request
# from webdriver_manager.chrome import ChromeDriverManager


# from seleniumwire.request import Request

# from urllib.parse import urlparse, parse_qs, unquote
# import zstandard as zstd
# import json
# import pandas as pd
# import time
# from pathlib import Path
# from typing import List, Dict, Union
# import uuid


# def setup_driver() -> Chrome:
#     options: Options = Options()
#     options.add_argument("--user-data-dir=/tmp/selenium-chrome-profile")
#     options.add_argument("--profile-directory=Default")
#     return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# def decompress_response(body: bytes, encoding: str) -> str:
#     if "zstd" in encoding:
#         dctx: zstd.ZstdDecompressor = zstd.ZstdDecompressor()
#         return dctx.decompress(body).decode("utf-8")
#     elif "gzip" in encoding:
#         import gzip
#         import io
#         gz: gzip.GzipFile = gzip.GzipFile(fileobj=io.BytesIO(body))
#         return gz.read().decode("utf-8")
#     else:
#         return body.decode("utf-8")


# def is_comment_request(request: Request) -> bool:
#     """Verifica se a requisição é relevante para coleta de comentários com base no conteúdo real do JSON."""
#     if "graphql/query" not in request.url or not request.response:
#         return False

#     try:
#         encoding: str = request.response.headers.get("Content-Encoding", "")
#         body_text: str = decompress_response(request.response.body, encoding)
#         data = json.loads(body_text)

#         if contains_username_and_text(data):
#             print("🔍 JSON contém pelo menos um objeto com 'username' e 'text'")
#             return True

#         # fallback opcional (menos importante agora)
#         query: Dict[str, List[str]] = parse_qs(urlparse(request.url).query)
#         raw_variables: str = query.get("variables", ["{}"])[0]
#         variables: Dict[str, Union[str, int, dict]] = json.loads(unquote(raw_variables))
#         if "shortcode" in variables:
#             print("🔍 Requisição com shortcode detectada")
#             return True

#     except Exception as e:
#         print(f"⚠️ Erro ao verificar comentário na request: {e}")

#     return False

# def contains_username_and_text(obj: Union[dict, list]) -> bool:
#             """Verifica se há ao menos um 'node' com 'user.username' e 'text' no JSON."""
#             def walk(o: Union[dict, list]) -> bool:
#                 if isinstance(o, dict):
#                     # Verifica se esse dict é um node com as chaves que queremos
#                     if (
#                         "user" in o and isinstance(o["user"], dict)
#                         and "username" in o["user"]
#                         and "text" in o
#                     ):
#                         print(f"✅ Comentário encontrado: @{o['user']['username']} — {o['text'][:30]}...")
#                         return True
#                     # Caso contrário, continua navegando
#                     return any(walk(v) for v in o.values())
#                 elif isinstance(o, list):
#                     return any(walk(item) for item in o)
#                 return False

#             return walk(obj)

# def extract_comments_from_body(body: str) -> List[Dict[str, Union[str, int]]]:
#     comments: List[Dict[str, Union[str, int]]] = []
#     try:
#         data = json.loads(body)

#         def walk(obj):
#             """Busca recursiva por nós que tenham 'username' e 'text'."""
#             if isinstance(obj, dict):
#                 if "user" in obj and "text" in obj:
#                     comments.append({
#                         "username": obj["user"]["username"],
#                         "text": obj["text"],
#                         "type": "comentário"  # você pode melhorar isso depois
#                     })
#                 for value in obj.values():
#                     walk(value)
#             elif isinstance(obj, list):
#                 for item in obj:
#                     walk(item)

#         walk(data)

#     except Exception as e:
#         print("⚠️ Erro ao extrair comentários:", e)

#     return comments


# def scroll_and_collect(driver: Chrome, max_scrolls: int = 10) -> List[Dict[str, Union[str, int]]]:
#     all_comments: List[Dict[str, Union[str, int]]] = []
#     last_height: int = driver.execute_script("return document.body.scrollHeight")
#     scroll_attempts: int = 0
#     processed_urls: set[str] = set()

#     while scroll_attempts < max_scrolls:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(3)
#         new_height: int = driver.execute_script("return document.body.scrollHeight")

#         for request in driver.requests:
#             if "graphql/query" in request.url and request.response:
#                 # ⚠️ NÃO pule se já processou a URL — pode mudar o conteúdo mesmo sendo a mesma
#                 print("🎯 Nova query interceptada!")

#                 if is_comment_request(request):
#                     encoding: str = request.response.headers.get("Content-Encoding", "")
#                     print(f"📦 Codificação: {encoding}")

#                     try:
#                         body: str = decompress_response(request.response.body, encoding)

#                         # Dump para debug
#                         json_dump_path: Path = Path("data/debug/jsons")
#                         json_dump_path.mkdir(parents=True, exist_ok=True)
#                         file_path: Path = json_dump_path / f"{uuid.uuid4()}.json"
#                         with file_path.open("w", encoding="utf-8") as f:
#                             f.write(body)
#                         print(f"📂 JSON salvo para análise: {file_path}")

#                         new_comments = extract_comments_from_body(body)
#                         if new_comments:
#                             print(f"✅ Extraídos {len(new_comments)} novos comentários/respostas")
#                             all_comments.extend(new_comments)
#                         else:
#                             print("⚠️ Nenhum comentário extraído do JSON.")

#                     except Exception as e:
#                         print("⚠️ Erro ao processar resposta:", e)

#         # 🧼 Limpa somente após processar todas as requisições desse scroll
#         driver.requests.clear()

#         if new_height == last_height:
#             scroll_attempts += 1
#         else:
#             scroll_attempts = 0
#             last_height = new_height

#     return all_comments

# def save_comments(comments: List[Dict[str, Union[str, int]]], path: str = "data/raw/instagram_comments_json.csv") -> None:
#     df: pd.DataFrame = pd.DataFrame(comments)
#     Path(path).parent.mkdir(parents=True, exist_ok=True)
#     df.to_csv(path, index=False)
#     print(f"💾 Comentários salvos em {path}")


# def scrape_instagram_comments(url: str) -> None:
#     driver: Chrome = setup_driver()
#     driver.get(url)
#     print("🧭 Aguardando carregamento da página...")
#     time.sleep(5)

#     print("🔄 Scrollando e monitorando JSONs de comentários...")
#     comments: List[Dict[str, Union[str, int]]] = scroll_and_collect(driver)

#     print(f"✅ {len(comments)} comentários/respostas coletados via JSON!")
#     save_comments(comments)
#     driver.quit()
