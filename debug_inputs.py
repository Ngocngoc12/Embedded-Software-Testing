from selenium import webdriver
from selenium.webdriver.common.by import By
import time

opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=opts)

pages = [
    ("TRANG CHU /ha-noi", "https://shopeefood.vn/ha-noi"),
    ("DANH SACH QUAN", "https://shopeefood.vn/ha-noi/danh-sach-quan"),
    ("DANH SACH QUAN + keyword", "https://shopeefood.vn/ha-noi/danh-sach-quan?keyword=pho"),
]

for label, url in pages:
    driver.get(url)
    time.sleep(6)
    print("\n=== " + label + " ===")
    print("URL thuc te:", driver.current_url)
    inputs = driver.find_elements(By.TAG_NAME, "input")
    found = False
    for i in inputs:
        if i.is_displayed():
            cls = i.get_attribute("class") or ""
            ph  = i.get_attribute("placeholder") or ""
            tp  = i.get_attribute("type") or ""
            print("  INPUT class=" + repr(cls) + " placeholder=" + repr(ph) + " type=" + repr(tp))
            found = True
    if not found:
        print("  (Khong co input hien thi)")

    # In tat ca button
    btns = driver.find_elements(By.TAG_NAME, "button")
    for b in btns:
        if b.is_displayed():
            cls = b.get_attribute("class") or ""
            txt = b.text.strip()[:40]
            print("  BTN class=" + repr(cls) + " text=" + repr(txt))

driver.quit()
print("\nDONE")
