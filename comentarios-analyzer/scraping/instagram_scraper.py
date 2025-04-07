import re
import csv
import time
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Set, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


CSV_PATH = "data/instagram_comments_bs.csv"


def setup_driver() -> WebDriver:
    options = Options()
    options.add_argument("--user-data-dir=/tmp/selenium-chrome-profile")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def wait_for_spinner_to_disappear(driver: WebDriver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "[role='progressbar']"))
        )
    except:
        print("⏳ Timeout esperando carregamento (spinner ainda visível)")


def save_comments(comments: List[Dict[str, str]], path: str = CSV_PATH):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(path).is_file()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "text", "reply_to"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(comments)
    print(f"📥 Comentários adicionados ao arquivo ({len(comments)} novos)")


def extract_comment_data(block, seen: Set[Tuple[str, str]]) -> Dict[str, str] | None:
    if block.has_attr("style") and "height: 16px" in block["style"]:
        return None
    if block.find("div", role="button"):
        return None

    username_tag = block.find("span", class_="_ap3a")
    if not username_tag:
        return None
    username = username_tag.get_text(strip=True)

    text_spans = block.find_all("span", class_=lambda c: c and ("x193iq5w" in c or "x1lliihq" in c))
    clean_spans = [
        span for span in text_spans
        if span.get_text(strip=True).lower() not in ("ver tradução", "responder")
    ]
    comment_text = " ".join(span.get_text(" ", strip=True) for span in clean_spans).strip()

    # Remove @ duplicado no início
    comment_text = re.sub(rf"^@?{re.escape(username)}[\s:–-]*", "", comment_text).strip()

    if not comment_text:
        return None

    key = (username, comment_text)
    if key in seen:
        return None

    seen.add(key)
    return {
        "username": username,
        "text": comment_text,
        "reply_to": ""
    }


def expand_visible_replies(driver: WebDriver):
    reply_buttons = driver.find_elements(By.XPATH, "//span[contains(text(),'Ver todas as')]")
    for btn in reply_buttons:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            btn.click()
            wait_for_spinner_to_disappear(driver)
            time.sleep(0.5)
        except:
            continue


def click_load_more_buttons(driver: WebDriver) -> bool:
    clicked = False

    # "Ver mais comentários"
    try:
        more_btn = driver.find_element(By.XPATH, "//span[text()='Ver mais comentários']")
        driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
        more_btn.click()
        wait_for_spinner_to_disappear(driver)
        time.sleep(1)
        clicked = True
    except:
        pass

    # "Carregar mais comentários" (ícone com +)
    try:
        svg_btn = driver.find_element(By.XPATH, "//button[@aria-label='Carregar mais comentários']")
        driver.execute_script("arguments[0].scrollIntoView(true);", svg_btn)
        svg_btn.click()
        wait_for_spinner_to_disappear(driver)
        time.sleep(1)
        clicked = True
    except:
        pass

    return clicked


def scroll_to_bottom(driver: WebDriver, container) -> bool:
    prev_height = driver.execute_script("return arguments[0].scrollHeight", container)
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
    time.sleep(2)
    wait_for_spinner_to_disappear(driver)
    curr_height = driver.execute_script("return arguments[0].scrollHeight", container)
    return curr_height != prev_height


def scroll_and_extract(driver: WebDriver) -> List[Dict[str, str]]:
    print("🔄 Iniciando extração de comentários...")

    seen = set()
    all_comments: List[Dict[str, str]] = []

    container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "x5yr21d"))
    )

    while True:
        expand_visible_replies(driver)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        blocks = soup.find_all("div", class_="x9f619")
        print(f"🔍 Blocos visíveis: {len(blocks)}")

        new_batch = []
        for block in blocks:
            comment = extract_comment_data(block, seen)
            if comment:
                print(f"✅ @{comment['username']}: {comment['text']}")
                new_batch.append(comment)

        if new_batch:
            save_comments(new_batch)
            all_comments.extend(new_batch)

        any_click = click_load_more_buttons(driver)
        scrolled = scroll_to_bottom(driver, container)

        if not any_click and not scrolled:
            print("🛑 Nenhum novo conteúdo após scroll e cliques. Finalizando...")
            break

    print("✅ Extração concluída.")
    return all_comments


def scrape_instagram_with_bs(url: str) -> List[Dict[str, str]]:
    Path(CSV_PATH).unlink(missing_ok=True)

    driver = setup_driver()
    driver.get(url)
    print("🧭 Aguardando carregamento inicial...")
    time.sleep(5)

    try:
        comments = scroll_and_extract(driver)
    finally:
        driver.quit()

    return comments


if __name__ == "__main__":
    url = input("📎 Cole aqui a URL do post do Instagram: ").strip()
    scrape_instagram_with_bs(url)
