# MewMod WuWa

<p align="center">
  <img src="./app_icon.png" width="110" height="110" alt="MewMod WuWa Logo" style="border-radius: 16px;"><br><br>
  <b>Ứng dụng quản lý và cài đặt Mod Skin cho Wuthering Waves (鸣潮)</b>
</p>

<p align="center">
  <a href="https://github.com/WahuVN/MewMod-WuWa/releases"><img src="https://img.shields.io/badge/Bản_mới_nhất-v1.0.0-brightgreen?style=flat-square" alt="Version"></a>
  <img src="https://img.shields.io/badge/Hỗ_trợ-Windows_10%2F11-blue?style=flat-square" alt="Platform">
</p>

---

## 📌 Giới thiệu

**MewMod WuWa** là công cụ giúp bạn dễ dàng cài đặt, quản lý và tải các bản Mod Skin cho game **Wuthering Waves**. Ứng dụng kết nối trực tiếp với WWMI, giúp bạn bật/tắt mod nhanh chóng và tự động sửa các lỗi mod thường gặp.

---

## ✨ Tính năng chính

* 🛡️ **Bật/Tắt Mod thông minh**: Mỗi nhân vật khi bật 1 skin sẽ tự động tắt các skin khác để tránh bị lỗi đè model trong game.
* 🔧 **Tự động sửa lỗi Mod**: Tích hợp sẵn công cụ sửa lỗi mất bộ phận, tàng hình, nhấp nháy texture sau mỗi lần game cập nhật.
* 🌐 **Tải Mod trực tuyến**: Tìm và tải mod trực tiếp từ GameBanana, Huihui168, NexusMods hoặc dán link tải nhanh.
* ⌨️ **Chỉnh phím tắt phụ kiện**: Đổi phím tắt bật/tắt váy, tất, tóc, phụ kiện (`mod.ini`) ngay trên giao diện mà không cần sửa file thủ công.
* 🖼️ **Xem trước ảnh Mod**: Xem ảnh phóng to, album ảnh đầy đủ trước khi quyết định tải mod.
* 🚀 **Tự động cập nhật**: Tự động thông báo khi có phiên bản mới trên GitHub và tải về chỉ với 1 cú nhấp chuột.

---

## 🚀 Hướng dẫn sử dụng

### Dành cho người dùng thông thường (Khuyên dùng)
1. Vào mục **[Releases](https://github.com/WahuVN/MewMod-WuWa/releases)** và tải file **`MewModWuWa-v1.0.0-Standalone.zip`**.
2. Giải nén vào thư mục bất kỳ.
3. Mở file **`MewModWuWa.exe`** để sử dụng ngay (không cần cài Python).

### Dành cho lập trình viên (Chạy bằng Python)
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy ứng dụng
pythonw MewModWuWa.py
```

---

## 📂 Thư mục dự án

```text
MewMod-WuWa/
├── avatars/                 # Ảnh icon các nhân vật
├── tools/                   # Công cụ 7-Zip và WuWa Mod Fixer
├── 1_Mo_MewMod_WuWa.bat     # File mở nhanh ứng dụng
├── 2_Mo_Thu_Muc_Mods.bat    # File mở nhanh thư mục Mods của game
├── MewModWuWa.py            # File mã nguồn chính
├── build_release.py         # Script đóng gói thành file .exe
├── requirements.txt         # Thư viện Python cần thiết
└── README.md                # Hướng dẫn sử dụng
```

---

## 👤 Tác giả
* Phát triển bởi **WahuVN / MewMod Team**.
* Miễn phí phi lợi nhuận cho cộng đồng Wuthering Waves.

