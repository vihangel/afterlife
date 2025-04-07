from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver
import time
import csv
from pathlib import Path
from typing import List, Dict


def setup_driver() -> WebDriver:
    options = Options()
    options.add_argument("--user-data-dir=/tmp/selenium-chrome-profile")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def scroll_and_expand(driver: WebDriver, max_rounds: int = 10) -> None:
    print("🔄 Iniciando scroll e expansão de comentários...")
    try:
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "x5yr21d"))
        )
    except:
        print("❌ Container de comentários não encontrado")
        return

    rounds = 0
    while rounds < max_rounds:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", container)
        time.sleep(2)

        # Tentar clicar nos botões "Ver todas as respostas"
        try:
            reply_buttons = driver.find_elements(By.XPATH, "//span[contains(text(),'Ver todas as')]")
            print(f"🔘 Encontrados {len(reply_buttons)} botões para expandir respostas")
            for btn in reply_buttons:
                try:
                    btn.click()
                    time.sleep(1.5)
                except:
                    continue
        except:
            pass

        rounds += 1
        
def extract_comments_with_bs(html: str) -> List[Dict[str, str]]:
    from bs4 import BeautifulSoup
    import re
    soup = BeautifulSoup(html, 'html.parser')
    comments_data: List[Dict[str, str]] = []
    seen = set()

    all_blocks = soup.find_all("div", class_="x9f619")
    print(f"🔎 Total bruto de blocos: {len(all_blocks)}")

    for block in all_blocks:
        if block.has_attr("style") and "height: 16px" in block["style"]:
            continue
        if block.find("div", role="button"):
            continue

        username_tag = block.find("span", class_="_ap3a")
        if not username_tag:
            continue
        username = username_tag.get_text(strip=True)

        text_spans = block.find_all("span", class_=lambda c: c and (c.startswith("x193iq5w") or c.startswith("x1lliihq")))

        # Limpar spans inúteis
        clean_spans = [
            span for span in text_spans
            if span.get_text(strip=True).lower() not in ("ver tradução", "responder")
            and not span.get_text(strip=True).strip().endswith("sem")
        ]

        comment_text = " ".join(
            span.get_text(" ", strip=True) for span in clean_spans
        ).strip()

        # Remover username duplicado do começo
        comment_text = re.sub(rf"^{re.escape(username)}[\s:–-]*", "", comment_text).strip()

        # Ignorar se não tem texto útil (ou é só o nome)
        if not comment_text or comment_text == username:
            continue

        key = (username, comment_text)
        if key in seen:
            continue
        seen.add(key)

        comments_data.append({
            "username": username,
            "text": comment_text,
            "reply_to": ""
        })
        print(f"✅ @{username}: {comment_text}")

    return comments_data


def save_comments_to_csv(comments: List[Dict[str, str]], path: str = "data/instagram_comments_bs.csv") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "text", "reply_to"])
        writer.writeheader()
        writer.writerows(comments)
    print(f"💾 Comentários salvos em {path}")
    print(f"📊 Total de comentários salvos: {len(comments)}")


def scrape_instagram_with_bs(url: str) -> List[Dict[str, str]]:
    driver: WebDriver = setup_driver()
    driver.get(url)
    print("🧭 Aguardando carregamento inicial...")
    time.sleep(5)

    scroll_and_expand(driver)

    html: str = driver.page_source
    driver.quit()

    comments: List[Dict[str, str]] = extract_comments_with_bs(html)
    save_comments_to_csv(comments)

    return comments


if __name__ == "__main__":
    url = input("📎 Cole aqui a URL do post do Instagram: ").strip()
    scrape_instagram_with_bs(url)
