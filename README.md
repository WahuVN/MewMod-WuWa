# 🐾 MEWMOD WUWA - Ultimate Wuthering Waves Mod Manager

<p align="center">
  <img src="https://img.shields.io/badge/Wuthering_Waves-Mod_Manager-ff79c6?style=for-the-badge&logo=unrealengine" alt="WuWa">
  <img src="https://img.shields.io/badge/Version-v4.0_Ultimate-8be9fd?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Engine-WebView2_120FPS-50fa7b?style=for-the-badge" alt="Engine">
  <img src="https://img.shields.io/badge/Language-Vietnamese_100%25-bd93f9?style=for-the-badge" alt="Lang">
</p>

---

## 📖 Giới Thiệu (Introduction)

**MewMod WuWa** là siêu ứng dụng quản lý và tải Mod Skin toàn diện nhất dành cho **Wuthering Waves (鸣潮)**. Được xây dựng dựa trên sự kết hợp hoàn hảo giữa hai nền tảng Mod hàng đầu thế giới: **JASM (Just Another Skin Manager)** và **MODORA**, mang lại trải nghiệm mượt mà 120 FPS, giao diện chuẩn Dark Anime Gaming Glassmorphism, và Việt Hóa 100%.

---

## ✨ Tính Năng Nổi Bật (Key Features)

### 1. 🔍 Bảng Quản Lý Chi Tiết & Tùy Biến Phím Tắt `mod.ini` (JASM Pro)
* **Xem Bảng Chi Tiết (Table View)**: Quản lý danh sách Mod theo từng nhân vật với các cột Bật/Tắt checkbox, Tên Mod, Tác Giả, Ngày thêm và Ghi chú riêng.
* **⚙️ Tùy Biến Phím Tắt Phụ Kiện Trực Tiếp**: Tự động phân tích các khối `[Keyqunzi] (Váy)`, `[Keysiwa] (Tất)`, `[Keyfaxing] (Tóc)`, `[Keyxiezi] (Giày)`... cho phép đổi phím tắt ngay trên giao diện và bấm `💾 Lưu Cấu Hình mod.ini` ghi thẳng vào file game.
* **⚡ Thao Tác Hàng Loạt**: 1-Click `🚫 Tắt Hết Mod` hoặc `✅ Bật Hết Mod` theo từng nhân vật.

### 2. 🔧 Trình Sửa Lỗi Mod WuWa v3.6.0 Việt Hóa 100% (MODORA Official Fixer)
* Tích hợp công cụ sửa lỗi Vertex / Mesh / Shader mới nhất (CFG 3.6.0) từ **Moonholder & MODORA**:
  * **🏷️ Thêm Hash Trạng Thái Mới (Derived Hashes)**: Vá hash LOD Bias, Cantarella ướt, Chisa E, Aemeath tụ lực...
  * **🎨 Áp Dụng Texture Ổn Định (Stable Texture)**: RabbitFX chống nhấp nháy texture.
  * **🕳️ Sửa Lỗ Hổng Mesh / Mất Bộ Phận**: Khắc phục hiện tượng thủng thân, mất chi hoặc tàng hình sau cập nhật game.
  * **🤖 Sửa Lỗi Cơ Khí Aemeath**: Khắc phục model dạng cơ khí của Aemeath.
  * **🔄 Khôi Phục Bản Gốc (Rollback)**: Khôi phục lại trạng thái ban đầu từ file backup `.BAK`.

### 3. 🌐 Tích Hợp 4 Nguồn Mod Trực Tuyến & Tải Tốc Độ Cao 1-Click
* **🌐 GameBanana**: Hơn 6.000+ Mod quốc tế qua API thời gian thực.
* **🇨🇳 Huihui168 (Hui盘)**: Hơn 10.000+ Mod Trung Quốc & Bilibili, tự động dịch tiêu đề sang tiếng Việt.
* **🎮 NexusMods**: Kho Mod Wuthering Waves từ Nexus.
* **⚡ Nạp Bằng Link**: Dán link Cloudreve, Hui盘, Baidu, Quark, Google Drive để tự động tải và giải nén pass `huihui`.

### 4. 🖼️ Trình Xem Album Ảnh Phóng To (Fullscreen Gallery Lightbox)
* Xem toàn bộ 5-20 bức ảnh mẫu độ nét cao của từng bản mod.
* Hỗ trợ dải thumbnail cuộn ngang, phím mũi tên `◀ / ▶` và nút `⚡ Tự Động Tải & Nạp Ngay` trực tiếp trong album.

### 5. 🏍️ Phân Loại Đầy Đủ Nhân Vật, Xe Máy, NPC, Vũ Khí, Cánh, UI & QoL
* Hỗ trợ đầy đủ toàn bộ Resonators: Aemeath, Shorekeeper, Camellya, Changli, Jinhsi, Qingxiao, Dania, Suisui, Mornye, Lothella, Lucy, Rebecca, Feixue, Sigelika, Cartethyia, Phrolova, Zani, Lupa, v.v.
* Danh mục chuyên biệt: `🏍️ Xe Máy / Phương Tiện`, `👥 NPC & Quái Vật`, `🗡️ Vũ Khí`, `🪽 Dù Lượn / Cánh`, `🎮 Giao Diện UI`, `🛠️ Mod Tính Năng QoL`.

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
├── ⚡ 1_Mo_MewMod_WuWa.bat      # Khởi chạy siêu ứng dụng MewMod WuWa
├── 🎨 2_Mo_JASM_VietHoa.bat    # Mở JASM Việt Hóa
├── 📁 3_Mo_Thu_Muc_Mods.bat    # Mở thư mục Mods
├── 🔧 4_Mo_WuWa_Mod_Fixer.bat  # Mở công cụ sửa lỗi Mod
├── 🚀 5_Mo_MODORA.bat          # Mở MODORA Preview
├── 🐍 MewModWuWa.py            # Mã nguồn chính của MewMod WuWa
├── 📄 requirements.txt         # Danh sách thư viện Python phụ thuộc
└── 📘 README.md                # Tài liệu hướng dẫn sử dụng
```

---

## 📜 Giấy Phép & Bản Quyền (License & Credits)
* Dự án được phát triển phi lợi nhuận phục vụ cộng đồng mod Wuthering Waves.
* Cảm ơn cộng đồng **3DMigoto**, **JASM**, **MODORA** và **Moonholder** về các công cụ và cơ sở dữ liệu quy tắc.
