import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=options)

url = "https://www.foody.vn/ho-chi-minh/dynasty-house-hongkong-dimsum-hotpot"
print(f"Dang mo trang Foody: {url}")
driver.get(url)
time.sleep(3)

print("\n=== KẾT QUẢ CÀO DỮ LIỆU ===")

# 1. Điểm đánh giá (Rate)
try:
    rate = driver.find_element(By.CSS_SELECTOR, ".microsite-point-avg").text
    print(f"⭐ Điểm Rate: {rate}")
except:
    try:
        # Fallback XPath
        rate = driver.find_element(By.XPATH, "//div[contains(@class,'microsite-top-points')]//span | //div[contains(@class,'avg-txt')]").text
        print(f"⭐ Điểm Rate: {rate}")
    except Exception as e:
        print(f"⭐ Lỗi lấy Rate: {e}")

# 2. Số lượt bình luận
try:
    comments = driver.find_element(By.XPATH, "//div[contains(@class, 'microsite-review-count')] | //span[contains(text(), 'Bình luận')]/preceding-sibling::span | //*[contains(text(), 'Bình luận')]").text
    print(f"💬 Số lượt bình luận: {comments}")
except Exception as e:
    print(f"💬 Lỗi lấy số bình luận: {e}")

# 3. Khoảng giá (Price)
try:
    price = driver.find_element(By.XPATH, "//span[@itemprop='priceRange'] | //div[contains(@class, 'res-common-price')] | //*[contains(text(), 'đ - ')]").text
    print(f"💰 Khoảng giá: {price}")
except Exception as e:
    print(f"💰 Lỗi lấy Giá: {e}")

driver.quit()
