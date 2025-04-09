import time
import csv
import json
from pathlib import Path
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

selectors = {
    "post_elements": "div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x1ntc13c.x9i3mqj.x11i5rnm.x2pgyrj > a",
    "comment_container": "div.x6s0dn4.x78zum5.xdt5ytf.xdj266r.xkrivgy.xat24cr.x1gryazu.x1n2onr6.xh8yej3 > div > div.x4h1yfo > div > div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6",
    "comment_elements": "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1cy8zhl.x1oa3qoh.x1nhvcw1 > span",
    "username_elements": "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x1ji0vk5.x18bv5gf.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj > span > span > div > a > div > div > span._ap3a._aaco._aacw._aacx._aad7._aade",
    "datetime_elements": "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x1ji0vk5.x18bv5gf.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x1roi4f4.x10wh9bi.x1wdrske.x8viiok.x18hxmgj > a > time",
    "view_replies_button": "//span[contains(text(), 'Ver todas as')]",
    "number_of_likes": "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1xmf6yo.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1 span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft",
    "number_of_comments": "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x1ji0vk5.x18bv5gf.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.x1fhwpqd.x1s688f.x1roi4f4.x1s3etm8.x676frb.x10wh9bi.x1wdrske.x8viiok.x18hxmgj",
}

CSV_PATH = "data/instagram_comments_bs.csv"

def setup_driver():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--headless=new")  
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-data-dir=/tmp/selenium-chrome-profile")
    options.add_argument("--profile-directory=Default")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def wait_spinner_disappear(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "[role='progressbar']"))
        )
    except:
        print("⏳ Aguardando carregamento...")

def save_comments(comments: List[Dict[str, str]]):
    Path(CSV_PATH).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(CSV_PATH).exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "text", "likes"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(comments)
    print(f"💾 Salvo: {len(comments)} comentários")

def click_all_view_replies(driver):
    while True:
        buttons = driver.find_elements(By.XPATH, selectors["view_replies_button"])
        if not buttons:
            break

        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
            except Exception:
                pass

def scroll_to_bottom(driver):
    container = driver.find_element(By.CSS_SELECTOR, selectors["comment_container"])
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
    print("🧭 Scrollando para o fim do container de comentários")
    time.sleep(0.5)
    wait_spinner_disappear(driver)

def extract_comments(driver) -> List[Dict[str, str]]:
    usernames = driver.find_elements(By.CSS_SELECTOR, selectors["username_elements"])
    text_comment = driver.find_elements(By.CSS_SELECTOR, selectors["comment_elements"])
    likes = driver.find_elements(By.CSS_SELECTOR, selectors["number_of_likes"])
    replys = driver.find_elements(By.CSS_SELECTOR, selectors["number_of_comments"])
    
    print(f"🔍 Extraindo {len(usernames)} comentários... ")
    data = []
    seen = set()
    for user_elem, comment_elem, likes_elem, reply_elem in zip(usernames, text_comment, likes, replys):
        username = user_elem.text.strip()
        comment = comment_elem.text.strip()
        like = likes_elem.text.strip() if likes_elem else "0"
        reply = reply_elem.text.strip() if reply_elem else "0"
   
        if username and comment and (username, comment) not in seen:
            like_count = ''.join(filter(str.isdigit, like))
            data.append({
                "username": username, 
                "text": comment,
                "likes": like_count,
            })
            seen.add((username, comment, like_count))
            print(f"✅ @{username}: {comment[:80]}")
    return data

def scrape_instagram_with_bs(url: str):
    Path(CSV_PATH).unlink(missing_ok=True)
    driver = setup_driver()
    driver.get(url)
    print("🧭 Carregando post...")
    time.sleep(5)

    try:
        all_comments = []
        previous_count = -1
        rounds = 0

        while True:
            rounds += 1
            print(f"\n🔁 RODADA {rounds}")
            click_all_view_replies(driver)
            scroll_to_bottom(driver)
            time.sleep(1)
            current_comments = extract_comments(driver)
            new_comments = [c for c in current_comments if c not in all_comments]

            if new_comments:
                save_comments(new_comments)
                all_comments.extend(new_comments)

            if len(all_comments) == previous_count:
                print("🛑 Nenhum novo comentário detectado. Encerrando.")
                break

            previous_count = len(all_comments)

    finally:
        driver.quit()

if __name__ == "__main__":
    url = input("📎 Cole aqui a URL do post do Instagram: ").strip()
    scrape_instagram_with_bs(url)
