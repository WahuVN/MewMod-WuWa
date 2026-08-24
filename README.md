# 🐾 MEWMOD WUWA - Ultimate Wuthering Waves Mod Manager

<p align="center">
  <img src="https://img.shields.io/badge/Wuthering_Waves-Mod_Manager-ff79c6?style=for-the-badge&logo=unrealengine" alt="WuWa">
  <img src="https://img.shields.io/badge/Version-v4.1.0_Ultimate-8be9fd?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Engine-WebView2_120FPS-50fa7b?style=for-the-badge" alt="Engine">
  <img src="https://img.shields.io/badge/Language-Vietnamese_100%25-bd93f9?style=for-the-badge" alt="Lang">
</p>

---

## 📖 Giới Thiệu (Introduction)

**MewMod WuWa** là siêu ứng dụng quản lý và cài đặt Mod Skin toàn diện nhất dành cho game **Wuthering Waves (鸣潮)**. Ứng dụng mang lại trải nghiệm mượt mà 120 FPS, giao diện chuẩn Dark Anime Gaming Glassmorphism, Việt Hóa 100%, tích hợp kho mod trực tuyến đa nguồn và cơ chế chống xung đột mod độc quyền.

---

## ✨ Tính Năng Nổi Bật (Key Features)

### 1. 🛡️ Cơ Chế Độc Quyền Skin & Quản Lý Chi Tiết (Single-Active Skin Mode)
* **Chống Trùng Lặp & Xung Đột 100%**: Khi BẬT một skin cho nhân vật, hệ thống tự động TẮT các skin khác của cùng nhân vật đó để tránh vẽ đè đa giác (mesh overlap) hoặc lỗi texture trong game.
* **Xem Bảng Chi Tiết (Table View)**: Quản lý danh sách Mod theo từng nhân vật với các cột Bật/Tắt, Tên Mod, Tác Giả, Dung lượng, Album ảnh và Ghi chú riêng.
* **⚙️ Tùy Biến Phím Tắt Phụ Kiện Trực Tiếp**: Tự động phân tích các khối phím tắt `[Keyqunzi] (Váy)`, `[Keysiwa] (Tất)`, `[Keyfaxing] (Tóc)`... cho phép đổi phím ngay trên giao diện và lưu trực tiếp vào game.

### 2. 🚀 Tự Động Cập Nhật Trực Tuyến Từ GitHub (Auto-Updater)
* Tự động kiểm tra các bản phát hành mới nhất từ kho lưu trữ GitHub chính thức.
* Hiển thị thông báo changelog và nút 1-Click tải bản cập nhật mới nhất mà không cần thao tác thủ công phức tạp.

### 3. 🔧 Trình Sửa Lỗi Mod WuWa v3.6.0 Tích Hợp Sẵn
* Tích hợp sẵn bộ công cụ sửa lỗi Vertex / Mesh / Shader mới nhất (CFG 3.6.0):
  * **🏷️ Thêm Hash Trạng Thái Mới (Derived Hashes)**: Tự động vá hash trạng thái thiếu (LOD Bias, trạng thái ướt, chiêu nộ...).
  * **🎨 Áp Dụng Texture Ổn Định (Stable Texture)**: Chống nhấp nháy texture khi nhân vật di chuyển.
  * **🕳️ Sửa Lỗ Hổng Mesh / Mất Bộ Phận**: Khắc phục thủng thân, mất chân tay, tàng hình sau các bản cập nhật game.
  * **🤖 Sửa Lỗi Cơ Khí Aemeath**: Khắc phục model dạng cơ khí của Aemeath.
  * **🔄 Khôi Phục Bản Gốc (Rollback)**: Khôi phục lại trạng thái ban đầu từ file backup `.BAK`.

### 4. 🌐 Tích Hợp 4 Nguồn Mod Trực Tuyến & Tải Tốc Độ Cao
* **🌐 GameBanana**: Hơn 6.000+ Mod quốc tế qua API thời gian thực.
* **🇨🇳 Huihui168 (Hui盘)**: Hơn 10.000+ Mod Trung Quốc & Bilibili, tự động dịch tiêu đề sang tiếng Việt.
* **🎮 NexusMods**: Kho Mod Wuthering Waves từ Nexus.
* **⚡ Nạp Bằng Link**: Dán link Cloudreve, Hui盘, Baidu, Quark, Google Drive để tự động tải và giải nén pass `huihui`.

### 5. 🖼️ Khung Preview Cao Thoáng & Gallery Album Lightbox
* Khung ảnh preview lớn, tự động căn chỉnh đỉnh đầu nhân vật và hỗ trợ nút chuyển đổi tỷ lệ `📐 Vừa Khung` / `🖼️ Đầy Khung`.
* Trình xem phóng to album ảnh toàn màn hình với thanh thu nhỏ đa chiều.

---

## 🚀 Cài Đặt & Sử Dụng (Installation & Usage)

### Yêu Cầu Hệ Thống:
* Hệ điều hành: Windows 10 / Windows 11 (64-bit).
* Python 3.10 trở lên + Microsoft Edge WebView2 Runtime.

### Cài Đặt Thư Viện:
```bash
pip install -r requirements.txt
```

### Khởi Chạy Ứng Dụng:
Chạy file `1_Mo_MewMod_WuWa.bat` hoặc lệnh:
```bash
pythonw MewModWuWa.py
```

---

## 📂 Cấu Trúc Dự Án (Project Structure)

```
D:\TOOL\WuWa Mod Skin\
├── ⚡ 1_Mo_MewMod_WuWa.bat      # Khởi chạy ứng dụng MewMod WuWa
├── 📁 2_Mo_Thu_Muc_Mods.bat    # Mở nhanh thư mục Mods game
├── 🐍 MewModWuWa.py            # Mã nguồn chính của MewMod WuWa
├── 🔨 build_release.py         # Script tự động đóng gói ứng dụng Standalone (.exe)
├── 🖼️ avatars/                 # Bộ icon avatar nhân vật độ phân giải cao
├── 🛠️ tools/                   # Bộ công cụ 7-Zip và WuWa Mod Fixer v3.6.0 tích hợp
├── 📄 requirements.txt         # Danh sách thư viện Python phụ thuộc
└── 📘 README.md                # Tài liệu hướng dẫn sử dụng
```

---

## 📜 Bản Quyền & Tác Giả
* Phát triển bởi **WahuVN / MewMod Team**.
* Phiên bản: **v4.1.0 Ultimate**.
