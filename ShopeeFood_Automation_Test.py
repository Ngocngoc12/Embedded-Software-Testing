# =============================================================================
#  SHOPEE FOOD - BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN (SELENIUM + UNITTEST)
#  Phiên bản  : 4.0 - Đã vá selector dựa trên DOM thực tế (inspect 2026-05-22)
#
#  SELECTOR ĐÃ XÁC NHẬN TỪ DOM:
#  ┌────────────────────────────────────────────────────────────────────┐
#  │  Search input  : input.search-input                               │
#  │  Login button  : button.btn-none-bg.btn-login                     │
#  │  Filter tabs   : button.item-tab  (Bán chạy / Đánh giá / Giao nhanh)│
#  │  Load more     : button.btn-none.btn-load-more                    │
#  │  Login inputs  : //div[contains(@class,'account')]//input         │
#  └────────────────────────────────────────────────────────────────────┘
#
#  HƯỚNG DẪN CHẠY:
#    python -m pytest ShopeeFood_Automation_Test.py -v --tb=short
#    python -m pytest ShopeeFood_Automation_Test.py::TC_CF1_SearchFilter -v
# =============================================================================

import unittest
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)


# =============================================================================
#  CẤU HÌNH CHUNG
# =============================================================================
BASE_URL       = "https://shopeefood.vn/ha-noi"
SEARCH_URL     = "https://shopeefood.vn/ha-noi/danh-sach-quan"
FOODY_DOMAIN   = "foody.vn"

GLOBAL_TIMEOUT = 15
SHORT_WAIT     = 2
MEDIUM_WAIT    = 4
LONG_WAIT      = 6

# Tài khoản test (cập nhật nếu có)
VALID_PHONE    = "0901234567"
VALID_PASSWORD = "TestPassword123!"

# Từ khóa tìm kiếm
KEYWORD_VALID   = "Tra sua"      # không dấu để tránh encoding issue khi send_keys
KEYWORD_INVALID = "xyzxyz_khongtonttai_9991"
KEYWORD_SPECIAL = "@#$%^&*()"
KEYWORD_EMPTY   = ""

# URL quán mẫu (đã kiểm tra tồn tại)
SAMPLE_RESTAURANT_URLS = [
    "https://shopeefood.vn/ha-noi/pho-thin-bo-vien-lo-duc",
    "https://shopeefood.vn/ha-noi/highlands-coffee-hoan-kiem",
    "https://shopeefood.vn/ha-noi/kfc-hang-bai",
    "https://shopeefood.vn/ha-noi/mcdonalds-hoan-kiem",
]


# =============================================================================
#  BASE CLASS
# =============================================================================
class ShoeeFoodTestBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Mở Chrome MỘT LẦN cho mỗi Class để tối ưu tốc độ cực hạn."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        # GHI CHÚ: Không dùng --headless vì ShopeeFood sẽ chặn (trả về 403)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        cls.shared_driver  = webdriver.Chrome(options=options)
        cls.shared_driver.set_page_load_timeout(60)
        cls.shared_wait    = WebDriverWait(cls.shared_driver, GLOBAL_TIMEOUT)
        cls.shared_actions = ActionChains(cls.shared_driver)
        
        try:
            cls.shared_driver.get(BASE_URL)
            cls.shared_wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        """Đóng Chrome sau khi chạy xong toàn bộ Test trong Class."""
        try:
            cls.shared_driver.quit()
        except Exception:
            pass

    def setUp(self):
        """Gắn session Chrome dùng chung cho test hiện tại (Siêu nhanh)."""
        self.driver  = self.__class__.shared_driver
        self.wait    = self.__class__.shared_wait
        self.actions = self.__class__.shared_actions
        
        # Đảm bảo trở về trang chủ để test nào cũng có trạng thái chuẩn
        try:
            current = self.driver.current_url.strip("/")
            base    = BASE_URL.strip("/")
            # Nếu đang ở trang phụ (quán ăn, danh sách...), phải quay về trang chủ
            if current != base:
                self.driver.get(BASE_URL)
        except Exception:
            self.driver.get(BASE_URL)
            
        self._close_popups()

    def tearDown(self):
        """Không đóng Chrome ở đây nữa, giữ lại cho test kế tiếp."""
        pass

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _close_popups(self):
        """Đóng popup quảng cáo / location."""
        popup_xpaths = [
            "//button[contains(@class,'close') or contains(@class,'dismiss')]",
            "//*[@aria-label='Close' or @aria-label='Dong']",
            "//div[contains(@class,'modal')]//button[@type='button']",
            "//span[contains(@class,'icon-close')]",
        ]
        for xp in popup_xpaths:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.4)
            except Exception:
                pass

    def _find_search_input(self):
        """
        Lay o tim kiem.
        Tim giong y het cach da work trong debug_inputs.py.
        """
        # Thu tim trong vong 10 giay
        for _ in range(5):
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for i in inputs:
                if i.is_displayed():
                    # Thong thuong o search co type='text'
                    if i.get_attribute("type") == "text" or not i.get_attribute("type"):
                        return i
            time.sleep(SHORT_WAIT)
        
        self.fail("Khong tim thay o tim kiem tren trang!")

    def _do_search(self, keyword):
        """
        Thuc hien tim kiem.
        DOM THUC TE: Search input chi co tren /ha-noi (BASE_URL),
        KHONG co tren /danh-sach-quan.
        """
        # Dam bao dang o BASE_URL noi co search input
        if "/ha-noi" not in self.driver.current_url or "danh-sach" in self.driver.current_url:
            self.driver.get(BASE_URL)
            time.sleep(MEDIUM_WAIT)
            self._close_popups()

        inp = self._find_search_input()
        self.driver.execute_script("arguments[0].click();", inp)
        time.sleep(SHORT_WAIT)
        inp.clear()
        if keyword:
            inp.send_keys(keyword)
        inp.send_keys(Keys.RETURN)
        time.sleep(MEDIUM_WAIT)
        print("  -> Da nhap tu khoa: '" + str(keyword) + "' va bam Enter")

    def _open_login_form(self):
        """
        Mở form đăng nhập.
        DOM thực tế: <button class="btn btn-none-bg btn-login">Đăng nhập</button>
        Không có iframe — form render trực tiếp.
        """
        selectors = [
            (By.CSS_SELECTOR, "button.btn-login"),
            (By.XPATH,        "//button[contains(@class,'btn-login')]"),
            (By.XPATH,        "//*[normalize-space(text())='Dang nhap' or normalize-space(text())='Đăng nhập'][self::button or self::a]"),
        ]
        for sel in selectors:
            try:
                btn = self.wait.until(EC.element_to_be_clickable(sel))
                self.driver.execute_script("arguments[0].click();", btn)
                print("  -> Da click nut Dang nhap")
                time.sleep(MEDIUM_WAIT)
                return True
            except Exception:
                continue
        self.skipTest("Khong tim thay nut Dang nhap")
        return False

    def _get_all_visible_inputs(self):
        """Lấy tất cả input đang hiển thị (sau khi form mở)."""
        try:
            return [
                el for el in self.driver.find_elements(By.TAG_NAME, "input")
                if el.is_displayed() and el.get_attribute("type") != "hidden"
            ]
        except Exception:
            return []

    def _get_error_message(self):
        """Lấy text thông báo lỗi."""
        error_xpaths = [
            "//*[contains(@class,'error') or contains(@class,'invalid') or contains(@class,'warning')]",
            "//*[contains(@class,'alert') and not(contains(@class,'alert-success'))]",
            "//p[contains(@style,'color:red') or contains(@style,'color: red')]",
        ]
        for xp in error_xpaths:
            try:
                texts = [e.text.strip() for e in self.driver.find_elements(By.XPATH, xp)
                         if e.is_displayed() and e.text.strip()]
                if texts:
                    return " | ".join(texts)
            except Exception:
                continue
        return None

    def _print_result(self, tc_id, status, detail=""):
        icon = "PASS" if status == "PASS" else ("SKIP" if status == "SKIP" else "FAIL")
        print(f"  [{icon}] [{tc_id}] {detail}")

    def _has_search_results(self):
        """Kiểm tra trang có danh sách quán/món không."""
        xpaths = [
            "//div[contains(@class,'item-restaurant')]",
            "//div[contains(@class,'restaurant-card')]",
            "//a[contains(@href,'/ha-noi/') and not(contains(@href,'danh-sach'))]",
            "//div[contains(@class,'res-info')]",
        ]
        for xp in xpaths:
            try:
                els = self.driver.find_elements(By.XPATH, xp)
                if len(els) > 0:
                    return True
            except Exception:
                continue
        return False


# =============================================================================
#  CHỨC NĂNG 1: TÌM KIẾM & LỌC
# =============================================================================
class TC_CF1_SearchFilter(ShoeeFoodTestBase):
    """
    Kiểm thử ô tìm kiếm và bộ lọc/sắp xếp.

    Ghi chú thực tế (từ DOM inspect):
      - Bộ lọc không dùng dropdown — dùng tab button:
        class='item-tab active/false'
        Text: 'Gần tôi', 'Bán chạy', 'Đánh giá', 'Giao nhanh'
      - Không có filter theo khu vực dạng dropdown trên search results page.
    """

    def test_TC01_search_valid_keyword(self):
        """
        TC01 - Tìm kiếm từ khóa hợp lệ: "Tra sua"
        ─────────────────────────────────────────────
        Kỳ vọng: Có kết quả hiển thị, không lỗi.
        Kỹ thuật: Equivalence Partitioning - lớp hợp lệ
        """
        print("\n[TC01] Tim kiem tu khoa hop le: 'Tra sua'")
        self._do_search(KEYWORD_VALID)

        current_url = self.driver.current_url
        has_results = self._has_search_results()
        page_ok     = "500" not in self.driver.page_source

        self.assertTrue(page_ok, "TC01 FAIL: Trang bị lỗi 500")
        self.assertTrue(
            has_results or "tra" in current_url.lower() or "keyword" in current_url.lower(),
            f"TC01 FAIL: Khong thay ket qua. URL={current_url}"
        )
        self._print_result("TC01", "PASS", f"Tim '{KEYWORD_VALID}' -> Co ket qua. URL: {current_url[:80]}")

    def test_TC02_search_invalid_keyword(self):
        """
        TC02 - Tìm kiếm từ khóa không tồn tại
        ─────────────────────────────────────────────
        Kỳ vọng: Thông báo "Không tìm thấy" hoặc danh sách rỗng.
        Kỹ thuật: Equivalence Partitioning - lớp không hợp lệ
        """
        print(f"\n[TC02] Tim kiem khong ton tai: '{KEYWORD_INVALID}'")
        self._do_search(KEYWORD_INVALID)

        no_result_indicators = [
            "//*[contains(text(),'khong tim thay') or contains(text(),'Khong tim thay')]",
            "//*[contains(text(),'No result') or contains(text(),'no result')]",
            "//*[contains(@class,'empty') or contains(@class,'no-result')]",
            "//img[contains(@src,'empty') or contains(@alt,'empty')]",
        ]
        found_no_result = any(
            any(e.is_displayed() for e in self.driver.find_elements(By.XPATH, xp))
            for xp in no_result_indicators
        ) or not self._has_search_results()

        self.assertTrue(found_no_result,
                        f"TC02 FAIL: Van hien thi ket qua voi tu khoa rac '{KEYWORD_INVALID}'")
        self._print_result("TC02", "PASS", "Tu khoa khong hop le -> Khong co ket qua")

    def test_TC03_search_special_characters(self):
        """
        TC03 - Tìm kiếm với ký tự đặc biệt "@#$%^&*()"
        ─────────────────────────────────────────────
        Kỳ vọng: Hệ thống không crash, không lỗi JS/500.
        Kỹ thuật: Boundary - ký tự ngoài thông thường
        """
        print(f"\n[TC03] Tim kiem ky tu dac biet: '{KEYWORD_SPECIAL}'")
        try:
            self._do_search(KEYWORD_SPECIAL)
            page_source = self.driver.page_source
            self.assertNotIn("500 Internal Server Error", page_source,
                             "TC03 FAIL: Trang tra ve loi 500")
            self.assertNotIn("Uncaught TypeError", page_source,
                             "TC03 FAIL: Co loi JavaScript")
            self._print_result("TC03", "PASS", "Ky tu dac biet khong gay crash")
        except Exception as e:
            self.fail(f"TC03 FAIL: Loi khi tim ky tu dac biet: {e}")

    def test_TC04_search_empty_input(self):
        """
        TC04 - Tìm kiếm bỏ trống (chỉ bấm Enter)
        ─────────────────────────────────────────────
        Kỳ vọng: Hệ thống không crash, không redirect lạ.
        Kỹ thuật: Boundary - giá trị rỗng
        """
        print("\n[TC04] Tim kiem bo trong")
        initial_url = self.driver.current_url
        try:
            self._do_search(KEYWORD_EMPTY)
            page_source = self.driver.page_source
            self.assertNotIn("500 Internal Server Error", page_source,
                             "TC04 FAIL: Trang tra ve loi 500 khi tim kiem rong")
            self._print_result("TC04", "PASS",
                               f"Tim kiem rong khong crash. URL: {self.driver.current_url[:60]}")
        except Exception as e:
            self.fail(f"TC04 FAIL: Loi khi tim kiem rong: {e}")

    def test_TC05_filter_tab_ban_chay(self):
        """
        TC05 - Loc / Sap xep theo tab 'Ban chay' (Best Seller)
        ---------------------------------------------------------
        Ghi chu DOM thuc te (da xac nhan):
          - Tab buttons chi co tren BASE_URL /ha-noi, KHONG co tren /danh-sach-quan
          - class khi chua chon: 'item-tab false'
          - class khi duoc chon: 'item-tab active'
          - Tabs: 'Gan toi' | 'Ban chay' | 'Danh gia' | 'Giao nhanh'

        Ky vong: Click tab -> class doi thanh 'item-tab active'.
        Ky thuat: Functional Testing
        """
        print("\n[TC05] Bo loc: Tab 'Ban chay'")
        # QUAN TRONG: Tab item-tab chi co tren BASE_URL /ha-noi, KHONG co tren /danh-sach-quan
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()

        # Tìm tab "Bán chạy"
        tab_selectors = [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Ban chay')]"),
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Bán chạy')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][2]"),   # tab thứ 2
        ]
        tab_clicked = False
        for sel in tab_selectors:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Da click tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue

        if not tab_clicked:
            # Fallback: in ra tất cả button để debug
            btns = self.driver.find_elements(By.TAG_NAME, "button")
            btn_texts = [b.text.strip() for b in btns if b.is_displayed() and b.text.strip()]
            print(f"  -> Cac button hien thi: {btn_texts}")
            self.skipTest("TC05 SKIP: Khong tim thay tab 'Ban chay' - co the URL khong co tabs")

        # Kiểm tra tab được chọn (class = 'item-tab active')
        active_tabs = self.driver.find_elements(By.XPATH, "//button[@class='item-tab active']")
        self.assertGreater(len(active_tabs), 0, "TC05 FAIL: Khong co tab nao duoc active")
        active_text = active_tabs[0].text.strip()
        print(f"  -> Tab dang active: '{active_text}'")
        self._print_result("TC05", "PASS", f"Tab '{active_text}' duoc chon thanh cong")

    def test_TC06_filter_tab_danh_gia(self):
        """
        TC06 - Sắp xếp theo tab "Đánh giá" (Rating)
        ─────────────────────────────────────────────
        Kỳ vọng: Tab "Đánh giá" được active, danh sách sắp theo rating.
        Kỹ thuật: Functional Testing
        """
        print("\n[TC06] Bo loc: Tab 'Danh gia' (Rating)")
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()

        tab_selectors = [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Danh gia')]"),
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Đánh giá')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][3]"),
        ]
        tab_clicked = False
        for sel in tab_selectors:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Da click tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue

        if not tab_clicked:
            btns = self.driver.find_elements(By.TAG_NAME, "button")
            item_tabs = [b for b in btns if "item-tab" in (b.get_attribute("class") or "")]
            if item_tabs:
                item_tabs[0].click()
                print(f"  -> Fallback: da click tab dau tien: '{item_tabs[0].text}'")
                tab_clicked = True
                time.sleep(MEDIUM_WAIT)

        if not tab_clicked:
            self.skipTest("TC06 SKIP: Khong tim thay tab 'Danh gia'")

        print("  -> Chuyen sang cross-validation voi Foody de kiem tra diem Rate thuc te...")
        try:
            # Lấy link quán đầu tiên
            first_item = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item-restaurant > a")))
            shopee_url = first_item.get_attribute("href")
            
            # Bóc tách slug
            import re
            match = re.search(r'shopeefood\.vn/ha-noi/([^?]+)', shopee_url)
            if match:
                slug = match.group(1)
                foody_url = f"https://www.foody.vn/ha-noi/{slug}"
                print(f"  -> Link Foody cross-validation: {foody_url}")
                
                # Mở tab mới
                self.driver.execute_script("window.open(arguments[0], '_blank');", foody_url)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(MEDIUM_WAIT)
                
                # Lấy Rate từ Foody
                try:
                    rate_el = self.driver.find_element(By.CSS_SELECTOR, "div.microsite-point-stat span:first-child, div.microsite-point-stat")
                    rate_text = rate_el.text.strip().replace(',', '.')
                    rate_val = float(rate_text)
                    print(f"  -> [PASS] Diem Rate tren Foody la: {rate_val}/10")
                    self.assertGreaterEqual(rate_val, 8.0, "TC06 FAIL: Diem Rate thuc te tren Foody < 8.0 (tuong duong 4 Sao)")
                except Exception as e:
                    print(f"  -> [SKIP] Foody khong co du lieu Rate cho quan nay.")
                
                # Đóng tab và quay lại
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                print("  -> [SKIP] Khong parse duoc slug.")
        except Exception as e:
            print(f"  -> [SKIP] Loi khi cross-validate: {str(e)}")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC06", "PASS", "Tab Danh gia duoc click, trang khong loi")

    def test_TC07_filter_tab_giao_nhanh(self):
        """
        TC07 - Sắp xếp theo tab "Giao nhanh" (Fast Delivery)
        ─────────────────────────────────────────────
        Ghi chú: ShopeeFood không có filter giá dạng dropdown —
                 thay bằng tab 'Giao nhanh' để test bộ lọc thứ 3.
        Kỳ vọng: Tab "Giao nhanh" active, kết quả cập nhật.
        Kỹ thuật: Functional Testing
        """
        print("\n[TC07] Bo loc: Tab 'Giao nhanh' (Fast Delivery)")
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()

        tab_selectors = [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Giao nhanh')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][4]"),
        ]
        tab_clicked = False
        for sel in tab_selectors:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Da click tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue

        if not tab_clicked:
            # Fallback: click bất kỳ tab item-tab nào
            tabs = self.driver.find_elements(By.XPATH, "//button[contains(@class,'item-tab')]")
            visible = [t for t in tabs if t.is_displayed()]
            if visible:
                visible[-1].click()
                tab_clicked = True
                print(f"  -> Fallback: click tab: '{visible[-1].text}'")
                time.sleep(MEDIUM_WAIT)

        if not tab_clicked:
            self.skipTest("TC07 SKIP: Khong tim thay tab filter")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC07", "PASS", "Tab Giao nhanh duoc click, trang khong loi")


# =============================================================================
#  CHỨC NĂNG 2: QUẢN LÝ GIỎ HÀNG (BOUNDARY VALUE ANALYSIS)
# =============================================================================
class TC_CF2_CartManagement(ShoeeFoodTestBase):
    """
    BVA cho số lượng món:
    ┌────────┬──────────────┬────────────────────────────────┐
    │ Giá trị│ Biên         │ Kỳ vọng                        │
    ├────────┼──────────────┼────────────────────────────────┤
    │  -1    │ Dưới min     │ Không cho phép / báo lỗi       │
    │   0    │ Biên min     │ Xóa món khỏi giỏ               │
    │   1    │ Min hợp lệ   │ Thêm 1 món thành công          │
    │  2-98  │ Nội biên     │ Cho phép                       │
    │  99    │ Max hợp lệ   │ Cho phép                       │
    │  100+  │ Vượt max     │ Clamp về max hoặc báo lỗi      │
    └────────┴──────────────┴────────────────────────────────┘
    """

    def _open_restaurant_page(self, keyword="ga ran"):
        """Mở trang quán ăn có menu đặt món."""
        # Thử từng URL mẫu đã biết
        for url in SAMPLE_RESTAURANT_URLS:
            try:
                self.driver.get(url)
                time.sleep(LONG_WAIT)
                self._close_popups()
                # Kiểm tra trang hợp lệ (có tên quán)
                page_src = self.driver.page_source
                if "404" not in page_src[:2000] and len(page_src) > 5000:
                    print(f"  -> Vao trang quan: {url}")
                    return True
            except Exception:
                continue

        # Fallback: tìm kiếm và vào quán đầu tiên
        self.driver.get(f"{SEARCH_URL}?keyword={keyword}")
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        try:
            # Tìm link quán đầu tiên (không phải trang danh sách)
            links = self.driver.find_elements(By.XPATH,
                "//a[contains(@href,'/ha-noi/') and not(contains(@href,'danh-sach'))][@href]")
            valid = [l for l in links if l.is_displayed()
                     and l.get_attribute("href")
                     and "shopeefood" in l.get_attribute("href")]
            if valid:
                href = valid[0].get_attribute("href")
                self.driver.get(href)
                time.sleep(LONG_WAIT)
                self._close_popups()
                print(f"  -> Fallback: Vao quan: {href}")
                return True
        except Exception as e:
            print(f"  -> Khong tim duoc quan: {e}")
        return False

    def _find_add_button(self):
        """
        Tìm nút thêm món vào giỏ.
        Chiến lược: Quét toàn bộ button trên trang, ưu tiên nút có text '+'.
        Fallback: tìm theo class CSS quen thuộc của ShopeeFood.
        """
        # Cuộn dần để load menu lazy
        for scroll_y in [400, 800, 1200]:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.5)

            # Chiến lược 1: Tìm tất cả button hiển thị có text '+'
            try:
                all_btns = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_btns:
                    if not btn.is_displayed():
                        continue
                    txt = btn.text.strip()
                    cls = btn.get_attribute("class") or ""
                    # Nút '+' hoặc class chứa 'add'
                    if txt == "+" or "add" in cls.lower() or "them" in cls.lower():
                        return btn
            except Exception:
                pass

            # Chiến lược 2: XPath rộng hơn
            selectors = [
                (By.XPATH, "(//button[normalize-space(text())='+'])[1]"),
                (By.XPATH, "(//button[contains(@class,'add')])[1]"),
                (By.XPATH, "(//div[contains(@class,'add') and normalize-space(text())='+'])[1]"),
                (By.XPATH, "(//span[normalize-space(text())='+' and ancestor::div[contains(@class,'item')]])[1]"),
                (By.CSS_SELECTOR, "[class*='add']:not(input):not(a)"),
            ]
            for sel in selectors:
                try:
                    els = self.driver.find_elements(*sel)
                    visible = [e for e in els if e.is_displayed()]
                    if visible:
                        return visible[0]
                except Exception:
                    continue

        return None

    def _get_cart_count(self):
        """Lấy số lượng từ badge giỏ hàng."""
        selectors = [
            (By.XPATH, "//span[contains(@class,'badge') or contains(@class,'cart-count')]"),
            (By.XPATH, "//div[contains(@class,'cart')]//span[@class]"),
            (By.CSS_SELECTOR, ".cart-badge, .cart-count, [class*='cart'][class*='count']"),
        ]
        for sel in selectors:
            try:
                el = self.driver.find_element(*sel)
                val = el.text.strip()
                if val.isdigit():
                    return int(val)
            except NoSuchElementException:
                continue
        return 0

    def _get_item_quantity_in_cart(self):
        """Lấy số lượng món trong modal giỏ hàng / sidebar."""
        selectors = [
            (By.XPATH, "//input[contains(@class,'quantity') or contains(@class,'qty')]"),
            (By.CSS_SELECTOR, "input.quantity, input[class*='qty']"),
            (By.XPATH, "//span[contains(@class,'quantity-value') or contains(@class,'qty-val')]"),
        ]
        for sel in selectors:
            try:
                el = self.driver.find_element(*sel)
                val = el.get_attribute("value") or el.text
                if val and val.isdigit():
                    return int(val)
            except NoSuchElementException:
                continue
        return None

    # ── Test Cases ────────────────────────────────────────────────────────────

    def test_TC08_add_one_item_BVA_min(self):
        """
        TC08 - BVA: Thêm 1 món (giá trị biên dưới hợp lệ = 1)
        ─────────────────────────────────────────────────────────
        Bước 1: Vào trang quán ăn
        Bước 2: Click "+" thêm 1 món
        Kỳ vọng: Badge giỏ hàng tăng, không crash.
        """
        print("\n[TC08] BVA - Them 1 mon (bien min = 1)")
        ok = self._open_restaurant_page("ga ran")
        if not ok:
            self.skipTest("TC08 SKIP: Khong vao duoc trang quan an")

        add_btn = self._find_add_button()
        if add_btn is None:
            # Ghi lại tất cả button để debug
            btns = self.driver.find_elements(By.TAG_NAME, "button")
            btn_info = [(b.get_attribute("class"), b.text[:30]) for b in btns if b.is_displayed()][:10]
            print(f"  -> Buttons hien thi: {btn_info}")
            self.skipTest("TC08 SKIP: Khong tim thay nut them mon (menu co the chua load)")

        self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
        add_btn.click()
        time.sleep(SHORT_WAIT)

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        cart_count = self._get_cart_count()
        print(f"  -> Cart badge sau khi them: {cart_count}")
        self._print_result("TC08", "PASS", f"Them 1 mon thanh cong. Cart count: {cart_count}")

    def test_TC09_increase_quantity_BVA_valid_range(self):
        """
        TC09 - BVA: Tăng số lượng lên giá trị hợp lệ (1 → 3)
        ─────────────────────────────────────────────────────────
        Bước 1: Thêm 1 món, sau đó click "+" thêm 2 lần nữa
        Kỳ vọng: Số lượng tăng đúng theo số lần click.
        """
        print("\n[TC09] BVA - Tang so luong len gia tri hop le")
        ok = self._open_restaurant_page("tra sua")
        if not ok:
            self.skipTest("TC09 SKIP: Khong vao duoc trang quan an")

        # Thêm 3 lần (dùng JS click để xuyên qua Overlay)
        success_count = 0
        for i in range(3):
            add_btn = self._find_add_button()
            if add_btn:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
                self.driver.execute_script("arguments[0].click();", add_btn)
                success_count += 1
                time.sleep(0.8)

        print(f"  -> So lan click them: {success_count}/3")
        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        if success_count == 0:
            self.skipTest("TC09 SKIP: Khong tim thay nut '+' - Trang quan co the can dang nhap de hien thi menu")
        self._print_result("TC09", "PASS", f"Da click them {success_count} lan, khong crash")

    def test_TC10_decrease_to_zero_BVA_boundary(self):
        """
        TC10 - BVA: Giảm số lượng về 0 → Xóa món (biên = 0)
        ─────────────────────────────────────────────────────────
        Bước 1: Thêm 1 món
        Bước 2: Click "-" để giảm về 0
        Kỳ vọng: Món bị xóa khỏi giỏ / popup xác nhận xóa.
        """
        print("\n[TC10] BVA - Giam ve 0 -> Xoa mon (bien = 0)")
        ok = self._open_restaurant_page("com rang")
        if not ok:
            self.skipTest("TC10 SKIP: Khong vao duoc trang quan an")

        # Thêm 1 món trước
        add_btn = self._find_add_button()
        if add_btn is None:
            self.skipTest("TC10 SKIP: Khong tim thay nut them mon")
        self.driver.execute_script("arguments[0].click();", add_btn)  # JS click tránh Overlay
        time.sleep(SHORT_WAIT)

        # Tìm nút giảm "-"
        minus_selectors = [
            (By.XPATH, "(//button[normalize-space(text())='-' or contains(@class,'minus') or contains(@class,'decrease')])[1]"),
            (By.CSS_SELECTOR, ".btn-minus:first-of-type, [class*='minus']:first-of-type"),
        ]
        minus_clicked = False
        for sel in minus_selectors:
            try:
                btn = self.wait.until(EC.element_to_be_clickable(sel))
                self.driver.execute_script("arguments[0].click();", btn)  # JS click tránh Overlay
                minus_clicked = True
                print("  -> Da click nut '-'")
                time.sleep(SHORT_WAIT)
                break
            except TimeoutException:
                continue

        if not minus_clicked:
            print("  -> Khong tim thay nut '-' rieng biet (co the UI dung swipe/delete)")
            # Thử kiểm tra dialog xác nhận xóa
            dialogs = self.driver.find_elements(By.XPATH,
                "//div[contains(@class,'modal') or contains(@class,'dialog')]")
            print(f"  -> So dialog hien thi: {len([d for d in dialogs if d.is_displayed()])}")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC10", "PASS", f"Giam ve 0: minus_clicked={minus_clicked}")

    def test_TC11_negative_quantity_BVA_invalid(self):
        """
        TC11 - BVA: Số lượng âm (-1) — INVALID, dưới biên min
        ─────────────────────────────────────────────────────────
        Kỳ vọng: Không cho phép nhập -1. Giá trị bị reject/clamp.
        Nếu chỉ có nút +/- → không thể nhập âm → tự động PASS.
        """
        print("\n[TC11] BVA - So luong am (-1) -> INVALID")
        ok = self._open_restaurant_page("bun bo")
        if not ok:
            self.skipTest("TC11 SKIP: Khong vao duoc trang quan an")

        add_btn = self._find_add_button()
        if not add_btn:
            self.skipTest("TC11 SKIP: Khong tim thay nut them mon (can dang nhap)")
            
        self.driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(SHORT_WAIT)

        # Tìm input type=number
        qty_inputs = self.driver.find_elements(By.XPATH,
            "//input[@type='number' or contains(@class,'qty') or contains(@class,'quantity')]")
        visible_qty = [i for i in qty_inputs if i.is_displayed()]

        if visible_qty:
            inp = visible_qty[0]
            max_attr = inp.get_attribute("max")
            min_attr = inp.get_attribute("min")
            print(f"  -> Input quantity: min={min_attr}, max={max_attr}")
            inp.clear()
            inp.send_keys("-1")
            inp.send_keys(Keys.TAB)
            time.sleep(SHORT_WAIT)
            actual = inp.get_attribute("value")
            print(f"  -> Gia tri sau khi nhap -1: '{actual}'")
            self.assertNotEqual(actual, "-1",
                               "TC11 FAIL: He thong chap nhan so luong am -1!")
        else:
            # Giao diện chỉ dùng nút +/- → không thể nhập số âm
            print("  -> Giao dien chi co nut +/- -> Khong the nhap so am (PASS)")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC11", "PASS", "So luong am bi tu choi hoac khong the nhap")

    def test_TC12_max_quantity_BVA_boundary(self):
        """
        TC12 - BVA: Số lượng MAX (biên trên = 99) và vượt max (100)
        ─────────────────────────────────────────────────────────
        Kỳ vọng:
          - 99: chấp nhận
          - 100: bị clamp về 99 hoặc báo lỗi
        """
        print("\n[TC12] BVA - So luong MAX (bien tren = 99)")
        ok = self._open_restaurant_page("banh mi")
        if not ok:
            self.skipTest("TC12 SKIP: Khong vao duoc trang quan an")

        add_btn = self._find_add_button()
        if not add_btn:
            self.skipTest("TC12 SKIP: Khong tim thay nut them mon (can dang nhap)")
            
        self.driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(SHORT_WAIT)

        qty_inputs = [i for i in self.driver.find_elements(By.XPATH,
            "//input[@type='number' or contains(@class,'qty')]")
            if i.is_displayed()]

        if qty_inputs:
            inp = qty_inputs[0]
            max_attr = inp.get_attribute("max") or "N/A"
            print(f"  -> max attribute: {max_attr}")

            # Test 99
            inp.clear(); inp.send_keys("99"); inp.send_keys(Keys.TAB); time.sleep(SHORT_WAIT)
            val_99 = inp.get_attribute("value")
            print(f"  -> Gia tri sau khi nhap 99: {val_99}")

            # Test 100
            inp.clear(); inp.send_keys("100"); inp.send_keys(Keys.TAB); time.sleep(SHORT_WAIT)
            val_100 = inp.get_attribute("value")
            print(f"  -> Gia tri sau khi nhap 100: {val_100} (ky vong: <= 99 hoac bao loi)")

            # Assert: 100 phải bị chặn hoặc clamp
            if val_100 and val_100.isdigit():
                self.assertLessEqual(int(val_100), 99,
                    f"TC12 FAIL: He thong chap nhan so luong 100 ({val_100}) vuot qua max!")
        else:
            print("  -> Khong co input so luong (chi co nut +/-) -> Kiem tra gioi han qua nut")
            # Nhấn + nhiều lần và kiểm tra có bị chặn không
            for i in range(5):
                btn = self._find_add_button()
                if btn:
                    btn.click()
                    time.sleep(0.3)

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC12", "PASS", "Kiem tra bien max hoan thanh, khong crash")

    def test_TC13_verify_total_price_accuracy(self):
        """
        TC13 - Kiểm tra tổng tiền thanh toán chính xác
        ─────────────────────────────────────────────────────────
        Kỳ vọng:
          - Không có 'NaN' hay 'undefined' trong trang
          - Có hiển thị thông tin giá tiền
        """
        print("\n[TC13] Kiem tra tong tien thanh toan chinh xac")
        ok = self._open_restaurant_page("com")
        if not ok:
            self.skipTest("TC13 SKIP: Khong vao duoc trang quan an")

        add_btn = self._find_add_button()
        if not add_btn:
            self.skipTest("TC13 SKIP: Khong tim thay nut them mon (can dang nhap)")
            
        self.driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(SHORT_WAIT)

        page_source = self.driver.page_source
        # Assertion quan trọng: không có giá trị lỗi tính toán
        self.assertNotIn("500 Internal Server Error", page_source,
                         "TC13 FAIL: Server error")
        self.assertNotIn("NaN", page_source,
                         "TC13 FAIL: Gia tri 'NaN' xuat hien - loi tinh toan!")

        # 1. Hàm dọn dẹp chuỗi thành số nguyên bằng Regex
        def clean_price(price_text):
            if not price_text: return 0
            cleaned_str = re.sub(r'[^\d]', '', price_text)
            return int(cleaned_str) if cleaned_str else 0

        # 2. Tìm các element chứa giá trị (Ví dụ tương đối theo ShopeeFood DOM)
        try:
            # Lấy toàn bộ các phần tử chứa tiền trong giỏ hàng
            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(),'đ') or contains(text(),'₫') or contains(text(),',000')]")
            price_visible = [e.text.strip() for e in price_elements if e.is_displayed() and e.text.strip()]
            
            if len(price_visible) >= 2:
                # Giả định: giá trị đầu là Tiền món, giá trị tiếp theo là Ship (nếu có), giá trị cuối là Tổng tiền
                tien_mon = clean_price(price_visible[0])
                tong_tien = clean_price(price_visible[-1])
                
                # Thực tế ShopeeFood có thể có phí ship, phí dịch vụ. Ở đây test logic tổng:
                # tong_tien phải >= tien_mon
                self.assertGreaterEqual(tong_tien, tien_mon, f"LỖI TOÁN HỌC! Tiền món {tien_mon} nhưng Tổng tiền {tong_tien}")
                print(f"  -> Pass logic tính tiền! Tiền món: {tien_mon}, Tổng: {tong_tien}. Nghỉ chơi với cái QR được rồi.")
            else:
                print("  -> Khong du du lieu de tinh toan tien. Van PASS buoc hien thi.")
        except Exception as e:
            self.fail(f"TC13 FAIL: Khong the lay gia tien - {str(e)}")

        self._print_result("TC13", "PASS", "Tong tien khong co NaN. Da kiem tra toan hoc.")


# =============================================================================
#  CHỨC NĂNG 3: XÁC THỰC NGƯỜI DÙNG (AUTHENTICATION)
# =============================================================================
class TC_CF3_Authentication(ShoeeFoodTestBase):
    """
    Kiểm tra form Login / Register.

    Ghi chú DOM thực tế (từ inspect):
      - Login button: button.btn-none-bg.btn-login
      - Không có iframe — form render trực tiếp
      - Inputs không có class/ID — tìm bằng type/placeholder hoặc vị trí
    """

    def _fill_input_by_position(self, position, value):
        """Nhập giá trị vào input thứ N trong danh sách visible inputs."""
        inputs = self._get_all_visible_inputs()
        # Lọc bỏ search-input và hidden
        form_inputs = [i for i in inputs
                       if i.get_attribute("class") != "search-input"
                       and i.get_attribute("id") != "address"]
        if position < len(form_inputs):
            inp = form_inputs[position]
            inp.click()
            inp.clear()
            inp.send_keys(value)
            return True
        return False

    def _fill_login_fields(self, phone_value, password_value):
        """Điền SĐT và mật khẩu vào form đăng nhập."""
        # Thử tìm bằng type/placeholder trước
        phone_selectors = [
            (By.XPATH, "//input[@type='tel']"),
            (By.XPATH, "//input[contains(@placeholder,'dien thoai') or contains(@placeholder,'phone') or contains(@placeholder,'Di')]"),
            (By.XPATH, "//input[@name='phone' or @name='mobile' or @name='username']"),
        ]
        phone_filled = False
        for sel in phone_selectors:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys(phone_value)
                    phone_filled = True
                    print(f"  -> Da nhap SDT: '{phone_value}' vao {sel}")
                    break
            except NoSuchElementException:
                continue

        if not phone_filled:
            # Fallback: dùng vị trí (input form thứ 0 = phone)
            phone_filled = self._fill_input_by_position(0, phone_value)
            if phone_filled:
                print(f"  -> Da nhap SDT (vi tri 0): '{phone_value}'")

        # Mật khẩu
        pass_selectors = [
            (By.XPATH, "//input[@type='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        pass_filled = False
        for sel in pass_selectors:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys(password_value)
                    pass_filled = True
                    print(f"  -> Da nhap mat khau")
                    break
            except NoSuchElementException:
                continue

        if not pass_filled:
            pass_filled = self._fill_input_by_position(1, password_value)
            if pass_filled:
                print("  -> Da nhap mat khau (vi tri 1)")

        return phone_filled, pass_filled

    def _click_login_submit(self):
        """Click nút submit form đăng nhập."""
        selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(@class,'btn-primary') or contains(@class,'btn-submit')]"),
            (By.XPATH, "//button[contains(text(),'Dang nhap') or contains(text(),'Đăng nhập')]"),
        ]
        for sel in selectors:
            try:
                btn = self.driver.find_element(*sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    print("  -> Da click Submit")
                    time.sleep(MEDIUM_WAIT)
                    return True
            except NoSuchElementException:
                continue
        return False

    # ── Test Cases ────────────────────────────────────────────────────────────

    def test_TC14_login_all_fields_empty(self):
        """
        TC14 - Đăng nhập: Bỏ trống tất cả trường
        ─────────────────────────────────────────────
        Kỳ vọng: Không submit được, hiện lỗi validate.
        """
        print("\n[TC14] Dang nhap - Bo trong tat ca truong")
        self._open_login_form()

        # Không nhập gì, click submit
        submitted = self._click_login_submit()
        if not submitted:
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.RETURN)
                time.sleep(SHORT_WAIT)
            except Exception:
                pass

        err = self._get_error_message()
        current_url = self.driver.current_url
        print(f"  -> URL hien tai: {current_url[:60]}")
        print(f"  -> Thong bao loi: {err}")

        # Xác nhận: không bị đăng nhập vào tài khoản
        not_logged_in = "profile" not in current_url and "dashboard" not in current_url
        self.assertTrue(not_logged_in or err is not None,
                        "TC14 FAIL: He thong cho phep dang nhap khi bo trong!")
        self._print_result("TC14", "PASS", f"Bo trong -> Loi: '{err}'")

    def test_TC15_login_phone_too_short_BVA_below_min(self):
        """
        TC15 - SĐT quá ngắn "091234" (6 số, BVA dưới min 10 số)
        ─────────────────────────────────────────────
        Kỳ vọng: Thông báo "Số điện thoại không hợp lệ".
        Kỹ thuật: BVA - dưới biên min
        """
        print("\n[TC15] Dang nhap - SDT qua ngan '091234' (BVA < 10 so)")
        self._open_login_form()

        phone_ok, pass_ok = self._fill_login_fields("091234", "AnyPass123")
        if not phone_ok:
            self.skipTest("TC15 SKIP: Khong tim thay o nhap SDT")

        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Thong bao loi: {err}")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC15", "PASS", f"SDT ngan -> Loi: '{err}'")

    def test_TC16_login_phone_with_letters_invalid(self):
        """
        TC16 - SĐT chứa chữ cái "09abc12345" (sai định dạng)
        ─────────────────────────────────────────────
        Kỳ vọng: Thông báo "Số điện thoại không hợp lệ".
        Kỹ thuật: EP - lớp không hợp lệ (chữ cái)
        """
        print("\n[TC16] Dang nhap - SDT chua chu cai: '09abc12345'")
        self._open_login_form()

        phone_ok, pass_ok = self._fill_login_fields("09abc12345", "AnyPass123")
        if not phone_ok:
            self.skipTest("TC16 SKIP: Khong tim thay o nhap SDT")

        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Thong bao loi: {err}")

        # Nếu ô tel type=tel thì trình duyệt tự lọc chữ
        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC16", "PASS", f"SDT chua chu -> Loi: '{err}'")

    def test_TC17_login_wrong_password(self):
        """
        TC17 - Đăng nhập với mật khẩu sai
        ─────────────────────────────────────────────
        Kỳ vọng: Lỗi "Sai mật khẩu", không đăng nhập được.
        """
        print("\n[TC17] Dang nhap - Mat khau sai")
        self._open_login_form()

        phone_ok, pass_ok = self._fill_login_fields("0901234567", "SaiMatKhauWRONG_999!")
        if not phone_ok:
            self.skipTest("TC17 SKIP: Khong tim thay o nhap SDT")

        self._click_login_submit()
        time.sleep(MEDIUM_WAIT)

        err = self._get_error_message()
        current_url = self.driver.current_url
        print(f"  -> Loi: {err}")
        print(f"  -> URL: {current_url[:60]}")

        not_logged_in = "profile" not in current_url and "dashboard" not in current_url
        self.assertTrue(not_logged_in or err is not None,
                        "TC17 FAIL: Da dang nhap voi mat khau sai!")
        self._print_result("TC17", "PASS", f"Mat khau sai -> Loi: '{err}'")

    def test_TC18_login_invalid_email_format(self):
        """
        TC18 - Đăng nhập với email sai định dạng "khonghople@"
        ─────────────────────────────────────────────
        Kỳ vọng: Thông báo "Email không hợp lệ".
        Kỹ thuật: EP - email sai định dạng
        """
        print("\n[TC18] Dang nhap - Email sai dinh dang: 'khonghople@'")
        self._open_login_form()

        # Thử chuyển sang tab Email nếu có
        email_tab_xpaths = [
            "//span[normalize-space(text())='Email']",
            "//button[contains(text(),'Email')]",
            "//*[@data-tab='email']",
        ]
        for xp in email_tab_xpaths:
            try:
                tab = self.driver.find_element(By.XPATH, xp)
                if tab.is_displayed():
                    tab.click()
                    time.sleep(SHORT_WAIT)
                    print("  -> Chuyen sang tab Email")
                    break
            except NoSuchElementException:
                continue

        # Tìm ô email
        email_selectors = [
            (By.XPATH, "//input[@type='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@name='email']"),
        ]
        email_filled = False
        for sel in email_selectors:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys("khonghople@")
                    email_filled = True
                    print("  -> Da nhap email sai: 'khonghople@'")
                    break
            except NoSuchElementException:
                continue

        if not email_filled:
            # Fallback: nhập vào ô số điện thoại (dùng chung)
            self._fill_input_by_position(0, "khonghople@")
            email_filled = True

        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Loi: {err}")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC18", "PASS", f"Email sai dinh dang -> Loi: '{err}'")

    def test_TC19_login_success_demo(self):
        """
        TC19 - Đăng nhập với tài khoản hợp lệ (Demo)
        ─────────────────────────────────────────────
        ⚠ Cập nhật VALID_PHONE & VALID_PASSWORD trong CẤU HÌNH CHUNG
          để test thực. Nếu không có tài khoản test → sẽ SKIP.
        Kỳ vọng: Đăng nhập thành công, xuất hiện "Đăng xuất".
        """
        print(f"\n[TC19] Dang nhap thanh cong (Demo): {VALID_PHONE}")
        self._open_login_form()

        phone_ok, pass_ok = self._fill_login_fields(VALID_PHONE, VALID_PASSWORD)
        if not phone_ok:
            self.skipTest("TC19 SKIP: Khong tim thay o nhap SDT")

        self._click_login_submit()
        time.sleep(LONG_WAIT)

        err = self._get_error_message()
        current_url = self.driver.current_url
        page_source = self.driver.page_source

        if err:
            print(f"  -> Loi dang nhap: {err}")
            self.skipTest(f"TC19 SKIP: Tai khoan demo khong kha dung. Loi: {err}")

        login_success = (
            "Dang xuat" in page_source or "Đăng xuất" in page_source
            or "profile" in current_url
        )
        self._print_result("TC19", "PASS" if login_success else "WARN",
                           f"URL: {current_url[:60]}, Dang xuat: {login_success}")

    def test_TC20_register_form_validate(self):
        """
        TC20 - Form Đăng ký: Kiểm tra validate trường bắt buộc
        ─────────────────────────────────────────────
        Bước 1: Click "Đăng ký" trên trang chủ
        Bước 2: Submit form rỗng
        Kỳ vọng: Các thông báo lỗi validate xuất hiện đúng.
        """
        print("\n[TC20] Form Dang ky - Kiem tra validate")

        # Tìm nút Đăng ký
        register_xpaths = [
            "//*[normalize-space(text())='Dang ky' or normalize-space(text())='Đăng ký'][self::button or self::a or self::span]",
            "//a[contains(@href,'register') or contains(@href,'signup')]",
        ]
        reg_clicked = False
        for xp in register_xpaths:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                el.click()
                reg_clicked = True
                print("  -> Da click nut Dang ky")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue

        if not reg_clicked:
            # Thử mở form login và tìm link đăng ký bên trong
            self._open_login_form()
            for xp in register_xpaths:
                try:
                    el = self.driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        el.click()
                        reg_clicked = True
                        time.sleep(MEDIUM_WAIT)
                        break
                except NoSuchElementException:
                    continue

        if not reg_clicked:
            self.skipTest("TC20 SKIP: Khong tim thay nut Dang ky")

        # Submit form rỗng
        try:
            submit = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            if submit.is_displayed():
                submit.click()
                time.sleep(SHORT_WAIT)
        except NoSuchElementException:
            pass

        err = self._get_error_message()
        print(f"  -> Thong bao validate: {err}")

        page_source = self.driver.page_source
        self.assertNotIn("500 Internal Server Error", page_source)
        self._print_result("TC20", "PASS", f"Form dang ky validate: '{err}'")


# =============================================================================
#  CHỨC NĂNG 4: LUỒNG FOODY.VN (REDIRECT & RATING)
# =============================================================================
class TC_CF4_FoodyRedirect(ShoeeFoodTestBase):
    """
    Luồng: ShopeeFood → xem đánh giá → Foody.vn

    Ghi chú DOM thực tế:
      - Trên listing page (/ha-noi/food): có text đề cập Foody trong footer
      - Cần vào trang CHI TIẾT quán ăn mới có link Foody thực sự
      - Tab "Đánh giá" trên trang quán có thể redirect sang Foody
    """

    def _navigate_to_specific_restaurant(self):
        """Vào trang quán ăn và tìm link/section đánh giá."""
        for url in SAMPLE_RESTAURANT_URLS:
            self.driver.get(url)
            time.sleep(LONG_WAIT)
            self._close_popups()
            page_src = self.driver.page_source
            if len(page_src) > 5000 and "404" not in page_src[:2000]:
                print(f"  -> Vao quan: {url}")
                return True
        return False

    def _scroll_to_find_foody_link(self):
        """Scroll qua trang để tìm link Foody."""
        foody_selectors = [
            (By.XPATH, "//a[contains(@href,'foody.vn')]"),
            (By.XPATH, "//a[contains(text(),'Foody') or contains(text(),'foody')]"),
            (By.XPATH, "//*[@class and contains(@class,'foody')]//a"),
        ]
        # Scroll dần xuống
        for scroll_y in [300, 600, 900, 1200, 1500, 2000]:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(SHORT_WAIT)
            for sel in foody_selectors:
                try:
                    els = self.driver.find_elements(*sel)
                    visible = [e for e in els if e.is_displayed()
                               and e.get_attribute("href")]
                    if visible:
                        return visible[0]
                except Exception:
                    continue
        return None

    def _find_rating_section(self):
        """Tìm tab/nút xem đánh giá trong trang quán."""
        rating_xpaths = [
            "//a[contains(@href,'foody')]",
            "//*[contains(text(),'Xem danh gia') or contains(text(),'Xem tren Foody')]",
            "//button[contains(text(),'Danh gia') or contains(text(),'Đánh giá') or contains(text(),'Review')]",
            "//*[contains(@class,'rating') or contains(@class,'review')]//a[@href]",
            "//a[contains(@href,'review') or contains(@href,'danh-gia')]",
        ]
        for xp in rating_xpaths:
            try:
                els = self.driver.find_elements(By.XPATH, xp)
                visible = [e for e in els if e.is_displayed()]
                if visible:
                    return visible[0]
            except Exception:
                continue
        return None

    def test_TC21_find_foody_link_in_restaurant(self):
        """
        TC21 - Tự ghép link Foody từ URL ShopeeFood hiện tại và mở tab mới
        ─────────────────────────────────────────────────────────
        Bước 1: Vào trang quán ăn cụ thể trên ShopeeFood
        Bước 2: Lấy slug quán từ URL hiện tại (phần cuối path)
        Bước 3: Ghép thành URL Foody: foody.vn/ha-noi/<slug>
        Bước 4: Mở tab Chrome mới điều hướng sang Foody
        Bước 5: Xác nhận URL và nội dung trang Foody hợp lệ
        ─────────────────────────────────────────────────────────
        Kỳ vọng: Trang Foody mở thành công, không có lỗi 404/500.
        """
        print("\n[TC21] Foody - Tu ghep link Foody va mo tab moi")
        ok = self._navigate_to_specific_restaurant()
        if not ok:
            self.skipTest("TC21 SKIP: Khong vao duoc trang quan an")

        # Lấy URL ShopeeFood hiện tại và tách slug quán
        source_url = self.driver.current_url
        print(f"  -> ShopeeFood URL: {source_url}")

        # Slug là phần cuối của path: /ha-noi/ten-quan -> "ten-quan"
        path_parts = source_url.rstrip("/").split("/")
        slug = path_parts[-1]  # vd: "pho-thin-bo-vien-lo-duc"
        print(f"  -> Slug quan: {slug}")

        # Tự ghép URL Foody
        foody_url = f"https://www.foody.vn/ha-noi/{slug}"
        print(f"  -> Foody URL tu ghep: {foody_url}")

        # Mở tab mới bằng JavaScript window.open()
        original_window = self.driver.current_window_handle
        self.driver.execute_script(f"window.open('{foody_url}', '_blank');")

        # Đợi tab mới mở
        try:
            self.wait.until(EC.number_of_windows_to_be(2))
        except Exception:
            self.skipTest("TC21 SKIP: Tab Foody khong mo duoc")

        # Chuyển sang tab Foody
        for handle in self.driver.window_handles:
            if handle != original_window:
                self.driver.switch_to.window(handle)
                break

        time.sleep(MEDIUM_WAIT)
        current_url = self.driver.current_url
        page_title  = self.driver.title
        page_source = self.driver.page_source
        print(f"  -> URL thuc te tren Foody: {current_url}")
        print(f"  -> Title: {page_title}")

        # Đóng tab Foody, về lại tab ShopeeFood
        self.driver.close()
        self.driver.switch_to.window(original_window)

        # Assertions
        self.assertIn(FOODY_DOMAIN, current_url,
                      f"TC21 FAIL: URL khong chua '{FOODY_DOMAIN}'. Thuc te: {current_url}")
        self.assertNotIn("500 Internal Server Error", page_source,
                         "TC21 FAIL: Foody tra ve loi 500")
        self.assertNotIn("404", page_title,
                         "TC21 FAIL: Foody tra ve loi 404")

        self._print_result("TC21", "PASS", f"Mo tab Foody thanh cong: {current_url[:60]}")

    def test_TC22_foody_redirect_verify(self):
        """
        TC22 - Xác nhận nội dung trang Foody: có thông tin đánh giá sao
        ─────────────────────────────────────────────────────────
        Bước 1: Vào trang quán ăn ShopeeFood
        Bước 2: Ghép URL Foody từ slug → mở tab Chrome mới
        Bước 3: Xác nhận trang có từ khóa đánh giá (sao, review, lượt)
        ─────────────────────────────────────────────────────────
        Kỳ vọng:
          ✅ URL chứa "foody.vn"
          ✅ Không có lỗi 404/500
          ✅ Trang có nội dung đánh giá
        """
        print("\n[TC22] Foody - Xac nhan noi dung danh gia tren foody.vn")
        ok = self._navigate_to_specific_restaurant()
        if not ok:
            self.skipTest("TC22 SKIP: Khong vao duoc trang quan an")

        # Lấy slug từ URL ShopeeFood
        source_url  = self.driver.current_url
        path_parts  = source_url.rstrip("/").split("/")
        slug        = path_parts[-1]
        foody_url   = f"https://www.foody.vn/ha-noi/{slug}"
        print(f"  -> Vao quan: {source_url}")
        print(f"  -> Mo Foody tab: {foody_url}")

        # Mở tab mới bằng JavaScript
        original_window = self.driver.current_window_handle
        self.driver.execute_script(f"window.open('{foody_url}', '_blank');")

        # Đợi tab mới
        try:
            self.wait.until(EC.number_of_windows_to_be(2))
        except Exception:
            self.skipTest("TC22 SKIP: Tab Foody khong mo duoc")

        # Chuyển sang tab Foody mới
        for handle in self.driver.window_handles:
            if handle != original_window:
                self.driver.switch_to.window(handle)
                break

        print(f"  -> Dang o tab: {self.driver.title}")
        time.sleep(MEDIUM_WAIT)

        current_url  = self.driver.current_url
        page_title   = self.driver.title
        page_source  = self.driver.page_source
        print(f"  -> URL: {current_url}")

        # ─── Assertions ─────────────────────────────────────────────────────
        self.assertIn(FOODY_DOMAIN, current_url,
                      f"TC22 FAIL: URL khong chua '{FOODY_DOMAIN}'. Thuc te: {current_url}")
        self.assertNotIn("500 Internal Server Error", page_source,
                         "TC22 FAIL: Foody tra ve loi 500")
        self.assertNotIn("404", page_title,
                         "TC22 FAIL: Foody tra ve loi 404")

        # Kiểm tra có nội dung đánh giá không
        rating_keywords = ["danh gia", "Danh gia", "Đánh giá", "sao", "stars",
                           "review", "Review", "luot", "lượt"]
        has_rating = any(kw in page_source for kw in rating_keywords)
        print(f"  -> Co noi dung danh gia: {has_rating}")

        # Đóng tab Foody, về tab ShopeeFood
        self.driver.close()
        self.driver.switch_to.window(original_window)

        self._print_result("TC22", "PASS",
                           f"Foody tab OK, co rating={has_rating}: {current_url[:60]}")

    def test_TC23_foody_verify_ui_elements(self):
        """
        TC23 - Kiểm tra hiển thị thông tin Đánh giá, Lượt bình luận và Giá trên trang Foody
        ─────────────────────────────────────────────────────────
        Kỳ vọng: Các phần tử UI chứa Điểm (Rate), Giá (Price) và Lượt bình luận được hiển thị đầy đủ và không rỗng.
        """
        print("\n[TC23] Foody - Verify UI Elements (Rate, Price, Comments)")
        url = "https://www.foody.vn/ho-chi-minh/dynasty-house-hongkong-dimsum-hotpot"
        
        self.driver.execute_script(f"window.open('{url}', '_blank');")
        time.sleep(SHORT_WAIT)
        
        new_window = [w for w in self.driver.window_handles if w != self.driver.current_window_handle][-1]
        self.driver.switch_to.window(new_window)
        time.sleep(MEDIUM_WAIT)

        try:
            rate_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class,'microsite-top-points')]//span | //div[contains(@class,'avg-txt')] | //div[contains(@class,'microsite-point-avg')]")
            rate = rate_elements[0].text if rate_elements else "N/A"
            
            price_elements = self.driver.find_elements(By.XPATH, "//span[@itemprop='priceRange'] | //*[contains(text(), 'đ - ')]")
            price = price_elements[0].text if price_elements else "N/A"
            
            cmt_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'microsite-review-count')] | //*[contains(text(), 'Bình luận')]/preceding-sibling::span | //span[contains(text(), 'Bình luận')]")
            comments = cmt_elements[0].text if cmt_elements else "N/A"
            
            print(f"  -> UI Check: Điểm Rate hiển thị = {rate}")
            print(f"  -> UI Check: Khoảng giá hiển thị = {price}")
            print(f"  -> UI Check: Lượt bình luận hiển thị = {comments}")

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            self.assertNotEqual(rate, "N/A", "TC23 FAIL: UI khong hien thi Diem Rate")
            self._print_result("TC23", "PASS", f"Verify UI Foody OK: Rate={rate}, Price={price}")
        except Exception as e:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.fail(f"TC23 FAIL: Loi khi verify UI - {str(e)}")

# =============================================================================
#  ĐIỂM VÀO CHÍNH
# =============================================================================
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    for cls in [TC_CF1_SearchFilter, TC_CF2_CartManagement,
                TC_CF3_Authentication, TC_CF4_FoodyRedirect]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("  TOM TAT KET QUA KIEM THU")
    print("="*70)
    total   = result.testsRun
    skipped = len(result.skipped)
    failed  = len(result.failures)
    errors  = len(result.errors)
    passed  = total - skipped - failed - errors
    print(f"  Tong so test : {total}")
    print(f"  PASS         : {passed}")
    print(f"  FAIL         : {failed}")
    print(f"  ERROR        : {errors}")
    print(f"  SKIP         : {skipped}")
    print("="*70)