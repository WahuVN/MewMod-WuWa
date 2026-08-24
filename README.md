# MewMod WuWa

<p align="center">
  <img src="./app_icon.png" width="120" height="120" alt="MewMod WuWa Logo" style="border-radius: 18px;"><br><br>
  <b>A Comprehensive Mod Management and Deployment Platform for Wuthering Waves</b><br>
  <i>Hệ thống quản lý, cấu hình và tối ưu hóa bản mod cho tựa game Wuthering Waves</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows_10%2F11-blue?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Version-4.1.0-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/Language-Python_%2F_WebView2-orange?style=flat-square" alt="Tech">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="License">
</p>

---

## 1. Giới thiệu tổng quan

**MewMod WuWa** là giải pháp phần mềm chuyên dụng hỗ trợ quản lý, tải xuống, cấu hình và xử lý xung đột cho các bản mod của tựa game **Wuthering Waves (鸣潮)**. Ứng dụng tích hợp trực tiếp với bộ khung nạp mod **WWMI (3DMigoto)**, cung cấp khả năng kiểm soát tập trung, tự động vá lỗi shader/mesh sau các đợt cập nhật trò chơi, cùng hệ thống duyệt mod trực tuyến đa nguồn tốc độ cao.

---

## 2. Tính năng chính

### 🛡️ Cơ chế kiểm soát xung đột (Single-Active Mod Allocation)
* **Triệt tiêu xung đột đa giác**: Tự động vô hiệu hóa các bản mod cùng loại khi một bản mod mới được kích hoạt, loại bỏ hoàn toàn hiện tượng chồng lấn đa giác (mesh overlap), sai lệch vân phủ hoặc crash game.
* **Quản lý biến phụ kiện (`mod.ini`)**: Tự động phân tích các biến chuyển đổi trạng thái và khối gán phím nóng (`[Key...]`), cho phép cấu hình trực tiếp trên giao diện và áp dụng tức thì vào game.

### 🚀 Tự động kiểm tra và cập nhật phiên bản (In-App Auto-Updater)
* Tự động đồng bộ với kho lưu trữ GitHub chính thức khi khởi chạy.
* Hiển thị chi tiết nhật ký cập nhật (Changelog) và hỗ trợ tải bản phát hành mới nhất với một thao tác.

### 🔧 Bộ công cụ chuẩn hóa & sửa lỗi mod tích hợp (WuWa Mod Fixer)
* Tích hợp bộ quy tắc vá cấu trúc Vertex Shader phiên bản 3.6.0:
  * **Cập nhật Hash trạng thái dẫn xuất (Derived Hashes)**: Tự động vá các hash trạng thái phụ (LOD Bias, trạng thái ướt, kỹ năng kích hoạt...) nhằm đảm bảo tính toàn vẹn của model.
  * **Ổn định bề mặt vân phủ (Stable Texture)**: Triệt tiêu hiện tượng nhấp nháy vân phủ texture khi di chuyển.
  * **Khắc phục biến dạng Mesh**: Tự động sửa chữa các khoảng trống hình học hoặc tàng hình bộ phận sau các bản cập nhật trò chơi.
  * **Cơ chế sao lưu an toàn**: Tự động lưu bản sao dự phòng `.BAK` trước khi can thiệp vào tệp tin gốc.

### 🌐 Tích hợp trung tâm mod đa nguồn (Multi-Store Integration)
* **GameBanana**: Kết nối trực tiếp qua REST API thời gian thực.
* **Huihui168**: Kho dữ liệu cộng đồng phong phú kèm bộ dịch tự động.
* **NexusMods**: Hỗ trợ tìm kiếm danh mục từ nền tảng Nexus.
* **Nhập liên kết trực tiếp (Direct Link Importer)**: Hỗ trợ tự động tải xuống và giải nén từ các dịch vụ lưu trữ đám mây (Cloudreve, Baidu, Google Drive, v.v.).

### 🖼️ Trình xem trước & Quản lý danh mục (Visual Inspector)
* Tích hợp bộ sưu tập hình ảnh xem trước độ nét cao cho từng nhân vật và trang phục.
* Hệ thống phân loại thông minh theo Resonators, Phương tiện, NPC, Vũ khí, Dù lượn và Giao diện người dùng.

---

## 3. Hướng dẫn cài đặt và sử dụng

### Yêu cầu hệ thống
* **Hệ điều hành**: Windows 10 / Windows 11 (64-bit).
* **Môi trường**: Microsoft Edge WebView2 Runtime (tích hợp sẵn trên Windows 10/11) hoặc Python 3.10+ (đối với bản chạy mã nguồn).

### Khởi chạy từ mã nguồn
1. Cài đặt các gói thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
2. Khởi chạy ứng dụng:
   ```bash
   pythonw MewModWuWa.py
   ```
   *Hoặc nhấp đúp tệp tin `1_Mo_MewMod_WuWa.bat`.*

### Đóng gói bản thực thi độc lập (Standalone `.exe`)
Chạy kịch bản đóng gói:
```bash
python build_release.py
```
Gói phân phối hoàn chỉnh sẽ được tạo tại thư mục `dist/MewModWuWa/`.

---

## 4. Cấu trúc thư mục dự án

```text
MewMod-WuWa/
├── .github/workflows/       # Quy trình CI/CD tự động đóng gói bản phát hành
├── avatars/                 # Bộ biểu tượng nhận diện nhân vật độ phân giải cao
├── tools/                   # Bộ công cụ tích hợp (7-Zip, WuWa Mod Fixer v3.6.0)
├── 1_Mo_MewMod_WuWa.bat     # Tệp tin khởi động nhanh
├── 2_Mo_Thu_Muc_Mods.bat    # Lối tắt truy cập thư mục Mods của game
├── MewModWuWa.py            # Mã nguồn chính của ứng dụng
├── build_release.py         # Kịch bản đóng gói ứng dụng Standalone
├── requirements.txt         # Danh sách thư viện Python phụ thuộc
└── README.md                # Tài liệu kỹ thuật
```

---

## 5. Bản quyền và Giấy phép

* Dự án được phát triển bởi **WahuVN / MewMod Team**.
* Phát hành phi thương mại phục vụ mục đích hỗ trợ cộng đồng người chơi Wuthering Waves.
