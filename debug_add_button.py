"""
debug_add_button.py
Soi DOM trang quan an de tim nut them mon (+)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=opts)
driver.set_page_load_timeout(60)

URL = "https://shopeefood.vn/ha-noi/pho-thin-bo-vien-lo-duc"
try:
    driver.get(URL)
except Exception:
    pass
time.sleep(8)

# Dong popup neu co
for sel in ["button.close", "button[class*='close']", "[class*='modal'] button"]:
    try:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for e in els:
            if e.is_displayed():
                e.click()
                time.sleep(1)
                break
    except Exception:
        pass

print("\n=== SCROLL Y=0: ALL VISIBLE BUTTONS ===")
btns = driver.find_elements(By.TAG_NAME, "button")
for b in btns:
    if b.is_displayed():
        cls = b.get_attribute("class") or ""
        txt = b.text.strip()[:30]
        aria = b.get_attribute("aria-label") or ""
        print(f"  BTN class={repr(cls[:60])} text={repr(txt)} aria={repr(aria)}")

# Scroll xuong va xem them
for scroll_y in [400, 800, 1200]:
    driver.execute_script(f"window.scrollTo(0, {scroll_y});")
    time.sleep(2)
    print(f"\n=== SCROLL Y={scroll_y}: ALL VISIBLE ELEMENTS WITH '+' ===")
    
    # Tim tat ca element co text '+'
    all_els = driver.find_elements(By.XPATH, "//*[normalize-space(text())='+']")
    for e in all_els:
        if e.is_displayed():
            tag = e.tag_name
            cls = e.get_attribute("class") or ""
            print(f"  TAG={tag} class={repr(cls[:60])}")

    # In tat ca button moi
    btns = driver.find_elements(By.TAG_NAME, "button")
    for b in btns:
        if b.is_displayed():
            cls = b.get_attribute("class") or ""
            txt = b.text.strip()[:30]
            if txt or "add" in cls.lower():
                print(f"  BTN class={repr(cls[:60])} text={repr(txt)}")

driver.quit()
print("\nDONE")
