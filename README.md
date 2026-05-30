# Bộ Test Tự Động ShopeeFood

Kiểm thử giao diện người dùng tự động cho [ShopeeFood Việt Nam](https://shopeefood.vn) sử dụng **Python + Selenium WebDriver + unittest**, có thể chạy bằng **pytest**.

---

## Cấu Trúc Dự Án

```
Embedded-Software-Testing/
├── ShopeeFood_Automation_Test.py   # File test chính (15 test case)
└── README.md
```

---

## Công Nghệ Sử Dụng

| Thành phần | Chi tiết |
|---|---|
| Ngôn ngữ | Python 3.10+ |
| Framework kiểm thử | `unittest` (tương thích pytest) |
| Tự động hóa trình duyệt | Selenium WebDriver (Chrome) |
| Công cụ chạy test | `pytest` |
| Báo cáo | `pytest-html` |

---

## Cài Đặt

```bash
pip install selenium pytest pytest-html
```

> ChromeDriver phải khớp với phiên bản Chrome đang cài đặt.  
> Tải tại: https://chromedriver.chromium.org/downloads

---

## Chạy Test

### Chạy toàn bộ test case
```bash
python -m pytest ShopeeFood_Automation_Test.py -v --tb=short
```

### Chạy một class cụ thể
```bash
python -m pytest ShopeeFood_Automation_Test.py::TC_CF1_SearchFilter -v
python -m pytest ShopeeFood_Automation_Test.py::TC_CF2_CartManagement -v
python -m pytest ShopeeFood_Automation_Test.py::TC_CF3_Authentication -v
```

### Chạy một test case cụ thể
```bash
python -m pytest ShopeeFood_Automation_Test.py::TC_CF3_Authentication::test_TC14_login_success_demo -v -s
```

### Lọc theo từ khóa
```bash
python -m pytest ShopeeFood_Automation_Test.py -k "TC08" -v -s
```

### Xuất báo cáo HTML
```bash
python -m pytest ShopeeFood_Automation_Test.py -v --html=report.html --self-contained-html
```

### Hiển thị output print trong terminal
```bash
python -m pytest ShopeeFood_Automation_Test.py -v -s --tb=long
```

---

## Các Test Case

### CF1 — Tìm kiếm & Lọc (`TC_CF1_SearchFilter`)

| TC | Phương thức | Mô tả | Kỹ thuật | Kết quả mong đợi |
|---|---|---|---|---|
| TC01 | `test_TC01_search_valid_keyword` | Tìm kiếm "Trà sữa" | Phân hoạch tương đương (hợp lệ) | Có kết quả, không có lỗi 500 |
| TC02 | `test_TC02_search_invalid_keyword` | Tìm từ khóa không tồn tại | Phân hoạch tương đương (không hợp lệ) | Không có kết quả / hiển thị trạng thái trống |
| TC03 | `test_TC03_search_special_characters` | Tìm kiếm `@#$%^&*()` | Biên — ký tự đặc biệt | Không crash, không có lỗi JS |
| TC04 | `test_TC04_search_empty_input` | Tìm kiếm với ô trống | Biên — giá trị rỗng | Không crash, không có lỗi 500 |
| TC05 | `test_TC05_filter_tab_ban_chay` | Bấm tab "Bán chạy" | Kiểm thử chức năng | Tab được kích hoạt |
| TC06 | `test_TC06_filter_tab_danh_gia` | Bấm tab "Đánh giá" + đối chiếu Foody | Chức năng + Đối chiếu chéo | Tab active, đánh giá ≥ 4.0/5 |
| TC07 | `test_TC07_filter_tab_giao_nhanh` | Bấm tab "Giao nhanh" | Kiểm thử chức năng | Tab active, không có lỗi |

---

### CF2 — Giỏ hàng / Tương tác UI (`TC_CF2_CartManagement`)

| TC | Phương thức | Mô tả | Kỹ thuật | Kết quả mong đợi |
|---|---|---|---|---|
| TC08 | `test_TC08_scroll_to_qrcode_in_viewport` | Bấm thêm vào giỏ, kiểm tra `id="QRcode"` cuộn vào viewport | Chức năng — Hành vi cuộn trang | `#QRcode` hiển thị đầy đủ trong viewport |

**URL mục tiêu cho TC08:**
```
https://shopeefood.vn/ha-noi/tra-sua-tocotoco-trieu-khuc
```

**Kiểm tra viewport bằng JavaScript `getBoundingClientRect()`:**
```
rect.top >= 0 VÀ rect.left >= 0
VÀ rect.bottom <= viewportHeight VÀ rect.right <= viewportWidth
```

---

### CF3 — Xác thực (`TC_CF3_Authentication`)

| TC | Phương thức | Mô tả | Đầu vào | Kết quả mong đợi |
|---|---|---|---|---|
| TC09 | `test_TC09_login_all_fields_empty` | Gửi form đăng nhập khi tất cả ô trống | (rỗng) | Hiển thị lỗi xác thực |
| TC10 | `test_TC10_login_phone_too_short_BVA_below_min` | Số điện thoại quá ngắn (BVA dưới min) | `091234` (6 chữ số) | Lỗi: số điện thoại không hợp lệ |
| TC11 | `test_TC11_login_phone_with_letters_invalid` | Số điện thoại chứa chữ cái (EP lớp không hợp lệ) | `09abc12345` | Lỗi: định dạng không hợp lệ |
| TC12 | `test_TC12_login_wrong_password` | Sai mật khẩu | `0901234567` + sai mật khẩu | Lỗi: thông tin đăng nhập sai |
| TC13 | `test_TC13_login_invalid_email_format` | Định dạng email sai (EP không hợp lệ) | `khonghople@` | Lỗi: email không hợp lệ |
| TC14 | `test_TC14_login_success_demo` | Luồng đăng nhập OTP đầy đủ (người dùng nhập thủ công) | SĐT thật + OTP | `div.user-acc` xuất hiện, URL = trang chủ |
| TC15 | `test_TC15_register_form_validate` | Gửi form đăng ký khi tất cả ô trống | (rỗng) | Hiển thị lỗi xác thực |

---

## Kiến Trúc

### Phiên Chrome Dùng Chung

Mỗi class test chỉ mở Chrome **một lần** qua `setUpClass` và dùng lại cho tất cả các phương thức test — tránh overhead khởi động trình duyệt mới cho từng test.

```
setUpClass()        ← Mở Chrome một lần cho mỗi class
  setUp()           ← Reset về BASE_URL trước mỗi test
    test_TCxx()     ← Thực thi test
  tearDown()        ← Không làm gì (giữ trình duyệt mở)
tearDownClass()     ← Đóng Chrome sau khi chạy hết test trong class
```

### Các Hàm Hỗ Trợ Base Class

| Hàm hỗ trợ | Mục đích |
|---|---|
| `_close_popups()` | Đóng các popup quảng cáo / vị trí |
| `_find_search_input()` | Tìm ô `<input>` tìm kiếm (polling, thử 5 lần) |
| `_do_search(keyword)` | Nhập từ khóa và nhấn Enter |
| `_open_login_form()` | Bấm nút đăng nhập, chờ form xuất hiện |
| `_get_all_visible_inputs()` | Lấy tất cả ô input đang hiển thị |
| `_get_error_message()` | Trích xuất thông báo lỗi từ DOM |
| `_has_search_results()` | Kiểm tra có thẻ kết quả không |
| `_print_result(tc_id, status, detail)` | In `[PASS/FAIL/SKIP] [TCxx] chi tiết` |

### TC14 — Chi Tiết Luồng Đăng Nhập OTP

```
driver.get("https://shopeefood.vn/")
  ↓
Bấm btn-login
  ↓
Bấm .item.phone  →  Cửa sổ popup mới mở ra (gsso.shopeefood.vn/sms_login)
  ↓
switch_to.window(popup_handle)
  ↓
[Bước SĐT] Kiểm tra button.btn mỗi 0.5s (tối đa 60s)
  Người dùng nhập số điện thoại → thuộc tính disabled bị xóa → click
  ↓
[Bước OTP] Kiểm tra button.btn mỗi 0.5s (tối đa 120s)
  Người dùng nhập OTP → thuộc tính disabled bị xóa → click
  ↓
Popup đóng → switch_to.window(main_window)
  ↓
Kiểm tra: div.user-acc.col-auto hiển thị VÀ URL = shopeefood.vn
```

---

## Cấu Hình

Chỉnh sửa các hằng số ở đầu file `ShopeeFood_Automation_Test.py`:

```python
BASE_URL        = "https://shopeefood.vn/ha-noi"
SEARCH_URL      = "https://shopeefood.vn/ha-noi/danh-sach-quan"
GLOBAL_TIMEOUT  = 15   # giây — timeout của WebDriverWait
SHORT_WAIT      = 2    # giây
MEDIUM_WAIT     = 4    # giây
LONG_WAIT       = 6    # giây

KEYWORD_VALID   = "Tra sua"
KEYWORD_INVALID = "xyzxyz_khongtonttai_9991"
KEYWORD_SPECIAL = "@#$%^&*()"
KEYWORD_EMPTY   = ""

SAMPLE_RESTAURANT_URLS = []   # thêm URL nhà hàng đã biết cho các test CF2
```

---

## Định Dạng Log

Tất cả output in ra theo định dạng nhất quán:

```
[TCxx] <mô tả test>
  -> <bước hoặc thông tin>
  -> <bước hoặc thông tin>
  [PASS/FAIL/SKIP] [TCxx] <chi tiết kết quả>
```

**Ví dụ output:**
```
[TC08] Verify page scrolls to id='QRcode' into viewport after clicking add button
  -> Opening: https://shopeefood.vn/ha-noi/tra-sua-tocotoco-trieu-khuc
  -> Page loaded: Trà Sữa ToCoToCo Triệu Khúc
  -> Searching for add-to-cart button...
  -> Found add button: text='+' class='btn-add-item'
  -> Clicked add-to-cart button
  -> Found element id='QRcode': tag=<div>
  -> Viewport: 1920x1080 px
  -> QRcode rect: top=200, bottom=400, left=100, right=300
  -> In viewport: True
  [PASS] [TC08] id='QRcode' is in viewport (top=200, bottom=400)
```

---

## Điều Kiện PASS / FAIL / SKIP

| Kết quả | Điều kiện kích hoạt |
|---|---|
| **PASS** | Phương thức test chạy bình thường (không có ngoại lệ) |
| **FAIL** | `self.fail("thông báo")` hoặc `self.assertX(...)` ném `AssertionError` |
| **SKIP** | `self.skipTest("lý do")` ném `SkipTest` |

---

## Lưu Ý

- **Chế độ headless bị tắt** — ShopeeFood trả về lỗi 403 với Chrome headless.
- **TC08** yêu cầu trang nhà hàng hiển thị nút thêm vào giỏ hàng. Nếu cần đăng nhập, test sẽ FAIL kèm thông báo rõ ràng.
- **TC14** yêu cầu người dùng tương tác thủ công: nhập số điện thoại và OTP trong khoảng thời gian chờ (60 giây và 120 giây tương ứng).
- **TC06** thực hiện đối chiếu chéo bằng cách mở tab Foody.vn. Nếu Foody không có dữ liệu cho nhà hàng đó, bước này sẽ được bỏ qua.
- **`SAMPLE_RESTAURANT_URLS`** mặc định là rỗng. Thêm các URL nhà hàng ShopeeFood hợp lệ vào đây để tăng độ ổn định của test CF2.
