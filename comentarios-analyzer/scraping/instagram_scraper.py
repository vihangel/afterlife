from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver

from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict
import time
import csv
import re


def setup_driver() -> WebDriver:
    options = Options()
    options.add_argument("--user-data-dir=/tmp/selenium-chrome-profile")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def append_comments_to_csv(comments: List[Dict[str, str]], path: str = "data/instagram_comments_bs.csv") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(path).is_file()

    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "text", "reply_to"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(comments)
    print(f"📥 Comentários adicionados ao arquivo ({len(comments)} novos)")


def scroll_and_extract(driver: WebDriver, max_rounds: int = 1000, pause_time: float = 2.5) -> List[Dict[str, str]]:
    print("🔄 Iniciando scroll + extração incremental...")

    comments_data: List[Dict[str, str]] = []
    batch_to_save: List[Dict[str, str]] = []
    seen = set()
    last_total_blocks = 0
    last_username = None

    try:
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "x5yr21d"))
        )
    except:
        print("❌ Container de comentários não encontrado")
        return []

    for round_number in range(max_rounds):
        print(f"\\n🔁 Rodada {round_number + 1} de extração")

        try:
            while True:
                more_button = driver.find_element(By.XPATH, "//span[text()='Ver mais comentários']")
                driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                more_button.click()
                print("➕ Cliquei em 'Ver mais comentários'")
                time.sleep(1.5)
        except:
            pass

        try:
            reply_buttons = driver.find_elements(By.XPATH, "//span[contains(text(),'Ver todas as')]")
            print(f"🔘 {len(reply_buttons)} botões 'Ver todas as respostas' encontrados")
            for btn in reply_buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    btn.click()
                    time.sleep(1.2)
                except Exception as e:
                    print(f"⚠️ Falha ao clicar: {e}")
        except Exception as e:
            print(f"⚠️ Erro ao buscar botões: {e}")

        try:
            last_comment = driver.find_elements(By.CLASS_NAME, "x9f619")[-1]
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});", last_comment)
            print("🧭 Scroll até último comentário visível")
        except:
            print("⚠️ Não foi possível fazer scroll até o último comentário.")

        time.sleep(pause_time)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        all_blocks = soup.find_all("div", class_="x9f619")
        print(f"🔍 Total de blocos no DOM: {len(all_blocks)}")

        bloco_processado = 0
        for idx, block in enumerate(all_blocks[last_total_blocks:], start=last_total_blocks + 1):
            if block.has_attr("style") and "height: 16px" in block["style"]:
                continue
            if block.find("div", role="button"):
                continue

            username_tag = block.find("span", class_="_ap3a")
            if not username_tag:
                continue
            username = username_tag.get_text(strip=True)

            text_spans = block.find_all("span", class_=lambda c: c and (c.startswith("x193iq5w") or c.startswith("x1lliihq")))
            clean_spans = [
                span for span in text_spans
                if span.get_text(strip=True).lower() not in ("ver tradução", "responder")
                and not span.get_text(strip=True).strip().endswith("sem")
            ]

            comment_text = " ".join(span.get_text(" ", strip=True) for span in clean_spans).strip()
            comment_text = re.sub(rf"^{re.escape(username)}[\\s:–-]*", "", comment_text).strip()

            if not comment_text or comment_text == username:
                continue

            key = (username, comment_text)
            if key in seen:
                continue
            seen.add(key)

            comment = {
                "username": username,
                "text": comment_text,
                "reply_to": ""
            }

            comments_data.append(comment)
            batch_to_save.append(comment)
            last_username = username
            bloco_processado += 1
            print(f"✅ @{username}: {comment_text}")

        if batch_to_save:
            append_comments_to_csv(batch_to_save)
            batch_to_save.clear()

        if bloco_processado == 0:
            print("🚫 Nenhum novo comentário visível no scroll atual.")
            if last_username:
                print(f"🧾 Último usuário visível: @{last_username}")
            break

        last_total_blocks = len(all_blocks)

    print("✅ Extração e scroll finalizados.")
    return comments_data


def scrape_instagram_with_bs(url: str) -> List[Dict[str, str]]:
    csv_path = "data/instagram_comments_bs.csv"
    Path(csv_path).unlink(missing_ok=True)

    driver: WebDriver = setup_driver()
    driver.get(url)
    print("🧭 Aguardando carregamento inicial...")
    time.sleep(5)

    comments: List[Dict[str, str]] = scroll_and_extract(driver)
    driver.quit()
    return comments


if __name__ == "__main__":
    url = input("📎 Cole aqui a URL do post do Instagram: ").strip()
    scrape_instagram_with_bs(url)
