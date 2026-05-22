# =============================================================================
#  TOOL: Inspect ShopeeFood DOM - Tìm selector cho Filter & Cart & Login
#  Chạy: python inspect_shopeefood.py
#  Kết quả: In ra các class/XPath thực tế đang dùng trên trang
# =============================================================================
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=options)
wait   = WebDriverWait(driver, 15)

DIVIDER = "\n" + "="*70

def dump_elements(label, elements):
    print(f"\n--- {label} ({len(elements)} found) ---")
    for i, el in enumerate(elements[:8]):
        try:
            tag  = el.tag_name
            cls  = el.get_attribute("class") or ""
            txt  = el.text.strip()[:60]
            href = el.get_attribute("href") or ""
            pid  = el.get_attribute("id") or ""
            dtype = el.get_attribute("data-type") or ""
            print(f"  [{i}] <{tag}> id='{pid}' class='{cls[:80]}' text='{txt}' href='{href[:40]}' data-type='{dtype}'")
        except Exception as e:
            print(f"  [{i}] ERROR: {e}")

# ─── 1. TRANG TÌM KIẾM: Inspect filter buttons ─────────────────────────────
print(DIVIDER)
print("  BƯỚC 1: Mở trang tìm kiếm 'trà sữa'")
print(DIVIDER)

driver.get("https://shopeefood.vn/ha-noi/danh-sach-quan?keyword=tra+sua")
time.sleep(6)

# Đóng popup
for sel in ["//button[contains(@class,'close')]", "//*[@aria-label='Close']", "//span[@class='icon-close']"]:
    try:
        btns = driver.find_elements(By.XPATH, sel)
        for b in btns:
            if b.is_displayed(): b.click(); time.sleep(0.3)
    except: pass

print("\n>>> Tìm tất cả button trên trang tìm kiếm:")
dump_elements("ALL BUTTONS", driver.find_elements(By.TAG_NAME, "button"))

print("\n>>> Tìm tất cả div có class chứa 'filter' hoặc 'Filter':")
dump_elements("FILTER DIVS", driver.find_elements(By.XPATH,
    "//*[contains(@class,'filter') or contains(@class,'Filter')]"))

print("\n>>> Tìm các element có text liên quan đến lọc:")
for keyword in ["Khu vực", "Đánh giá", "Giá", "Sắp xếp", "Lọc", "Sort", "Filter", "Rating"]:
    els = driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{keyword}' or contains(text(),'{keyword}')]")
    visible = [e for e in els if e.is_displayed()]
    if visible:
        dump_elements(f"TEXT='{keyword}'", visible)

print("\n>>> HTML vùng filter (đầu trang kết quả):")
try:
    body = driver.find_element(By.CSS_SELECTOR, "#app")
    src  = body.get_attribute("innerHTML")[:8000]
    # Tìm vùng chứa filter
    import re
    filter_chunks = re.findall(r'<[^>]*(filter|Filter|sort|Sort|area|rating)[^>]*>.*?</[a-z]+>', src[:4000], re.DOTALL|re.IGNORECASE)
    for chunk in filter_chunks[:5]:
        print("  CHUNK:", chunk[:200])
except Exception as e:
    print("  Lỗi:", e)

# ─── 2. TRANG QUÁN ĂN: Inspect nút thêm vào giỏ ─────────────────────────────
print(DIVIDER)
print("  BƯỚC 2: Vào trang quán ăn - tìm nút thêm món")
print(DIVIDER)

driver.get("https://shopeefood.vn/ha-noi/danh-sach-quan?keyword=pho")
time.sleep(5)

# Click vào quán đầu tiên
try:
    links = driver.find_elements(By.XPATH, "//a[contains(@href,'/ha-noi/') and not(contains(@href,'danh-sach'))]")
    first_restaurant_links = [l for l in links if l.is_displayed() and l.get_attribute("href")]
    if first_restaurant_links:
        url = first_restaurant_links[0].get_attribute("href")
        print(f"  → Vào quán: {url}")
        driver.get(url)
        time.sleep(6)
except Exception as e:
    print(f"  Lỗi tìm quán: {e}")

print("\n>>> Tìm nút '+' thêm món:")
dump_elements("ADD BUTTONS", driver.find_elements(By.XPATH,
    "//*[text()='+' or @aria-label='add' or contains(@class,'add') or contains(@class,'plus')]"))

print("\n>>> Tìm tất cả button trên trang quán:")
dump_elements("ALL BTN on restaurant", driver.find_elements(By.TAG_NAME, "button"))

print("\n>>> Tìm section giá tiền:")
dump_elements("PRICE elements", driver.find_elements(By.XPATH,
    "//*[contains(text(),'đ') or contains(text(),'₫')]"))

print("\n>>> Tìm link Foody:")
dump_elements("FOODY LINKS", driver.find_elements(By.XPATH,
    "//a[contains(@href,'foody')] | //*[contains(text(),'Foody') or contains(text(),'foody')]"))

# ─── 3. FORM ĐĂNG NHẬP: Inspect input fields ─────────────────────────────────
print(DIVIDER)
print("  BƯỚC 3: Mở form đăng nhập - tìm input fields")
print(DIVIDER)

driver.get("https://shopeefood.vn/ha-noi")
time.sleep(5)

login_btns = driver.find_elements(By.XPATH, "//*[contains(text(),'Đăng nhập')]")
visible_login = [b for b in login_btns if b.is_displayed()]
dump_elements("LOGIN BUTTONS", visible_login)

if visible_login:
    visible_login[0].click()
    time.sleep(4)
    print("\n>>> Sau khi click Đăng nhập - tìm inputs:")
    dump_elements("ALL INPUTS", driver.find_elements(By.TAG_NAME, "input"))

    # Thử switch iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\n>>> Số iframe tìm thấy: {len(iframes)}")
    for i, fr in enumerate(iframes):
        src = fr.get_attribute("src") or ""
        print(f"  iframe[{i}] src='{src[:80]}'")
        try:
            driver.switch_to.frame(fr)
            inputs_in_frame = driver.find_elements(By.TAG_NAME, "input")
            dump_elements(f"INPUTS IN iframe[{i}]", inputs_in_frame)
            btns_in_frame = driver.find_elements(By.TAG_NAME, "button")
            dump_elements(f"BUTTONS IN iframe[{i}]", btns_in_frame)
            driver.switch_to.default_content()
        except Exception as e:
            print(f"    Lỗi switch iframe: {e}")
            driver.switch_to.default_content()

print(DIVIDER)
print("  HOÀN THÀNH INSPECT - Xem output ở trên để lấy selector đúng")
print(DIVIDER)

input("\nBấm ENTER để đóng trình duyệt...")
driver.quit()
