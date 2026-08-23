"""
=============================================================================
🐾 MEWMOD WUWA v4.0 - PHIÊN BẢN TỐI THƯỢNG (FULL JASM & MODORA PRO)
=============================================================================
TÍCH HỢP ĐẦY ĐỦ 100% CÁC TÍNH NĂNG ĐỈNH CAO:
1. [JASM PRO] Bảng Chi Tiết & Tùy Biến Mod (Right Inspector Panel):
   - Xem & Đổi Ảnh Bìa Mod (Cover)
   - Đổi Tên, Tác Giả, Ghi Chú Cá Nhân
   - Bảng Quản Lý Phím Tắt Phụ Kiện `mod.ini` (Qunzi/Váy, Faxing/Tóc, Siwa/Tất, Xiezi/Giày...)
   - Chỉnh sửa phím tắt & Lưu trực tiếp vào file `mod.ini`
2. [JASM PRO] 2 Chế Độ Xem: Bảng Chi Tiết (Table View) & Lưới Ảnh (Grid View)
3. [JASM PRO] Thao Tác Hàng Loạt: 'Tắt Hết Mod Nhân Vật', 'Bật Hết Mod', 'Lưu Preset Bộ Cài'
4. [MODORA PRO] 4 Nguồn Mod Trực Tuyến: GameBanana, Huihui168, NexusMods, Universal Link
5. [MODORA PRO] Tự Động Tải 1-Click Siêu Tốc (Cloudreve S3 & GameBanana CDN), Tự Giải Nén pass huihui
6. [MODORA PRO] Unblur NSFW, Tự dịch tiếng Trung sang Tiếng Việt 100%
=============================================================================
"""

import os
import sys
import re
import json
import time
import shutil
import base64
import subprocess
import threading
import webbrowser
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import webview

# ĐƯỜNG DẪN HỆ THỐNG GOM TẬP TRUNG
BASE_DIR = r"D:\TOOL\WuWa Mod Skin"
CACHE_DIR = os.path.join(BASE_DIR, ".cache", "thumbnails")
os.makedirs(CACHE_DIR, exist_ok=True)

WWMI_PATH = os.path.join(BASE_DIR, "WWMI")
WWMI_MODS_PATH = os.path.join(WWMI_PATH, "mods")
WWMI_CHAR_PATH = os.path.join(WWMI_MODS_PATH, "character")
os.makedirs(WWMI_CHAR_PATH, exist_ok=True)

PRESETS_FILE = os.path.join(BASE_DIR, "mewmod_presets.json")

JASM_DIR = os.path.join(BASE_DIR, "JASM")
JASM_EXE = os.path.join(JASM_DIR, "JASM - Just Another Skin Manager.exe")
if not os.path.exists(JASM_EXE):
    JASM_EXE = r"C:\Users\ADMIN\AppData\Local\Programs\JASM\JASM - Just Another Skin Manager.exe"

CHAR_IMG_DIR = os.path.join(JASM_DIR, "Assets", "Games", "WuWa", "Images", "Characters")
if not os.path.exists(CHAR_IMG_DIR):
    CHAR_IMG_DIR = r"C:\Users\ADMIN\AppData\Local\Programs\JASM\Assets\Games\WuWa\Images\Characters"

MODORA_DIR = os.path.join(BASE_DIR, "MODORA", "MODORA-0.1.90-preview-win-x64")
MODORA_EXE = os.path.join(MODORA_DIR, "MODORA Preview.exe")
WUWA_MOD_FIXER_EXE = os.path.join(MODORA_DIR, "resources", "tools", "wuwa-mod-fixer", "v3.6.0", "Wuwa_Mod_Fixer_v3.6.0.exe")

XXMI_EXE = r"C:\Users\ADMIN\AppData\Roaming\XXMI Launcher\Resources\Bin\XXMI Launcher.exe"
DOWNLOADS_PATH = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
SEVEN_ZIP_PATH = os.path.join(JASM_DIR, "Assets", "7z", "7z.exe")
if not os.path.exists(SEVEN_ZIP_PATH):
    SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"


SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

DICT_NAMES = [
    ("达妮娅", "Dania"), ("清宵", "Qingxiao"), ("穗穗", "Suisui"), ("洛瑟菈", "Lothella"),
    ("爱弥斯", "Aemeath"), ("艾梅斯", "Aemeath"), ("莫宁", "Mornye"), ("琳奈", "Lynae"),
    ("卜灵", "Buling"), ("布玲", "Buling"), ("夏空", "Xiakong"), ("桃祈", "Taoqi"),
    ("卡提希娅", "Cartethyia"), ("弗洛洛", "Phrolova"), ("露帕", "Lupa"), ("卢帕", "Lupa"),
    ("赞妮", "Zani"), ("守岸人", "Shorekeeper"), ("椿", "Camellya"), ("长离", "Changli"),
    ("今汐", "Jinhsi"), ("奥古斯塔", "Augusta"), ("尤诺", "Iuno"), ("珂莱塔", "Carlotta"),
    ("柯莱塔", "Carlotta"), ("菲比", "Phoebe"), ("坎特蕾拉", "Cantarella"), ("千咲", "Chisa"),
    ("吟霖", "Yinlin"), ("折枝", "Zhezhi"), ("相里要", "Xiangliyao"), ("漂泊者", "Rover"),
    ("散华", "Sanhua"), ("丹瑾", "Danjin"), ("秧秧·玄翎", "Yangyang Xuanling"), ("玄翎", "Xuanling"),
    ("秧秧", "Yangyang"), ("鉴心", "Jianxin"), ("忌炎", "Jiyan"), ("卡卡罗", "Calcharo"),
    ("安可", "Encore"), ("维里奈", "Verina"), ("炽霞", "Chixia"), ("白芷", "Baizhi"),
    ("釉瑚", "Youhu"), ("灯灯", "Lumi"), ("绯雪", "Feixue"), ("西格莉卡", "Sigelika"),
    ("丽贝卡", "Rebecca"), ("秋水", "Aalto"), ("渊武", "Yuanwu"), ("凌阳", "Lingyang"),
    ("洛可可", "Roccia"), ("鸣潮", "WuWa")
]

DICT_PHRASES = [
    # Sự kiện & Phiên bản
    ("二周年庆典", "Kỷ Niệm 2 Năm"), ("周年庆", "Kỷ Niệm Năm"), ("庆典", "Lễ Hội"),
    ("完整版", "Bản Full"), ("重置版", "Bản Remake"), ("重制版", "Bản Remake"), ("优化版", "Bản Tối Ưu"),
    ("整合包", "Gói Tổng Hợp"), ("全整合", "Tổng Hợp Toàn Bộ"), ("自用", "Custom"), ("分享", "Share"),
    ("合1", "Trong 1"), ("九合一", "9 Trong 1"), ("支持发光", "Hỗ Trợ Glow"), ("发光插件", "Plugin Glow"),
    ("发光", "Phát Sáng Glow"), ("反虚化", "Xóa Mờ Anti-Blur"), ("去虚化", "Xóa Mờ"),
    ("去UI", "Ẩn UI"), ("去葫芦", "Xóa Hồ Lô"), ("去除轮廓线", "Xóa Viền Đen"), ("修复工具", "Công Cụ Sửa Lỗi"),
    ("修复版", "Bản Fix"), ("修复", "Fix Lỗi"), ("教程", "Hướng Dẫn"), ("用户指南", "Hướng Dẫn"),
    # Kiểu dáng & Trang phục
    ("捆绑", "Trói Buộc (Bondage)"), ("甜实", "Ngọt Ngào"), ("淫荡指令", "Chỉ Lệnh Gợi Cảm"),
    ("指令", "Chỉ Lệnh"), ("景君", "Jingjun"), ("兔兔泡芙", "Bánh Su Thỏ Con"), ("泡芙", "Bánh Su"),
    ("兔兔", "Thỏ Con"), ("夏日清风", "Gió Mát Mùa Hè"), ("盛夏", "Nắng Hè"), ("夏日", "Mùa Hè"),
    ("清风", "Gió Mát"), ("晚礼服", "Váy Dạ Hội"), ("礼服", "Lễ Phục"), ("金色古典花纹", "Họa Tiết Cổ Điển Mạ Vàng"),
    ("金色", "Mạ Vàng"), ("古典", "Cổ Điển"), ("花纹", "Họa Tiết"), ("短发", "Tóc Ngắn"),
    ("长发", "Tóc Dài"), ("双马尾", "Tóc Hai Bên"), ("翅膀", "Đôi Cánh"), ("时韵", "Thời Vận"),
    ("时韵银白", "Ngân Bạch"), ("果体", "Skin Nude"), ("全果", "Skin Nude"), ("半果", "Nửa Kín"),
    ("裸体", "Skin Nude"), ("黑丝", "Tất Đen"), ("白丝", "Tất Trắng"), ("肉丝", "Tất Da"),
    ("连裤袜", "Quần Tất"), ("丝袜", "Tất Dài"), ("光腿", "Chân Trần"), ("赤脚", "Chân Trần"),
    ("高跟鞋", "Giày Cao Gót"), ("长靴", "Bốt Cao Cổ"), ("短靴", "Giày Cổ Thấp"), ("靴子", "Bốt"),
    ("短裙", "Váy Ngắn"), ("长裙", "Váy Dài"), ("裙子", "Váy"), ("露背", "Hở Lưng"),
    ("透视", "Trong Suốt"), ("透明", "Trong Suốt"), ("透明蕾丝", "Ren Trong Suốt"), ("无内", "Không Nội Y"),
    ("泳装", "Bikini Áo Tắm"), ("泳衣", "Bikini"), ("比基尼", "Bikini"), ("水着", "Bikini"),
    ("旗袍", "Sườn Xám"), ("女仆", "Hầu Gái Maid"), ("特工兔女郎", "Thỏ Ngọc Điệp Viên"),
    ("兔女郎", "Thỏ Ngọc Bunny"), ("纯白花嫁", "Váy Cưới Tinh Khôi"), ("花嫁", "Váy Cưới Cô Dâu"),
    ("婚纱", "Váy Cưới"), ("机甲", "Cơ Khí Mecha"), ("护士", "Y Tá"), ("学生装", "Đồng Phục Nữ Sinh"),
    ("JK", "Đồng Phục JK"), ("西装女士", "Suit Quý Tộc"), ("西装", "Âu Phục Suit"),
    ("战术", "Chiến Thuật"), ("恶魔", "Ác Quỷ"), ("天使", "Thiên Thần"), ("魅魔姐妹", "Chị Em Succubus"),
    ("魅魔", "Succubus"), ("修女妹妹", "Nữ Tu Sĩ"), ("修女", "Nữ Tu Sĩ"), ("白色毛衣", "Áo Len Trắng"),
    ("无瑕侍礼", "Lễ Phục Hoàn Mỹ"), ("夜之魅影", "Bóng Ma Đêm"), ("巨乳", "Vòng 1 Lớn"),
    ("胸部", "Vòng 1"), ("大胸", "Vòng 1 Lớn"), ("女剑仙", "Nữ Kiếm Tiên"), ("简约切换", "Tối Giản"),
    ("过去的岁月", "Hoài Niệm"), ("红豆", "Hồng Đậu"), ("除夕", "Đêm Giao Thừa"), ("午夜潜行", "Đột Kích Đêm"),
    ("光彩照人", "Rạng Rỡ"), ("光天化日之下", "Ban Ngày"), ("国韵·落红", "Cổ Phong"),
    ("国韵·金翎", "Kim Linh"), ("国韵", "Cổ Phong"), ("云岚", "Vân Lam"), ("云中之风", "Gió Trong Mây"),
    ("猎人", "Thợ Săn"), ("白澜穗光", "Bạch Lan"), ("花间舞", "Vũ Điệu Hoa"), ("神祇少女", "Thần Thánh"),
    ("夜行性蝴蝶", "Bướm Đêm"), ("引起共鸣", "Cộng Hưởng"), ("休闲装", "Đồ Ở Nhà"), ("晨间休闲装", "Đồ Ngủ"),
    ("旖夜咏奏", "Đêm Tình"), ("蕾米的礼物", "Quà Remi"), ("月潮", "Thủy Triều Trăng"), ("琳琅", "Châu Báu"),
    ("纹身", "Hình Xăm"), ("改金属质感", "Chất Liệu Kim Loại"), ("虚狩", "Hunter"),
    ("白丝透乳", "Tất Trắng Quyến Rũ"), ("白丝浴衣", "Kimono Tất Trắng"), ("浴衣", "Kimono"),
    # Phương tiện, Vũ khí, UI
    ("载具", "Phương Tiện"), ("摩托车", "Xe Máy"), ("摩托", "Xe Máy"), ("机车", "Xe Máy"),
    ("御宅车涂装", "Decal Xe Wibu"), ("涂装", "Decal Sơn"), ("滑翔翼", "Dù Lượn"), ("滑翔机", "Dù Lượn"),
    ("羽翼", "Đôi Cánh"), ("武器", "Vũ Khí"), ("光刃", "Kiếm Sáng"), ("长刃", "Đại Đao"),
    ("佩枪", "Súng"), ("音感仪", "Pháp Khí"), ("功能", "Tính Năng"), ("界面", "Giao Diện UI"),
    ("编队图片", "Ảnh Đội Hình"), ("配队图片", "Ảnh Phối Đội"), ("配队", "Phối Đội"),
    ("转场加载", "Màn Chuyển Cảnh"), ("转场", "Chuyển Cảnh"), ("动态", "Ảnh Động"),
    ("红发", "Tóc Đỏ"), ("白发", "Tóc Bạch Kim"), ("银发", "Tóc Bạch Kim"), ("金发", "Tóc Vàng"),
    ("黑发", "Tóc Đen"), ("粉发", "Tóc Hồng"), ("蓝发", "Tóc Xanh"), ("版", "Bản")
]

# TỪ ĐIỂN PHỤ KIỆN KEYBIND ĐỂ HIỂN THỊ DỄ HIỂU NHẤT
DICT_ACCESSORIES = {
    "qunzi": "Váy / Đầm (Dress)",
    "faxing": "Kiểu Tóc (Hair)",
    "siwa": "Tất Chân (Stockings)",
    "toujin": "Khăn Trùm Đầu (Veil)",
    "toushi": "Phụ Kiện Tóc (Headwear)",
    "touhuan": "Vòng Đầu (Crown)",
    "xiezi": "Giày / Dép (Shoes)",
    "aixin": "Hình Xăm / Trái Tim (Tattoo)",
    "shouzhuo": "Vòng Tay / Găng (Gloves)",
    "jingji": "Gai Nhọn (Thorns)",
    "fajia": "Kẹp Tóc (Hairpin)",
    "fagu": "Băng Đô (Headband)",
    "tui": "Vòng Đùi (Leg Band)",
    "coat": "Áo Khoác (Jacket)",
    "glasses": "Kính Mắt (Glasses)",
    "weapon": "Vũ Khí (Weapon)"
}

HANVIET_MAP = {
    '丝': 'Tất', '丰': 'Phong', '之': 'Của', '乳': 'Ngực', '亡': 'Vong', '人': 'Người',
    '代': 'Đại', '修': 'Sửa', '停': 'Dừng', '元': 'Nguyên', '光': 'Sáng', '免': 'Miễn',
    '公': 'Công', '内': 'Nội', '冰': 'Băng', '切': 'Cắt', '列': 'Liệt', '刘': 'Lưu',
    '利': 'Lợi', '办': 'Biện', '千': 'Thiên', '华': 'Hoa', '博': 'Bác', '卡': 'Thẻ',
    '去': 'Xóa', '友': 'Hữu', '发': 'Tóc', '合': 'Hợp', '后': 'Hậu', '含': 'Gồm',
    '商': 'Thương', '喵': 'Mèo', '嘉': 'Gia', '器': 'Khí', '团': 'Đoàn', '图': 'Ảnh',
    '垢': 'Bẩn', '堡': 'Bảo', '墨': 'Mực', '声': 'Thanh', '夏': 'Hạ', '多': 'Nhiều',
    '大': 'Lớn', '头': 'Đầu', '契': 'Khế', '女': 'Nữ', '如': 'Như', '娘': 'Nương',
    '娜': 'Na', '季': 'Mùa', '安': 'An', '官': 'Quan', '定': 'Định', '室': 'Phòng',
    '寻': 'Tìm', '小': 'Nhỏ', '带': 'Dây', '年': 'Năm', '店': 'Tiệm', '归': 'Về',
    '彩': 'Sắc', '影': 'Bóng', '彼': 'Bỉ', '德': 'Đức', '性': 'Tính', '情': 'Tình',
    '愿': 'Nguyện', '成': 'Thành', '戮': 'Lục', '户': 'Hộ', '技': 'Kỹ', '持': 'Trì',
    '换': 'Đổi', '支': 'Chi', '改': 'Sửa', '斯': 'Tư', '新': 'Mới', '方': 'Phương',
    '旅': 'Lữ', '旗': 'Kỳ', '无': 'Không', '日': 'Ngày', '时': 'Thời', '明': 'Minh',
    '星': 'Sao', '春': 'Xuân', '晨': 'Sáng', '暂': 'Tạm', '曲': 'Khúc', '最': 'Nhất',
    '月': 'Trăng', '服': 'Đồ', '望': 'Vọng', '机': 'Cơ', '杀': 'Sát', '果': 'Nude',
    '根': 'Căn', '格': 'Cách', '桃': 'Đào', '水': 'Nước', '永': 'Vĩnh', '洁': 'Khiết',
    '流': 'Lưu', '浪': 'Sóng', '涂': 'Sơn', '淫': 'Gợi Cảm', '清': 'Thanh', '满': 'Mãn',
    '潮': 'Triều', '火': 'Hỏa', '牛': 'Ngưu', '牵': 'Khiên', '狐': 'Hồ', '猫': 'Mèo',
    '玉': 'Ngọc', '现': 'Hiện', '理': 'Lý', '瓷': 'Sứ', '用': 'Dùng', '白': 'Trắng',
    '的': 'Của', '皇': 'Hoàng', '皮': 'Skin', '着': 'Mặc', '睡': 'Ngủ', '空': 'Không',
    '站': 'Trạm', '管': 'Quản', '粉': 'Hồng', '糖': 'Đường', '系': 'Hệ', '紀': 'Kỷ',
    '素': 'Tố', '紧': 'Chặt', '约': 'Ước', '纱': 'Voan', '编': 'Biên', '美': 'Mỹ',
    '翠': 'Thúy', '翡': 'Phỉ', '者': 'Giả', '肚': 'Bụng', '肤': 'Da', '肩': 'Vai',
    '胜': 'Thắng', '能': 'Năng', '膝': 'Gối', '舞': 'Vũ', '舰': 'Hạm', '良': 'Lương',
    '色': 'Màu', '芙': 'Phù', '花': 'Hoa', '荡': 'Đãng', '荷': 'Hà', '莉': 'Lỵ',
    '萌': 'Moe', '蓝': 'Lam', '蔚': 'Úy', '蕾': 'Nụ', '薄': 'Mỏng', '虔': 'Kiền',
    '蜜': 'Mật', '蝶': 'Bướm', '衣': 'Áo', '补': 'Bù', '袜': 'Tất', '装': 'Trang Phục',
    '裤': 'Quần', '语': 'Ngữ', '调': 'Điệu', '贝': 'Bối', '赛': 'Tái', '赦': 'Xá',
    '身': 'Thân', '轨': 'Quỹ', '过': 'Qua', '迹': 'Tích', '透': 'Lộ', '速': 'Tốc',
    '道': 'Đạo', '重': 'Trọng', '间': 'Gian', '队': 'Đội', '阴': 'Âm', '随': 'Tùy',
    '集': 'Tập', '雪': 'Tuyết', '雷': 'Lôi', '雾': 'Sương', '露': 'Lộ', '青': 'Thanh',
    '面': 'Mặt', '音': 'Âm', '風': 'Phong', '骸': 'Hài', '鸣': 'Minh', '鸦': 'Nha', '黑': 'Đen'
}

def translate_mod_title(zh_title):
    res = zh_title.strip()
    char_prefix = ""
    for zh, en in DICT_NAMES:
        if zh in res:
            char_prefix = f"[{en}] "
            res = res.replace(zh, "")
            break
    for zh, vi in DICT_PHRASES:
        res = res.replace(zh, f" {vi} ")
        
    for ch in re.findall(r'[\u4e00-\u9fff]', res):
        vi_word = HANVIET_MAP.get(ch, '')
        if vi_word:
            res = res.replace(ch, f" {vi_word} ")
        else:
            res = res.replace(ch, " ")
            
    res = char_prefix + " ".join(res.split())
    res = re.sub(r'\s+', ' ', res).strip()
    return res


CHARACTER_LIST = [
    {"name": "Tất Cả Nhân Vật", "query": "", "query_cn": "", "folder": "", "icon": "All.png"},
    {"name": "Qingxiao (清宵)", "query": "Qingxiao", "query_cn": "清宵", "folder": "qingxiao", "icon": "Qingxiao.png"},
    {"name": "Dania (达妮娅)", "query": "Dania", "query_cn": "达妮娅", "folder": "dania", "icon": "Dania.png"},
    {"name": "Suisui (穗穗)", "query": "Suisui", "query_cn": "穗穗", "folder": "suisui", "icon": "Suisui.png"},
    {"name": "Yangyang Xuanling (秧秧·玄翎)", "query": "Yangyang Xuanling", "query_cn": "玄翎", "folder": "yangyangxuanling", "icon": "Yangyang.png"},
    {"name": "Lothella (洛瑟菈)", "query": "Lothella", "query_cn": "洛瑟菈", "folder": "lothella", "icon": "Lothella.png"},
    {"name": "Lucy", "query": "Lucy", "query_cn": "Lucy", "folder": "lucy", "icon": "Lucy.png"},
    {"name": "Rebecca (丽贝卡)", "query": "Rebecca", "query_cn": "丽贝卡", "folder": "rebecca", "icon": "Rebecca.png"},
    {"name": "Feixue (绯雪)", "query": "Feixue", "query_cn": "绯雪", "folder": "feixue", "icon": "Feixue.png"},
    {"name": "Sigelika (西格莉卡)", "query": "Sigelika", "query_cn": "西格莉卡", "folder": "sigelika", "icon": "Sigrika.png"},
    {"name": "Aemeath (爱弥斯)", "query": "Aemeath", "query_cn": "爱弥斯", "folder": "aemeath", "icon": "Aemeath.png"},
    {"name": "Mornye (莫宁)", "query": "Mornye", "query_cn": "莫宁", "folder": "mornye", "icon": "Mornye.png"},
    {"name": "Lynae (琳奈)", "query": "Lynae", "query_cn": "琳奈", "folder": "lynae", "icon": "Lynae.png"},
    {"name": "Buling (卜灵)", "query": "Buling", "query_cn": "卜灵", "folder": "buling", "icon": "Buling.png"},
    {"name": "Xiakong (夏空)", "query": "Xiakong", "query_cn": "夏空", "folder": "xiakong", "icon": "Xiakong.png"},
    {"name": "Taoqi (桃祈)", "query": "Taoqi", "query_cn": "桃祈", "folder": "taoqi", "icon": "Taoqi.png"},
    {"name": "Cartethyia (卡提希娅)", "query": "Cartethyia", "query_cn": "卡提希娅", "folder": "cartethyia", "icon": "Cartethyia.png"},
    {"name": "Phrolova (弗洛洛)", "query": "Phrolova", "query_cn": "弗洛洛", "folder": "phrolova", "icon": "Phrolova.png"},
    {"name": "Lupa (露帕)", "query": "Lupa", "query_cn": "露帕", "folder": "lupa", "icon": "Lupa.png"},
    {"name": "Zani (赞妮)", "query": "Zani", "query_cn": "赞妮", "folder": "zani", "icon": "Zani.png"},
    {"name": "Shorekeeper (守岸人)", "query": "Shorekeeper", "query_cn": "守岸人", "folder": "shorekeeper", "icon": "Shorekeeper.png"},
    {"name": "Camellya (椿)", "query": "Camellya", "query_cn": "椿", "folder": "camellya", "icon": "Camellya.png"},
    {"name": "Changli (长离)", "query": "Changli", "query_cn": "长离", "folder": "changli", "icon": "Changli.png"},
    {"name": "Jinhsi (今汐)", "query": "Jinhsi", "query_cn": "今汐", "folder": "jinhsi", "icon": "Jinhsi.png"},
    {"name": "Augusta (奥古斯塔)", "query": "Augusta", "query_cn": "奥古斯塔", "folder": "augusta", "icon": "Augusta.png"},
    {"name": "Iuno (尤诺)", "query": "Iuno", "query_cn": "尤诺", "folder": "iuno", "icon": "Iuno.png"},
    {"name": "Carlotta (珂莱塔)", "query": "Carlotta", "query_cn": "珂莱塔", "folder": "carlotta", "icon": "Carlotta.png"},
    {"name": "Phoebe (菲比)", "query": "Phoebe", "query_cn": "菲比", "folder": "phoebe", "icon": "Phoebe.png"},
    {"name": "Cantarella (坎特蕾拉)", "query": "Cantarella", "query_cn": "坎特蕾拉", "folder": "cantarella", "icon": "Cantarella.png"},
    {"name": "Chisa (千咲)", "query": "Chisa", "query_cn": "千咲", "folder": "chisa", "icon": "Chisa.png"},
    {"name": "Yinlin (吟霖)", "query": "Yinlin", "query_cn": "吟霖", "folder": "yinlin", "icon": "Yinlin.png"},
    {"name": "Zhezhi (折枝)", "query": "Zhezhi", "query_cn": "折枝", "folder": "zhezhi", "icon": "Zhezhi.png"},
    {"name": "Xiangliyao (相里要)", "query": "Xiangliyao", "query_cn": "相里要", "folder": "xiangliyao", "icon": "Xiangliyao.png"},
    {"name": "Rover (漂泊者)", "query": "Rover", "query_cn": "漂泊者", "folder": "rover", "icon": "Rover.png"},
    {"name": "Sanhua (散华)", "query": "Sanhua", "query_cn": "散华", "folder": "sanhua", "icon": "Sanhua.png"},
    {"name": "Danjin (丹瑾)", "query": "Danjin", "query_cn": "丹瑾", "folder": "danjin", "icon": "Danjin.png"},
    {"name": "Yangyang (秧秧)", "query": "Yangyang", "query_cn": "秧秧", "folder": "yangyang", "icon": "Yangyang.png"},
    {"name": "Jianxin (鉴心)", "query": "Jianxin", "query_cn": "鉴心", "folder": "jianxin", "icon": "Jianxin.png"},
    {"name": "Jiyan (忌炎)", "query": "Jiyan", "query_cn": "忌炎", "folder": "jiyan", "icon": "Jiyan.png"},
    {"name": "Calcharo (卡卡罗)", "query": "Calcharo", "query_cn": "卡卡罗", "folder": "calcharo", "icon": "Calcharo.png"},
    {"name": "Encore (安可)", "query": "Encore", "query_cn": "安可", "folder": "encore", "icon": "Encore.png"},
    {"name": "Verina (维里奈)", "query": "Verina", "query_cn": "维里奈", "folder": "verina", "icon": "Verina.png"},
    {"name": "Chixia (炽霞)", "query": "Chixia", "query_cn": "炽霞", "folder": "chixia", "icon": "Chixia.png"},
    {"name": "Baizhi (白芷)", "query": "Baizhi", "query_cn": "白芷", "folder": "baizhi", "icon": "Baizhi.png"},
    {"name": "Youhu (釉瑚)", "query": "Youhu", "query_cn": "釉瑚", "folder": "youhu", "icon": "Youhu.png"},
    {"name": "Lumi (灯灯)", "query": "Lumi", "query_cn": "灯灯", "folder": "lumi", "icon": "LUMI.png"}
]



SPECIAL_CATEGORIES = [
    {
        "id": "motorbikes",
        "name": "Xe Máy / Phương Tiện",
        "icon": "🏍️",
        "huihui_kw": "摩托",
        "gb_kw": "motor",
        "folder": "motorbikes"
    },
    {
        "id": "npcs",
        "name": "NPC & Quái Vật / Boss",
        "icon": "👥",
        "huihui_kw": "NPC",
        "gb_kw": "npc",
        "folder": "npcs"
    },
    {
        "id": "weapons",
        "name": "Vũ Khí (Weapons)",
        "icon": "🗡️",
        "huihui_kw": "武器",
        "gb_kw": "weapon",
        "folder": "weapons"
    },
    {
        "id": "gliders",
        "name": "Dù Lượn / Cánh (Gliders)",
        "icon": "🪽",
        "huihui_kw": "翅膀",
        "gb_kw": "glider",
        "folder": "gliders"
    },
    {
        "id": "ui",
        "name": "Giao Diện UI / HUD",
        "icon": "🎮",
        "huihui_kw": "界面",
        "gb_kw": "ui",
        "folder": "ui"
    },
    {
        "id": "qol",
        "name": "Mod Tính Năng (QoL)",
        "icon": "🛠️",
        "huihui_kw": "功能",
        "gb_kw": "utility",
        "folder": "qol"
    }
]


GUID_MAPPING = {
    "273777": "camellya", "282999": "aemeath", "282998": "carlotta",
    "263888": "shorekeeper", "263999": "changli", "263777": "jinhsi",
    "263666": "zhezhi", "263555": "xiangliyao", "263444": "yinlin"
}

def clean_filename(name):
    name = re.sub(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}[_ -]*', '', name)
    name = re.sub(r'\.(zip|rar|7z|tar|gz)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[【\[\(][^】\]\)]*[】\]\)]', '', name)
    name = name.strip(' _-.')
    return name if name else f"Mod_{int(time.time())}"

def detect_character(text_hints, ini_content=""):
    combined = " ".join(text_hints).lower()
    if ini_content:
        for guid, char_id in GUID_MAPPING.items():
            if guid in ini_content:
                return char_id
    for item in CHARACTER_LIST:
        f = item["folder"]
        if not f:
            continue
        if f.lower() in combined or item["name"].lower() in combined or item["query"].lower() in combined:
            return f
    return "others"

def extract_archive(archive_path, extract_dir, password="huihui"):
    os.makedirs(extract_dir, exist_ok=True)
    cmd = [SEVEN_ZIP_PATH, "x", archive_path, f"-o{extract_dir}", "-y"]
    if password:
        cmd.append(f"-p{password}")
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        if res.returncode == 0:
            return True
        cmd2 = [SEVEN_ZIP_PATH, "x", archive_path, f"-o{extract_dir}", "-y"]
        res2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        return res2.returncode == 0
    except Exception as e:
        print("7z Error:", e)
    return False

def optimize_mod_structure(extracted_root, base_mod_name):
    ini_dirs = []
    for root, dirs, files in os.walk(extracted_root):
        for f in files:
            if f.lower() == "mod.ini" or f.lower().endswith(".ini"):
                ini_dirs.append(root)
                break
                
    if not ini_dirs:
        source_dir = extracted_root
        ini_content = ""
    else:
        ini_dirs.sort(key=lambda x: len(x.split(os.sep)))
        source_dir = ini_dirs[0]
        try:
            with open(os.path.join(source_dir, "mod.ini"), "r", encoding="utf-8", errors="ignore") as f:
                ini_content = f.read()
        except:
            ini_content = ""

    char_folder_name = detect_character([base_mod_name, os.path.basename(source_dir)], ini_content)
    char_dest_path = os.path.join(WWMI_CHAR_PATH, char_folder_name)
    os.makedirs(char_dest_path, exist_ok=True)
    
    clean_name = clean_filename(base_mod_name)
    final_mod_dir = os.path.join(char_dest_path, clean_name)
    if os.path.exists(final_mod_dir):
        final_mod_dir = f"{final_mod_dir}_{int(time.time()) % 10000}"
        
    shutil.copytree(source_dir, final_mod_dir, dirs_exist_ok=True)
    
    preview_images = []
    for root, dirs, files in os.walk(final_mod_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.webp'] and f.lower() != ".jasm_cover.jpg":
                preview_images.append(os.path.join(root, f))
            if ext == '.url':
                try:
                    os.remove(os.path.join(root, f))
                except:
                    pass
                    
    cover_path = os.path.join(final_mod_dir, ".JASM_Cover.jpg")
    if not os.path.exists(cover_path) and preview_images:
        try:
            shutil.copy2(preview_images[0], cover_path)
        except:
            pass

    config_path = os.path.join(final_mod_dir, ".JASM_ModConfig.json")
    if not os.path.exists(config_path):
        config_data = {
            "ModName": clean_name,
            "Author": "Modder",
            "Version": "1.0",
            "Description": "Tối ưu bởi MewMod WuWa",
            "Note": "",
            "ToggleOptions": []
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
            
    return char_folder_name, clean_name, final_mod_dir

def parse_mod_ini_keybinds(mod_dir):
    ini_path = os.path.join(mod_dir, "mod.ini")
    if not os.path.exists(ini_path):
        for f in os.listdir(mod_dir):
            if f.lower().endswith(".ini"):
                ini_path = os.path.join(mod_dir, f)
                break
    if not os.path.exists(ini_path):
        return []

    keybinds = []
    try:
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        current_sec = None
        current_data = {}
        for line in lines:
            line_str = line.strip()
            sec_m = re.match(r'^\[Key(.*?)\]', line_str, re.IGNORECASE)
            if sec_m:
                if current_sec and "key" in current_data:
                    keybinds.append(current_data)
                sec_name = sec_m.group(1).lower()
                desc = DICT_ACCESSORIES.get(sec_name, sec_name)
                current_sec = sec_name
                current_data = {
                    "section": f"Key{sec_m.group(1)}",
                    "var_name": sec_name,
                    "display_name": f"[{sec_name}] {desc}",
                    "key": "",
                    "values": "0,1"
                }
            elif current_sec:
                if line_str.startswith("["):
                    if "key" in current_data:
                        keybinds.append(current_data)
                    current_sec = None
                    current_data = {}
                else:
                    k_m = re.match(r'^key\s*=\s*(.*)', line_str, re.IGNORECASE)
                    if k_m:
                        current_data["key"] = k_m.group(1).strip()
                    val_m = re.match(r'^\$([a-zA-Z0-9_]+)\s*=\s*(.*)', line_str)
                    if val_m and val_m.group(1).lower() == current_sec:
                        current_data["values"] = val_m.group(2).strip()

        if current_sec and "key" in current_data:
            keybinds.append(current_data)
    except Exception as e:
        print("Lỗi đọc keybinds mod.ini:", e)
    return keybinds

def save_mod_ini_keybinds(mod_dir, new_keybinds):
    ini_path = os.path.join(mod_dir, "mod.ini")
    if not os.path.exists(ini_path):
        for f in os.listdir(mod_dir):
            if f.lower().endswith(".ini"):
                ini_path = os.path.join(mod_dir, f)
                break
    if not os.path.exists(ini_path):
        return False

    try:
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for kb in new_keybinds:
            sec = kb["section"]
            new_k = kb["key"]
            pattern = rf'(\[{sec}\][\s\S]*?key\s*=\s*)([^\r\n]+)'
            content = re.sub(pattern, rf'\g<1>{new_k}', content, flags=re.IGNORECASE)

        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print("Lỗi ghi keybinds mod.ini:", e)
        return False

def get_avatar_base64(icon_name):
    for ext in [".png", ".webp"]:
        raw_name = icon_name.split('.')[0] + ext
        icon_path = os.path.join(CHAR_IMG_DIR, raw_name)
        if os.path.exists(icon_path):
            try:
                with open(icon_path, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except:
                pass
    return ""

def get_image_base64_from_path(img_path):
    if os.path.exists(img_path):
        try:
            with open(img_path, "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except:
            pass
    return ""


# =============================================================================
# BACKEND API CHO GIAO DIỆN WEBVIEW
# =============================================================================

class MewModAPI:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def log(self, message):
        t = time.strftime("[%H:%M:%S] ")
        if self._window:
            self._window.evaluate_js(f"window.appendLog('{t}{message}');")

    def get_characters(self):
        chars = []
        for c in CHARACTER_LIST:
            count = 0
            if c["folder"]:
                cf = os.path.join(WWMI_CHAR_PATH, c["folder"])
                if os.path.exists(cf):
                    count = len([x for x in os.listdir(cf) if os.path.isdir(os.path.join(cf, x))])
            avatar = get_avatar_base64(c["icon"])
            chars.append({
                "name": c["name"],
                "query": c["query"],
                "query_cn": c.get("query_cn", ""),
                "folder": c["folder"],
                "icon": avatar,
                "count": count,
                "type": "character"
            })

            
        cats = []
        for sc in SPECIAL_CATEGORIES:
            count = 0
            sc_folder = os.path.join(WWMI_CHAR_PATH, sc["folder"])
            if os.path.exists(sc_folder):
                count = len([x for x in os.listdir(sc_folder) if os.path.isdir(os.path.join(sc_folder, x))])
            cats.append({
                "name": sc["name"],
                "query": sc["id"],
                "folder": sc["folder"],
                "icon": sc["icon"],
                "huihui_kw": sc["huihui_kw"],
                "gb_kw": sc["gb_kw"],
                "count": count,
                "type": "category"
            })
        return {"characters": chars, "categories": cats}


    def get_online_mods(self, source, query="", page=1):
        if source == "gamebanana":
            return self._fetch_gamebanana(query, page)
        elif source == "nexus":
            return self._fetch_nexus(query, page)
        else:
            return self._fetch_huihui(query, page)

    def _fetch_gamebanana(self, query="", page=1):
        if not query:
            url = f"https://gamebanana.com/apiv11/Game/20357/Subfeed?_nPage={page}&_nPerpage=50&_sSort=new&_csvModelInclusions=Mod"
        else:
            url = f"https://gamebanana.com/apiv11/Util/Search/Results?_sModelName=Mod&_sSearchString={urllib.parse.quote(query)}&_aFilters[Generic_Game]=20357&_nPage={page}&_nPerpage=50"

        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
            records = data.get("_aRecords", [])
            items = []
            for r in records:
                # Chỉ lấy mục là Mod thực thụ
                if r.get("_sModelName") and r.get("_sModelName") != "Mod":
                    continue
                mod_id = r.get("_idRow")
                title = r.get("_sName", "Mod")
                author = r.get("_aSubmitter", {}).get("_sName", "Tác giả")
                likes = r.get("_nLikeCount", 0)
                
                medias = r.get("_aPreviewMedia", {}).get("_aImages", [])
                img_url = ""
                if medias:
                    img_base = medias[0].get("_sBaseUrl", "")
                    img_file = medias[0].get("_sFile", "")
                    img_url = f"{img_base}/{img_file}"
                    
                items.append({
                    "id": str(mod_id),
                    "title": title,
                    "raw_title": title,
                    "author": author,
                    "likes": f"{likes} ❤️",
                    "img_url": img_url,
                    "link": f"https://gamebanana.com/mods/{mod_id}",
                    "source": "gamebanana"
                })
            return {"success": True, "items": items, "page": page}
        except Exception as e:
            return {"success": False, "error": str(e), "items": [], "page": page}


    def _fetch_huihui(self, query="", page=1):
        if not query:
            url = "https://huihui168.org/?list_1/" if page <= 1 else f"https://huihui168.org/?list_1_{page}/"
        else:
            encoded_kw = urllib.parse.quote(query)
            url = f"https://huihui168.org/?keyword={encoded_kw}" if page <= 1 else f"https://huihui168.org/?keyword={encoded_kw}&page={page}"
            
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                
            items = []
            cards = re.findall(r'<a[^>]*href="([^"]*list_11/([0-9]+)\.html)"[^>]*>[\s\S]*?<img[^>]*src="([^"]+)"[\s\S]*?<h3[^>]*>([^<]+)</h3>', html)
            if not cards:
                cards = re.findall(r'<a[^>]*href="([^"]*list_11/([0-9]+)\.html)"[^>]*>[\s\S]*?<img[^>]*src="([^"]+)"[\s\S]*?alt="([^"]+)"', html)
                
            for link, post_id, img, title in cards:
                raw_title = title.strip()
                vi_title = translate_mod_title(raw_title)
                views_match = re.search(r'([0-9]{2,6})', raw_title)
                likes = f"{views_match.group(1)} ❤️" if views_match else "Hot ❤️"
                
                full_link = f"https://huihui168.org/{link.lstrip('/')}" if not link.startswith("http") else link
                full_img = f"https://huihui168.org/{img.lstrip('/')}" if not img.startswith("http") else img
                    
                items.append({
                    "id": post_id,
                    "title": vi_title,
                    "raw_title": raw_title,
                    "author": "Huihui / Diễn Đàn TQ",
                    "likes": likes,
                    "img_url": full_img,
                    "link": full_link,
                    "source": "huihui168"
                })
            return {"success": True, "items": items, "page": page}
        except Exception as e:
            return {"success": False, "error": str(e), "items": [], "page": page}


    def get_mod_gallery_images(self, source, mod_id, link=""):
        try:
            if source == "gamebanana":
                url = f"https://gamebanana.com/apiv11/Mod/{mod_id}/ProfilePage"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                images = []
                for img in data.get("_aPreviewMedia", {}).get("_aImages", []):
                    base = img.get("_sBaseUrl", "")
                    f = img.get("_sFile", "")
                    if base and f:
                        images.append(f"{base}/{f}")
                return {"success": True, "images": images}
            else:
                target_url = link if link else f"https://huihui168.org/?list_11/{mod_id}.html"
                req = urllib.request.Request(target_url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                
                # Filter images inside article
                raw_imgs = re.findall(r'<img[^>]*src="([^"]+)"', html)
                images = []
                for i in raw_imgs:
                    if not i.endswith(('.svg', 'logo.png', 'favicon.ico', 'qrcode.png')) and 'upload/image' in i:
                        full_img = f"https://huihui168.org/{i.lstrip('/')}" if not i.startswith("http") else i
                        if full_img not in images:
                            images.append(full_img)
                return {"success": True, "images": images}
        except Exception as e:
            return {"success": False, "error": str(e), "images": []}


    def _fetch_nexus(self, query="", page=1):
        url = f"https://www.nexusmods.com/wutheringwaves/mods/?BH=0"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            tiles = re.findall(r'<a[^>]*href="(/wutheringwaves/mods/([0-9]+))"[^>]*>[\s\S]*?<img[^>]*src="([^"]+)"[\s\S]*?<p[^>]*class="tile-name"[^>]*>([^<]+)</p>', html)
            items = []
            for link, mod_id, img, title in tiles:
                items.append({
                    "id": mod_id,
                    "title": title.strip(),
                    "raw_title": title.strip(),
                    "author": "NexusMods",
                    "likes": "Hot ❤️",
                    "img_url": img,
                    "link": f"https://nexusmods.com{link}",
                    "source": "nexus"
                })
            return {"success": True, "items": items if items else []}
        except Exception as e:
            return {"success": False, "error": str(e), "items": []}

    def download_and_install(self, mod_json):
        mod = json.loads(mod_json)
        source = mod.get("source")
        mod_id = mod.get("id")
        title = mod.get("title")
        link = mod.get("link")
        
        threading.Thread(target=self._download_worker, args=(source, mod_id, title, link), daemon=True).start()
        return {"started": True}

    def _download_worker(self, source, mod_id, title, link):
        self.log(f"🚀 Bắt đầu tự động tải 1-Click: {title}...")
        self._window.evaluate_js("window.showDownloadModal();")
        
        try:
            def _prog(pct, cur_mb, tot_mb, speed_mb):
                pct_100 = round(pct * 100, 1)
                self._window.evaluate_js(f"window.updateDownloadProgress({pct_100}, '{cur_mb:.2f}', '{tot_mb:.2f}', '{speed_mb:.2f}');")

            if source == "gamebanana":
                profile_url = f"https://gamebanana.com/apiv11/Mod/{mod_id}/ProfilePage"
                req = urllib.request.Request(profile_url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                files = data.get("_aFiles", [])
                if not files:
                    raise Exception("Không tìm thấy file trên GameBanana!")
                f_obj = files[0]
                dl_url = f_obj.get("_sDownloadUrl")
                fname = f_obj.get("_sFile", f"GB_Mod_{mod_id}.zip")
                fsize = f_obj.get("_nFilesize", 0)
                
                temp_file = os.path.join(os.environ.get("TEMP", ""), fname)
                dl_req = urllib.request.Request(dl_url, headers=HEADERS)
                with urllib.request.urlopen(dl_req, context=SSL_CTX, timeout=120) as r, open(temp_file, "wb") as out_f:
                    tot = int(r.headers.get('content-length', fsize))
                    dl = 0
                    st = time.time()
                    while True:
                        c = r.read(1024 * 64)
                        if not c:
                            break
                        out_f.write(c)
                        dl += len(c)
                        if tot > 0:
                            el = max(0.1, time.time() - st)
                            _prog(dl / tot, dl / (1024*1024), tot / (1024*1024), (dl / (1024*1024)) / el)
                            
                temp_ext = os.path.join(os.environ.get("TEMP", ""), "WuWaExtract")
                if os.path.exists(temp_ext):
                    shutil.rmtree(temp_ext, ignore_errors=True)
                extract_archive(temp_file, temp_ext, password="")
                char_f, clean_n, final_d = optimize_mod_structure(temp_ext, fname)
                shutil.rmtree(temp_ext, ignore_errors=True)
                try:
                    os.remove(temp_file)
                except:
                    pass
            elif source == "nexus":
                webbrowser.open(link)
                self.log(f"🌐 Đã mở liên kết NexusMods: {link}")
                self._window.evaluate_js(f"window.finishDownloadSuccess('{title}', 'others');")
                return
            else:
                req = urllib.request.Request(link, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                share_match = re.search(r'cloudreve\.huihui123\.org/s/([a-zA-Z0-9_-]+)', html)
                if not share_match:
                    share_match = re.search(r'cloudreve%3A%2F%2F([a-zA-Z0-9_-]+)%40share', html)
                if not share_match:
                    raise Exception("Không tìm thấy link chia sẻ Cloudreve!")
                share_key = share_match.group(1)
                
                list_url = f"https://cloudreve.huihui123.org/api/v4/file?uri={urllib.parse.quote(f'cloudreve://{share_key}@share/')}"
                with urllib.request.urlopen(urllib.request.Request(list_url, headers=HEADERS), context=SSL_CTX, timeout=12) as resp:
                    list_data = json.loads(resp.read().decode('utf-8'))
                files = list_data.get("data", {}).get("files", [])
                if not files:
                    raise Exception("Không tìm thấy file nào!")
                target_file = files[0]
                filename = target_file["name"]
                
                url_req_endpoint = "https://cloudreve.huihui123.org/api/v4/file/url"
                payload = {"uris": [f"cloudreve://{share_key}@share/{filename}"], "download": True}
                with urllib.request.urlopen(urllib.request.Request(url_req_endpoint, data=json.dumps(payload).encode('utf-8'), headers=HEADERS, method='POST'), context=SSL_CTX, timeout=12) as resp:
                    url_data = json.loads(resp.read().decode('utf-8'))
                direct_url = url_data.get("data", {}).get("urls", [{}])[0].get("url")
                
                temp_file = os.path.join(os.environ.get("TEMP", ""), filename)
                with urllib.request.urlopen(urllib.request.Request(direct_url, headers=HEADERS), context=SSL_CTX, timeout=120) as r, open(temp_file, "wb") as out_f:
                    tot = int(r.headers.get('content-length', target_file.get("size", 0)))
                    dl = 0
                    st = time.time()
                    while True:
                        c = r.read(1024 * 64)
                        if not c:
                            break
                        out_f.write(c)
                        dl += len(c)
                        if tot > 0:
                            el = max(0.1, time.time() - st)
                            _prog(dl / tot, dl / (1024*1024), tot / (1024*1024), (dl / (1024*1024)) / el)
                            
                temp_ext = os.path.join(os.environ.get("TEMP", ""), "WuWaExtract")
                if os.path.exists(temp_ext):
                    shutil.rmtree(temp_ext, ignore_errors=True)
                extract_archive(temp_file, temp_ext, password="huihui")
                char_f, clean_n, final_d = optimize_mod_structure(temp_ext, filename)
                shutil.rmtree(temp_ext, ignore_errors=True)
                try:
                    os.remove(temp_file)
                except:
                    pass

            self.log(f"🎉 TỰ ĐỘNG NẠP THÀNH CÔNG: [{clean_n}] -> {char_f.upper()}!")
            self._window.evaluate_js(f"window.finishDownloadSuccess('{clean_n}', '{char_f}');")
        except Exception as e:
            self.log(f"⚠️ Lỗi tải mod: {e}")
            self._window.evaluate_js(f"window.finishDownloadError('{str(e)}');")

    def import_from_direct_link(self, link_url):
        self.log(f"📥 Đang phân tích liên kết: {link_url}...")
        if "cloudreve" in link_url or "huihui" in link_url:
            threading.Thread(target=self._download_worker, args=("huihui168", "", "Mod Liên Kết Trực Tiếp", link_url), daemon=True).start()
            return {"success": True, "msg": "Đang bắt đầu nạp từ Cloudreve/Hui盘"}
        elif "gamebanana.com/mods/" in link_url:
            m = re.search(r'mods/([0-9]+)', link_url)
            if m:
                threading.Thread(target=self._download_worker, args=("gamebanana", m.group(1), f"GameBanana Mod {m.group(1)}", link_url), daemon=True).start()
                return {"success": True, "msg": "Đang bắt đầu nạp từ GameBanana"}
        webbrowser.open(link_url)
        return {"success": True, "msg": "Đã mở trình duyệt tải"}

    def get_installed_mods(self, filter_folder=""):
        items = []
        if not os.path.exists(WWMI_CHAR_PATH):
            return items
        for c_f in os.listdir(WWMI_CHAR_PATH):
            if filter_folder and c_f.lower() != filter_folder.lower():
                continue
            full_c = os.path.join(WWMI_CHAR_PATH, c_f)
            if os.path.isdir(full_c):
                for m_f in os.listdir(full_c):
                    full_m = os.path.join(full_c, m_f)
                    if os.path.isdir(full_m):
                        is_disabled = m_f.startswith("DISABLED_")
                        clean_n = m_f.replace("DISABLED_", "")
                        cover_path = os.path.join(full_m, ".JASM_Cover.jpg")
                        cover_b64 = get_image_base64_from_path(cover_path)
                        
                        config_path = os.path.join(full_m, ".JASM_ModConfig.json")
                        author = "Modder"
                        note = ""
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, "r", encoding="utf-8") as f:
                                    cfg = json.load(f)
                                    author = cfg.get("Author", "Modder")
                                    note = cfg.get("Note", "")
                            except:
                                pass
                                
                        mod_date = time.strftime('%m/%d/%Y', time.localtime(os.path.getmtime(full_m)))
                        
                        items.append({
                            "char_folder": c_f,
                            "folder_name": m_f,
                            "clean_name": clean_n,
                            "full_path": full_m,
                            "is_disabled": is_disabled,
                            "cover": cover_b64,
                            "author": author,
                            "date": mod_date,
                            "note": note
                        })
        return items

    def get_mod_detail(self, full_path):
        keybinds = parse_mod_ini_keybinds(full_path)
        config_path = os.path.join(full_path, ".JASM_ModConfig.json")
        author = "Modder"
        desc = ""
        note = ""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    author = cfg.get("Author", "Modder")
                    desc = cfg.get("Description", "")
                    note = cfg.get("Note", "")
            except:
                pass
        cover_path = os.path.join(full_path, ".JASM_Cover.jpg")
        cover_b64 = get_image_base64_from_path(cover_path)
        clean_n = os.path.basename(full_path).replace("DISABLED_", "")
        is_disabled = os.path.basename(full_path).startswith("DISABLED_")
        
        return {
            "full_path": full_path,
            "clean_name": clean_n,
            "is_disabled": is_disabled,
            "cover": cover_b64,
            "author": author,
            "description": desc,
            "note": note,
            "keybinds": keybinds
        }

    def save_mod_detail(self, mod_json):
        data = json.loads(mod_json)
        full_path = data["full_path"]
        note = data.get("note", "")
        author = data.get("author", "")
        keybinds = data.get("keybinds", [])
        
        config_path = os.path.join(full_path, ".JASM_ModConfig.json")
        cfg = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except:
                pass
        cfg["Author"] = author
        cfg["Note"] = note
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            
        if keybinds:
            save_mod_ini_keybinds(full_path, keybinds)
            
        self.log(f"💾 Đã lưu cấu hình & phím tắt cho: {os.path.basename(full_path)}")
        return {"success": True}

    def toggle_all_mods_for_char(self, char_folder, is_enable):
        char_p = os.path.join(WWMI_CHAR_PATH, char_folder)
        if not os.path.exists(char_p):
            return {"success": False}
        count = 0
        for m in os.listdir(char_p):
            full_m = os.path.join(char_p, m)
            if os.path.isdir(full_m):
                is_dis = m.startswith("DISABLED_")
                clean_n = m.replace("DISABLED_", "")
                if is_enable and is_dis:
                    os.rename(full_m, os.path.join(char_p, clean_n))
                    count += 1
                elif not is_enable and not is_dis:
                    os.rename(full_m, os.path.join(char_p, f"DISABLED_{clean_n}"))
                    count += 1
        self.log(f"⚡ Đã {'BẬT' if is_enable else 'TẮT'} toàn bộ mod cho nhân vật: {char_folder.upper()}")
        return {"success": True, "count": count}

    def toggle_mod(self, full_path, is_enable):
        parent_dir = os.path.dirname(full_path)
        base_name = os.path.basename(full_path).replace("DISABLED_", "")
        new_name = base_name if is_enable else f"DISABLED_{base_name}"
        new_path = os.path.join(parent_dir, new_name)
        try:
            os.rename(full_path, new_path)
            self.log(f"🔄 Đã {'BẬT' if is_enable else 'TẮT'} Mod: {base_name}")
            return {"success": True, "new_path": new_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_mod(self, full_path):
        try:
            shutil.rmtree(full_path, ignore_errors=True)
            self.log(f"🗑️ Đã xóa Mod: {os.path.basename(full_path)}")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_folder(self, path=""):
        target = path if path else WWMI_CHAR_PATH
        if os.path.exists(target):
            os.startfile(target)
        else:
            os.startfile(WWMI_PATH)

    def run_advanced_fix(self, target_path, derived_hashes=False, stable_texture=False, rendering33=False, rollback=False):
        if not os.path.exists(WUWA_MOD_FIXER_EXE):
            return {"success": False, "msg": "Không tìm thấy WuWa Mod Fixer"}
        config_json = os.path.join(os.path.dirname(WUWA_MOD_FIXER_EXE), "config.json")
        
        args = [WUWA_MOD_FIXER_EXE, "--cli", "--path", target_path, "--config", config_json]
        if rollback:
            args.append("--rollback")
        else:
            if derived_hashes:
                args.append("--derived-hashes")
            if stable_texture:
                args.append("--stable-texture")
            if rendering33:
                args.append("--rendering-33")
                
        self.log(f"🔧 Đang chạy Sửa Lỗi Mod ({'Khôi phục' if rollback else 'Vá lỗi'}) trên: {os.path.basename(target_path)}...")
        try:
            res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
            log_output = (res.stderr + "\n" + res.stdout).strip()
            self.log(f"✅ HOÀN TẤT CHO [{os.path.basename(target_path)}]!")
            return {"success": True, "output": log_output}
        except Exception as e:
            self.log(f"❌ Lỗi: {e}")
            return {"success": False, "msg": str(e)}

    def fix_all_installed_mods_advanced(self, derived_hashes=False, stable_texture=False, rendering33=False):
        threading.Thread(target=self._fix_all_worker_adv, args=(derived_hashes, stable_texture, rendering33), daemon=True).start()
        return {"started": True}

    def reload_wwmi_mods(self):
        try:
            import ctypes
            # VK_F10 = 0x79
            ctypes.windll.user32.keybd_event(0x79, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x79, 0, 2, 0)
            self.log("🔄 Đã gửi phím [F10] nạp lại toàn bộ Mod trực tiếp trong game (WWMI)!")
            return {"success": True}
        except Exception as e:
            self.log(f"⚠️ Lỗi gửi lệnh F10: {e}")
            return {"success": False}

    def _fix_all_worker_adv(self, derived_hashes, stable_texture, rendering33):
        if not os.path.exists(WUWA_MOD_FIXER_EXE):
            self.log("❌ Không tìm thấy WuWa Mod Fixer!")
            return
        config_json = os.path.join(os.path.dirname(WUWA_MOD_FIXER_EXE), "config.json")
        self.log("🚀 Bắt đầu quét & Tự động sửa lỗi toàn bộ Mod trong thư mục WWMI...")
        
        count = 0
        for char_f in os.listdir(WWMI_CHAR_PATH):
            full_c = os.path.join(WWMI_CHAR_PATH, char_f)
            if os.path.isdir(full_c):
                for mod_f in os.listdir(full_c):
                    full_m = os.path.join(full_c, mod_f)
                    if os.path.isdir(full_m):
                        self.log(f"🔧 Đang sửa: [{char_f.upper()}] {mod_f}...")
                        args = [WUWA_MOD_FIXER_EXE, "--cli", "--path", full_m, "--config", config_json]
                        if derived_hashes: args.append("--derived-hashes")
                        if stable_texture: args.append("--stable-texture")
                        if rendering33: args.append("--rendering-33")
                        subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
                        count += 1
                        
        self.log(f"🎉 HOÀN TẤT! Đã sửa và tối ưu hóa {count} bản Mod cho phiên bản WuWa mới nhất.")


    def launch_mod_fixer(self):
        if os.path.exists(WUWA_MOD_FIXER_EXE):
            subprocess.Popen([WUWA_MOD_FIXER_EXE], cwd=os.path.dirname(WUWA_MOD_FIXER_EXE))
            self.log("🔧 Đã mở giao diện WuWa Mod Fixer v3.6.0!")
        else:
            self.log(f"⚠️ Không tìm thấy WuWa Mod Fixer tại: {WUWA_MOD_FIXER_EXE}")


    def launch_modora(self):
        if os.path.exists(MODORA_EXE):
            subprocess.Popen([MODORA_EXE], cwd=MODORA_DIR)
            self.log("🚀 Đã mở MODORA Preview!")
        else:
            self.log(f"⚠️ Không tìm thấy MODORA tại: {MODORA_EXE}")

    def launch_game(self):
        if os.path.exists(XXMI_EXE):
            subprocess.Popen([XXMI_EXE, "--nogui", "--xxmi", "WWMI"])
            self.log("🎮 Đã khởi động WuWa qua WWMI!")
        else:
            self.log("⚠️ Không tìm thấy XXMI Launcher.")


    def launch_jasm(self):
        if os.path.exists(JASM_EXE):
            subprocess.Popen([JASM_EXE], cwd=os.path.dirname(JASM_EXE))
            self.log("🎨 Đã mở JASM.")
        else:
            self.log("⚠️ Không tìm thấy JASM.")


# =============================================================================
# HTML / CSS / JS GIAO DIỆN JASM + MODORA CHUẨN ĐỈNH CAO
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>🐾 MewMod WuWa - Wuthering Waves Ultimate Mod Hub</title>
<style>
  :root {
    --bg-dark: #0f0f17;
    --sidebar-bg: #161622;
    --card-bg: #1c1c2b;
    --card-hover: #26263b;
    --accent: #f5c2e7;
    --accent-glow: rgba(245, 194, 231, 0.35);
    --green: #a6e3a1;
    --green-glow: rgba(166, 227, 161, 0.4);
    --blue: #89b4fa;
    --text-main: #cdd6f4;
    --text-muted: #898da0;
    --border: #262638;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body {
    background-color: var(--bg-dark);
    color: var(--text-main);
    font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }


  /* HEADER */
  header {
    height: 60px;
    background: var(--sidebar-bg);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    z-index: 10;
  }
  .brand { display: flex; align-items: center; gap: 10px; }
  .brand-logo { font-size: 26px; }
  .brand-title { font-size: 17px; font-weight: 800; color: var(--accent); letter-spacing: 0.5px; }
  .brand-sub { font-size: 10px; color: var(--text-muted); }

  .nav-tabs {
    display: flex;
    background: #0f0f17;
    padding: 3px;
    border-radius: 8px;
    gap: 4px;
  }
  .nav-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .nav-btn.active {
    background: var(--accent);
    color: #11111b;
    box-shadow: 0 0 12px var(--accent-glow);
  }
  .nav-btn:hover:not(.active) { color: var(--text-main); background: #1c1c2b; }

  .actions { display: flex; gap: 8px; align-items: center; }
  .btn-action {
    background: #232336;
    border: 1px solid var(--border);
    color: var(--text-main);
    padding: 7px 12px;
    font-size: 11px;
    font-weight: 700;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .btn-action:hover { background: #31314a; transform: translateY(-1px); }
  .btn-game { background: var(--green); color: #11111b; border: none; }
  .btn-game:hover { background: #94e2d5; box-shadow: 0 0 12px var(--green-glow); }
  .btn-jasm { background: #cba6f7; color: #11111b; border: none; }

  /* MAIN CONTAINER */
  .main-container { display: flex; flex: 1; overflow: hidden; }

  /* LEFT SIDEBAR */
  aside {
    width: 250px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }
  .sidebar-header {
    padding: 12px 14px 8px;
    font-size: 11px;
    font-weight: 800;
    color: #fab387;
    text-transform: uppercase;
  }
  .char-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .char-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--text-main);
  }
  .char-item:hover { background: #222234; }
  .char-item.active { background: #2d2d44; color: var(--accent); font-weight: 700; }
  .char-left { display: flex; align-items: center; gap: 10px; }
  .char-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
    background: #11111b;
    border: 1px solid var(--border);
  }
  .char-badge {
    background: #11111b;
    color: var(--blue);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 6px;
  }

  /* CONTENT AREA */
  main { flex: 1; display: flex; flex-direction: column; background: var(--bg-dark); overflow: hidden; }

  /* TOOLBAR / FILTER BAR */
  .filter-bar {
    height: 52px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid var(--border);
    background: #13131e;
  }
  .search-box { flex: 1; position: relative; }
  .search-box input {
    width: 100%;
    background: #1c1c2b;
    border: 1px solid var(--border);
    padding: 8px 12px 8px 34px;
    border-radius: 8px;
    color: var(--text-main);
    font-size: 12px;
    outline: none;
  }
  .search-box input:focus { border-color: var(--accent); }
  .search-icon { position: absolute; left: 10px; top: 9px; font-size: 13px; color: var(--text-muted); }

  /* VIEW CONTENT SPLIT (FOR INSTALLED VIEW: TABLE + RIGHT INSPECTOR) */
  .installed-split-wrap {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  .installed-table-area {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  /* TABLE STYLES (JASM STYLE) */
  .mod-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .mod-table th {
    text-align: left;
    padding: 10px 12px;
    background: #161624;
    color: var(--text-muted);
    font-weight: 700;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 2;
  }
  .mod-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #1a1a28;
    color: var(--text-main);
  }
  .mod-table tr {
    cursor: pointer;
    transition: background 0.15s;
  }
  .mod-table tr:hover { background: #1f1f30; }
  .mod-table tr.selected { background: #2b2b40; border-left: 3px solid var(--accent); }

  /* RIGHT INSPECTOR PANEL (JASM PRO) */
  .inspector-panel {
    width: 380px;
    background: #141420;
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 16px;
    gap: 14px;
  }
  .inspector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .inspector-title { font-size: 14px; font-weight: 800; color: var(--accent); }
  .cover-box {
    width: 100%;
    height: 190px;
    background: #0b0b10;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .cover-img { width: 100%; height: 100%; object-fit: cover; }
  
  .inspector-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .inspector-label { font-size: 11px; font-weight: 700; color: var(--text-muted); }
  .inspector-input {
    background: #1c1c2b;
    border: 1px solid var(--border);
    padding: 8px 10px;
    border-radius: 6px;
    color: var(--text-main);
    font-size: 12px;
    outline: none;
  }
  .inspector-input:focus { border-color: var(--accent); }

  /* KEYBINDS LIST BOX (JASM MOD.INI) */
  .keybinds-box {
    background: #181826;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .keybind-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #11111b;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }
  .keybind-name { font-size: 11px; color: var(--accent); font-weight: 700; }
  .keybind-input {
    width: 60px;
    text-align: center;
    background: #222234;
    border: 1px solid var(--border);
    color: #a6e3a1;
    font-weight: 800;
    padding: 4px;
    border-radius: 4px;
    font-size: 11px;
    outline: none;
  }

  /* GRID CARDS (ONLINE STORE - ANIME PORTRAIT DESIGN) */
  .grid-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 230px));
    gap: 18px;
    align-content: start;
  }
  .mod-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 390px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  }
  .mod-card:hover {
    transform: translateY(-6px);
    border-color: var(--accent);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.6), 0 0 20px var(--accent-glow);
  }
  .card-img-wrap {
    width: 100%;
    height: 265px;
    background: #0d0d14;
    position: relative;
    overflow: hidden;
    cursor: pointer;
  }
  .card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
    transition: transform 0.35s ease;
  }
  .mod-card:hover .card-img {
    transform: scale(1.06);
  }
  .badge-like {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(17, 17, 27, 0.85);
    backdrop-filter: blur(6px);
    color: #f38ba8;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .card-body {
    padding: 10px 12px 12px;
    display: flex;
    flex-direction: column;
    flex: 1;
    justify-content: space-between;
    background: #181827;
  }
  .card-title {
    font-size: 12px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1.35;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 32px;
    cursor: pointer;
  }
  .card-title:hover {
    color: #fff;
    text-decoration: underline;
  }
  .card-author {
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 4px;
  }
  .btn-dl-now {
    background: linear-gradient(135deg, #a6e3a1, #89dceb);
    color: #11111b;
    border: none;
    padding: 7px 0;
    font-size: 11px;
    font-weight: 800;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  .btn-dl-now:hover {
    filter: brightness(1.15);
    box-shadow: 0 0 14px var(--green-glow);
  }


  /* SWITCH TOGGLE */
  .switch { position: relative; display: inline-block; width: 38px; height: 20px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #313144; transition: .3s; border-radius: 20px; }
  .slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
  input:checked + .slider { background-color: var(--green); }
  input:checked + .slider:before { transform: translateX(18px); }

  /* MODAL */
  .modal-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px);
    display: none; align-items: center; justify-content: center; z-index: 100;
  }
  .modal-overlay.active { display: flex; }
  .modal-box { background: #181825; border: 1px solid var(--border); width: 480px; border-radius: 14px; padding: 24px; }
  .modal-title { font-size: 16px; font-weight: 800; color: var(--accent); margin-bottom: 12px; }
  .progress-wrap { background: #11111b; height: 12px; border-radius: 6px; overflow: hidden; margin: 16px 0 8px; }
  .progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg, #a6e3a1, #89dceb); transition: width 0.1s; }
  .progress-info { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); }

  .log-panel {
    height: 95px; background: #0b0b10; border-top: 1px solid var(--border); padding: 8px 14px;
    font-family: 'Consolas', monospace; font-size: 11px; color: #a6adc8; overflow-y: auto;
  }
  .log-entry { margin-bottom: 2px; }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #2b2b40; border-radius: 4px; }
</style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="brand">
      <div class="brand-logo">🐾</div>
      <div>
        <div class="brand-title">MEWMOD WUWA</div>
        <div class="brand-sub">Trình Quản Lý & Nạp Mod Wuthering Waves Độc Lập</div>
      </div>
    </div>

    <div class="nav-tabs">
      <button class="nav-btn" id="tab-gb" onclick="switchStore('gamebanana')">🌐 GameBanana</button>
      <button class="nav-btn" id="tab-hh" onclick="switchStore('huihui168')">🇨🇳 Huihui168</button>
      <button class="nav-btn" id="tab-nx" onclick="switchStore('nexus')">🎮 NexusMods</button>
      <button class="nav-btn active" id="tab-inst" onclick="switchView('installed')">📁 Quản Lý Mod Đã Cài</button>
      <button class="nav-btn" id="tab-imp" onclick="switchView('direct_link')">⚡ Nạp Bằng Link</button>
    </div>

    <div class="actions">
      <button class="btn-action" style="color: #fab387;" onclick="openFixerModal()">🔧 Sửa Lỗi Mod</button>
      <button class="btn-action" style="color: #89dceb;" onclick="pywebview.api.reload_wwmi_mods()">🔄 Nạp Lại (F10)</button>
      <button class="btn-action" onclick="pywebview.api.open_folder('')">📂 Thư Mục Mods</button>
      <button class="btn-action btn-game" onclick="pywebview.api.launch_game()">🎮 Chạy Game (WWMI)</button>
    </div>
  </header>


  <!-- MAIN CONTAINER -->
  <div class="main-container">
    <!-- LEFT SIDEBAR -->
    <aside>
      <div class="sidebar-header">👤 Danh Sách Nhân Vật</div>
      <div class="char-list" id="char-list">
        <!-- Rendered via JS -->
      </div>
    </aside>

    <!-- CONTENT AREA -->
    <main>
      <!-- TOOLBAR -->
      <div class="filter-bar" id="filter-bar">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input type="text" id="search-input" placeholder="Tìm kiếm Mod..." onkeypress="handleSearchKey(event)">
        </div>

        <!-- JASM BULK ACTIONS (INSTALLED MODE) -->
        <div id="installed-bulk-actions" style="display: flex; gap: 8px;">
          <button class="btn-action" style="color: #fab387;" onclick="fixAllMods()">🔧 Tự Động Sửa Toàn Bộ Mod</button>
          <button class="btn-action" style="color: #f38ba8;" onclick="toggleAllMods(false)">🚫 Tắt Hết Mod</button>
          <button class="btn-action" style="color: var(--green);" onclick="toggleAllMods(true)">✅ Bật Hết Mod</button>
        </div>


        <button class="btn-action" onclick="reloadCurrentView()">🔄 Làm Mới</button>
      </div>

      <!-- ONLINE MOD GRID -->
      <div class="grid-container" id="mod-grid" style="display: none;">
        <!-- Rendered via JS -->
      </div>

      <!-- INSTALLED VIEW (TABLE + RIGHT INSPECTOR) -->
      <div class="installed-split-wrap" id="installed-view">
        <div class="installed-table-area">
          <table class="mod-table">
            <thead>
              <tr>
                <th style="width: 70px;">Bật/Tắt</th>
                <th>Tên Bản Mod</th>
                <th style="width: 120px;">Tác Giả</th>
                <th style="width: 100px;">Thêm Mới</th>
                <th style="width: 140px;">Ghi Chú</th>
              </tr>
            </thead>
            <tbody id="installed-tbody">
              <!-- Rows -->
            </tbody>
          </table>
        </div>

        <!-- RIGHT INSPECTOR (JASM PRO) -->
        <div class="inspector-panel" id="inspector-panel">
          <div class="inspector-header">
            <div class="inspector-title">🔍 Chi Tiết & Tùy Biến Mod</div>
            <button class="btn-action" style="color: #f38ba8;" onclick="deleteSelectedMod()">🗑️ Xóa</button>
          </div>

          <div class="cover-box">
            <img id="insp-cover" class="cover-img" src="https://via.placeholder.com/340x190">
          </div>

          <div class="inspector-field">
            <label class="inspector-label">TÊN BẢN MOD:</label>
            <input type="text" class="inspector-input" id="insp-name" readonly>
          </div>

          <div class="inspector-field">
            <label class="inspector-label">TÁC GIẢ:</label>
            <input type="text" class="inspector-input" id="insp-author" placeholder="Tên tác giả...">
          </div>

          <div class="inspector-field">
            <label class="inspector-label">GHI CHÚ RIÊNG:</label>
            <input type="text" class="inspector-input" id="insp-note" placeholder="Ví dụ: Skin dạ hội chính, tóc dài...">
          </div>

          <div class="inspector-field">
            <label class="inspector-label">⚙️ PHÍM TẮT PHỤ KIỆN (MOD.INI):</label>
            <div class="keybinds-box" id="insp-keybinds">
              <!-- Keybind Rows -->
            </div>
          </div>

          <div style="display: flex; gap: 6px; margin-top: auto; flex-wrap: wrap;">
            <button class="btn-action btn-game" style="flex: 1; justify-content: center; height: 34px;" onclick="saveSelectedModConfig()">
              💾 Lưu Cấu Hình
            </button>
            <button class="btn-action" style="color: #fab387; height: 34px;" onclick="openFixerModal(selectedModDetail ? selectedModDetail.full_path : null)">
              🔧 Sửa Lỗi Mod Này
            </button>
            <button class="btn-action" style="height: 34px;" onclick="openSelectedModFolder()">
              📂 Thư Mục
            </button>
          </div>

        </div>
      </div>

      <!-- DIRECT LINK IMPORTER VIEW -->
      <div id="direct-link-view" style="display: none; padding: 20px;">
        <div style="background: #181825; border: 1px solid var(--border); border-radius: 10px; padding: 16px; display: flex; gap: 10px;">
          <input type="text" id="direct-link-input" style="flex: 1; background: #11111b; border: 1px solid var(--border); padding: 10px 14px; border-radius: 8px; color: var(--text-main); font-size: 12px; outline: none;" placeholder="Dán link Cloudreve, Hui盘, GameBanana, Baidu, Quark hoặc GG Drive vào đây...">
          <button class="btn-action btn-game" onclick="submitDirectLink()">⚡ Nạp Ngay</button>
        </div>
      </div>

      <!-- LOG PANEL -->
      <div class="log-panel" id="log-panel">
        <div class="log-entry">🐾 MewMod WuWa v4.0 Ultimate đã khởi động hoàn tất!</div>
      </div>
    </main>
  </div>

  <!-- MOD FIXER VIETNAMESE MODAL -->
  <div class="modal-overlay" id="fixer-modal">
    <div class="modal-box" style="width: 880px; max-width: 95vw; background: #141420; border: 1px solid var(--border); padding: 22px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 22px;">🔧</span>
          <div>
            <div class="modal-title" style="margin: 0; font-size: 16px; color: var(--accent);">TRÌNH SỬA LỖI MOD WUWA v3.6.0 (VIỆT HÓA 100%)</div>
            <div style="font-size: 11px; color: var(--text-muted);">Quy tắc sửa lỗi Vertex & Mesh mới nhất từ Moonholder & MODORA (CFG 3.6.0)</div>
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn-action" style="font-size: 11px;" onclick="pywebview.api.launch_mod_fixer()">🚀 Mở Tool Gốc</button>
          <button class="btn-action" style="color: #f38ba8; font-size: 16px;" onclick="closeFixerModal()">✕</button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
        <!-- TÙY CHỌN 1 -->
        <div style="background: #1a1a2a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
          <div style="padding-right: 10px;">
            <div style="font-size: 12px; font-weight: 700; color: #fab387;">🏷️ Thêm Hash Trạng Thái Mới (Derived Hashes)</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">Bổ sung hash thiếu (LOD Bias, Cantarella ướt, Chisa E, Aemeath tụ lực...) để hiển thị texture đúng.</div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-derived" checked><span class="slider"></span></label>
        </div>

        <!-- TÙY CHỌN 2 -->
        <div style="background: #1a1a2a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
          <div style="padding-right: 10px;">
            <div style="font-size: 12px; font-weight: 700; color: #89dceb;">🎨 Áp Dụng Texture Ổn Định (Stable Texture)</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">Sử dụng RabbitFX để ổn định texture chống nhấp nháy (Cantarella, Chisa, Cartethyia...).</div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-stable"><span class="slider"></span></label>
        </div>

        <!-- TÙY CHỌN 3 -->
        <div style="background: #1a1a2a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
          <div style="padding-right: 10px;">
            <div style="font-size: 12px; font-weight: 700; color: #a6e3a1;">🕳️ Sửa Lỗ Hổng Mesh / Mất Bộ Phận</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">Khắc phục hiện tượng thủng thân, mất chân tay hoặc tàng hình sau update game.</div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-mesh" checked><span class="slider"></span></label>
        </div>

        <!-- TÙY CHỌN 4 -->
        <div style="background: #1a1a2a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
          <div style="padding-right: 10px;">
            <div style="font-size: 12px; font-weight: 700; color: #cba6f7;">🤖 Sửa Lỗi Cơ Khí Aemeath</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">Tự động sửa lỗi dạng model cơ khí của Aemeath khi biến hình.</div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-aemeath"><span class="slider"></span></label>
        </div>
      </div>

      <!-- TARGET SELECTION -->
      <div style="background: #12121c; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">MỤC TIÊU SỬA LỖI HIỆN TẠI:</div>
        <div id="fixer-target-label" style="font-size: 13px; font-weight: 700; color: #fab387;">Toàn bộ kho Mod trong WWMI</div>
      </div>

      <!-- CONSOLE OUTPUT -->
      <div style="height: 140px; background: #0b0b10; border: 1px solid var(--border); border-radius: 8px; padding: 10px; font-family: 'Consolas', monospace; font-size: 11px; color: #a6adc8; overflow-y: auto; margin-bottom: 14px;" id="fixer-console">
        <div style="color: #6c7086;">[Hệ thống] Sẵn sàng thực thi lệnh sửa lỗi mod với cơ sở dữ liệu CFG 3.6.0...</div>
      </div>

      <!-- ACTION BUTTONS -->
      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button class="btn-action" style="color: #f38ba8;" onclick="executeFixerAction(true)">
          🔄 Khôi Phục Bản Gốc (.BAK)
        </button>
        <button class="btn-action btn-game" style="padding: 10px 22px; font-size: 12px;" onclick="executeFixerAction(false)">
          ⚡ Bắt Đầu Sửa Lỗi Ngay (1-Click)
        </button>
      </div>
    </div>
  </div>

  <!-- FULLSCREEN GALLERY LIGHTBOX MODAL -->

  <div class="modal-overlay" id="gallery-modal">
    <div class="modal-box" style="width: 90vw; max-width: 1050px; height: 90vh; display: flex; flex-direction: column; padding: 18px; position: relative;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <div>
          <div class="modal-title" id="gal-title" style="margin-bottom: 2px;">Tên Mod</div>
          <div style="font-size: 11px; color: var(--text-muted);" id="gal-author">Tác giả: ...</div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          <button class="btn-action btn-game" id="gal-btn-dl" onclick="downloadCurrentGalleryMod()">⚡ Tự Động Tải & Nạp Ngay (1-Click)</button>
          <button class="btn-action" style="color: #f38ba8; font-size: 16px;" onclick="closeGalleryModal()">✕</button>
        </div>
      </div>

      <!-- MAIN BIG PREVIEW WITH ARROWS -->
      <div style="flex: 1; background: #0b0b10; border-radius: 10px; overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center;">
        <img id="gal-big-img" src="" style="max-width: 100%; max-height: 100%; object-fit: contain;">
        <button class="btn-action" style="position: absolute; left: 14px; padding: 12px 16px; font-size: 18px; background: rgba(17,17,27,0.7); backdrop-filter: blur(4px);" onclick="prevGalleryImage()">◀</button>
        <button class="btn-action" style="position: absolute; right: 14px; padding: 12px 16px; font-size: 18px; background: rgba(17,17,27,0.7); backdrop-filter: blur(4px);" onclick="nextGalleryImage()">▶</button>
        <div style="position: absolute; bottom: 12px; background: rgba(0,0,0,0.6); padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; color: #fff;" id="gal-counter">1 / 1</div>
      </div>

      <!-- BOTTOM THUMBNAILS STRIP -->
      <div style="height: 85px; display: flex; gap: 8px; overflow-x: auto; margin-top: 10px; padding: 4px 0;" id="gal-thumbs">
        <!-- Thumbnails -->
      </div>
    </div>
  </div>

  <!-- DOWNLOAD MODAL -->
  <div class="modal-overlay" id="dl-modal">
    <div class="modal-box">
      <div class="modal-title" id="dl-title">⚡ Đang Tự Động Tải & Nạp Mod...</div>
      <div style="font-size: 12px; color: var(--text-muted);" id="dl-subtitle">Đang kết nối máy chủ tốc độ cao...</div>
      <div class="progress-wrap">
        <div class="progress-fill" id="dl-bar"></div>
      </div>
      <div class="progress-info">
        <span id="dl-pct">0%</span>
        <span id="dl-speed">Tốc độ: Đang tính toán...</span>
      </div>
    </div>
  </div>


<script>
  let currentSource = 'gamebanana';
  let currentView = 'installed'; // default to installed skins
  let currentChar = '';
  let currentCharFolder = '';
  let onlineMods = [];
  let characters = [];
  let installedMods = [];
  let selectedModDetail = null;

  window.addEventListener('pywebviewready', () => {
    loadCharacters();
    loadInstalled();
  });

  function appendLog(msg) {
    const p = document.getElementById('log-panel');
    const d = document.createElement('div');
    d.className = 'log-entry';
    d.innerText = msg;
    p.appendChild(d);
    p.scrollTop = p.scrollHeight;
  }

  let currentSelectedItem = null;

  async function loadCharacters() {
    const data = await pywebview.api.get_characters();
    const list = document.getElementById('char-list');
    list.innerHTML = '';

    // SECTION 1: RESONATORS
    const sec1 = document.createElement('div');
    sec1.style = "font-size: 10px; font-weight: 800; color: var(--text-muted); padding: 8px 12px 4px; text-transform: uppercase; letter-spacing: 0.5px;";
    sec1.innerText = "👤 Nhân Vật (Resonators)";
    list.appendChild(sec1);

    (data.characters || []).forEach(c => {
      const item = document.createElement('div');
      const isAct = currentSelectedItem && currentSelectedItem.name === c.name;
      item.className = `char-item ${isAct ? 'active' : ''}`;
      item.onclick = () => selectItem(c);
      item.innerHTML = `
        <div class="char-left">
          <img src="${c.icon || 'https://via.placeholder.com/28'}" class="char-avatar">
          <span style="font-size: 12px;">${c.name}</span>
        </div>
        ${c.count > 0 ? `<span class="char-badge">${c.count}</span>` : ''}
      `;
      list.appendChild(item);
    });

    // SECTION 2: SPECIAL CATEGORIES (MOTORBIKES, NPCS, WEAPONS, GLIDERS, UI, QOL)
    const sec2 = document.createElement('div');
    sec2.style = "font-size: 10px; font-weight: 800; color: var(--text-muted); padding: 14px 12px 4px; text-transform: uppercase; letter-spacing: 0.5px; border-top: 1px solid var(--border); margin-top: 6px;";
    sec2.innerText = "🏍️ Phương Tiện & Phụ Kiện";
    list.appendChild(sec2);

    (data.categories || []).forEach(c => {
      const item = document.createElement('div');
      const isAct = currentSelectedItem && currentSelectedItem.name === c.name;
      item.className = `char-item ${isAct ? 'active' : ''}`;
      item.onclick = () => selectItem(c);
      item.innerHTML = `
        <div class="char-left">
          <span style="font-size: 18px; width: 28px; text-align: center;">${c.icon}</span>
          <span style="font-size: 12px; font-weight: 600;">${c.name}</span>
        </div>
        ${c.count > 0 ? `<span class="char-badge">${c.count}</span>` : ''}
      `;
      list.appendChild(item);
    });
  }

  function selectItem(item) {
    currentSelectedItem = item;
    if (item.name === 'Tất Cả Nhân Vật') {
      currentChar = '';
      currentCharFolder = '';
    } else {
      currentChar = item.name;
      currentCharFolder = item.folder || '';
    }

    loadCharacters();
    if (currentView === 'installed') {
      loadInstalled(currentCharFolder);
    } else if (currentView === 'store') {
      loadMods();
    }
  }

  function getActiveQuery() {
    if (!currentSelectedItem || currentSelectedItem.name === 'Tất Cả Nhân Vật') return '';
    if (currentSelectedItem.type === 'category') {
      if (currentSource === 'huihui168') return currentSelectedItem.huihui_kw;
      if (currentSource === 'gamebanana') return currentSelectedItem.gb_kw;
      return currentSelectedItem.folder;
    }
    if (currentSource === 'huihui168' && currentSelectedItem.query_cn) {
      return currentSelectedItem.query_cn;
    }
    return currentSelectedItem.query || currentSelectedItem.name;
  }



  function switchStore(src) {
    currentSource = src;
    currentView = 'store';
    ['tab-gb', 'tab-hh', 'tab-nx', 'tab-inst', 'tab-imp'].forEach(id => document.getElementById(id).className = 'nav-btn');
    document.getElementById(src === 'gamebanana' ? 'tab-gb' : (src === 'nexus' ? 'tab-nx' : 'tab-hh')).className = 'nav-btn active';
    
    document.getElementById('filter-bar').style.display = 'flex';
    document.getElementById('installed-bulk-actions').style.display = 'none';
    document.getElementById('mod-grid').style.display = 'grid';
    document.getElementById('installed-view').style.display = 'none';
    document.getElementById('direct-link-view').style.display = 'none';
    loadMods();
  }

  function switchView(view) {
    currentView = view;
    ['tab-gb', 'tab-hh', 'tab-nx', 'tab-inst', 'tab-imp'].forEach(id => document.getElementById(id).className = 'nav-btn');
    document.getElementById(view === 'installed' ? 'tab-inst' : 'tab-imp').className = 'nav-btn active';
    
    if (view === 'installed') {
      document.getElementById('filter-bar').style.display = 'flex';
      document.getElementById('installed-bulk-actions').style.display = 'flex';
      document.getElementById('mod-grid').style.display = 'none';
      document.getElementById('installed-view').style.display = 'flex';
      document.getElementById('direct-link-view').style.display = 'none';
      loadInstalled(currentCharFolder);
    } else {
      document.getElementById('filter-bar').style.display = 'none';
      document.getElementById('mod-grid').style.display = 'none';
      document.getElementById('installed-view').style.display = 'none';
      document.getElementById('direct-link-view').style.display = 'block';
    }
  }

  function reloadCurrentView() {
    if (currentView === 'installed') loadInstalled(currentCharFolder);
    else loadMods();
  }

  async function loadInstalled(filterFolder = '') {
    const tbody = document.getElementById('installed-tbody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px; color: var(--text-muted);">⏳ Đang đọc danh sách Mod...</td></tr>';
    
    installedMods = await pywebview.api.get_installed_mods(filterFolder);
    
    if (!installedMods || installedMods.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: var(--text-muted);">Chưa có bản Mod nào cho nhân vật này.</td></tr>';
      clearInspector();
      return;
    }

    tbody.innerHTML = '';
    installedMods.forEach((m, idx) => {
      const tr = document.createElement('tr');
      tr.id = `row-mod-${idx}`;
      if (idx === 0) {
        tr.className = 'selected';
        inspectMod(m.full_path);
      }
      tr.onclick = () => {
        document.querySelectorAll('#installed-tbody tr').forEach(r => r.className = '');
        tr.className = 'selected';
        inspectMod(m.full_path);
      };

      tr.innerHTML = `
        <td onclick="event.stopPropagation();">
          <label class="switch">
            <input type="checkbox" ${m.is_disabled ? '' : 'checked'} onchange="toggleMod('${m.full_path.replace(/\\\\/g, '\\\\\\\\')}', this.checked)">
            <span class="slider"></span>
          </label>
        </td>
        <td style="font-weight: 700; color: ${m.is_disabled ? 'var(--text-muted)' : 'var(--accent)'};">
          [${m.char_folder.toUpperCase()}] ${m.clean_name}
        </td>
        <td>${m.author}</td>
        <td>${m.date}</td>
        <td style="color: var(--text-muted);">${m.note || '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function inspectMod(fullPath) {
    selectedModDetail = await pywebview.api.get_mod_detail(fullPath);
    if (!selectedModDetail) return;
    
    document.getElementById('insp-cover').src = selectedModDetail.cover || 'https://via.placeholder.com/340x190';
    document.getElementById('insp-name').value = selectedModDetail.clean_name;
    document.getElementById('insp-author').value = selectedModDetail.author || '';
    document.getElementById('insp-note').value = selectedModDetail.note || '';

    const kbContainer = document.getElementById('insp-keybinds');
    kbContainer.innerHTML = '';
    
    if (!selectedModDetail.keybinds || selectedModDetail.keybinds.length === 0) {
      kbContainer.innerHTML = '<div style="font-size: 11px; color: var(--text-muted); text-align: center;">Bản Mod này không có phím tắt phụ kiện trong mod.ini</div>';
      return;
    }

    selectedModDetail.keybinds.forEach((kb, idx) => {
      const row = document.createElement('div');
      row.className = 'keybind-row';
      row.innerHTML = `
        <span class="keybind-name">${kb.display_name}</span>
        <input type="text" class="keybind-input" id="kb-input-${idx}" value="${kb.key}" onchange="updateKeybindValue(${idx}, this.value)">
      `;
      kbContainer.appendChild(row);
    });
  }

  function updateKeybindValue(idx, newVal) {
    if (selectedModDetail && selectedModDetail.keybinds[idx]) {
      selectedModDetail.keybinds[idx].key = newVal.trim();
    }
  }

  async function saveSelectedModConfig() {
    if (!selectedModDetail) return;
    selectedModDetail.author = document.getElementById('insp-author').value.trim();
    selectedModDetail.note = document.getElementById('insp-note').value.trim();
    
    await pywebview.api.save_mod_detail(JSON.stringify(selectedModDetail));
    loadInstalled(currentCharFolder);
  }

  function openSelectedModFolder() {
    if (selectedModDetail) pywebview.api.open_folder(selectedModDetail.full_path);
  }

  async function deleteSelectedMod() {
    if (!selectedModDetail) return;
    if (confirm(`Bạn có chắc muốn xóa bản Mod '${selectedModDetail.clean_name}'?`)) {
      await pywebview.api.delete_mod(selectedModDetail.full_path);
      loadInstalled(currentCharFolder);
      loadCharacters();
    }
  }

  async function fixSelectedMod() {
    if (!selectedModDetail) return;
    const res = await pywebview.api.fix_selected_mod(selectedModDetail.full_path);
    if (res.success) {
      alert(`Đã sửa lỗi thành công cho bản mod '${selectedModDetail.clean_name}'!`);
      inspectMod(selectedModDetail.full_path);
    } else {
      alert(`Lỗi: ${res.msg}`);
    }
  }

  async function fixAllMods() {
    if (confirm('Bạn có muốn tự động quét và sửa lỗi toàn bộ các bản Mod đã cài cho phiên bản game mới nhất?')) {
      await pywebview.api.fix_all_installed_mods();
      alert('Đang tiến hành sửa lỗi trong nền. Bạn có thể theo dõi tiến độ ở ô Nhật Ký bên dưới!');
    }
  }

  function clearInspector() {

    document.getElementById('insp-cover').src = 'https://via.placeholder.com/340x190';
    document.getElementById('insp-name').value = '';
    document.getElementById('insp-author').value = '';
    document.getElementById('insp-note').value = '';
    document.getElementById('insp-keybinds').innerHTML = '<div style="font-size: 11px; color: var(--text-muted); text-align: center;">Chọn một bản Mod để xem chi tiết</div>';
  }

  async function toggleMod(path, isEnable) {
    await pywebview.api.toggle_mod(path, isEnable);
    loadInstalled(currentCharFolder);
  }

  async function toggleAllMods(isEnable) {
    if (!currentCharFolder) {
      alert('Vui lòng chọn một nhân vật cụ thể ở danh sách bên trái!');
      return;
    }
    await pywebview.api.toggle_all_mods_for_char(currentCharFolder, isEnable);
    loadInstalled(currentCharFolder);
  }

  let currentStorePage = 1;

  async function loadMods(page = 1) {
    currentStorePage = Math.max(1, page);
    const grid = document.getElementById('mod-grid');
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">⏳ Đang tải trang ' + currentStorePage + ' từ ' + currentSource.toUpperCase() + '...</div>';
    
    const search = document.getElementById('search-input').value.trim();
    const activeQ = getActiveQuery();
    const q = (activeQ + ' ' + search).trim();
    const res = await pywebview.api.get_online_mods(currentSource, q, currentStorePage);
    
    if (!res.success || !res.items || res.items.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #f38ba8;">
          ❌ Không tìm thấy bản mod nào ở trang ${currentStorePage}.
          <div style="margin-top: 12px;">
            <button class="btn-action" onclick="loadMods(1)">Quay lại trang 1</button>
          </div>
        </div>
      `;
      return;
    }
    
    onlineMods = res.items;
    renderGrid();
  }

  function changeStorePage(delta) {
    const target = currentStorePage + delta;
    if (target >= 1) {
      loadMods(target);
    }
  }

  let currentGalleryImages = [];
  let currentGalleryIndex = 0;
  let activeGalleryMod = null;

  let currentFixerTarget = null;

  function openFixerModal(targetPath = null) {
    currentFixerTarget = targetPath;
    const label = document.getElementById('fixer-target-label');
    if (targetPath) {
      label.innerText = `Bản Mod: ${targetPath.split('\\\\').pop() || targetPath}`;
      label.style.color = 'var(--accent)';
    } else {
      label.innerText = 'Toàn bộ kho Mod trong WWMI (Tự động quét tất cả nhân vật)';
      label.style.color = '#fab387';
    }
    document.getElementById('fixer-console').innerHTML = '<div style="color: #6c7086;">[Hệ thống] Sẵn sàng thực thi lệnh sửa lỗi mod với cơ sở dữ liệu CFG 3.6.0...</div>';
    document.getElementById('fixer-modal').className = 'modal-overlay active';
  }

  function closeFixerModal() {
    document.getElementById('fixer-modal').className = 'modal-overlay';
  }

  async function executeFixerAction(isRollback) {
    const derived = document.getElementById('fix-opt-derived').checked;
    const stable = document.getElementById('fix-opt-stable').checked;
    const mesh = document.getElementById('fix-opt-mesh').checked;
    const consoleBox = document.getElementById('fixer-console');

    consoleBox.innerHTML += `<div style="color: var(--accent); margin-top: 6px;">▶ Đang khởi chạy ${isRollback ? 'Khôi phục bản gốc' : 'Sửa lỗi Mod'}...</div>`;
    consoleBox.scrollTop = consoleBox.scrollHeight;

    if (currentFixerTarget) {
      const res = await pywebview.api.run_advanced_fix(currentFixerTarget, derived, stable, mesh, isRollback);
      if (res.success) {
        consoleBox.innerHTML += `<div style="color: #a6e3a1; white-space: pre-wrap;">${res.output || 'Đã hoàn tất thành công!'}</div>`;
        alert(isRollback ? 'Đã khôi phục file gốc từ .BAK thành công!' : 'Đã sửa lỗi thành công!');
        if (selectedModDetail) inspectMod(selectedModDetail.full_path);
      } else {
        consoleBox.innerHTML += `<div style="color: #f38ba8;">Lỗi: ${res.msg}</div>`;
      }
    } else {
      consoleBox.innerHTML += `<div style="color: #89dceb;">🚀 Đang quét và sửa lỗi toàn bộ thư mục mod trong nền... Theo dõi thanh trạng thái bên dưới!</div>`;
      await pywebview.api.fix_all_installed_mods_advanced(derived, stable, mesh);
      alert('Đang tiến hành sửa lỗi toàn bộ Mod trong nền!');
    }
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  function renderGrid() {

    const grid = document.getElementById('mod-grid');
    grid.innerHTML = '';
    onlineMods.forEach((m, idx) => {
      const card = document.createElement('div');
      card.className = 'mod-card';
      card.innerHTML = `
        <div class="card-img-wrap" style="cursor: pointer;" onclick='openGalleryModal(${JSON.stringify(m)})'>
          <img src="${m.img_url || 'https://via.placeholder.com/210x290'}" class="card-img" loading="lazy" onerror="this.src='https://via.placeholder.com/210x290?text=WuWa+Mod'">
          <span class="badge-like">${m.likes}</span>
        </div>
        <div class="card-body">
          <div>
            <div class="card-title" title="${m.title}" style="cursor: pointer;" onclick='openGalleryModal(${JSON.stringify(m)})'>${m.title}</div>
            <div class="card-author">Tác giả: ${m.author}</div>
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="btn-dl-now" style="flex: 1;" onclick='downloadMod(${JSON.stringify(m)})'>
              ⚡ Tải 1-Click
            </button>
            <button class="btn-action" style="padding: 6px 10px; font-size: 11px; background: #28283d;" title="Xem toàn bộ album ảnh" onclick='openGalleryModal(${JSON.stringify(m)})'>
              🖼️ Ảnh
            </button>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });

    // PAGINATION BAR
    const pagBar = document.createElement('div');
    pagBar.style = "grid-column: 1/-1; display: flex; justify-content: center; align-items: center; gap: 10px; padding: 24px 0 40px; margin-top: 10px; border-top: 1px solid var(--border);";
    pagBar.innerHTML = `
      <button class="btn-action" style="padding: 8px 16px; font-weight: 700;" ${currentStorePage <= 1 ? 'disabled style="opacity: 0.5; pointer-events: none;"' : ''} onclick="changeStorePage(-1)">
        ◀ Trang Trước
      </button>
      <span style="font-size: 14px; font-weight: 800; color: var(--accent); background: #181825; border: 1px solid var(--border); padding: 8px 18px; border-radius: 8px;">
        Trang ${currentStorePage}
      </span>
      <button class="btn-action" style="padding: 8px 16px; font-weight: 700;" onclick="changeStorePage(1)">
        Trang Sau ▶
      </button>
    `;
    grid.appendChild(pagBar);
  }


  async function openGalleryModal(modObj) {
    activeGalleryMod = modObj;
    document.getElementById('gal-title').innerText = modObj.title;
    document.getElementById('gal-author').innerText = `Tác giả: ${modObj.author} | Nguồn: ${modObj.source}`;
    document.getElementById('gal-big-img').src = modObj.img_url;
    document.getElementById('gal-counter').innerText = '⏳ Đang tải toàn bộ album ảnh...';
    document.getElementById('gal-thumbs').innerHTML = '';
    document.getElementById('gallery-modal').className = 'modal-overlay active';

    currentGalleryImages = [modObj.img_url];
    currentGalleryIndex = 0;

    const res = await pywebview.api.get_mod_gallery_images(modObj.source, modObj.id, modObj.link);
    if (res.success && res.images && res.images.length > 0) {
      currentGalleryImages = res.images;
      renderGalleryThumbs();
      setGalleryImage(0);
    } else {
      renderGalleryThumbs();
      document.getElementById('gal-counter').innerText = '1 / 1';
    }
  }

  function renderGalleryThumbs() {
    const thumbsBox = document.getElementById('gal-thumbs');
    thumbsBox.innerHTML = '';
    currentGalleryImages.forEach((imgUrl, idx) => {
      const thumb = document.createElement('img');
      thumb.src = imgUrl;
      thumb.style = `height: 75px; width: 110px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 2px solid ${idx === currentGalleryIndex ? 'var(--accent)' : 'var(--border)'}; transition: all 0.2s;`;
      thumb.onclick = () => setGalleryImage(idx);
      thumbsBox.appendChild(thumb);
    });
  }

  function setGalleryImage(idx) {
    if (idx < 0) idx = currentGalleryImages.length - 1;
    if (idx >= currentGalleryImages.length) idx = 0;
    currentGalleryIndex = idx;
    document.getElementById('gal-big-img').src = currentGalleryImages[idx];
    document.getElementById('gal-counter').innerText = `${idx + 1} / ${currentGalleryImages.length}`;
    
    // Update border on thumbs
    const thumbImgs = document.querySelectorAll('#gal-thumbs img');
    thumbImgs.forEach((img, i) => {
      img.style.borderColor = (i === idx) ? 'var(--accent)' : 'var(--border)';
    });
  }

  function prevGalleryImage() { setGalleryImage(currentGalleryIndex - 1); }
  function nextGalleryImage() { setGalleryImage(currentGalleryIndex + 1); }

  function closeGalleryModal() {
    document.getElementById('gallery-modal').className = 'modal-overlay';
  }

  function downloadCurrentGalleryMod() {
    if (activeGalleryMod) {
      closeGalleryModal();
      downloadMod(activeGalleryMod);
    }
  }

  // Keyboard navigation for Gallery modal
  window.addEventListener('keydown', (e) => {
    if (document.getElementById('gallery-modal').classList.contains('active')) {
      if (e.key === 'ArrowLeft') prevGalleryImage();
      if (e.key === 'ArrowRight') nextGalleryImage();
      if (e.key === 'Escape') closeGalleryModal();
    }
  });


  function downloadMod(modObj) {
    document.getElementById('dl-title').innerText = '📥 Đang Tải: ' + modObj.title;
    document.getElementById('dl-subtitle').innerText = 'Đang kết nối máy chủ tốc độ cao...';
    document.getElementById('dl-bar').style.width = '0%';
    document.getElementById('dl-pct').innerText = '0%';
    document.getElementById('dl-speed').innerText = 'Tốc độ: Đang tính toán...';
    document.getElementById('dl-modal').className = 'modal-overlay active';
    pywebview.api.download_and_install(JSON.stringify(modObj));
  }

  function showDownloadModal() {
    document.getElementById('dl-modal').className = 'modal-overlay active';
  }

  function updateDownloadProgress(pct, cur, tot, speed) {
    document.getElementById('dl-bar').style.width = pct + '%';
    document.getElementById('dl-pct').innerText = pct + '% (' + cur + '/' + tot + ' MB)';
    document.getElementById('dl-speed').innerText = '⚡ Tốc độ: ' + speed + ' MB/s';
  }

  function finishDownloadSuccess(name, char) {
    document.getElementById('dl-bar').style.width = '100%';
    document.getElementById('dl-subtitle').innerText = '🎉 ĐÃ NẠP THÀNH CÔNG VÀO GAME!';
    setTimeout(() => {
      document.getElementById('dl-modal').className = 'modal-overlay';
      switchView('installed');
      loadCharacters();
    }, 1200);
  }

  function finishDownloadError(err) {
    document.getElementById('dl-subtitle').innerText = '⚠️ Lỗi: ' + err;
    setTimeout(() => {
      document.getElementById('dl-modal').className = 'modal-overlay';
    }, 3000);
  }

  async function submitDirectLink() {
    const link = document.getElementById('direct-link-input').value.trim();
    if (!link) return;
    const res = await pywebview.api.import_from_direct_link(link);
    appendLog(res.msg);
  }

  function handleSearchKey(e) {
    if (e.key === 'Enter') reloadCurrentView();
  }
</script>
</body>
</html>
"""

def main():
    api = MewModAPI()
    window = webview.create_window(
        title="🐾 MewMod WuWa v4.0 - Siêu Trung Tâm Mod Skin (Full JASM & MODORA)",
        html=HTML_TEMPLATE,
        js_api=api,
        width=1320,
        height=880,
        min_size=(1120, 720),
        background_color='#0f0f17'
    )
    api.set_window(window)
    webview.start(debug=False)

if __name__ == "__main__":
    main()
