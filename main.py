import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pymysql
import config

def safe_parse_array(array_str):
    # Only allow [[n,n,n],...] where n is 0-15
    pattern = r"\[\s*(\[\s*\d{1,2}\s*,\s*\d{1,2}\s*,\s*\d{1,2}\s*\]\s*,?\s*)+\]"
    if not re.fullmatch(pattern, array_str.replace('\n', '').replace(' ', '')):
        print("Array format not allowed!")
        return None
    # Extract all triplets
    triplets = re.findall(r"\[\s*(\d{1,2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\]", array_str)
    return [[int(a), int(b), int(c)] for a, b, c in triplets]

def fetch_target_iv(url):
    options = Options()
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    try:
        wait = WebDriverWait(driver, 15)
        button = wait.until(EC.presence_of_element_located((By.ID, "tIVsButton")))
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        div = wait.until(EC.visibility_of_element_located((By.ID, "tIVsCollapsible")))
        time.sleep(1)
        array_str = div.text.strip()
        print(f"DEBUG: div.text = {array_str!r}")
        driver.quit()
        if not array_str:
            print("Div is empty after clicking the button.")
            return None
        return safe_parse_array(array_str)
    except Exception as e:
        print("Failed to fetch or parse:", e)
        driver.quit()
        return None

def main():
    urls = [
        "https://pvpivs.com/searchStr.html?mon=Jangmo_O&cp=All&r=1-1-1-1_1-1-1-1_1-1-1-1_f_f&slMax=35",  # base
        "https://pvpivs.com/searchStr.html?mon=Jangmo_O&cp=All&r=1-1-1-1_1-1-1-1_1-1-1-1_f_f&m=50&slMax=35"  # best buddy
    ]
    sets = []
    name = "Unknown"

    for url in urls:
        parsed_data = fetch_target_iv(url)
        if not parsed_data:
            print(f"No data to store for {url}")
            sets.append(set())
            continue

        # Extract name from URL (mon=...)
        match = re.search(r"mon=([A-Za-z0-9_]+)", url)
        name = match.group(1) if match else "Unknown"

        sets.append(set(tuple(iv) for iv in parsed_data))

    if not sets or not any(sets):
        print("No unique data to store.")
        return

    base_set = sets[0]
    buddy_set = sets[1]

    # IVs only in buddy_set need best buddy
    need_buddy = buddy_set - base_set
    # IVs in base_set (with or without buddy) do not need best buddy
    no_buddy = base_set

    connection = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    try:
        with connection.cursor() as cursor:
            # Insert IVs that do NOT need best buddy
            for iv in no_buddy:
                attack, defense, hp = iv
                sql = """
                INSERT IGNORE INTO pokemon (Name, Attack, Defense, Hp, NeedBestBuddy)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (name, attack, defense, hp, 0))
            # Insert IVs that DO need best buddy
            for iv in need_buddy:
                attack, defense, hp = iv
                sql = """
                INSERT IGNORE INTO pokemon (Name, Attack, Defense, Hp, NeedBestBuddy)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (name, attack, defense, hp, 1))
        connection.commit()
        print(f"Inserted {len(no_buddy)} rows with NeedBestBuddy=0 and {len(need_buddy)} rows with NeedBestBuddy=1 for {name}.")
    finally:
        connection.close()

if __name__ == "__main__":
    main()