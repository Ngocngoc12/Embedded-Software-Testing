import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_tc06():
    print("Khởi động Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        print("Mở trang chủ ShopeeFood...")
        driver.get("https://shopeefood.vn/ha-noi")
        time.sleep(4)

        # Đóng popup
        print("Đóng popup...")
        popup_xpaths = [
            "//button[contains(@class,'close') or contains(@class,'dismiss')]",
            "//*[@aria-label='Close' or @aria-label='Dong']",
            "//div[contains(@class,'modal')]//button[@type='button']",
            "//span[contains(@class,'icon-close')]"
        ]
        for xp in popup_xpaths:
            try:
                for el in driver.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.5)
            except:
                pass

        print("Đang tìm Tab 'Đánh giá' trên trang...")
        tab_selectors = [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Danh gia')]"),
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Đánh giá')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][3]"),
            (By.XPATH, "//*[contains(text(),'Đánh giá')]"),
        ]
        
        tab_clicked = False
        for sel in tab_selectors:
            try:
                tab = wait.until(EC.element_to_be_clickable(sel))
                try:
                    tab.click()
                except:
                    driver.execute_script("arguments[0].click();", tab)
                print(f"Đã click tab 'Đánh giá' bằng {sel}")
                tab_clicked = True
                break
            except:
                continue
                
        time.sleep(3)  # Chờ UI update
        
        print("Đang chụp ảnh màn hình kết quả...")
        driver.save_screenshot("C:/Users/hoang/Downloads/Tester/screenshot_tc06_v2.png")
        print("Đã chụp thành công: screenshot_tc06_v2.png")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_tc06()
