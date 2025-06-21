import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
    url = "https://pvpivs.com/searchStr.html?mon=Jangmo_O&cp=All&r=1-1-1-1_1-1-1-1_1-1-1-1_f_f&slMax=35"
    parsed_data = fetch_target_iv(url)
    print(parsed_data)

if __name__ == "__main__":
    main()