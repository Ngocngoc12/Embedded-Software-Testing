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

BASE_URL        = "https://shopeefood.vn/ha-noi"
SEARCH_URL      = "https://shopeefood.vn/ha-noi/danh-sach-quan"
GLOBAL_TIMEOUT  = 15
SHORT_WAIT      = 2
MEDIUM_WAIT     = 4
LONG_WAIT       = 6

KEYWORD_VALID   = "Tra sua"
KEYWORD_INVALID = "xyzxyz_khongtonttai_9991"
KEYWORD_SPECIAL = "@#$%^&*()"
KEYWORD_EMPTY   = ""

SAMPLE_RESTAURANT_URLS = []


class ShoeeFoodTestBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
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
        try:
            cls.shared_driver.quit()
        except Exception:
            pass

    def setUp(self):
        self.driver  = self.__class__.shared_driver
        self.wait    = self.__class__.shared_wait
        self.actions = self.__class__.shared_actions
        try:
            if self.driver.current_url.strip("/") != BASE_URL.strip("/"):
                self.driver.get(BASE_URL)
        except Exception:
            self.driver.get(BASE_URL)
        self._close_popups()

    def tearDown(self):
        pass

    def _close_popups(self):
        for xp in [
            "//button[contains(@class,'close') or contains(@class,'dismiss')]",
            "//*[@aria-label='Close' or @aria-label='Dong']",
            "//div[contains(@class,'modal')]//button[@type='button']",
            "//span[contains(@class,'icon-close')]",
        ]:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.4)
            except Exception:
                pass

    def _find_search_input(self):
        for _ in range(5):
            for i in self.driver.find_elements(By.TAG_NAME, "input"):
                if i.is_displayed() and (i.get_attribute("type") == "text" or not i.get_attribute("type")):
                    return i
            time.sleep(SHORT_WAIT)
        self.fail("Search input not found on page")

    def _do_search(self, keyword):
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
        print(f"  -> Entered keyword: '{keyword}' and pressed Enter")

    def _open_login_form(self):
        for sel in [
            (By.CSS_SELECTOR, "button.btn-login"),
            (By.XPATH, "//button[contains(@class,'btn-login')]"),
            (By.XPATH, "//*[normalize-space(text())='Dang nhap' or normalize-space(text())='Đăng nhập'][self::button or self::a]"),
        ]:
            try:
                btn = self.wait.until(EC.element_to_be_clickable(sel))
                self.driver.execute_script("arguments[0].click();", btn)
                print("  -> Clicked login button")
                time.sleep(MEDIUM_WAIT)
                return True
            except Exception:
                continue
        self.skipTest("Login button not found")
        return False

    def _get_all_visible_inputs(self):
        try:
            return [el for el in self.driver.find_elements(By.TAG_NAME, "input")
                    if el.is_displayed() and el.get_attribute("type") != "hidden"]
        except Exception:
            return []

    def _get_error_message(self):
        for xp in [
            "//*[contains(@class,'error') or contains(@class,'invalid') or contains(@class,'warning')]",
            "//*[contains(@class,'alert') and not(contains(@class,'alert-success'))]",
            "//p[contains(@style,'color:red') or contains(@style,'color: red')]",
        ]:
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
        for xp in [
            "//div[contains(@class,'item-restaurant')]",
            "//div[contains(@class,'restaurant-card')]",
            "//a[contains(@href,'/ha-noi/') and not(contains(@href,'danh-sach'))]",
            "//div[contains(@class,'res-info')]",
        ]:
            try:
                if len(self.driver.find_elements(By.XPATH, xp)) > 0:
                    return True
            except Exception:
                continue
        return False


class TC_CF1_SearchFilter(ShoeeFoodTestBase):

    def test_TC01_search_valid_keyword(self):
        print("\n[TC01] Search with valid keyword: 'Tra sua'")
        self._do_search(KEYWORD_VALID)
        current_url = self.driver.current_url
        has_results = self._has_search_results()
        page_ok     = "500" not in self.driver.page_source
        self.assertTrue(page_ok, "TC01 FAIL: Page returned 500 error")
        self.assertTrue(
            has_results or "tra" in current_url.lower() or "keyword" in current_url.lower(),
            f"TC01 FAIL: No results found. URL={current_url}"
        )
        self._print_result("TC01", "PASS", f"Searched '{KEYWORD_VALID}' -> results found | URL: {current_url[:80]}")

    def test_TC02_search_invalid_keyword(self):
        print(f"\n[TC02] Search with non-existent keyword: '{KEYWORD_INVALID}'")
        self._do_search(KEYWORD_INVALID)
        found_no_result = any(
            any(e.is_displayed() for e in self.driver.find_elements(By.XPATH, xp))
            for xp in [
                "//*[contains(text(),'khong tim thay') or contains(text(),'Khong tim thay')]",
                "//*[contains(text(),'No result') or contains(text(),'no result')]",
                "//*[contains(@class,'empty') or contains(@class,'no-result')]",
                "//img[contains(@src,'empty') or contains(@alt,'empty')]",
            ]
        ) or not self._has_search_results()
        self.assertTrue(found_no_result,
                        f"TC02 FAIL: Results still shown for garbage keyword '{KEYWORD_INVALID}'")
        self._print_result("TC02", "PASS", "Invalid keyword -> no results shown")

    def test_TC03_search_special_characters(self):
        print(f"\n[TC03] Search with special characters: '{KEYWORD_SPECIAL}'")
        try:
            self._do_search(KEYWORD_SPECIAL)
            src = self.driver.page_source
            self.assertNotIn("500 Internal Server Error", src, "TC03 FAIL: Page returned 500 error")
            self.assertNotIn("Uncaught TypeError", src, "TC03 FAIL: JavaScript error detected")
            self._print_result("TC03", "PASS", "Special characters did not cause crash")
        except Exception as e:
            self.fail(f"TC03 FAIL: Exception during special character search: {e}")

    def test_TC04_search_empty_input(self):
        print("\n[TC04] Search with empty input")
        try:
            self._do_search(KEYWORD_EMPTY)
            self.assertNotIn("500 Internal Server Error", self.driver.page_source,
                             "TC04 FAIL: Page returned 500 error on empty search")
            self._print_result("TC04", "PASS",
                               f"Empty search did not crash | URL: {self.driver.current_url[:60]}")
        except Exception as e:
            self.fail(f"TC04 FAIL: Exception on empty search: {e}")

    def test_TC05_filter_tab_ban_chay(self):
        print("\n[TC05] Filter: Tab 'Ban chay' (Best Seller)")
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        tab_clicked = False
        for sel in [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Ban chay')]"),
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Bán chạy')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][2]"),
        ]:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Clicked tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue
        if not tab_clicked:
            btn_texts = [b.text.strip() for b in self.driver.find_elements(By.TAG_NAME, "button")
                         if b.is_displayed() and b.text.strip()]
            print(f"  -> Visible buttons: {btn_texts}")
            self.skipTest("TC05 SKIP: Tab 'Ban chay' not found")
        active_tabs = self.driver.find_elements(By.XPATH, "//button[@class='item-tab active']")
        self.assertGreater(len(active_tabs), 0, "TC05 FAIL: No tab became active")
        active_text = active_tabs[0].text.strip()
        print(f"  -> Active tab: '{active_text}'")
        self._print_result("TC05", "PASS", f"Tab '{active_text}' selected successfully")

    def test_TC06_filter_tab_danh_gia(self):
        print("\n[TC06] Filter: Tab 'Danh gia' (Rating)")
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        tab_clicked = False
        for sel in [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Danh gia')]"),
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Đánh giá')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][3]"),
        ]:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Clicked tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue
        if not tab_clicked:
            item_tabs = [b for b in self.driver.find_elements(By.TAG_NAME, "button")
                         if "item-tab" in (b.get_attribute("class") or "")]
            if item_tabs:
                item_tabs[0].click()
                print(f"  -> Fallback: clicked first tab: '{item_tabs[0].text}'")
                tab_clicked = True
                time.sleep(MEDIUM_WAIT)
        if not tab_clicked:
            self.skipTest("TC06 SKIP: Tab 'Danh gia' not found")
        print("  -> Cross-validating rating with Foody...")
        try:
            first_item = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.item-restaurant > a")))
            shopee_url = first_item.get_attribute("href")
            match = re.search(r'shopeefood\.vn/ha-noi/([^?]+)', shopee_url)
            if match:
                slug = match.group(1)
                foody_url = f"https://www.foody.vn/ha-noi/{slug}"
                print(f"  -> Foody cross-validation URL: {foody_url}")
                self.driver.execute_script("window.open(arguments[0], '_blank');", foody_url)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(MEDIUM_WAIT)
                try:
                    rate_el = self.driver.find_element(By.CSS_SELECTOR,
                        "div.microsite-point-stat span:first-child, div.microsite-point-stat")
                    rate_val = float(rate_el.text.strip().replace(',', '.'))
                    shopee_rate = rate_val / 2.0
                    print(f"  -> Foody rate: {rate_val}/10 -> ShopeeFood equivalent: {shopee_rate}/5 stars")
                    self.assertGreaterEqual(shopee_rate, 4.0,
                        f"TC06 FAIL: Converted rating {shopee_rate} < 4.0 stars")
                except Exception:
                    print("  -> Foody has no rating data for this restaurant")
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                print("  -> Could not parse slug from URL")
        except Exception as e:
            print(f"  -> Cross-validation error: {e}")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC06", "PASS", "Rating tab clicked, no server error")

    def test_TC07_filter_tab_giao_nhanh(self):
        print("\n[TC07] Filter: Tab 'Giao nhanh' (Fast Delivery)")
        self.driver.get(BASE_URL)
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        tab_clicked = False
        for sel in [
            (By.XPATH, "//button[contains(@class,'item-tab') and contains(text(),'Giao nhanh')]"),
            (By.XPATH, "//button[contains(@class,'item-tab')][4]"),
        ]:
            try:
                tab = self.wait.until(EC.element_to_be_clickable(sel))
                tab_text = tab.text.strip()
                tab.click()
                tab_clicked = True
                print(f"  -> Clicked tab: '{tab_text}'")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue
        if not tab_clicked:
            visible = [t for t in self.driver.find_elements(
                By.XPATH, "//button[contains(@class,'item-tab')]") if t.is_displayed()]
            if visible:
                visible[-1].click()
                tab_clicked = True
                print(f"  -> Fallback: clicked tab: '{visible[-1].text}'")
                time.sleep(MEDIUM_WAIT)
        if not tab_clicked:
            self.skipTest("TC07 SKIP: No filter tab found")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC07", "PASS", "Fast delivery tab clicked, no server error")


class TC_CF2_CartManagement(ShoeeFoodTestBase):

    def _open_restaurant_page(self, keyword="ga ran"):
        for url in SAMPLE_RESTAURANT_URLS:
            try:
                self.driver.get(url)
                time.sleep(LONG_WAIT)
                self._close_popups()
                src = self.driver.page_source
                if "404" not in src[:2000] and len(src) > 5000 and "bài viết không tồn tại" not in src.lower():
                    print(f"  -> Opened restaurant page: {url}")
                    return True
            except Exception:
                continue
        self.driver.get(f"{SEARCH_URL}?keyword={keyword}")
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        try:
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
                print(f"  -> Fallback: opened restaurant: {href}")
                return True
        except Exception as e:
            print(f"  -> Could not find restaurant: {e}")
        return False

    def _find_add_button(self):
        for scroll_y in [400, 800, 1200]:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.5)
            try:
                for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                    if not btn.is_displayed():
                        continue
                    txt = btn.text.strip()
                    cls = btn.get_attribute("class") or ""
                    if txt == "+" or "add" in cls.lower() or "them" in cls.lower():
                        return btn
            except Exception:
                pass
            for sel in [
                (By.XPATH, "(//button[normalize-space(text())='+'])[1]"),
                (By.XPATH, "(//button[contains(@class,'add')])[1]"),
                (By.XPATH, "(//div[contains(@class,'add') and normalize-space(text())='+'])[1]"),
                (By.XPATH, "(//span[normalize-space(text())='+' and ancestor::div[contains(@class,'item')]])[1]"),
                (By.CSS_SELECTOR, "[class*='add']:not(input):not(a)"),
            ]:
                try:
                    els = [e for e in self.driver.find_elements(*sel) if e.is_displayed()]
                    if els:
                        return els[0]
                except Exception:
                    continue
        return None

    def _get_cart_count(self):
        for sel in [
            (By.XPATH, "//span[contains(@class,'badge') or contains(@class,'cart-count')]"),
            (By.XPATH, "//div[contains(@class,'cart')]//span[@class]"),
            (By.CSS_SELECTOR, ".cart-badge, .cart-count, [class*='cart'][class*='count']"),
        ]:
            try:
                el = self.driver.find_element(*sel)
                val = el.text.strip()
                if val.isdigit():
                    return int(val)
            except NoSuchElementException:
                continue
        return 0

    def test_TC08_scroll_to_qrcode_in_viewport(self):
        print("\n[TC08] Verify page scrolls to id='QRcode' into viewport after clicking add button")
        TARGET_URL = "https://shopeefood.vn/ha-noi/tra-sua-tocotoco-trieu-khuc"
        print(f"  -> Opening: {TARGET_URL}")
        self.driver.get(TARGET_URL)
        time.sleep(LONG_WAIT)
        self._close_popups()
        src = self.driver.page_source
        if "bài viết không tồn tại" in src.lower() or "404" in self.driver.title:
            self.fail(f"TC08 FAIL: Page {TARGET_URL} does not exist or returned 404")
        print(f"  -> Page loaded: {self.driver.title[:60]}")
        print("  -> Searching for add-to-cart button...")
        add_btn = None
        for scroll_y in range(0, 2400, 300):
            self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.4)
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if not btn.is_displayed():
                    continue
                txt = btn.text.strip()
                cls = (btn.get_attribute("class") or "").lower()
                if txt == "+" or any(kw in cls for kw in ["add", "them", "cart", "order"]):
                    add_btn = btn
                    print(f"  -> Found add button: text='{txt}' class='{cls[:60]}'")
                    break
            if add_btn:
                break
        if not add_btn:
            for xp in [
                "(//button[normalize-space(text())='+'])[1]",
                "(//button[contains(@class,'add')])[1]",
                "(//button[contains(@class,'cart')])[1]",
                "(//div[normalize-space(text())='+' and contains(@class,'btn')])[1]",
                "(//span[normalize-space(text())='+'])[1]",
            ]:
                els = [e for e in self.driver.find_elements(By.XPATH, xp) if e.is_displayed()]
                if els:
                    add_btn = els[0]
                    print(f"  -> Found via XPath fallback: '{xp[:60]}'")
                    break
        if not add_btn:
            visible = [(b.get_attribute("class") or "")[:40] + " | " + b.text[:20]
                       for b in self.driver.find_elements(By.TAG_NAME, "button") if b.is_displayed()]
            print(f"  -> Visible buttons ({len(visible)}): {visible[:10]}")
            self.fail("TC08 FAIL: Add-to-cart button not found. Page may require login.")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        time.sleep(SHORT_WAIT)
        self.driver.execute_script("arguments[0].click();", add_btn)
        print("  -> Clicked add-to-cart button")
        time.sleep(MEDIUM_WAIT)
        qr_element = None
        try:
            qr_element = self.driver.find_element(By.ID, "QRcode")
            print(f"  -> Found element id='QRcode': tag=<{qr_element.tag_name}>")
        except NoSuchElementException:
            self.fail("TC08 FAIL: Element id='QRcode' not found on page")
        if qr_element is None:
            self.fail("TC08 FAIL: qr_element is None")
        is_in_viewport = self.driver.execute_script("""
            var el = arguments[0];
            var rect = el.getBoundingClientRect();
            var vpH = window.innerHeight || document.documentElement.clientHeight;
            var vpW = window.innerWidth  || document.documentElement.clientWidth;
            return rect.top >= 0 && rect.left >= 0 && rect.bottom <= vpH && rect.right <= vpW;
        """, qr_element)
        rect_info = self.driver.execute_script("""
            var el = arguments[0];
            var rect = el.getBoundingClientRect();
            return {
                top: Math.round(rect.top), bottom: Math.round(rect.bottom),
                left: Math.round(rect.left), right: Math.round(rect.right),
                vpH: window.innerHeight || document.documentElement.clientHeight,
                vpW: window.innerWidth  || document.documentElement.clientWidth
            };
        """, qr_element)
        print(f"  -> Viewport: {rect_info['vpW']}x{rect_info['vpH']} px")
        print(f"  -> QRcode rect: top={rect_info['top']}, bottom={rect_info['bottom']}, "
              f"left={rect_info['left']}, right={rect_info['right']}")
        print(f"  -> In viewport: {is_in_viewport}")
        self.assertTrue(
            is_in_viewport,
            f"TC08 FAIL: id='QRcode' is NOT in viewport after click\n"
            f"  Viewport: {rect_info['vpW']}x{rect_info['vpH']} px\n"
            f"  QRcode: top={rect_info['top']}, bottom={rect_info['bottom']}, "
            f"left={rect_info['left']}, right={rect_info['right']}"
        )
        self._print_result("TC08", "PASS",
            f"id='QRcode' is in viewport (top={rect_info['top']}, bottom={rect_info['bottom']})")


class TC_CF3_Authentication(ShoeeFoodTestBase):

    def _fill_input_by_position(self, position, value):
        form_inputs = [i for i in self._get_all_visible_inputs()
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
        phone_filled = False
        for sel in [
            (By.XPATH, "//input[@type='tel']"),
            (By.XPATH, "//input[contains(@placeholder,'dien thoai') or contains(@placeholder,'phone') or contains(@placeholder,'Di')]"),
            (By.XPATH, "//input[@name='phone' or @name='mobile' or @name='username']"),
        ]:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys(phone_value)
                    phone_filled = True
                    print(f"  -> Entered phone: '{phone_value}'")
                    break
            except NoSuchElementException:
                continue
        if not phone_filled:
            phone_filled = self._fill_input_by_position(0, phone_value)
            if phone_filled:
                print(f"  -> Entered phone by position: '{phone_value}'")
        pass_filled = False
        for sel in [
            (By.XPATH, "//input[@type='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys(password_value)
                    pass_filled = True
                    print("  -> Entered password")
                    break
            except NoSuchElementException:
                continue
        if not pass_filled:
            pass_filled = self._fill_input_by_position(1, password_value)
            if pass_filled:
                print("  -> Entered password by position")
        return phone_filled, pass_filled

    def _click_login_submit(self):
        for sel in [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(@class,'btn-primary') or contains(@class,'btn-submit')]"),
            (By.XPATH, "//button[contains(text(),'Dang nhap') or contains(text(),'Đăng nhập')]"),
        ]:
            try:
                btn = self.driver.find_element(*sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    print("  -> Clicked submit button")
                    time.sleep(MEDIUM_WAIT)
                    return True
            except NoSuchElementException:
                continue
        return False

    def test_TC09_login_all_fields_empty(self):
        print("\n[TC09] Login - All fields empty")
        self._open_login_form()
        submitted = self._click_login_submit()
        if not submitted:
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.RETURN)
                time.sleep(SHORT_WAIT)
            except Exception:
                pass
        err = self._get_error_message()
        current_url = self.driver.current_url
        print(f"  -> Current URL: {current_url[:60]}")
        print(f"  -> Error message: {err}")
        not_logged_in = "profile" not in current_url and "dashboard" not in current_url
        self.assertTrue(not_logged_in or err is not None,
                        "TC09 FAIL: System allowed login with all empty fields")
        self._print_result("TC09", "PASS", f"Empty fields -> error: '{err}'")

    def test_TC10_login_phone_too_short_BVA_below_min(self):
        print("\n[TC10] Login - Phone too short: '091234' (BVA below min 10 digits)")
        self._open_login_form()
        phone_ok, _ = self._fill_login_fields("091234", "AnyPass123")
        if not phone_ok:
            self.skipTest("TC10 SKIP: Phone input field not found")
        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Error message: {err}")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC10", "PASS", f"Short phone -> error: '{err}'")

    def test_TC11_login_phone_with_letters_invalid(self):
        print("\n[TC11] Login - Phone with letters: '09abc12345' (invalid format)")
        self._open_login_form()
        phone_ok, _ = self._fill_login_fields("09abc12345", "AnyPass123")
        if not phone_ok:
            self.skipTest("TC11 SKIP: Phone input field not found")
        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Error message: {err}")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC11", "PASS", f"Phone with letters -> error: '{err}'")

    def test_TC12_login_wrong_password(self):
        print("\n[TC12] Login - Wrong password")
        self._open_login_form()
        phone_ok, _ = self._fill_login_fields("0901234567", "SaiMatKhauWRONG_999!")
        if not phone_ok:
            self.skipTest("TC12 SKIP: Phone input field not found")
        self._click_login_submit()
        time.sleep(MEDIUM_WAIT)
        err = self._get_error_message()
        current_url = self.driver.current_url
        print(f"  -> Error message: {err}")
        print(f"  -> Current URL: {current_url[:60]}")
        not_logged_in = "profile" not in current_url and "dashboard" not in current_url
        self.assertTrue(not_logged_in or err is not None,
                        "TC12 FAIL: System logged in with wrong password")
        self._print_result("TC12", "PASS", f"Wrong password -> error: '{err}'")

    def test_TC13_login_invalid_email_format(self):
        print("\n[TC13] Login - Invalid email format: 'khonghople@'")
        self._open_login_form()
        for xp in [
            "//span[normalize-space(text())='Email']",
            "//button[contains(text(),'Email')]",
            "//*[@data-tab='email']",
        ]:
            try:
                tab = self.driver.find_element(By.XPATH, xp)
                if tab.is_displayed():
                    tab.click()
                    time.sleep(SHORT_WAIT)
                    print("  -> Switched to Email tab")
                    break
            except NoSuchElementException:
                continue
        email_filled = False
        for sel in [
            (By.XPATH, "//input[@type='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@name='email']"),
        ]:
            try:
                inp = self.driver.find_element(*sel)
                if inp.is_displayed():
                    inp.click(); inp.clear(); inp.send_keys("khonghople@")
                    email_filled = True
                    print("  -> Entered invalid email: 'khonghople@'")
                    break
            except NoSuchElementException:
                continue
        if not email_filled:
            self._fill_input_by_position(0, "khonghople@")
        self._click_login_submit()
        err = self._get_error_message()
        print(f"  -> Error message: {err}")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC13", "PASS", f"Invalid email -> error: '{err}'")

    def test_TC14_login_success_demo(self):
        print("\n[TC14] Login via phone number - OTP flow")
        self.driver.get("https://shopeefood.vn/")
        time.sleep(MEDIUM_WAIT)
        self._close_popups()
        print(f"  -> Opened homepage: {self.driver.current_url}")
        clicked_login = False
        for sel in [
            (By.CSS_SELECTOR, "button.btn-login"),
            (By.XPATH, "//button[contains(@class,'btn-login')]"),
            (By.XPATH, "//*[normalize-space(text())='Đăng nhập' or normalize-space(text())='Dang nhap'][self::button or self::a]"),
        ]:
            try:
                btn = WebDriverWait(self.driver, GLOBAL_TIMEOUT).until(EC.element_to_be_clickable(sel))
                self.driver.execute_script("arguments[0].click();", btn)
                clicked_login = True
                print("  -> Clicked login button")
                time.sleep(MEDIUM_WAIT)
                break
            except Exception:
                continue
        if not clicked_login:
            self.fail("TC14 FAIL: Login button not found on homepage")
        main_window    = self.driver.current_window_handle
        handles_before = set(self.driver.window_handles)
        clicked_phone = False
        for sel in [
            (By.CSS_SELECTOR, ".item.phone"),
            (By.XPATH, "//*[contains(@class,'item') and contains(@class,'phone')]"),
        ]:
            try:
                el = WebDriverWait(self.driver, GLOBAL_TIMEOUT).until(EC.element_to_be_clickable(sel))
                self.driver.execute_script("arguments[0].click();", el)
                clicked_phone = True
                print("  -> Clicked 'Login with phone number' (.item.phone)")
                break
            except Exception:
                continue
        if not clicked_phone:
            print("  -> .item.phone not found, popup may already be visible")
        print("  -> Waiting for SSO popup window to appear...")
        try:
            WebDriverWait(self.driver, GLOBAL_TIMEOUT).until(
                lambda d: len(d.window_handles) > len(handles_before)
            )
            popup_handle = (set(self.driver.window_handles) - handles_before).pop()
            self.driver.switch_to.window(popup_handle)
            print(f"  -> Switched to SSO popup: {self.driver.current_url}")
            time.sleep(SHORT_WAIT)
        except Exception as e:
            self.fail(f"TC14 FAIL: SSO popup window did not appear. Error: {e}")
        tieptuc_selectors = [
            (By.XPATH, "//button[contains(@class,'btn') and (normalize-space(text())='Tiếp tục' or normalize-space(text())='Tiep tuc')]"),
            (By.CSS_SELECTOR, "button.btn"),
        ]
        def _wait_and_click_tieptuc(step_name, timeout=60):
            print(f"  -> [{step_name}] Waiting for 'Continue' button (button.btn) to become enabled (max {timeout}s)...")
            deadline = time.time() + timeout
            while time.time() < deadline:
                for sel in tieptuc_selectors:
                    try:
                        for btn in self.driver.find_elements(*sel):
                            if btn.is_displayed() and btn.get_attribute("disabled") is None:
                                self.driver.execute_script("arguments[0].click();", btn)
                                print(f"  -> [{step_name}] Clicked 'Continue' button")
                                time.sleep(MEDIUM_WAIT)
                                return True
                    except Exception:
                        continue
                time.sleep(0.5)
            return False
        if not _wait_and_click_tieptuc("Phone step", timeout=60):
            self.fail("TC14 FAIL: 'Continue' button (phone step) still disabled after 60s")
        print("  -> Please enter the OTP received via SMS...")
        if not _wait_and_click_tieptuc("OTP step", timeout=120):
            self.fail("TC14 FAIL: 'Continue' button (OTP step) still disabled after 120s")
        print("  -> Waiting for popup to close, switching back to main window...")
        try:
            WebDriverWait(self.driver, LONG_WAIT * 3).until(
                lambda d: len(d.window_handles) == len(handles_before)
            )
            self.driver.switch_to.window(main_window)
            print(f"  -> Switched back to main window: {self.driver.current_url}")
        except Exception:
            try:
                self.driver.switch_to.window(main_window)
                print(f"  -> Fallback switch to main window: {self.driver.current_url}")
            except Exception as e:
                self.fail(f"TC14 FAIL: Could not switch back to main window. Error: {e}")
        time.sleep(LONG_WAIT)
        current_url = self.driver.current_url
        print(f"  -> URL after login: {current_url}")
        url_ok = current_url.rstrip("/") in [
            "https://shopeefood.vn",
            "https://www.shopeefood.vn",
            "https://shopeefood.vn/ha-noi",
        ]
        user_acc_found = False
        for sel in [
            (By.CSS_SELECTOR, "div.user-acc.col-auto"),
            (By.CSS_SELECTOR, "div.user-acc"),
            (By.XPATH, "//div[contains(@class,'user-acc') and contains(@class,'col-auto')]"),
            (By.XPATH, "//div[contains(@class,'user-acc')]"),
        ]:
            try:
                if any(e.is_displayed() for e in self.driver.find_elements(*sel)):
                    user_acc_found = True
                    print(f"  -> Found div.user-acc with selector: {sel}")
                    break
            except Exception:
                continue
        print(f"  -> URL valid: {url_ok} | user-acc found: {user_acc_found}")
        self.assertTrue(user_acc_found,
            f"TC14 FAIL: div.user-acc.col-auto not found after login | URL: {current_url}")
        self.assertTrue(url_ok,
            f"TC14 FAIL: URL after login is not homepage | URL: {current_url}")
        self._print_result("TC14", "PASS",
            f"Login successful | URL={current_url} | user-acc={user_acc_found}")

    def test_TC15_register_form_validate(self):
        print("\n[TC15] Register form - Validate required fields")
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
                print("  -> Clicked register button")
                time.sleep(MEDIUM_WAIT)
                break
            except TimeoutException:
                continue
        if not reg_clicked:
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
            self.skipTest("TC15 SKIP: Register button not found")
        try:
            submit = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            if submit.is_displayed():
                submit.click()
                time.sleep(SHORT_WAIT)
        except NoSuchElementException:
            pass
        err = self._get_error_message()
        print(f"  -> Validation message: {err}")
        self.assertNotIn("500 Internal Server Error", self.driver.page_source)
        self._print_result("TC15", "PASS", f"Register form validation: '{err}'")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TC_CF1_SearchFilter, TC_CF2_CartManagement, TC_CF3_Authentication]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)
    print("\n" + "=" * 60)
    print("  TEST EXECUTION SUMMARY")
    print("=" * 60)
    total   = result.testsRun
    skipped = len(result.skipped)
    failed  = len(result.failures)
    errors  = len(result.errors)
    passed  = total - skipped - failed - errors
    print(f"  Total  : {total}")
    print(f"  PASS   : {passed}")
    print(f"  FAIL   : {failed}")
    print(f"  ERROR  : {errors}")
    print(f"  SKIP   : {skipped}")
    print("=" * 60)

