"""
=============================================================================
RESONAMOD STUDIO - WUTHERING WAVES MOD MANAGEMENT PLATFORM
=============================================================================
Phát triển bởi WahuVN.
Hệ thống quản lý, cấu hình, xử lý xung đột và tối ưu hóa bản mod cho Wuthering Waves.
=============================================================================
"""

import os
import sys

class SafeWriter:
    def __init__(self, target=None):
        self.target = target
    def write(self, s):
        if self.target:
            try:
                self.target.write(s)
            except:
                pass
    def flush(self):
        if self.target:
            try:
                self.target.flush()
            except:
                pass

if sys.stdout is None:
    sys.stdout = SafeWriter()
elif hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass

if sys.stderr is None:
    sys.stderr = SafeWriter()
elif hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass

import io
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
import queue
import socket
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

# ĐƯỜNG DẪN HỆ THỐNG GOM TẬP TRUNG TỰ ĐỘNG NHẬN DIỆN
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r"D:\TOOL\WuWa Mod Skin"

CACHE_DIR = os.path.join(BASE_DIR, ".cache", "thumbnails")
os.makedirs(CACHE_DIR, exist_ok=True)

GLOBAL_EVENT_QUEUE = queue.Queue()
LAST_HEARTBEAT = time.time()
APP_STARTED = False


def pick_folder_dialog(title="Chọn thư mục"):
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.FolderBrowserDialog
$f.Description = '{title}'
$f.ShowNewFolderButton = $true
if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.SelectedPath
}}
'''
    res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], stdout=subprocess.PIPE, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
    out = res.stdout.strip()
    return (out,) if out else ()


def pick_files_dialog(title="Chọn tệp tin", filter_str="Tất cả (*.*)|*.*", multi=False):
    multi_flag = "$true" if multi else "$false"
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.OpenFileDialog
$f.Title = '{title}'
$f.Filter = '{filter_str}'
$f.Multiselect = {multi_flag}
if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
    $f.FileNames | ForEach-Object {{ Write-Output $_ }}
}}
'''
    res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], stdout=subprocess.PIPE, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
    lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
    return tuple(lines)


class WindowProxy:
    def __init__(self):
        pass

    def evaluate_js(self, js_code):
        GLOBAL_EVENT_QUEUE.put(js_code)

    def create_file_dialog(self, dialog_type=0, directory="", allow_multiple=False, save_filename="", file_types=()):
        if str(dialog_type).lower() == "folder" or dialog_type == 10 or "FOLDER" in str(dialog_type):
            return pick_folder_dialog("Chọn thư mục WWMI")
        filter_str = "|".join(file_types) if file_types else "Tất cả (*.*)|*.*"
        return pick_files_dialog("Chọn tệp tin", filter_str=filter_str, multi=allow_multiple)


CONFIG_FILE = os.path.join(BASE_DIR, "resonamod_config.json")
OLD_CONFIG_FILE = os.path.join(BASE_DIR, "mewmod_config.json")

def load_app_config():
    for fpath in [CONFIG_FILE, OLD_CONFIG_FILE]:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
    return {}

def save_app_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except:
        pass

APP_CONFIG = load_app_config()

XXMI_CONFIG_PATH = os.path.join(
    os.environ.get("APPDATA", ""),
    "XXMI Launcher",
    "XXMI Launcher Config.json",
)


def resolve_wwmi_path():
    """Lấy đúng thư mục WWMI mà XXMI Launcher, cấu hình riêng hoặc các thư mục chuẩn đang sử dụng."""
    # 1. Cấu hình người dùng tùy chỉnh
    custom_wwmi = APP_CONFIG.get("wwmi_path")
    if custom_wwmi and os.path.isdir(custom_wwmi):
        return os.path.abspath(custom_wwmi)

    # 2. Kiểm tra nếu Tool được đặt trực tiếp bên trong thư mục WWMI
    # Ví dụ: D:\WWMI\ResonaMod hoặc D:\WWMI\MewMod\ResonaMod.exe
    for direct_cand in [BASE_DIR, os.path.dirname(BASE_DIR)]:
        if direct_cand and os.path.isdir(direct_cand):
            if os.path.exists(os.path.join(direct_cand, "3DMigoto Loader.exe")) or \
               os.path.exists(os.path.join(direct_cand, "d3dx.ini")) or \
               (os.path.exists(os.path.join(direct_cand, "Mods")) and os.path.basename(direct_cand).lower() in ["wwmi", "3dmigoto"]):
                return os.path.abspath(direct_cand)

    # 3. Cấu hình XXMI Launcher
    try:
        with open(XXMI_CONFIG_PATH, "r", encoding="utf-8-sig") as config_file:
            config = json.load(config_file)
        configured_path = (
            config.get("Importers", {})
            .get("WWMI", {})
            .get("Importer", {})
            .get("importer_folder", "")
        )
        if configured_path:
            configured_path = os.path.abspath(
                os.path.expandvars(os.path.expanduser(configured_path))
            )
            if os.path.isdir(configured_path):
                return configured_path
    except (OSError, ValueError, TypeError):
        pass

    # 4. Quét các đường dẫn cài đặt game & WWMI thông dụng trên các ổ đĩa
    common_cands = [
        os.path.join(BASE_DIR, "WWMI"),
        r"D:\WWMI", r"C:\WWMI", r"E:\WWMI", r"F:\WWMI",
        r"D:\Game\WWMI", r"D:\Games\WWMI", r"D:\Wuwa\WWMI", r"D:\Wuthering Waves\WWMI",
        r"C:\Game\WWMI", r"C:\Games\WWMI", r"C:\Wuwa\WWMI", r"C:\Wuthering Waves\WWMI",
        r"E:\Game\WWMI", r"E:\Games\WWMI", r"E:\Wuwa\WWMI",
    ]
    for cand in common_cands:
        if os.path.isdir(cand) and (
            os.path.exists(os.path.join(cand, "3DMigoto Loader.exe")) or
            os.path.exists(os.path.join(cand, "d3dx.ini")) or
            os.path.exists(os.path.join(cand, "Mods"))
        ):
            return os.path.abspath(cand)

    for cand in [r"D:\Game\WWMI", r"D:\Wuwa\WWMI", r"C:\Game\WWMI", r"C:\Wuwa\WWMI", os.path.join(BASE_DIR, "WWMI")]:
        if os.path.isdir(cand):
            return os.path.abspath(cand)

    # 5. Dự phòng
    return os.path.join(BASE_DIR, "WWMI")


WWMI_PATH = resolve_wwmi_path()
WWMI_MODS_PATH = os.path.join(WWMI_PATH, "Mods") if os.path.exists(os.path.join(WWMI_PATH, "Mods")) else os.path.join(WWMI_PATH, "mods")
WWMI_CHAR_PATH = os.path.join(WWMI_MODS_PATH, "Character") if os.path.exists(os.path.join(WWMI_MODS_PATH, "Character")) else os.path.join(WWMI_MODS_PATH, "character")
os.makedirs(WWMI_CHAR_PATH, exist_ok=True)

AVATARS_DIR = os.path.join(getattr(sys, '_MEIPASS', BASE_DIR), "avatars")
if not os.path.exists(AVATARS_DIR):
    AVATARS_DIR = os.path.join(BASE_DIR, "avatars")
APP_NAME = "ResonaMod"
APP_VERSION = "1.0.2"
GITHUB_REPO = "WahuVN/ResonaMod"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

TOOLS_DIR = os.path.join(getattr(sys, '_MEIPASS', BASE_DIR), "tools")
if not os.path.exists(TOOLS_DIR):
    TOOLS_DIR = os.path.join(BASE_DIR, "tools")

SEVEN_ZIP_PATH = os.path.join(TOOLS_DIR, "7z.exe")
if not os.path.exists(SEVEN_ZIP_PATH):
    SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"

WUWA_MOD_FIXER_EXE = os.path.join(TOOLS_DIR, "wuwa-mod-fixer", "Wuwa_Mod_Fixer_v3.6.0.exe")
if not os.path.exists(WUWA_MOD_FIXER_EXE):
    WUWA_MOD_FIXER_EXE = os.path.join(BASE_DIR, "MODORA", "MODORA-0.1.90-preview-win-x64", "resources", "tools", "wuwa-mod-fixer", "v3.6.0", "Wuwa_Mod_Fixer_v3.6.0.exe")

XXMI_EXE = os.path.join(os.environ.get("APPDATA", ""), "XXMI Launcher", "Resources", "Bin", "XXMI Launcher.exe")
DOWNLOADS_PATH = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")


def run_silent_cmd(cmd_args, cwd=None):
    """Thực thi tiến trình dòng lệnh hoàn toàn ẩn cửa sổ CMD đen (Windows Silent Execution)"""
    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    return subprocess.run(
        cmd_args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors='ignore',
        startupinfo=startupinfo,
        creationflags=creationflags
    )


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
    {"name": "All Characters", "query": "", "query_cn": "", "folder": "", "icon": "All.png", "gb_cat_id": None},
    {"name": "Qingxiao", "query": "Qingxiao", "query_cn": "清宵", "folder": "qingxiao", "icon": "Qingxiao.png", "gb_cat_id": 46596},
    {"name": "Denia", "query": "Denia", "query_cn": "达妮娅", "folder": "dania", "icon": "Denia.png", "gb_cat_id": 44602},
    {"name": "Suisui", "query": "Suisui", "query_cn": "穗穗", "folder": "suisui", "icon": "Suisui.png", "gb_cat_id": 46595},
    {"name": "Suoming", "query": "Suoming", "query_cn": "索命", "folder": "suoming", "icon": "Suoming.png", "gb_cat_id": None},
    {"name": "Yangyang Xuanling", "query": "Yangyang Xuanling", "query_cn": "玄翎", "folder": "yangyangxuanling", "icon": "Yangyang Xuanling.png", "gb_cat_id": 46594},
    {"name": "Lucy", "query": "Lucy", "query_cn": "Lucy", "folder": "lucy", "icon": "Lucy.png", "gb_cat_id": 46187},
    {"name": "Rebecca", "query": "Rebecca", "query_cn": "丽贝卡", "folder": "rebecca", "icon": "Rebecca.png", "gb_cat_id": 46188},
    {"name": "Hiyuki", "query": "Hiyuki", "query_cn": "绯雪", "folder": "feixue", "icon": "Hiyuki.png", "gb_cat_id": 44603},
    {"name": "Sigrika", "query": "Sigrika", "query_cn": "西格莉卡", "folder": "sigelika", "icon": "Sigrika.png", "gb_cat_id": 44420},
    {"name": "Luuk Herssen", "query": "Luuk", "query_cn": "卢克", "folder": "luuk", "icon": "Luuk Herssen.png", "gb_cat_id": 43761},
    {"name": "Mornye", "query": "Mornye", "query_cn": "莫宁", "folder": "mornye", "icon": "Mornye.png", "gb_cat_id": 41930},
    {"name": "Lucilla", "query": "Lucilla", "query_cn": "夏空", "folder": "xiakong", "icon": "Lucilla.png", "gb_cat_id": 44604},
    {"name": "Lynae", "query": "Lynae", "query_cn": "琳奈", "folder": "lynae", "icon": "Lynae.png", "gb_cat_id": 41929},
    {"name": "Aemeath", "query": "Aemeath", "query_cn": "爱弥斯", "folder": "aemeath", "icon": "Aemeath.png", "gb_cat_id": 43048},
    {"name": "Buling", "query": "Buling", "query_cn": "卜灵", "folder": "buling", "icon": "Buling.png", "gb_cat_id": 41161},
    {"name": "Cartethyia", "query": "Cartethyia", "query_cn": "卡提希娅", "folder": "cartethyia", "icon": "Cartethyia.png", "gb_cat_id": 37392},
    {"name": "Phrolova", "query": "Phrolova", "query_cn": "弗洛洛", "folder": "phrolova", "icon": "Phrolova.png", "gb_cat_id": 38371},
    {"name": "Lupa", "query": "Lupa", "query_cn": "露帕", "folder": "lupa", "icon": "Lupa.png", "gb_cat_id": 37891},
    {"name": "Zani", "query": "Zani", "query_cn": "赞妮", "folder": "zani", "icon": "Zani.png", "gb_cat_id": 36665},
    {"name": "The Shorekeeper", "query": "Shorekeeper", "query_cn": "守岸人", "folder": "shorekeeper", "icon": "The Shorekeeper.png", "gb_cat_id": 32220},
    {"name": "Camellya", "query": "Camellya", "query_cn": "椿", "folder": "camellya", "icon": "Camellya.png", "gb_cat_id": 33179},
    {"name": "Changli", "query": "Changli", "query_cn": "长离", "folder": "changli", "icon": "Changli.png", "gb_cat_id": 30265},
    {"name": "Jinhsi", "query": "Jinhsi", "query_cn": "今汐", "folder": "jinhsi", "icon": "Jinhsi.png", "gb_cat_id": 30264},
    {"name": "Augusta", "query": "Augusta", "query_cn": "奥古斯塔", "folder": "augusta", "icon": "Augusta.png", "gb_cat_id": 39143},
    {"name": "Iuno", "query": "Iuno", "query_cn": "尤诺", "folder": "iuno", "icon": "Iuno.png", "gb_cat_id": 39624},
    {"name": "Galbrena", "query": "Galbrena", "query_cn": "嘉贝莉娜", "folder": "gabriella", "icon": "Galbrena.png", "gb_cat_id": 40281},
    {"name": "Roccia", "query": "Roccia", "query_cn": "洛可可", "folder": "rococo", "icon": "Roccia.png", "gb_cat_id": 34733},
    {"name": "Carlotta", "query": "Carlotta", "query_cn": "珂莱塔", "folder": "carlotta", "icon": "Carlotta.png", "gb_cat_id": 34264},
    {"name": "Phoebe", "query": "Phoebe", "query_cn": "菲比", "folder": "phoebe", "icon": "Phoebe.png", "gb_cat_id": 35119},
    {"name": "Cantarella", "query": "Cantarella", "query_cn": "坎特蕾拉", "folder": "cantarella", "icon": "Cantarella.png", "gb_cat_id": 36003},
    {"name": "Chisa", "query": "Chisa", "query_cn": "千咲", "folder": "chisa", "icon": "Chisa.png", "gb_cat_id": 41155},
    {"name": "Yinlin", "query": "Yinlin", "query_cn": "吟霖", "folder": "yinlin", "icon": "Yinlin.png", "gb_cat_id": 30261},
    {"name": "Zhezhi", "query": "Zhezhi", "query_cn": "折枝", "folder": "zhezhi", "icon": "Zhezhi.png", "gb_cat_id": 30472},
    {"name": "Xiangli Yao", "query": "Xiangli Yao", "query_cn": "相里要", "folder": "xiangliyao", "icon": "Xiangli Yao.png", "gb_cat_id": 30471},
    {"name": "Rover", "query": "Rover", "query_cn": "漂泊者", "folder": "rover", "icon": "Rover.png", "gb_cat_id": 30250},
    {"name": "Sanhua", "query": "Sanhua", "query_cn": "散华", "folder": "sanhua", "icon": "Sanhua.png", "gb_cat_id": 30252},
    {"name": "Danjin", "query": "Danjin", "query_cn": "丹瑾", "folder": "danjin", "icon": "Danjin.png", "gb_cat_id": 30255},
    {"name": "Yangyang", "query": "Yangyang", "query_cn": "秧秧", "folder": "yangyang", "icon": "Yangyang.png", "gb_cat_id": 30246},
    {"name": "Jianxin", "query": "Jianxin", "query_cn": "鉴心", "folder": "jianxin", "icon": "Jianxin.png", "gb_cat_id": 30263},
    {"name": "Jiyan", "query": "Jiyan", "query_cn": "忌炎", "folder": "jiyan", "icon": "Jiyan.png", "gb_cat_id": 30256},
    {"name": "Calcharo", "query": "Calcharo", "query_cn": "卡卡罗", "folder": "calcharo", "icon": "Calcharo.png", "gb_cat_id": 30262},
    {"name": "Encore", "query": "Encore", "query_cn": "安可", "folder": "encore", "icon": "Encore.png", "gb_cat_id": 30253},
    {"name": "Verina", "query": "Verina", "query_cn": "维里奈", "folder": "verina", "icon": "Verina.png", "gb_cat_id": 30248},
    {"name": "Chixia", "query": "Chixia", "query_cn": "炽霞", "folder": "chixia", "icon": "Chixia.png", "gb_cat_id": 30247},
    {"name": "Baizhi", "query": "Baizhi", "query_cn": "白芷", "folder": "baizhi", "icon": "Baizhi.png", "gb_cat_id": 30251},
    {"name": "Youhu", "query": "Youhu", "query_cn": "釉瑚", "folder": "youhu", "icon": "Youhu.png", "gb_cat_id": 33791},
    {"name": "Lumi", "query": "Lumi", "query_cn": "灯灯", "folder": "lumi", "icon": "Lumi.png", "gb_cat_id": 33764},
    {"name": "Aalto", "query": "Aalto", "query_cn": "秋水", "folder": "aalto", "icon": "Aalto.png", "gb_cat_id": 30257},
    {"name": "Taoqi", "query": "Taoqi", "query_cn": "桃祈", "folder": "taoqi", "icon": "Taoqi.png", "gb_cat_id": 30254},
    {"name": "Yuanwu", "query": "Yuanwu", "query_cn": "渊武", "folder": "yuanwu", "icon": "Yuanwu.png", "gb_cat_id": 30260},
    {"name": "Lingyang", "query": "Lingyang", "query_cn": "凌阳", "folder": "lingyang", "icon": "Lingyang.png", "gb_cat_id": 30259},
    {"name": "Brant", "query": "Brant", "query_cn": "布兰特", "folder": "brant", "icon": "Brant.png", "gb_cat_id": 35523},
    {"name": "Mortefi", "query": "Mortefi", "query_cn": "莫特斐", "folder": "mortefi", "icon": "Mortefi.png", "gb_cat_id": 30258},
    {"name": "Ciaccona", "query": "Ciaccona", "query_cn": "恰空", "folder": "ciaccona", "icon": "Ciaccona.png", "gb_cat_id": 36990},
    {"name": "Qiuyuan", "query": "Qiuyuan", "query_cn": "秋渊", "folder": "qiuyuan", "icon": "Qiuyuan.png", "gb_cat_id": 40825},
    {"name": "Hsin", "query": "Hsin", "query_cn": "辛", "folder": "hsin", "icon": "Hsin.png", "gb_cat_id": None},
    {"name": "Jingran", "query": "Jingran", "query_cn": "景燃", "folder": "jingran", "icon": "Jingran.png", "gb_cat_id": None}
]



SPECIAL_CATEGORIES = [
    {
        "id": "motorbikes",
        "name": "Xe Máy / Phương Tiện",
        "icon": "🏍️",
        "huihui_kw": "摩托",
        "gb_kw": "motor",
        "gb_cat_id": 29493,
        "folder": "motorbikes"
    },
    {
        "id": "npcs",
        "name": "NPC & Quái Vật / Boss",
        "icon": "👥",
        "huihui_kw": "NPC",
        "gb_kw": "npc",
        "gb_cat_id": 31838,
        "folder": "npcs"
    },
    {
        "id": "weapons",
        "name": "Vũ Khí (Weapons)",
        "icon": "🗡️",
        "huihui_kw": "武器",
        "gb_kw": "weapon",
        "gb_cat_id": 29493,
        "folder": "weapons"
    },
    {
        "id": "gliders",
        "name": "Dù Lượn / Cánh (Gliders)",
        "icon": "🪽",
        "huihui_kw": "翅膀",
        "gb_kw": "glider",
        "gb_cat_id": 29493,
        "folder": "gliders"
    },
    {
        "id": "ui",
        "name": "Giao Diện UI / HUD",
        "icon": "🎮",
        "huihui_kw": "界面",
        "gb_kw": "ui",
        "gb_cat_id": 29496,
        "folder": "ui"
    },
    {
        "id": "qol",
        "name": "Mod Tính Năng (QoL)",
        "icon": "🛠️",
        "huihui_kw": "功能",
        "gb_kw": "utility",
        "gb_cat_id": 29493,
        "folder": "qol"
    },
    {
        "id": "others",
        "name": "Khác (Others)",
        "icon": "📦",
        "huihui_kw": "其他",
        "gb_kw": "misc",
        "gb_cat_id": 29493,
        "folder": "others"
    }
]

INITIAL_CHARACTERS_JSON = json.dumps({
    "characters": [{"name": c["name"], "query": c["query"], "query_cn": c.get("query_cn", ""), "folder": c["folder"], "icon": "", "count": 0, "type": "character"} for c in CHARACTER_LIST],
    "categories": [{"name": sc["name"], "query": sc["id"], "folder": sc["folder"], "icon": sc["icon"], "huihui_kw": sc["huihui_kw"], "gb_kw": sc["gb_kw"], "count": 0, "type": "category"} for sc in SPECIAL_CATEGORIES]
}, ensure_ascii=False)


def load_char_hashes():
    char_hashes = {}
    cfg_path = os.path.join(os.path.dirname(WUWA_MOD_FIXER_EXE), "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for c_name, c_data in cfg.get("characters", {}).items():
                for mh in c_data.get("main_hashes", []):
                    new_h = mh.get("new")
                    if new_h:
                        char_hashes[new_h.lower()] = c_name.lower()
                    for old_h in mh.get("old", []):
                        char_hashes[old_h.lower()] = c_name.lower()
        except:
            pass
    return char_hashes

CHAR_MAIN_HASHES = load_char_hashes()

def clean_filename(name):
    name = re.sub(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}[_ -]*', '', name)
    name = re.sub(r'\.(zip|rar|7z|tar|gz)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[【\[\(][^】\]\)]*[】\]\)]', '', name)
    name = name.strip(' _-.')
    return name if name else f"Mod_{int(time.time())}"

def detect_character(text_hints, ini_content=""):
    combined = " ".join(text_hints).lower()
    
    # 1. Nhận diện chính xác 100% qua Main Hash trong tệp INI
    if ini_content and CHAR_MAIN_HASHES:
        ini_lower = ini_content.lower()
        for h, char_folder in CHAR_MAIN_HASHES.items():
            if f"hash = {h}" in ini_lower or f"hash={h}" in ini_lower:
                return char_folder

    # 2. Nhận diện qua Từ điển Tên Nhân Vật (Trung - Anh)
    for cn, en in DICT_NAMES:
        if cn.lower() in combined or en.lower() in combined:
            for item in CHARACTER_LIST:
                if item["name"].lower() == en.lower() or item["folder"].lower() == en.lower():
                    return item["folder"]

    # 3. Nhận diện qua danh sách nhân vật
    for item in CHARACTER_LIST:
        f = item["folder"]
        if not f:
            continue
        q = item.get("query", "").lower()
        q_cn = item.get("query_cn", "").lower()
        name_l = item.get("name", "").lower()
        if f.lower() in combined or (q and q in combined) or (q_cn and q_cn in combined) or (name_l and name_l in combined):
            return f
            
    # 4. Nhận diện qua danh mục đặc biệt (Phương tiện, Vũ khí, v.v.)
    for sc in SPECIAL_CATEGORIES:
        f = sc["folder"]
        hh_kw = sc.get("huihui_kw", "").lower()
        gb_kw = sc.get("gb_kw", "").lower()
        name_l = sc.get("name", "").lower()
        if f.lower() in combined or (hh_kw and hh_kw in combined) or (gb_kw and gb_kw in combined) or (name_l and name_l in combined):
            return f
            
    return "others"

def extract_archive(archive_path, extract_dir, password="huihui"):
    os.makedirs(extract_dir, exist_ok=True)
    cmd = [SEVEN_ZIP_PATH, "x", archive_path, f"-o{extract_dir}", "-y"]
    if password:
        cmd.append(f"-p{password}")
    try:
        res = run_silent_cmd(cmd)
        if res.returncode == 0:
            return True
        cmd2 = [SEVEN_ZIP_PATH, "x", archive_path, f"-o{extract_dir}", "-y"]
        res2 = run_silent_cmd(cmd2)
        return res2.returncode == 0
    except Exception as e:
        print("7z Error:", e)
    return False

def optimize_mod_structure(extracted_root, base_mod_name, fallback_folder="", online_cover_url="", author="Modder", desc=""):
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
    if char_folder_name == "others" and fallback_folder and fallback_folder != "all":
        char_folder_name = fallback_folder
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
    # Đảm bảo luôn có tệp mod.ini chuẩn để WWMI/3DMigoto nạp 100%
    if not os.path.exists(os.path.join(final_mod_dir, "mod.ini")):
        for f in os.listdir(final_mod_dir):
            if f.lower().endswith(".ini") and not f.lower().startswith("disabled_"):
                try:
                    shutil.copy2(os.path.join(final_mod_dir, f), os.path.join(final_mod_dir, "mod.ini"))
                    break
                except:
                    pass

    cover_path = os.path.join(final_mod_dir, ".ResonaMod_Cover.jpg")
    if not os.path.exists(cover_path):
        if preview_images:
            try:
                shutil.copy2(preview_images[0], cover_path)
            except:
                pass
        elif online_cover_url and online_cover_url.startswith("http"):
            try:
                req = urllib.request.Request(online_cover_url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as r, open(cover_path, "wb") as f_out:
                    f_out.write(r.read())
            except:
                pass

    config_path = os.path.join(final_mod_dir, ".ResonaMod_ModConfig.json")
    config_data = {
        "ModName": clean_name,
        "Author": author if author else "Modder",
        "Version": "1.0",
        "Description": desc if desc else "Tối ưu bởi ResonaMod",
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

_AVATAR_CACHE = {}

def get_avatar_base64(icon_name):
    if not icon_name:
        return ""
    if icon_name in _AVATAR_CACHE:
        return _AVATAR_CACHE[icon_name]

    candidates = [
        os.path.join(AVATARS_DIR, icon_name),
        os.path.join(AVATARS_DIR, icon_name.split('.')[0] + ".png"),
        os.path.join(AVATARS_DIR, icon_name.split('.')[0] + ".webp"),
        os.path.join(AVATARS_DIR, icon_name.split('.')[0] + ".jpg"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with Image.open(p) as img:
                    img = img.convert('RGBA')
                    img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='WEBP', quality=85)
                    data_uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
                    _AVATAR_CACHE[icon_name] = data_uri
                    return data_uri
            except:
                try:
                    with open(p, "rb") as f:
                        data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
                        _AVATAR_CACHE[icon_name] = data_uri
                        return data_uri
                except:
                    pass
    _AVATAR_CACHE[icon_name] = ""
    return ""

def preload_avatar_cache():
    for c in CHARACTER_LIST:
        get_avatar_base64(c["icon"])

threading.Thread(target=preload_avatar_cache, daemon=True).start()

_IMG_BASE64_CACHE = {}

def get_image_base64_from_path(img_path, max_dim=1200):
    if not img_path or not os.path.exists(img_path):
        return ""
    try:
        mtime = os.path.getmtime(img_path)
        cache_key = (img_path, max_dim, mtime)
        if cache_key in _IMG_BASE64_CACHE:
            return _IMG_BASE64_CACHE[cache_key]

        with Image.open(img_path) as img:
            img = img.convert('RGB')
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.BILINEAR)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85, optimize=True)
            res = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
            if len(_IMG_BASE64_CACHE) > 300:
                _IMG_BASE64_CACHE.clear()
            _IMG_BASE64_CACHE[cache_key] = res
            return res
    except:
        try:
            with open(img_path, "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except:
            return ""


# =============================================================================
# BACKEND API CHO GIAO DIỆN WEBVIEW
# =============================================================================

class ResonaModAPI:
    def __init__(self):
        self._window = None
        self._cache = {}
        self._cache_time = {}

    def set_window(self, window):
        self._window = window

    def log(self, message):
        t = time.strftime("[%H:%M:%S] ")
        if self._window:
            self._window.evaluate_js(f"window.appendLog('{t}{message}');")

    def get_characters(self):
        mod_counts = {}
        total_all_mods = 0
        if os.path.exists(WWMI_CHAR_PATH):
            try:
                for entry in os.scandir(WWMI_CHAR_PATH):
                    if entry.is_dir():
                        c_name = entry.name.lower()
                        try:
                            c_count = sum(1 for e in os.scandir(entry.path) if e.is_dir())
                        except:
                            c_count = 0
                        mod_counts[c_name] = c_count
                        total_all_mods += c_count
            except:
                pass

        chars = []
        for c in CHARACTER_LIST:
            f = c["folder"]
            count = mod_counts.get(f.lower(), 0) if f else total_all_mods
            chars.append({
                "name": c["name"],
                "query": c["query"],
                "query_cn": c.get("query_cn", ""),
                "gb_cat_id": c.get("gb_cat_id"),
                "folder": f,
                "icon": get_avatar_base64(c["icon"]),
                "count": count,
                "type": "character"
            })

        cats = []
        for sc in SPECIAL_CATEGORIES:
            f = sc["folder"]
            count = mod_counts.get(f.lower(), 0) if f else 0
            cats.append({
                "name": sc["name"],
                "query": sc["id"],
                "folder": f,
                "icon": sc["icon"],
                "huihui_kw": sc["huihui_kw"],
                "gb_kw": sc["gb_kw"],
                "gb_cat_id": sc.get("gb_cat_id"),
                "count": count,
                "type": "category"
            })
        return {"characters": chars, "categories": cats}


    def get_online_mods(self, source, query="", page=1, cat_id=None):
        cache_key = f"{source}_{query}_{page}_{cat_id}"
        now = time.time()
        if cache_key in self._cache and (now - self._cache_time.get(cache_key, 0) < 300):
            return self._cache[cache_key]

        if source == "gamebanana":
            res = self._fetch_gamebanana(query, page, cat_id)
        elif source == "nexus":
            res = self._fetch_nexus(query, page)
        else:
            res = self._fetch_huihui(query, page)

        if res and res.get("success") and res.get("items"):
            self._cache[cache_key] = res
            self._cache_time[cache_key] = now
        return res

    def _fetch_gamebanana(self, query="", page=1, cat_id=None):
        try:
            records = []
            if cat_id:
                if query:
                    url = f"https://gamebanana.com/apiv11/Util/Search/Results?_sModelName=Mod&_sSearchString={urllib.parse.quote(query)}&_aFilters[Generic_Category]={cat_id}&_nPage={page}&_nPerpage=30"
                else:
                    url = f"https://gamebanana.com/apiv11/Mod/Index?_nPage={page}&_nPerpage=30&_aFilters[Generic_Category]={cat_id}"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    records = data.get("_aRecords", [])
            elif not query:
                # Single request for frontpage feed: 30 items per page
                url = f"https://gamebanana.com/apiv11/Game/20357/Subfeed?_nPage={page}&_nPerpage=30&_sSort=new&_csvModelInclusions=Mod"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    records = data.get("_aRecords", [])
            else:
                url = f"https://gamebanana.com/apiv11/Util/Search/Results?_sModelName=Mod&_sSearchString={urllib.parse.quote(query)}&_aFilters[Generic_Game]=20357&_nPage={page}&_nPerpage=30"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    records = data.get("_aRecords", [])
                
            items = []
            for r in records:
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
                    "title": translate_mod_title(title),
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
                
                # 1. Trích xuất chính xác vùng nội dung bài viết mod (loại trừ sidebar/gợi ý/quảng cáo)
                content_html = ""
                content_match = re.search(r'<div[^>]*class=["\']content["\'][^>]*>([\s\S]*?)</div>\s*(?:<div class="[^"]*tag|<div class="[^"]*footer|<div class="[^"]*comment|<div class="[^"]*share)', html, re.I)
                if not content_match:
                    content_match = re.search(r'<div[^>]*class=["\']content["\'][^>]*>([\s\S]*?)</div>', html, re.I)
                
                if content_match:
                    content_html = content_match.group(1)
                    # Loại bỏ comment HTML để tránh lấy ảnh bị ẩn
                    content_html = re.sub(r'<!--[\s\S]*?-->', '', content_html)
                
                # 2. Vùng gallery/swiper slider nếu có
                gallery_html = ""
                gal_match = re.search(r'<div[^>]*class=["\'][^"\']*(?:swiper-wrapper|article-gallery|pic-box)[^"\']*["\'][^>]*>([\s\S]*?)</div>', html, re.I)
                if gal_match:
                    gallery_html = re.sub(r'<!--[\s\S]*?-->', '', gal_match.group(1))

                combined = (gallery_html + "\n" + content_html).strip() if (gallery_html or content_html) else ""
                
                raw_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', combined) if combined else []
                images = []
                for i in raw_imgs:
                    i = i.strip()
                    if any(bad in i.lower() for bad in ['.svg', 'logo.png', 'favicon', 'qrcode', 'ad-', 'qumian', 'sailingnet']):
                        continue
                    if 'upload/' in i:
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
        context_folder = mod.get("context_folder", "")
        img_url = mod.get("img_url", "")
        author = mod.get("author", "Modder")
        
        threading.Thread(target=self._download_worker, args=(source, mod_id, title, link, context_folder, img_url, author), daemon=True).start()
        return {"started": True}

    def _download_worker(self, source, mod_id, title, link, context_folder="", img_url="", author="Modder"):
        self.log(f"[Tải Xuống] Bắt đầu tải bản mod: {title}...")
        self._window.evaluate_js(f"window.showDownloadWidget('{title.replace(chr(39), '')}');")
        
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
                    raise Exception("Không tìm thấy tệp tải trên GameBanana.")
                f_obj = files[0]
                dl_url = f_obj.get("_sDownloadUrl")
                fname = f_obj.get("_sFile", f"GB_Mod_{mod_id}.zip")
                fsize = f_obj.get("_nFilesize", 0)
                
                # Check for high-res preview image in GameBanana profile
                preview_media = data.get("_aPreviewMedia", {}).get("_aImages", [])
                if preview_media and not img_url:
                    base_u = preview_media[0].get("_sBaseUrl", "")
                    file_u = preview_media[0].get("_sFile", "")
                    if base_u and file_u:
                        img_url = f"{base_u}/{file_u}"
                
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
                char_f, clean_n, final_d = optimize_mod_structure(temp_ext, fname, context_folder, online_cover_url=img_url, author=author, desc=title)
                shutil.rmtree(temp_ext, ignore_errors=True)
                try:
                    os.remove(temp_file)
                except:
                    pass
            elif source == "nexus":
                webbrowser.open(link)
                self.log(f"[NexusMods] Đã mở liên kết trình duyệt: {link}")
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
                    raise Exception("Không tìm thấy liên kết chia sẻ Cloudreve.")
                share_key = share_match.group(1)
                
                list_url = f"https://cloudreve.huihui123.org/api/v4/file?uri={urllib.parse.quote(f'cloudreve://{share_key}@share/')}"
                with urllib.request.urlopen(urllib.request.Request(list_url, headers=HEADERS), context=SSL_CTX, timeout=12) as resp:
                    list_data = json.loads(resp.read().decode('utf-8'))
                files = list_data.get("data", {}).get("files", [])
                if not files:
                    raise Exception("Không tìm thấy tệp mod nào trong liên kết.")
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
                char_f, clean_n, final_d = optimize_mod_structure(temp_ext, filename, context_folder, online_cover_url=img_url, author=author, desc=title)
                shutil.rmtree(temp_ext, ignore_errors=True)
                try:
                    os.remove(temp_file)
                except:
                    pass

            self.log(f"[Cài Đặt] Đã cài đặt thành công: [{clean_n}] -> Thư mục: {char_f.upper()}")
            self._window.evaluate_js(f"window.finishDownloadSuccess('{clean_n}', '{char_f}');")
        except Exception as e:
            self.log(f"[Lỗi Tải Mod] {e}")
            self._window.evaluate_js(f"window.finishDownloadError('{str(e)}');")

    def import_from_direct_link(self, link_url):
        self.log(f"[Liên Kết] Đang phân tích liên kết: {link_url}...")
        if "cloudreve" in link_url or "huihui" in link_url:
            threading.Thread(target=self._download_worker, args=("huihui168", "", "Mod Liên Kết Trực Tiếp", link_url), daemon=True).start()
            return {"success": True, "msg": "Đang tiến hành tải từ Cloudreve/Hui盤"}
        elif "gamebanana.com/mods/" in link_url:
            m = re.search(r'mods/([0-9]+)', link_url)
            if m:
                threading.Thread(target=self._download_worker, args=("gamebanana", m.group(1), f"GameBanana Mod {m.group(1)}", link_url), daemon=True).start()
                return {"success": True, "msg": "Đang tiến hành tải từ GameBanana"}
        webbrowser.open(link_url)
        return {"success": True, "msg": "Đã mở liên kết tải trên trình duyệt"}

    def get_installed_mods(self, filter_folder=""):
        items = []
        if not os.path.exists(WWMI_CHAR_PATH):
            return items
        
        folders_to_scan = []
        if filter_folder:
            target = os.path.join(WWMI_CHAR_PATH, filter_folder)
            if os.path.isdir(target):
                folders_to_scan.append((filter_folder, target))
        else:
            try:
                for entry in os.scandir(WWMI_CHAR_PATH):
                    if entry.is_dir():
                        folders_to_scan.append((entry.name, entry.path))
            except:
                pass

        for c_f, full_c in folders_to_scan:
            try:
                for entry in os.scandir(full_c):
                    if entry.is_dir():
                        m_f = entry.name
                        full_m = entry.path
                        is_disabled = m_f.startswith("DISABLED_")
                        clean_n = m_f.replace("DISABLED_", "")
                        
                        has_cover = os.path.exists(os.path.join(full_m, ".ResonaMod_Cover.jpg")) or os.path.exists(os.path.join(full_m, ".MewMod_Cover.jpg")) or os.path.exists(os.path.join(full_m, ".JASM_Cover.jpg"))
                        
                        author = "Modder"
                        note = ""
                        for cfg_name in [".ResonaMod_ModConfig.json", ".MewMod_ModConfig.json", ".JASM_ModConfig.json"]:
                            config_path = os.path.join(full_m, cfg_name)
                            if os.path.exists(config_path):
                                try:
                                    with open(config_path, "r", encoding="utf-8") as f:
                                        cfg = json.load(f)
                                        author = cfg.get("Author", "Modder")
                                        note = cfg.get("Note", "")
                                        break
                                except:
                                    pass
                                    
                        try:
                            mod_date = time.strftime('%m/%d/%Y', time.localtime(entry.stat().st_mtime))
                        except:
                            mod_date = "-"
                            
                        items.append({
                            "name": clean_n,
                            "clean_name": clean_n,
                            "char_folder": c_f,
                            "folder_name": m_f,
                            "full_path": full_m,
                            "is_enabled": not is_disabled,
                            "is_disabled": is_disabled,
                            "has_cover": has_cover,
                            "cover": "",
                            "cover_base64": "",
                            "author": author,
                            "date": mod_date,
                            "note": note
                        })
            except Exception:
                pass
        return items

    def get_mod_detail(self, full_path):
        if not os.path.exists(full_path):
            return None

        keybinds = parse_mod_ini_keybinds(full_path)
        config_path = os.path.join(full_path, ".ResonaMod_ModConfig.json")
        if not os.path.exists(config_path):
            config_path = os.path.join(full_path, ".MewMod_ModConfig.json")
        if not os.path.exists(config_path):
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

        # Scan all images inside mod directory
        all_imgs = []
        cover_path = os.path.join(full_path, ".ResonaMod_Cover.jpg")
        if not os.path.exists(cover_path):
            cover_path = os.path.join(full_path, ".MewMod_Cover.jpg")
        if not os.path.exists(cover_path):
            cover_path = os.path.join(full_path, ".JASM_Cover.jpg")
        if os.path.exists(cover_path):
            all_imgs.append({"path": cover_path, "name": "Ảnh Bìa (.ResonaMod_Cover.jpg)", "base64": get_image_base64_from_path(cover_path)})

        for root, dirs, files in os.walk(full_path):
            for f in files:
                p = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp'] and f.lower() not in [".resonamod_cover.jpg", ".mewmod_cover.jpg", ".jasm_cover.jpg"]:
                    b64 = get_image_base64_from_path(p)
                    if b64:
                        all_imgs.append({"path": p, "name": f, "base64": b64})

        if not os.path.exists(cover_path) and all_imgs:
            cover_path = os.path.join(full_path, ".ResonaMod_Cover.jpg")
            try:
                shutil.copy2(all_imgs[0]["path"], cover_path)
            except:
                pass
            cover_b64 = all_imgs[0]["base64"]
        else:
            cover_b64 = get_image_base64_from_path(cover_path)

        clean_n = os.path.basename(full_path).replace("DISABLED_", "")
        is_disabled = os.path.basename(full_path).startswith("DISABLED_")
        parent_folder = os.path.basename(os.path.dirname(full_path))

        total_bytes = 0
        file_count = 0
        for root, dirs, files in os.walk(full_path):
            for f in files:
                file_count += 1
                try:
                    total_bytes += os.path.getsize(os.path.join(root, f))
                except:
                    pass
        size_mb = round(total_bytes / (1024 * 1024), 2)
        mod_date = time.strftime('%d/%m/%Y', time.localtime(os.path.getmtime(full_path)))

        return {
            "name": clean_n,
            "clean_name": clean_n,
            "char_folder": parent_folder.upper(),
            "full_path": full_path,
            "is_enabled": not is_disabled,
            "is_disabled": is_disabled,
            "cover": cover_b64,
            "cover_base64": cover_b64,
            "images": all_imgs,
            "author": author,
            "description": desc,
            "note": note,
            "keybinds": keybinds,
            "size_mb": f"{size_mb} MB",
            "file_count": file_count,
            "mod_date": mod_date
        }

    def save_mod_detail(self, mod_json):
        data = json.loads(mod_json)
        full_path = data["full_path"]
        note = data.get("note", "")
        author = data.get("author", "")
        keybinds = data.get("keybinds", [])
        
        config_path = os.path.join(full_path, ".ResonaMod_ModConfig.json")
        cfg = {}
        for old_cfg in [config_path, os.path.join(full_path, ".MewMod_ModConfig.json"), os.path.join(full_path, ".JASM_ModConfig.json")]:
            if os.path.exists(old_cfg):
                try:
                    with open(old_cfg, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    break
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
            if is_enable:
                # Cơ chế độc quyền: Khi BẬT một skin, tự động TẮT tất cả skin khác của cùng nhân vật để không bao giờ bị xung đột
                char_folder_name = os.path.basename(parent_dir).lower()
                if char_folder_name != "others":
                    for other_item in os.listdir(parent_dir):
                        full_other = os.path.join(parent_dir, other_item)
                        if os.path.isdir(full_other) and not other_item.startswith("DISABLED_") and os.path.abspath(full_other) != os.path.abspath(full_path):
                            dis_other_name = f"DISABLED_{other_item}"
                            os.rename(full_other, os.path.join(parent_dir, dis_other_name))
                            self.log(f"⏸️ Tự động TẮT skin khác để tránh xung đột: {other_item}")

            if os.path.exists(full_path) and os.path.abspath(full_path) != os.path.abspath(new_path):
                os.rename(full_path, new_path)
                
            self.log(f"🔄 Đã {'BẬT' if is_enable else 'TẮT'} Mod: {base_name}")
            return {"success": True, "new_path": new_path}
        except Exception as e:
            self.log(f"❌ Lỗi toggle_mod: {e}")
            return {"success": False, "error": str(e)}

    def delete_mod(self, full_path):
        try:
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path, ignore_errors=True)
                else:
                    os.remove(full_path)
            self.log(f"🗑️ Đã xóa vĩnh viễn Mod: {os.path.basename(full_path)}")
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
            elif stable_texture:
                args.append("--stable-texture")
            if rendering33:
                args.append("--rendering-33")
                
        self.log(f"🔧 Đang chạy Sửa Lỗi Mod ({'Khôi phục' if rollback else 'Vá lỗi'}) trên: {os.path.basename(target_path)}...")
        try:
            res = run_silent_cmd(args)
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
                        if derived_hashes:
                            args.append("--derived-hashes")
                        elif stable_texture:
                            args.append("--stable-texture")
                        if rendering33:
                            args.append("--rendering-33")
                        run_silent_cmd(args)
                        count += 1
                        
        self.log(f"🎉 HOÀN TẤT! Đã sửa và tối ưu hóa {count} bản Mod cho phiên bản WuWa mới nhất.")


    def get_app_settings(self):
        game_launcher = APP_CONFIG.get("game_exe", XXMI_EXE if os.path.exists(XXMI_EXE) else "")
        has_3dmigoto = os.path.exists(os.path.join(WWMI_PATH, "3DMigoto Loader.exe")) or \
                       os.path.exists(os.path.join(WWMI_PATH, "d3dx.ini")) or \
                       os.path.exists(os.path.join(WWMI_PATH, "WWMI.exe"))
        has_mods_dir = os.path.isdir(WWMI_MODS_PATH)
        is_wwmi_valid = os.path.isdir(WWMI_PATH) and (has_3dmigoto or has_mods_dir)
        return {
            "wwmi_path": WWMI_PATH,
            "mods_path": WWMI_MODS_PATH,
            "char_path": WWMI_CHAR_PATH,
            "game_exe": game_launcher,
            "has_7z": os.path.exists(SEVEN_ZIP_PATH),
            "has_fixer": os.path.exists(WUWA_MOD_FIXER_EXE),
            "has_game_launcher": (bool(game_launcher) and os.path.exists(game_launcher)) or os.path.exists(XXMI_EXE) or os.path.exists(os.path.join(WWMI_PATH, "WWMI.exe")) or os.path.exists(os.path.join(WWMI_PATH, "3DMigoto Loader.exe")),
            "has_3dmigoto": has_3dmigoto,
            "has_mods_dir": has_mods_dir,
            "is_wwmi_valid": is_wwmi_valid,
            "version": APP_VERSION
        }

    def choose_wwmi_folder(self):
        try:
            chosen = self._window.create_file_dialog(webview.FileDialog.FOLDER)
            if chosen and len(chosen) > 0:
                p = chosen[0]
                if os.path.isdir(p):
                    self.set_wwmi_path(p)
                    return {"success": True, "path": p}
            return {"success": False, "msg": "Chưa chọn thư mục"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def reset_wwmi_path(self):
        if "wwmi_path" in APP_CONFIG:
            del APP_CONFIG["wwmi_path"]
            save_app_config(APP_CONFIG)
        default_p = resolve_wwmi_path()
        self.set_wwmi_path(default_p)
        self.log(f"🔄 Đã khôi phục đường dẫn WWMI mặc định: {default_p}")
        return {"success": True, "path": default_p}

    def choose_game_exe(self):
        try:
            chosen = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=('Executable files (*.exe)', 'All files (*.*)'))
            if chosen and len(chosen) > 0:
                p = chosen[0]
                if os.path.isfile(p):
                    APP_CONFIG["game_exe"] = p
                    save_app_config(APP_CONFIG)
                    self.log(f"🎮 Đã thiết lập trình khởi chạy game: {p}")
                    return {"success": True, "path": p}
            return {"success": False, "msg": "Chưa chọn tệp"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def set_wwmi_path(self, new_path):
        global WWMI_PATH, WWMI_MODS_PATH, WWMI_CHAR_PATH
        WWMI_PATH = os.path.abspath(new_path)
        WWMI_MODS_PATH = os.path.join(WWMI_PATH, "Mods") if os.path.exists(os.path.join(WWMI_PATH, "Mods")) else os.path.join(WWMI_PATH, "mods")
        WWMI_CHAR_PATH = os.path.join(WWMI_MODS_PATH, "Character") if os.path.exists(os.path.join(WWMI_MODS_PATH, "Character")) else os.path.join(WWMI_MODS_PATH, "character")
        os.makedirs(WWMI_CHAR_PATH, exist_ok=True)
        APP_CONFIG["wwmi_path"] = WWMI_PATH
        save_app_config(APP_CONFIG)
        self.log(f"📁 Đã cập nhật thư mục WWMI: {WWMI_PATH}")
        return True

    def choose_and_install_local_mod(self):
        try:
            chosen = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=('Mod Archives (*.zip;*.rar;*.7z;*.tar;*.gz)', 'All files (*.*)'))
            if not chosen or len(chosen) == 0:
                return {"success": False, "msg": "Chưa chọn tệp nén Mod"}
            
            for file_path in chosen:
                fname = os.path.basename(file_path)
                threading.Thread(target=self._install_local_archive_worker, args=(file_path, fname), daemon=True).start()
            return {"success": True, "count": len(chosen)}
        except Exception as e:
            self.log(f"⚠️ Lỗi chọn tệp: {e}")
            return {"success": False, "msg": str(e)}

    def _install_local_archive_worker(self, archive_path, fname):
        self.log(f"[Cài Đặt Cục Bộ] Bắt đầu giải nén & nạp mod: {fname}...")
        self._window.evaluate_js(f"window.showDownloadWidget('Cài đặt file: {fname.replace(chr(39), '')}');")
        try:
            temp_ext = os.path.join(os.environ.get("TEMP", ""), f"WuWaExtract_{int(time.time()*1000)%100000}")
            if os.path.exists(temp_ext):
                shutil.rmtree(temp_ext, ignore_errors=True)
            extract_archive(archive_path, temp_ext, password="huihui")
            char_f, clean_n, final_d = optimize_mod_structure(temp_ext, fname, fallback_folder="", author="Local Mod", desc=fname)
            shutil.rmtree(temp_ext, ignore_errors=True)
            self.log(f"🎉 Cài đặt thành công bản mod [{clean_n}] vào thư mục {char_f.upper()}!")
            self._window.evaluate_js(f"window.finishDownloadSuccess('{clean_n}', '{char_f}');")
        except Exception as e:
            self.log(f"❌ Lỗi cài đặt tệp {fname}: {e}")
            self._window.evaluate_js(f"window.finishDownloadError('{str(e)}');")

    def launch_game(self):
        # 1. Custom configured game / launcher exe
        custom_exe = APP_CONFIG.get("game_exe", "")
        if custom_exe and os.path.exists(custom_exe):
            try:
                subprocess.Popen([custom_exe], cwd=os.path.dirname(custom_exe))
                self.log(f"🎮 Đã khởi động game qua: {os.path.basename(custom_exe)}!")
                return {"success": True}
            except Exception as e:
                self.log(f"⚠️ Lỗi khởi chạy: {e}")

        # 2. XXMI Launcher
        if os.path.exists(XXMI_EXE):
            try:
                subprocess.Popen([XXMI_EXE, "--nogui", "--xxmi", "WWMI"])
                self.log("🎮 Đã khởi động WuWa qua XXMI Launcher (WWMI)!")
                return {"success": True}
            except Exception as e:
                self.log(f"⚠️ Lỗi chạy XXMI: {e}")

        # 3. WWMI.exe or 3DMigoto Loader.exe in WWMI_PATH
        wwmi_candidates = [
            os.path.join(WWMI_PATH, "WWMI.exe"),
            os.path.join(WWMI_PATH, "3DMigoto Loader.exe"),
            os.path.join(WWMI_PATH, "..", "WWMI.exe"),
            os.path.join(WWMI_PATH, "..", "3DMigoto Loader.exe"),
        ]
        for exe in wwmi_candidates:
            if os.path.exists(exe):
                try:
                    subprocess.Popen([exe], cwd=os.path.dirname(exe))
                    self.log(f"🎮 Đã khởi động trình nạp Mod: {os.path.basename(exe)}!")
                    return {"success": True}
                except Exception as e:
                    pass

        self.log("⚠️ Chưa tìm thấy file chạy game/WWMI. Đang mở Cài Đặt để bạn chọn file .exe...")
        self._window.evaluate_js("window.openSettingsModal();")
        return {"success": False, "msg": "Chưa chọn file khởi chạy game"}

    def check_app_update(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "ResonaMod", "Accept": "application/vnd.github.v3+json"}
            )
            try:
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=6) as r:
                    data = json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as http_err:
                if http_err.code == 404:
                    return {
                        "success": True,
                        "current_version": APP_VERSION,
                        "latest_version": APP_VERSION,
                        "has_update": False,
                        "title": "ResonaMod",
                        "changelog": "Bạn đang sử dụng phiên bản mới nhất!",
                        "html_url": f"https://github.com/{GITHUB_REPO}",
                        "direct_url": f"https://github.com/{GITHUB_REPO}"
                    }
                raise http_err

            latest_tag = data.get("tag_name", "").strip().lstrip("v")
            cur_tag = APP_VERSION.strip().lstrip("v")
            
            def parse_ver(v):
                return [int(x) for x in re.findall(r'\d+', v)] if v else [0]
                
            has_update = parse_ver(latest_tag) > parse_ver(cur_tag)
            
            assets = data.get("assets", [])
            download_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
            direct_url = ""
            for a in assets:
                aname = a.get("name", "").lower()
                if aname.endswith(".exe") or aname.endswith(".zip"):
                    direct_url = a.get("browser_download_url", "")
                    break
            
            return {
                "success": True,
                "current_version": APP_VERSION,
                "latest_version": latest_tag if latest_tag else APP_VERSION,
                "has_update": has_update,
                "title": data.get("name", f"Bản cập nhật v{latest_tag}"),
                "changelog": data.get("body", "Không có ghi chú phiên bản."),
                "html_url": download_url,
                "direct_url": direct_url if direct_url else download_url
            }
        except Exception as e:
            return {
                "success": False,
                "current_version": APP_VERSION,
                "has_update": False,
                "error": str(e)
            }

    def open_external_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# LOGO BIỂU TƯỢNG ỨNG DỤNG (BASE64)
# =============================================================================
LOGO_FILE = os.path.join(getattr(sys, '_MEIPASS', BASE_DIR), "logo.png")
if not os.path.exists(LOGO_FILE):
    LOGO_FILE = os.path.join(BASE_DIR, "logo.png")

if os.path.exists(LOGO_FILE):
    try:
        with open(LOGO_FILE, "rb") as f:
            APP_LOGO_B64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except:
        APP_LOGO_B64 = ""
else:
    APP_LOGO_B64 = ""


# =============================================================================
# HTML / CSS / JS GIAO DIỆN CHUẨN ĐỈNH CAO
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>ResonaMod Studio - Trình Quản Lý & Cấu Hình Mod Wuthering Waves</title>
<style>
  /* =========================================================================
     DESIGN SYSTEM TOKENS - V0 / SHADCN CYBER DARK THEME
     ========================================================================= */
  :root {
    /* Surfaces & Backgrounds */
    --bg-canvas: #07090e;
    --bg-sidebar: rgba(11, 14, 24, 0.95);
    --bg-surface: rgba(15, 19, 32, 0.85);
    --bg-elevated: rgba(24, 29, 49, 0.9);
    --bg-card: rgba(16, 20, 35, 0.75);
    --bg-card-hover: rgba(22, 28, 50, 0.9);
    --bg-overlay: rgba(4, 6, 12, 0.85);

    /* Borders & Glass Highlights */
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: rgba(255, 255, 255, 0.15);
    --border-focus: #00f0ff;
    --border-glow: rgba(0, 240, 255, 0.35);

    /* Typography */
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    /* Accents & Gradients */
    --accent: #00f0ff;
    --accent-hover: #38bdf8;
    --accent-subtle: rgba(0, 240, 255, 0.12);
    --accent-purple: #a855f7;
    --gradient-primary: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%);
    --gradient-accent: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
    --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
    --gradient-card: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0) 100%);

    --success: #10b981;
    --danger: #f43f5e;
    --warning: #f59e0b;

    /* Radii */
    --radius-xs: 5px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-full: 9999px;

    /* Shadows & Glows */
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.55);
    --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.75);
    --shadow-glow: 0 0 20px rgba(0, 240, 255, 0.25);
    --shadow-glow-purple: 0 0 20px rgba(168, 85, 247, 0.25);
    --transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }

  body {
    background: radial-gradient(circle at 50% -20%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 100% 100%, rgba(168, 85, 247, 0.07) 0%, transparent 50%),
                var(--bg-canvas);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-size: 13px;
    line-height: 1.45;
  }

  /* CUSTOM ULTRA SLIM SCROLLBAR */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.16); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(0, 240, 255, 0.4); }

  /* =========================================================================
     TOP HEADER & BRAND BAR
     ========================================================================= */
  header {
    height: 58px;
    background: var(--bg-surface);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    z-index: 20;
    flex-shrink: 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: default;
  }
  .brand-logo-wrap {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .brand-logo-wrap::after {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 10px;
    background: var(--gradient-primary);
    opacity: 0.5;
    filter: blur(6px);
    z-index: 0;
  }
  .brand-logo {
    width: 38px;
    height: 38px;
    border-radius: var(--radius-sm);
    object-fit: cover;
    border: 1.5px solid rgba(255, 255, 255, 0.2);
    position: relative;
    z-index: 1;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .brand:hover .brand-logo {
    transform: scale(1.1) rotate(-3deg);
  }
  .brand-text { display: flex; flex-direction: column; }
  .brand-title {
    font-size: 14.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(90deg, #ffffff 40%, #00f0ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .brand-badge {
    font-size: 9px;
    font-weight: 800;
    padding: 2px 7px;
    background: rgba(0, 240, 255, 0.15);
    color: var(--accent);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    -webkit-text-fill-color: var(--accent);
  }
  .brand-sub {
    font-size: 10.5px;
    color: var(--text-muted);
    font-weight: 500;
  }

  /* SEGMENTED NAVIGATION */
  .nav-segmented {
    display: flex;
    background: rgba(15, 23, 42, 0.65);
    padding: 3px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    gap: 3px;
  }
  .nav-item {
    background: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    padding: 0 12px;
    height: 28px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 5px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 6px;
    user-select: none;
  }
  .nav-item svg {
    opacity: 0.7;
    transition: opacity 0.15s ease;
  }
  .nav-item:hover:not(.active) {
    color: #f1f5f9;
    background: rgba(255, 255, 255, 0.06);
  }
  .nav-item:hover:not(.active) svg {
    opacity: 1;
  }
  .nav-item.active {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.18);
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  }
  .nav-item.active svg {
    opacity: 1;
    stroke: #38bdf8;
  }

  /* HEADER ACTIONS */
  .header-actions { display: flex; align-items: center; gap: 6px; }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    padding: 0 12px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid transparent;
    outline: none;
    white-space: nowrap;
    box-sizing: border-box;
    user-select: none;
  }
  .btn svg {
    flex-shrink: 0;
    opacity: 0.85;
    transition: opacity 0.15s ease;
  }
  .btn:hover svg {
    opacity: 1;
  }
  .btn:active { transform: translateY(1px); }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #cbd5e1;
  }
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
  }
  .btn-primary {
    background: #0284c7;
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }
  .btn-primary:hover {
    background: #0369a1;
    border-color: #7dd3fc;
    box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
  }
  .btn-accent {
    background: rgba(14, 165, 233, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }
  .btn-accent:hover {
    background: rgba(14, 165, 233, 0.22);
    border-color: #38bdf8;
    color: #ffffff;
  }
  .btn-danger {
    background: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.28);
  }
  .btn-danger:hover {
    background: rgba(239, 68, 68, 0.22);
    border-color: #ef4444;
    color: #ffffff;
  }

  /* =========================================================================
     MAIN WORKSPACE LAYOUT
     ========================================================================= */
  .workspace {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* SIDEBAR */
  aside {
    width: 255px;
    background: var(--bg-sidebar);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.25);
  }
  .sidebar-filter-wrap {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border-subtle);
    position: relative;
  }
  .sidebar-search {
    width: 100%;
    background: rgba(7, 9, 14, 0.7);
    border: 1px solid var(--border-subtle);
    padding: 8px 12px 8px 34px;
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 12px;
    outline: none;
    transition: var(--transition);
  }
  .sidebar-search:focus {
    background: rgba(12, 16, 28, 0.9);
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-subtle), 0 0 15px rgba(0, 240, 255, 0.15);
  }
  .sidebar-search-icon {
    position: absolute;
    left: 24px;
    top: 21px;
    color: var(--text-muted);
    font-size: 12px;
    pointer-events: none;
  }

  .sidebar-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 10px 8px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .sidebar-group-title {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: var(--text-muted);
    padding: 12px 10px 5px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .sidebar-group-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-subtle);
  }
  .char-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 10px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition);
    color: var(--text-secondary);
    border: 1px solid transparent;
  }
  .char-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    transform: translateX(2px);
  }
  .char-item.active {
    background: linear-gradient(90deg, rgba(0, 240, 255, 0.15) 0%, rgba(168, 85, 247, 0.08) 100%);
    color: var(--accent);
    font-weight: 700;
    border-color: rgba(0, 240, 255, 0.35);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  }
  .char-left {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow: hidden;
  }
  .char-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    object-fit: cover;
    background: var(--bg-canvas);
    border: 1.5px solid var(--border-subtle);
    flex-shrink: 0;
    transition: var(--transition);
  }
  .char-item:hover .char-avatar, .char-item.active .char-avatar {
    border-color: var(--accent);
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
  }
  .char-name {
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .char-badge {
    font-size: 10px;
    font-weight: 800;
    background: rgba(0, 240, 255, 0.1);
    color: var(--accent);
    border: 1px solid rgba(0, 240, 255, 0.3);
    padding: 1px 7px;
    border-radius: var(--radius-full);
  }

  /* MAIN CONTENT AREA */
  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: transparent;
    overflow: hidden;
  }

  /* TOOLBAR / BREADCRUMB */
  .toolbar {
    height: 50px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border-subtle);
    background: var(--bg-surface);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    flex-shrink: 0;
    gap: 12px;
  }
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .context-title {
    font-size: 13.5px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 0.3px;
  }
  .context-count {
    font-size: 11px;
    color: var(--accent);
    font-weight: 700;
    background: rgba(0, 240, 255, 0.1);
    padding: 3px 10px;
    border-radius: var(--radius-full);
    border: 1px solid rgba(0, 240, 255, 0.3);
  }

  .toolbar-search-wrap {
    position: relative;
    display: flex;
    align-items: center;
  }
  .toolbar-search {
    width: 260px;
    background: rgba(7, 9, 14, 0.7);
    border: 1px solid var(--border-subtle);
    padding: 7px 12px 7px 32px;
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 12px;
    outline: none;
    transition: var(--transition);
  }
  .toolbar-search:focus {
    width: 320px;
    background: rgba(12, 16, 28, 0.9);
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-subtle), 0 0 15px rgba(0, 240, 255, 0.2);
  }
  .toolbar-search-icon {
    position: absolute;
    left: 10px;
    color: var(--text-muted);
    font-size: 12px;
    pointer-events: none;
  }

  /* =========================================================================
     STORE GRID (ONLINE MODS - CYBER GLASS CARDS)
     ========================================================================= */
  .grid-container {
    flex: 1;
    overflow-y: auto;
    padding: 22px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 245px));
    gap: 20px;
    align-content: start;
  }
  .mod-card {
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 395px;
    transition: var(--transition);
    box-shadow: var(--shadow-sm);
    position: relative;
  }
  .mod-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-md);
    padding: 1px;
    background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 60%);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }
  .mod-card:hover {
    transform: translateY(-6px);
    background: var(--bg-card-hover);
    border-color: rgba(0, 240, 255, 0.4);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6), 0 0 25px rgba(0, 240, 255, 0.2);
  }

  /* SKELETON SHIMMER CARDS */
  .skeleton-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    overflow: hidden;
    height: 395px;
    display: flex;
    flex-direction: column;
  }
  .skeleton-img {
    width: 100%;
    height: 260px;
    background: linear-gradient(90deg, #0e111d 25%, #191e32 50%, #0e111d 75%);
    background-size: 200% 100%;
    animation: shimmer 1.2s infinite linear;
  }
  .skeleton-body {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    background: var(--bg-surface);
  }
  .skeleton-line {
    height: 12px;
    background: linear-gradient(90deg, #131726 25%, #212844 50%, #131726 75%);
    background-size: 200% 100%;
    border-radius: var(--radius-xs);
    animation: shimmer 1.2s infinite linear;
  }
  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .card-img-wrap {
    width: 100%;
    height: 260px;
    background: #06070c;
    position: relative;
    overflow: hidden;
    cursor: pointer;
  }
  .card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease;
  }
  .mod-card:hover .card-img {
    transform: scale(1.07);
  }
  .card-img-wrap.blurred .card-img {
    filter: blur(22px) brightness(0.5);
    transform: scale(1.2);
  }
  .card-img-wrap .blur-overlay {
    display: none;
    position: absolute;
    inset: 0;
    background: rgba(6, 8, 14, 0.65);
    backdrop-filter: blur(8px);
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 6px;
    z-index: 2;
    pointer-events: none;
  }
  .card-img-wrap.blurred .blur-overlay {
    display: flex;
  }
  .blur-overlay-icon {
    font-size: 30px;
    filter: drop-shadow(0 2px 10px rgba(0, 0, 0, 0.9));
  }
  .blur-overlay-text {
    font-size: 11px;
    font-weight: 800;
    color: #f59e0b;
    background: rgba(0, 0, 0, 0.85);
    padding: 3px 12px;
    border-radius: var(--radius-full);
    border: 1px solid rgba(245, 158, 11, 0.4);
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
  }

  .badge-like {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(7, 9, 14, 0.85);
    backdrop-filter: blur(8px);
    color: #f43f5e;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: var(--radius-full);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .card-body {
    padding: 12px;
    display: flex;
    flex-direction: column;
    flex: 1;
    justify-content: space-between;
    background: var(--bg-surface);
    border-top: 1px solid var(--border-subtle);
  }
  .card-title {
    font-size: 12.5px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 35px;
    cursor: pointer;
    transition: color 0.15s ease;
  }
  .card-title:hover {
    color: var(--accent);
  }
  .card-author {
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
    margin-bottom: 6px;
  }

  .card-actions {
    display: flex;
    gap: 6px;
    margin-top: 8px;
  }
  .btn-card-dl {
    flex: 1.2;
    background: #0284c7;
    border: 1px solid #38bdf8;
    color: #fff;
    padding: 6px 8px;
    height: 28px;
    font-size: 11.5px;
    font-weight: 600;
    border-radius: 5px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    white-space: nowrap;
    box-sizing: border-box;
  }
  .btn-card-dl:hover {
    background: #0369a1;
    border-color: #7dd3fc;
  }
  .btn-card-blur {
    flex: 0.8;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #94a3b8;
    padding: 6px 6px;
    height: 28px;
    font-size: 11px;
    font-weight: 500;
    border-radius: 5px;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    box-sizing: border-box;
  }
  .btn-card-blur:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #f1f5f9;
    border-color: rgba(255, 255, 255, 0.18);
  }
  .btn-card-blur.active {
    background: rgba(245, 158, 11, 0.12);
    border-color: rgba(245, 158, 11, 0.35);
    color: #fbbf24;
  }

  /* =========================================================================
     INSTALLED VIEW (JASM PRO DATA TABLE + RIGHT INSPECTOR)
     ========================================================================= */
  .installed-split {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  .installed-table-area {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .mod-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 12.5px;
    background: var(--bg-surface);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: var(--radius-md);
    overflow: hidden;
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-sm);
  }
  .mod-table th {
    text-align: left;
    padding: 12px 16px;
    background: var(--bg-elevated);
    color: var(--text-muted);
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid var(--border-subtle);
    position: sticky;
    top: 0;
    z-index: 2;
  }
  .mod-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-subtle);
    color: var(--text-primary);
  }
  .mod-table tr {
    cursor: pointer;
    transition: var(--transition);
  }
  .mod-table tr:hover { background: rgba(255, 255, 255, 0.04); }
  .mod-table tr.selected {
    background: linear-gradient(90deg, rgba(0, 240, 255, 0.12) 0%, rgba(168, 85, 247, 0.05) 100%);
    border-left: 3px solid var(--accent);
  }

  /* RIGHT INSPECTOR PANEL */
  .inspector {
    width: 420px;
    background: var(--bg-sidebar);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-left: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 20px;
    gap: 16px;
    flex-shrink: 0;
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
  }
  .inspector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .inspector-title {
    font-size: 14.5px;
    font-weight: 800;
    color: var(--accent);
    letter-spacing: 0.4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .cover-box {
    width: 100%;
    height: 360px;
    background: #040509;
    border-radius: var(--radius-md);
    overflow: hidden;
    position: relative;
    border: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.8), var(--shadow-sm);
  }
  .cover-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
    transition: transform 0.3s ease;
  }
  .cover-box:hover .cover-img { transform: scale(1.03); }
  .cover-actions-overlay {
    position: absolute;
    bottom: 12px;
    right: 12px;
    display: flex;
    gap: 6px;
    z-index: 2;
  }
  .cover-action-btn {
    background: rgba(7, 9, 14, 0.9);
    backdrop-filter: blur(8px);
    color: #fff;
    font-size: 10.5px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-medium);
    cursor: pointer;
    transition: var(--transition);
  }
  .cover-action-btn:hover {
    background: rgba(0, 240, 255, 0.25);
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
  }
  .cover-zoom-hint {
    background: rgba(7, 9, 14, 0.9);
    color: var(--accent);
    font-size: 10.5px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-medium);
    pointer-events: none;
    box-shadow: var(--shadow-sm);
  }
  .gallery-strip {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 4px 0 8px;
  }
  .gallery-thumb {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-xs);
    object-fit: cover;
    border: 2px solid var(--border-subtle);
    cursor: pointer;
    flex-shrink: 0;
    transition: var(--transition);
  }
  .gallery-thumb:hover, .gallery-thumb.active {
    border-color: var(--accent);
    transform: scale(1.08);
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
  }
  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .meta-pill {
    background: rgba(7, 9, 14, 0.7);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .meta-lbl {
    font-size: 9.5px;
    font-weight: 800;
    color: var(--text-muted);
    letter-spacing: 0.5px;
  }
  .meta-val {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .form-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }
  .form-input {
    background: rgba(7, 9, 14, 0.7);
    border: 1px solid var(--border-subtle);
    padding: 9px 12px;
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 12px;
    outline: none;
    transition: var(--transition);
  }
  .form-input:focus {
    background: rgba(12, 16, 28, 0.9);
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-subtle), 0 0 12px rgba(0, 240, 255, 0.2);
  }

  /* KEYBINDS LIST */
  .keybinds-box {
    background: rgba(7, 9, 14, 0.7);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .keybind-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-surface);
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
  }
  .keybind-name { font-size: 11.5px; color: var(--accent); font-weight: 700; }
  .keybind-input {
    width: 65px;
    text-align: center;
    background: rgba(7, 9, 14, 0.9);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #10b981;
    font-weight: 800;
    padding: 5px;
    border-radius: var(--radius-xs);
    font-size: 11.5px;
    outline: none;
    box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.5);
  }

  /* TOGGLE SWITCH */
  .switch { position: relative; display: inline-block; width: 38px; height: 22px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider {
    position: absolute; cursor: pointer; inset: 0;
    background-color: #1e2438; transition: .25s; border-radius: var(--radius-full);
    border: 1px solid var(--border-subtle);
  }
  .slider:before {
    position: absolute; content: ""; height: 16px; width: 16px; left: 2px; bottom: 2px;
    background-color: white; transition: .25s; border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
  }
  input:checked + .slider {
    background: var(--gradient-success);
    border-color: rgba(16, 185, 129, 0.6);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
  }
  input:checked + .slider:before { transform: translateX(16px); }

  /* =========================================================================
     MODAL DIALOGS & CYBER CARDS (TOP-TIER V0 / SHADCN PRO)
     ========================================================================= */
  .modal-overlay {
    position: fixed; inset: 0;
    background: var(--bg-overlay);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    display: none; align-items: center; justify-content: center; z-index: 100;
    animation: modalOverlayFade 0.2s ease-out;
  }
  .modal-overlay.active { display: flex; }
  .modal-box {
    background: #0d121f;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.75);
    overflow: hidden;
    animation: modalBoxScale 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
  }
  @keyframes modalOverlayFade { from { opacity: 0; } to { opacity: 1; } }
  @keyframes modalBoxScale { from { opacity: 0; transform: scale(0.96) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

  /* CARDS */
  .cyber-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 14px 16px;
    transition: all 0.15s ease;
    position: relative;
  }
  .cyber-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.16);
  }
  .cyber-card-title {
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .cyber-card-desc {
    font-size: 11.5px;
    color: var(--text-muted);
    margin-top: 4px;
    line-height: 1.45;
  }

  /* BADGE TAGS */
  .badge-tag {
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .badge-tag.cyan {
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.25);
  }
  .badge-tag.amber {
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.25);
  }
  .badge-tag.green {
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }
  .badge-tag.purple {
    background: rgba(168, 85, 247, 0.12);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.25);
  }

  /* TERMINAL WINDOW */
  .terminal-window {
    background: #04060a;
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8), 0 4px 16px rgba(0, 0, 0, 0.5);
  }
  .terminal-header {
    height: 28px;
    background: rgba(14, 18, 30, 0.95);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
  }
  .terminal-dots {
    display: flex;
    gap: 6px;
  }
  .terminal-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }
  .terminal-dot.red { background: #ef4444; }
  .terminal-dot.yellow { background: #f59e0b; }
  .terminal-dot.green { background: #10b981; }
  .terminal-title {
    font-size: 10px;
    color: var(--text-muted);
    font-family: var(--font-mono);
    letter-spacing: 0.5px;
  }
  .terminal-body {
    height: 140px;
    padding: 12px 14px;
    font-family: 'Consolas', 'Fira Code', monospace;
    font-size: 11.5px;
    color: #93c5fd;
    overflow-y: auto;
    line-height: 1.5;
  }

  /* METRIC DASHBOARD CARDS */
  .metric-card {
    background: rgba(14, 18, 30, 0.85);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 14px;
    text-align: center;
    transition: var(--transition);
  }
  .metric-card:hover {
    border-color: rgba(0, 240, 255, 0.35);
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 240, 255, 0.15);
  }
  .metric-label {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }
  .metric-value {
    font-size: 13px;
    font-weight: 800;
    margin-top: 5px;
  }

  /* STEP GUIDE CARDS */
  .step-card {
    background: rgba(10, 14, 24, 0.7);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: 10px 12px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .step-num {
    width: 22px;
    height: 22px;
    background: rgba(0, 240, 255, 0.15);
    color: var(--accent);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 800;
    flex-shrink: 0;
  }
  .step-text {
    font-size: 11px;
    color: var(--text-secondary);
    line-height: 1.45;
  }

  /* NON-BLOCKING FLOATING CORNER DOWNLOAD WIDGET */
  .corner-dl-widget {
    position: fixed;
    top: 70px;
    right: 22px;
    width: 370px;
    background: rgba(13, 17, 30, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-md);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8), 0 0 25px rgba(0, 240, 255, 0.2);
    padding: 16px 18px;
    z-index: 9999;
    display: none;
    flex-direction: column;
    animation: slideInDown 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  .corner-dl-widget.active { display: flex; }
  .corner-dl-widget.success {
    border-color: rgba(16, 185, 129, 0.6);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8), 0 0 25px rgba(16, 185, 129, 0.3);
  }
  .corner-dl-widget.error {
    border-color: rgba(244, 63, 94, 0.6);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8), 0 0 25px rgba(244, 63, 94, 0.3);
  }
  .corner-dl-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .corner-dl-title-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow: hidden;
  }
  .corner-dl-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(0, 240, 255, 0.2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .corner-dl-title {
    font-size: 12.5px;
    font-weight: 700;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .corner-dl-close {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 13px;
    cursor: pointer;
    padding: 2px 7px;
    border-radius: var(--radius-xs);
    transition: var(--transition);
  }
  .corner-dl-close:hover { color: #fff; background: rgba(255, 255, 255, 0.12); }
  .corner-dl-subtitle {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .corner-dl-footer {
    display: flex;
    justify-content: space-between;
    font-size: 10.5px;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }
  @keyframes slideInDown {
    from { opacity: 0; transform: translateY(-18px) scale(0.96); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* PROGRESS BAR */
  .progress-wrap {
    background: rgba(7, 9, 14, 0.8);
    height: 7px;
    border-radius: var(--radius-full);
    overflow: hidden;
    margin: 10px 0 6px;
    border: 1px solid var(--border-subtle);
  }
  .progress-fill {
    height: 100%;
    width: 0%;
    background: var(--gradient-primary);
    transition: width 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
  }

  /* =========================================================================
     BOTTOM STATUS BAR
     ========================================================================= */
  .status-bar {
    height: 32px;
    background: var(--bg-surface);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-top: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    font-size: 11.5px;
    color: var(--text-muted);
    flex-shrink: 0;
    z-index: 10;
  }
  .status-left { display: flex; align-items: center; gap: 9px; overflow: hidden; }
  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.8);
  }
  .status-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-secondary); }
</style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="brand">
      <div class="brand-logo-wrap">
        <img class="brand-logo" src="{APP_LOGO_B64}" alt="Logo">
      </div>
      <div class="brand-text">
        <div class="brand-title">
          RESONAMOD <span class="brand-badge">v{APP_VERSION}</span>
        </div>
        <div class="brand-sub">Trình Quản Lý & Cài Đặt Mod Wuthering Waves</div>
      </div>
    </div>

    <!-- SEGMENTED TABS -->
    <div class="nav-segmented">
      <button class="nav-item active" id="tab-gb" onclick="switchStore('gamebanana')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        GameBanana
      </button>
      <button class="nav-item" id="tab-hh" onclick="switchStore('huihui168')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        Huihui168
      </button>
      <button class="nav-item" id="tab-nx" onclick="switchStore('nexus')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 12h4m-2-2v4m7-3h.01m3 2h.01"/></svg>
        NexusMods
      </button>
      <button class="nav-item" id="tab-inst" onclick="switchView('installed')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        Mods Đã Cài
      </button>
      <button class="nav-item" id="tab-imp" onclick="switchView('direct_link')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Nhập Link
      </button>
    </div>

    <!-- ACTIONS -->
    <div class="header-actions">
      <button class="btn" id="btn-update-badge" onclick="openUpdateModal()" style="display: none; background: #059669; border: 1px solid #34d399; color: #fff; font-weight: 600;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
        Cập Nhật <span id="lbl-new-ver"></span>
      </button>
      <button class="btn btn-secondary" onclick="openWelcomeWizardModal()" title="Hướng dẫn sử dụng & liên kết WWMI">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        Hướng Dẫn
      </button>
      <button class="btn btn-secondary" onclick="openSettingsModal()" title="Cài đặt đường dẫn WWMI, game launcher...">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        Cài Đặt
      </button>
      <button class="btn btn-secondary" onclick="openFixerModal()" title="Sửa lỗi vertex, hash, model skin">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        Vá Lỗi Mod
      </button>
      <button class="btn btn-secondary" onclick="window.pywebview.api.reload_wwmi_mods()" title="Nạp lại skin trong game (F10)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        Nạp Lại (F10)
      </button>
      <button class="btn btn-secondary" onclick="window.pywebview.api.open_folder('')" title="Mở thư mục chứa Mods">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        Thư Mục Mod
      </button>
      <button class="btn btn-secondary" onclick="window.pywebview.api.open_external_url('https://discord.gg/tuRCj47sy')" title="Tham gia Discord cộng đồng giao lưu & hỗ trợ">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
        Discord
      </button>
      <button class="btn btn-primary" onclick="window.pywebview.api.launch_game()" title="Khởi động Wuthering Waves qua WWMI">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Khởi Chạy Game
      </button>
    </div>
  </header>

  <!-- MAIN WORKSPACE -->
  <div class="workspace">
    <!-- LEFT SIDEBAR -->
    <aside>
      <div class="sidebar-filter-wrap">
        <span class="sidebar-search-icon">🔍</span>
        <input type="text" class="sidebar-search" id="sidebar-filter-input" placeholder="Tìm nhân vật..." oninput="filterSidebarList(this.value)">
      </div>
      <div class="sidebar-scroll" id="char-list">
        <!-- Characters Rendered via JS -->
      </div>
    </aside>

    <!-- CONTENT AREA -->
    <main>
      <!-- TOOLBAR -->
      <div class="toolbar" id="filter-bar">
        <div class="toolbar-left">
          <span class="context-title" id="context-char-name">Tất Cả Nhân Vật</span>
          <span class="context-count" id="context-mod-count">Đang tải...</span>
        </div>

        <!-- SEARCH BOX -->
        <div class="toolbar-search-wrap">
          <span class="toolbar-search-icon">🔍</span>
          <input type="text" class="toolbar-search" id="search-input" placeholder="Tìm kiếm bản Mod..." onkeypress="handleSearchKey(event)">
        </div>

        <!-- BULK ACTIONS -->
        <div id="store-bulk-actions" style="display: flex; gap: 6px;">
          <button class="btn btn-secondary" id="btn-safe-mode" style="height: 28px; padding: 0 10px; font-size: 11.5px;" onclick="toggleSafeMode()" title="Bật/tắt chế độ làm mờ ảnh xem trước">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <span>Safe Mode: TẮT</span>
          </button>
        </div>
        <div id="installed-bulk-actions" style="display: none; gap: 6px;">
          <button class="btn btn-danger" style="height: 28px; padding: 0 10px; font-size: 11px;" onclick="toggleAllModsForCurrentChar(false)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/></svg>
            <span>Tắt Toàn Bộ</span>
          </button>
          <button class="btn btn-accent" style="height: 28px; padding: 0 10px; font-size: 11px;" onclick="toggleAllModsForCurrentChar(true)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Bật Toàn Bộ</span>
          </button>
          <button class="btn btn-secondary" style="height: 28px; padding: 0 10px; font-size: 11px;" onclick="loadInstalled(currentCharFolder)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            <span>Làm Mới</span>
          </button>
        </div>
      </div>

      <!-- STORE MOD GRID -->
      <div class="grid-container" id="mod-grid">
        <!-- Mod Cards Rendered via JS -->
      </div>

      <!-- INSTALLED VIEW -->
      <div class="installed-split" id="installed-view" style="display: none;">
        <div class="installed-table-area">
          <table class="mod-table">
            <thead>
              <tr>
                <th style="width: 50px; text-align: center;">BẬT</th>
                <th>TÊN BẢN MOD</th>
                <th style="width: 140px;">TÁC GIẢ</th>
                <th style="width: 130px;">TRẠNG THÁI</th>
                <th style="width: 140px; text-align: right;">THAO TÁC</th>
              </tr>
            </thead>
            <tbody id="installed-tbody">
              <!-- Installed Rows -->
            </tbody>
          </table>
        </div>

        <!-- RIGHT INSPECTOR -->
        <div class="inspector" id="inspector-panel">
          <div class="inspector-header">
            <div class="inspector-title">THÔNG TIN MOD</div>
            <button class="btn btn-secondary" style="height: 26px; padding: 0 8px; font-size: 11px;" onclick="openSelectedModFolder()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              <span>Mở Thư Mục</span>
            </button>
          </div>

          <!-- HERO PREVIEW COVER -->
          <div class="cover-box" id="insp-cover-box" onclick="openInspectorFullPreview()" title="Bấm để xem ảnh phóng to toàn màn hình">
            <img src="" id="insp-cover-img" class="cover-img" style="display: none;">
            <div id="insp-no-cover" style="color: var(--text-muted); font-size: 11px;">Chưa có ảnh bìa (.ResonaMod_Cover.jpg)</div>
            <div class="cover-actions-overlay">
              <button class="cover-action-btn" onclick="event.stopPropagation(); toggleCoverFit();" title="Chuyển chế độ Vừa Khung / Đầy Khung" id="btn-cover-fit">📐 Vừa Khung</button>
              <div class="cover-zoom-hint" id="insp-zoom-hint" style="display: none;">🔍 Phóng To</div>
            </div>
          </div>

          <!-- SCREENSHOTS GALLERY STRIP -->
          <div id="insp-gallery-wrap" style="display: none;">
            <div class="form-label" style="margin-bottom: 4px; font-size: 10px;">📸 Album Ảnh Mod (<span id="insp-img-count">0</span> ảnh):</div>
            <div class="gallery-strip" id="insp-gallery-strip"></div>
          </div>

          <!-- METADATA BADGES -->
          <div class="meta-grid" id="insp-meta-grid">
            <div class="meta-pill">
              <span class="meta-lbl">👤 NHÂN VẬT</span>
              <span class="meta-val" id="insp-meta-char">-</span>
            </div>
            <div class="meta-pill">
              <span class="meta-lbl">💾 DUNG LƯỢNG</span>
              <span class="meta-val" id="insp-meta-size">-</span>
            </div>
            <div class="meta-pill">
              <span class="meta-lbl">📅 NGÀY CÀI</span>
              <span class="meta-val" id="insp-meta-date">-</span>
            </div>
            <div class="meta-pill">
              <span class="meta-lbl">⚡ TRẠNG THÁI</span>
              <span class="meta-val" id="insp-meta-status">-</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Tên Bản Mod</label>
            <input type="text" class="form-input" id="insp-name" placeholder="Tên mod...">
          </div>

          <div class="form-group">
            <label class="form-label">Tác GiẢ</label>
            <input type="text" class="form-input" id="insp-author" placeholder="Tác giả...">
          </div>

          <div class="form-group">
            <label class="form-label">Ghi Chú Riêng</label>
            <input type="text" class="form-input" id="insp-note" placeholder="Ghi chú...">
          </div>

          <div class="form-group">
            <label class="form-label">Phím Tắt Phụ Kiện (mod.ini)</label>
            <div class="keybinds-box" id="insp-keybinds">
              <!-- Keybind Rows -->
            </div>
          </div>

          <div style="display: flex; gap: 6px; margin-top: auto; padding-top: 10px;">
            <button class="btn btn-primary" style="flex: 1;" onclick="saveSelectedModConfig()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              <span>Lưu Cấu Hình</span>
            </button>
            <button class="btn btn-accent" onclick="openFixerModal(selectedModDetail ? selectedModDetail.full_path : null)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              <span>Sửa Lỗi</span>
            </button>
            <button class="btn btn-danger" onclick="deleteCurrentInspectedMod()" title="Xóa vĩnh viễn bản mod này">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              <span>Xóa</span>
            </button>
          </div>
        </div>
      </div>

      <!-- DIRECT LINK / LOCAL ARCHIVE IMPORT VIEW -->
      <div id="direct-link-view" style="display: none; padding: 28px; max-width: 820px; margin: 0 auto; width: 100%;">
        <!-- CARD 1: LOCAL MOD ARCHIVE -->
        <div class="cyber-card" style="margin-bottom: 22px; padding: 26px; border-color: rgba(0, 240, 255, 0.25);">
          <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(0, 240, 255, 0.12); border: 1px solid rgba(0, 240, 255, 0.35); display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);">
              📦
            </div>
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px; font-weight: 800; color: #fff;">Cài Đặt Mod Từ File Trên Máy</span>
                <span class="badge-tag cyan">1-CLICK EXTRACT</span>
              </div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-top: 5px; line-height: 1.5;">
                Hỗ trợ các định dạng <b>.zip, .7z, .rar</b>. Tự động nhận diện nhân vật WuWa, giải mã mật khẩu nén (pass huihui168), chuẩn hóa cấu trúc thư mục và nạp trực tiếp vào game.
              </div>
              <div style="margin-top: 18px;">
                <button class="btn btn-primary" style="padding: 12px 24px; font-size: 13px; font-weight: 700; width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px;" onclick="window.pywebview.api.choose_and_install_local_mod()">
                  <span>📂</span> Chọn Tệp Nén Mod Từ Máy Tính Để Cài Đặt
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- CARD 2: DIRECT LINK -->
        <div class="cyber-card" style="padding: 26px; border-color: rgba(168, 85, 247, 0.25);">
          <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.35); display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; box-shadow: 0 0 15px rgba(168, 85, 247, 0.2);">
              🌐
            </div>
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px; font-weight: 800; color: #fff;">Nhập Mod Từ Liên Kết Trực Tiếp</span>
                <span class="badge-tag purple">DIRECT DOWNLOAD</span>
              </div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-top: 5px; line-height: 1.5;">
                Dán link tải từ Cloudreve (Hui盤), GameBanana, NexusMods hoặc Google Drive để tự động tải về, giải nén và kích hoạt.
              </div>
              <div style="display: flex; gap: 10px; margin-top: 18px;">
                <input type="text" id="direct-link-input" class="form-input" style="flex: 1; padding: 11px 16px; font-size: 12.5px;" placeholder="Dán liên kết mod (https://...) vào đây...">
                <button class="btn btn-primary" style="padding: 11px 20px; font-size: 13px;" onclick="submitDirectLink()">⚡ Cài Đặt Ngay</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- STATUS BAR -->
  <div class="status-bar">
    <div class="status-left">
      <div class="status-dot"></div>
      <div class="status-text" id="status-log-text">Hệ thống ResonaMod Studio đã sẵn sàng hoạt động.</div>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
      <div>Khung nạp WWMI: <span style="color: var(--accent); font-weight: 800;">SẴN SÀNG</span></div>
      <div style="width: 1px; height: 14px; background: var(--border-subtle);"></div>
      <div>Phím nạp trong game: <span style="color: #10b981; font-weight: 800; background: rgba(16, 185, 129, 0.15); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.3);">F10</span></div>
    </div>
  </div>

  <!-- WELCOME SETUP WIZARD MODAL -->
  <div class="modal-overlay" id="welcome-wizard-modal" style="display: none;">
    <div class="modal-box" style="width: 820px; max-width: 95vw; padding: 26px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); display: flex; align-items: center; justify-content: center; color: #38bdf8;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #fff; letter-spacing: 0.2px;">HƯỚNG DẪN THIẾT LẬP & LIÊN KẾT WWMI</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">Thiết lập kết nối để mod tự động nạp vào game Wuthering Waves</div>
          </div>
        </div>
        <button class="btn btn-secondary" style="color: var(--danger); padding: 4px 10px;" onclick="closeWelcomeWizardModal()">✕ Đóng</button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px; max-height: 65vh; overflow-y: auto; padding-right: 4px;">
        <!-- Card 1: 2 Easy Setup Methods -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="cyber-card" style="border-color: rgba(16, 185, 129, 0.35);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
              <span style="font-size: 13px; font-weight: 700; color: #10b981;">CÁCH 1: ĐẶT TRONG THƯ MỤC WWMI</span>
              <span class="badge-tag green">KHUYÊN DÙNG</span>
            </div>
            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
              Copy hoặc giải nén thư mục <b>ResonaMod</b> bỏ trực tiếp vào trong thư mục <b>WWMI</b> của bạn.<br>
              <span style="color: var(--accent); font-family: var(--font-mono); font-size: 10.5px; display: block; margin-top: 6px; background: rgba(0,0,0,0.4); padding: 4px 8px; border-radius: 4px;">WWMI/ ➔ ResonaMod/ ➔ ResonaMod.exe</span>
              <div style="margin-top: 6px; color: #10b981; font-weight: 600;">Tự động nhận diện 100%, không cần cài đặt thêm.</div>
            </div>
          </div>

          <div class="cyber-card" style="border-color: rgba(56, 189, 248, 0.35);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
              <span style="font-size: 13px; font-weight: 700; color: #38bdf8;">CÁCH 2: CHỌN THƯ MỤC</span>
              <span class="badge-tag cyan">LINH HOẠT</span>
            </div>
            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
              Nếu bạn để tool ở thư mục khác, hãy bấm nút bên dưới để chọn đường dẫn tới thư mục WWMI.<br>
              <div style="margin-top: 10px;">
                <button class="btn btn-secondary" style="font-size: 11.5px; width: 100%; height: 32px;" onclick="chooseWwmiFolderInWizard()">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                  <span>Chọn Thư Mục WWMI</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 2: Live Verification Status -->
        <div class="cyber-card" style="background: rgba(15, 23, 42, 0.6);">
          <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
            <span>TÌNH TRẠNG KẾT NỐI HIỆN TẠI:</span>
            <span id="wiz-overall-badge" class="badge-tag green">ĐÃ KẾT NỐI</span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div style="background: rgba(14, 18, 30, 0.9); padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Thư mục WWMI:</div>
              <div style="font-size: 11px; font-weight: 600; color: var(--accent); margin-top: 3px; word-break: break-all;" id="wiz-wwmi-path">Đang kiểm tra...</div>
            </div>
            <div style="background: rgba(14, 18, 30, 0.9); padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Bộ nạp 3DMigoto:</div>
              <div style="font-size: 11.5px; font-weight: 600; color: #10b981; margin-top: 3px;" id="wiz-3d-status">Sẵn Sàng</div>
            </div>
            <div style="background: rgba(14, 18, 30, 0.9); padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Thư mục Mods:</div>
              <div style="font-size: 11.5px; font-weight: 600; color: #10b981; margin-top: 3px;" id="wiz-mods-status">Hợp Lệ</div>
            </div>
          </div>
        </div>

        <!-- Card 3: 3-Step Simple Play Guide -->
        <div class="cyber-card" style="background: rgba(56, 189, 248, 0.03); border-color: rgba(56, 189, 248, 0.2);">
          <div style="font-size: 12px; font-weight: 700; color: #38bdf8; margin-bottom: 10px;">
            3 BƯỚC ĐỂ BẮT ĐẦU:
          </div>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div class="step-card">
              <div class="step-num">1</div>
              <div class="step-text"><b>Tải Mod:</b> Chọn nhân vật ở cột trái ➔ Bấm <b>Tải Xuống</b> ở mod muốn chơi.</div>
            </div>
            <div class="step-card">
              <div class="step-num">2</div>
              <div class="step-text"><b>Vào Game:</b> Bấm <b>Khởi Chạy Game</b> ở góc trên cùng.</div>
            </div>
            <div class="step-card">
              <div class="step-num">3</div>
              <div class="step-text"><b>Nạp Skin:</b> Nhấn phím <b>F10</b> trên bàn phím khi đang trong game để nạp skin.</div>
            </div>
          </div>
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
        <button class="btn btn-secondary" onclick="chooseWwmiFolderInWizard()">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <span>Chọn Thư Mục WWMI Khác</span>
        </button>
        <button class="btn btn-primary" style="height: 34px; padding: 0 20px;" onclick="completeWelcomeWizard()">Bắt Đầu Sử Dụng</button>
      </div>
    </div>
  </div>

  <!-- UPDATE MODAL -->
  <div class="modal-overlay" id="update-modal" style="display: none;">
    <div class="modal-box" style="width: 560px; max-width: 95vw; padding: 26px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); display: flex; align-items: center; justify-content: center; color: #38bdf8;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #fff;" id="update-modal-title">CẬP NHẬT PHIÊN BẢN RESONAMOD</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">Phiên bản đang chạy: <b id="lbl-cur-ver" style="color: var(--accent);">v{APP_VERSION}</b></div>
          </div>
        </div>
        <button class="btn btn-secondary" style="color: var(--danger); padding: 4px 10px;" onclick="closeUpdateModal()">✕ Đóng</button>
      </div>
      <div id="update-modal-body" style="margin-bottom: 20px;">
        <!-- Body content generated by JS -->
      </div>
      <div id="update-modal-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn btn-secondary" onclick="closeUpdateModal()">Đóng</button>
      </div>
    </div>
  </div>

  <!-- SETTINGS MODAL -->
  <div class="modal-overlay" id="settings-modal" style="display: none;">
    <div class="modal-box" style="width: 760px; max-width: 95vw; padding: 26px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); display: flex; align-items: center; justify-content: center; color: #38bdf8;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #fff; letter-spacing: 0.2px;">CÀI ĐẶT HỆ THỐNG & ĐƯỜNG DẪN WWMI</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">Tùy chỉnh thư mục Mod, trình nạp game và kiểm tra tình trạng hệ thống</div>
          </div>
        </div>
        <button class="btn btn-secondary" style="color: var(--danger); padding: 4px 10px;" onclick="closeSettingsModal()">✕ Đóng</button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px; max-height: 65vh; overflow-y: auto; padding-right: 4px;">
        <!-- WWMI Path Card -->
        <div class="cyber-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div class="cyber-card-title">Thư Mục Mods WWMI:</div>
            <span class="badge-tag green">ACTIVE FOLDER</span>
          </div>
          <div style="font-size: 11.5px; color: var(--accent); font-family: var(--font-mono); word-break: break-all; margin-bottom: 12px; background: rgba(4, 6, 12, 0.85); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid rgba(0, 240, 255, 0.2);" id="set-wwmi-path">Đang tải...</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-secondary" style="font-size: 11.5px;" onclick="chooseWwmiFolder()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              <span>Chọn Thư Mục Khác</span>
            </button>
            <button class="btn btn-secondary" style="font-size: 11.5px;" onclick="window.pywebview.api.open_folder('')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              <span>Mở Thư Mục Này</span>
            </button>
            <button class="btn btn-secondary" style="font-size: 11.5px;" onclick="resetWwmiFolder()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              <span>Khôi Phục Tự Động</span>
            </button>
          </div>
        </div>

        <!-- Game Launcher Path Card -->
        <div class="cyber-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div class="cyber-card-title">Trình Khởi Chạy Game (.exe):</div>
            <span class="badge-tag cyan">AUTO LOADER</span>
          </div>
          <div style="font-size: 11.5px; color: var(--text-secondary); font-family: var(--font-mono); word-break: break-all; margin-bottom: 12px; background: rgba(4, 6, 12, 0.85); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);" id="set-game-exe">Tự động nhận diện (XXMI Launcher / WWMI Loader)</div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary" style="font-size: 11.5px;" onclick="chooseGameExe()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>Chọn File Khởi Chạy (.exe)</span>
            </button>
            <button class="btn btn-secondary" style="font-size: 11.5px;" onclick="window.pywebview.api.launch_game()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <span>Thử Khởi Chạy Ngay</span>
            </button>
          </div>
        </div>

        <!-- Tool Health Metrics -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
          <div class="metric-card">
            <div class="metric-label">Trình Giải Nén 7z</div>
            <div class="metric-value" style="color: #10b981;" id="set-7z-status">Sẵn Sàng</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">WuWa Mod Fixer</div>
            <div class="metric-value" style="color: #38bdf8;" id="set-fixer-status">v3.6.0 Moonholder</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Kho Resonators</div>
            <div class="metric-value" style="color: #c084fc;">58 Nhân Vật</div>
          </div>
        </div>

        <!-- Beginner Step Guide -->
        <div class="cyber-card" style="background: rgba(56, 189, 248, 0.03); border-color: rgba(56, 189, 248, 0.2);">
          <div style="font-size: 12px; font-weight: 700; color: #38bdf8; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
            HƯỚNG DẪN SỬ DỤNG NHANH CHO NGƯỜI MỚI:
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div class="step-card">
              <div class="step-num">1</div>
              <div class="step-text"><b>Tải Mod:</b> Chọn nhân vật ở cột trái ➔ Bấm <b>Tải Xuống</b> ở thẻ mod.</div>
            </div>
            <div class="step-card">
              <div class="step-num">2</div>
              <div class="step-text"><b>Chạy Game:</b> Nhấn <b>Khởi Chạy Game</b> ở góc trên cùng.</div>
            </div>
            <div class="step-card">
              <div class="step-num">3</div>
              <div class="step-text"><b>Nạp Mod:</b> Nhấn phím <b>F10</b> trên bàn phím trong khi chơi game để nạp.</div>
            </div>
            <div class="step-card">
              <div class="step-num">4</div>
              <div class="step-text"><b>Chỉnh Phím Tắt:</b> Vào <i>Mods Đã Cài</i> ➔ Click mod ➔ Đổi phím ➔ <b>Lưu Cấu Hình</b>.</div>
            </div>
          </div>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; padding-top: 10px; border-top: 1px solid var(--border-subtle);">
        <button class="btn btn-secondary" onclick="window.pywebview.api.open_external_url('https://github.com/WahuVN/Viet-Hoa-WuWa')" title="Xem bản Mod Việt Hóa Wuthering Waves của WahuVN">
          <span>🇻🇳 Mod Việt Hóa</span>
        </button>
        <button class="btn btn-secondary" onclick="checkAppUpdate(false)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          <span>Kiểm Tra Cập Nhật</span>
        </button>
        <button class="btn btn-primary" onclick="closeSettingsModal()">Hoàn Tất Cài Đặt</button>
      </div>
    </div>
  </div>

  <!-- MOD FIXER MODAL -->
  <div class="modal-overlay" id="fixer-modal">
    <div class="modal-box" style="width: 860px; max-width: 95vw; padding: 26px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); display: flex; align-items: center; justify-content: center; color: #38bdf8;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #fff; letter-spacing: 0.2px; display: flex; align-items: center; gap: 8px;">
              CÔNG CỤ VÁ LỖI & TỐI ƯU HÓA MOD <span class="badge-tag cyan">v3.6.0</span>
            </div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">Chuẩn hóa cấu trúc Vertex Shader, Derived Hashes và liên kết Mesh tương thích bản game mới nhất</div>
          </div>
        </div>
        <button class="btn btn-secondary" style="color: var(--danger); padding: 4px 10px;" onclick="closeFixerModal()">✕ Đóng</button>
      </div>

      <!-- FEATURE CARDS 2x2 GRID -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
        <!-- Card 1: Derived -->
        <div class="cyber-card" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;">
          <div style="padding-right: 12px;">
            <div style="font-size: 13px; font-weight: 600; color: #f1f5f9;">Cập Nhật Hash Dẫn Xuất (Derived Hashes)</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.4;">
              Bổ sung hash trạng thái phụ (LOD Bias, trạng thái ướt, hiệu ứng kích hoạt chiêu).
            </div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-derived" checked><span class="slider"></span></label>
        </div>

        <!-- Card 2: Stable Texture -->
        <div class="cyber-card" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;">
          <div style="padding-right: 12px;">
            <div style="font-size: 13px; font-weight: 600; color: #f1f5f9;">Ổn Định Bề Mặt Vân Phủ (Stable Texture)</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.4;">
              Kích hoạt thuật toán ổn định bề mặt, chống nhấp nháy vân phủ khi chuyển động.
            </div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-stable"><span class="slider"></span></label>
        </div>

        <!-- Card 3: Mesh Gap -->
        <div class="cyber-card" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;">
          <div style="padding-right: 12px;">
            <div style="font-size: 13px; font-weight: 600; color: #f1f5f9;">Khắc Phục Biến Dạng Mesh (Mesh Gap Fix)</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.4;">
              Tái lập cấu trúc polygon bị thiếu hoặc biến dạng sau các bản cập nhật game.
            </div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-mesh" checked><span class="slider"></span></label>
        </div>

        <!-- Card 4: Aemeath Model -->
        <div class="cyber-card" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;">
          <div style="padding-right: 12px;">
            <div style="font-size: 13px; font-weight: 600; color: #f1f5f9;">Tối Ưu Hóa Model Aemeath</div>
            <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.4;">
              Xử lý chuyên biệt trạng thái cơ khí và hiệu ứng hình thể độc quyền của Aemeath.
            </div>
          </div>
          <label class="switch"><input type="checkbox" id="fix-opt-aemeath"><span class="slider"></span></label>
        </div>
      </div>

      <!-- TARGET SCOPE -->
      <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 9px 12px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Mục Tiêu Áp Dụng:</div>
        <div id="fixer-target-label" style="font-size: 11.5px; font-weight: 500; color: #e2e8f0;">Toàn bộ kho Mod trong WWMI (Tự động quét tất cả nhân vật)</div>
      </div>

      <!-- TERMINAL CONSOLE -->
      <div class="terminal-window" style="margin-bottom: 18px;">
        <div class="terminal-header">
          <div class="terminal-dots">
            <div class="terminal-dot red"></div>
            <div class="terminal-dot yellow"></div>
            <div class="terminal-dot green"></div>
          </div>
          <div class="terminal-title">moonholder-fixer-engine-v3.6.0</div>
          <div style="font-size: 10px; color: var(--text-muted);">UTF-8</div>
        </div>
        <div class="terminal-body" id="fixer-console">
          <div style="color: #64748b;">[Hệ thống] Sẵn sàng thực thi quy trình chuẩn hóa và sửa lỗi bản mod...</div>
        </div>
      </div>

      <!-- ACTION BUTTONS -->
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn btn-secondary" style="height: 34px; padding: 0 14px;" onclick="executeFixerAction(true)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
          <span>Khôi Phục Bản Sao Lưu (.BAK)</span>
        </button>
        <button class="btn btn-primary" style="height: 34px; padding: 0 16px;" onclick="executeFixerAction(false)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
          <span>Bắt Đầu Sửa Lỗi</span>
        </button>
      </div>
    </div>
  </div>

  <!-- GALLERY LIGHTBOX MODAL -->
  <div class="modal-overlay" id="gallery-modal">
    <div class="modal-box" style="width: 92vw; max-width: 1140px; height: 90vh; display: flex; flex-direction: column; padding: 22px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #fff;" id="gal-title">Tên Mod</div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;" id="gal-author">Tác giả: ...</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" style="height: 32px; padding: 0 14px;" onclick="downloadCurrentGalleryMod()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Tải & Cài Đặt Mod</span>
          </button>
          <button class="btn btn-secondary" style="color: var(--danger); padding: 0 12px; height: 32px;" onclick="closeGalleryModal()">✕ Đóng</button>
        </div>
      </div>

      <div style="flex: 1; background: #030408; border-radius: var(--radius-md); overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-subtle); box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.85);">
        <img id="gal-big-img" src="" style="max-width: 100%; max-height: 100%; object-fit: contain; transition: transform 0.25s ease;">
        <button class="btn btn-secondary" style="position: absolute; left: 16px; width: 40px; height: 40px; font-size: 18px; border-radius: 50%; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);" onclick="prevGalleryImage()">‹</button>
        <button class="btn btn-secondary" style="position: absolute; right: 16px; width: 40px; height: 40px; font-size: 18px; border-radius: 50%; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);" onclick="nextGalleryImage()">›</button>
        <div style="position: absolute; bottom: 14px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); padding: 4px 14px; border-radius: var(--radius-full); font-size: 11.5px; font-weight: 600; color: #fff; border: 1px solid var(--border-subtle);" id="gal-counter">1 / 1</div>
      </div>

      <div style="height: 85px; display: flex; gap: 8px; overflow-x: auto; margin-top: 14px; padding: 4px 0;" id="gal-thumbs">
        <!-- Thumbs -->
      </div>
    </div>
  </div>

  <!-- FLOATING CORNER DOWNLOAD WIDGET (NON-BLOCKING) -->
  <div class="corner-dl-widget" id="dl-widget">
    <div class="corner-dl-header">
      <div class="corner-dl-title-wrap">
        <div class="corner-dl-spinner" id="dl-spinner"></div>
        <div class="corner-dl-title" id="dl-title">Đang tải bản mod...</div>
      </div>
      <button class="corner-dl-close" onclick="hideDownloadWidget()" title="Ẩn thông báo">✕</button>
    </div>
    <div class="corner-dl-subtitle" id="dl-subtitle">Đang kết nối máy chủ...</div>
    <div class="progress-wrap" style="margin: 8px 0 6px; height: 6px;">
      <div class="progress-fill" id="dl-bar"></div>
    </div>
    <div class="corner-dl-footer">
      <span id="dl-pct">0%</span>
      <span id="dl-speed">Đang chuẩn bị...</span>
    </div>
  </div>

<script>
  // Native bridge to Local Python Server
  window.pywebview = {
    api: new Proxy({}, {
      get(target, prop) {
        return async function(...args) {
          try {
            const res = await fetch('/api/' + prop, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(args)
            });
            return await res.json();
          } catch(e) {
            console.error("API error on " + prop + ":", e);
            return null;
          }
        }
      }
    })
  };

  // Real-time EventSource connection for evaluate_js pushes
  try {
    const evtSource = new EventSource('/events');
    evtSource.onmessage = function(e) {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'eval' && msg.code) {
          eval(msg.code);
        }
      } catch(err) {
        console.error("SSE eval error:", err);
      }
    };
  } catch(e) {}

  document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/heartbeat').catch(() => {});
    setInterval(() => {
      fetch('/api/heartbeat').catch(() => {});
    }, 2000);
    setTimeout(() => {
      window.dispatchEvent(new Event('pywebviewready'));
      if (typeof initApp === 'function') initApp();
    }, 50);
  });

  function safeGetStorage(key, defVal = '') {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const v = window.localStorage.getItem(key);
        return v !== null ? v : defVal;
      }
    } catch(e) {}
    return defVal;
  }

  function safeSetStorage(key, val) {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, val);
      }
    } catch(e) {}
  }

  let currentSource = 'gamebanana';
  let currentView = 'store';
  let currentChar = '';
  let currentCharFolder = '';
  let currentSelectedItem = null;
  let allCharactersData = {INITIAL_CHARACTERS_DATA};
  let onlineMods = [];
  let installedMods = [];
  let selectedModDetail = null;
  let currentStorePage = 1;
  let latestUpdateInfo = null;
  let isSafeMode = false;
  try { isSafeMode = safeGetStorage('resonamod_safe_mode') === 'true'; } catch(e){}
  let blurredModIds = new Set();
  try { blurredModIds = new Set(JSON.parse(safeGetStorage('resonamod_blurred_mods', '[]'))); } catch(e){}

  function updateSafeModeBtn() {
    const btn = document.getElementById('btn-safe-mode');
    if (btn) {
      if (isSafeMode) {
        btn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
          <span>Safe Mode: BẬT</span>
        `;
        btn.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        btn.style.color = '#fbbf24';
        btn.style.background = 'rgba(245, 158, 11, 0.12)';
      } else {
        btn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          <span>Safe Mode: TẮT</span>
        `;
        btn.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        btn.style.color = '#94a3b8';
        btn.style.background = 'rgba(255, 255, 255, 0.04)';
      }
    }
  }

  function toggleSafeMode() {
    isSafeMode = !isSafeMode;
    safeSetStorage('resonamod_safe_mode', isSafeMode ? 'true' : 'false');
    updateSafeModeBtn();
    renderGrid();
  }

  function toggleBlurMod(modKey, idx, e) {
    if (e && e.stopPropagation) e.stopPropagation();
    if (blurredModIds.has(modKey)) {
      blurredModIds.delete(modKey);
    } else {
      blurredModIds.add(modKey);
    }
    safeSetStorage('resonamod_blurred_mods', JSON.stringify(Array.from(blurredModIds)));
    
    const isItemBlurred = blurredModIds.has(modKey);
    const isBlurred = isSafeMode || isItemBlurred;
    const cardEl = document.getElementById(`mod-card-${idx}`);
    if (cardEl) {
      const imgWrap = cardEl.querySelector('.card-img-wrap');
      const blurBtn = cardEl.querySelector('.btn-card-blur');
      if (imgWrap) {
        imgWrap.classList.toggle('blurred', isBlurred);
        imgWrap.title = isBlurred ? 'Bấm để mở xem ảnh này' : 'Bấm để phóng to xem ảnh';
      }
      if (blurBtn) {
        blurBtn.classList.toggle('active', isItemBlurred);
        blurBtn.innerHTML = isItemBlurred ? `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          <span>Hiện Ảnh</span>
        ` : `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
          <span>Làm Mờ</span>
        `;
        blurBtn.title = isItemBlurred ? 'Bỏ làm mờ ảnh này' : 'Làm mờ ảnh xem trước này';
      }
    }
  }

  function handleCardImgClick(modObj, modKey, idx) {
    const isBlurred = isSafeMode || blurredModIds.has(modKey);
    if (isBlurred) {
      toggleBlurMod(modKey, idx);
      return;
    }
    openGalleryModal(modObj);
  }

  async function checkAppUpdate(isSilent = false) {
    if (!isSilent) {
      appendLog('[Cập Nhật] Đang kiểm tra phiên bản mới từ GitHub...');
    }
    try {
      await ensureApiReady();
      if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.check_app_update) return;
      const res = await window.pywebview.api.check_app_update();
      if (res && res.success) {
        latestUpdateInfo = res;
        const badge = document.getElementById('btn-update-badge');
        const lbl = document.getElementById('lbl-new-ver');
        if (res.has_update) {
          if (badge && lbl) {
            lbl.innerText = `v${res.latest_version}`;
            badge.style.display = 'inline-flex';
          }
          appendLog(`[Cập Nhật] Đã có phiên bản mới v${res.latest_version}!`);
          openUpdateModal();
        } else {
          if (badge) badge.style.display = 'none';
          if (!isSilent) {
            alert(`Bạn đang sử dụng phiên bản mới nhất (v${res.current_version})!`);
          }
        }
      } else {
        if (!isSilent) {
          alert('Không thể kết nối đến máy chủ GitHub để kiểm tra cập nhật. Vui lòng kiểm tra lại mạng.');
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  function openUpdateModal() {
    if (!latestUpdateInfo) return;
    const body = document.getElementById('update-modal-body');
    const footer = document.getElementById('update-modal-footer');
    const title = document.getElementById('update-modal-title');
    const curVer = document.getElementById('lbl-cur-ver');
    
    if (curVer) curVer.innerText = `v${latestUpdateInfo.current_version}`;
    if (title) title.innerText = latestUpdateInfo.has_update ? `CÓ BẢN CẬP NHẬT MỚI: v${latestUpdateInfo.latest_version}` : `RESONAMOD v${latestUpdateInfo.current_version}`;
    
    if (body) {
      body.innerHTML = `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 14px;">
          <div style="font-weight: 700; color: #10b981; font-size: 14px; margin-bottom: 8px;">${latestUpdateInfo.title || 'Bản Cập Nhật Mới'}</div>
          <div style="font-size: 12px; color: var(--text-secondary); white-space: pre-wrap; max-height: 220px; overflow-y: auto; line-height: 1.6; font-family: var(--font-mono);">${latestUpdateInfo.changelog || 'Tối ưu hóa hệ thống và sửa lỗi.'}</div>
        </div>
      `;
    }
    
    if (footer) {
      footer.innerHTML = `
        <button class="btn btn-secondary" onclick="closeUpdateModal()">Đóng</button>
        <button class="btn btn-secondary" onclick="window.pywebview.api.open_external_url('${latestUpdateInfo.html_url}')">🌐 Xem Release GitHub</button>
        <button class="btn btn-primary" style="background: linear-gradient(135deg, #10b981, #059669);" onclick="window.pywebview.api.open_external_url('${latestUpdateInfo.direct_url}')">⬇️ Tải Cập Nhật Ngay</button>
      `;
    }
    
    document.getElementById('update-modal').style.display = 'flex';
  }

  function closeUpdateModal() {
    document.getElementById('update-modal').style.display = 'none';
  }

  async function openSettingsModal() {
    try {
      await ensureApiReady();
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_app_settings) {
        const res = await window.pywebview.api.get_app_settings();
        if (res) {
          document.getElementById('set-wwmi-path').innerText = res.wwmi_path || 'Chưa thiết lập';
          document.getElementById('set-game-exe').innerText = res.game_exe || 'Tự động nhận diện (XXMI / WWMI Loader)';
          document.getElementById('set-7z-status').innerText = res.has_7z ? '✅ Sẵn Sàng' : '⚠️ Chưa tìm thấy';
          document.getElementById('set-fixer-status').innerText = res.has_fixer ? '✅ v3.6.0 Moonholder' : '⚠️ Chưa tìm thấy';
        }
      }
    } catch(e) {
      console.error(e);
    }
    document.getElementById('settings-modal').style.display = 'flex';
  }

  function closeSettingsModal() {
    document.getElementById('settings-modal').style.display = 'none';
  }

  async function openWelcomeWizardModal(presetSettings = null) {
    try {
      await ensureApiReady();
      let settings = presetSettings;
      if (!settings && window.pywebview && window.pywebview.api && window.pywebview.api.get_app_settings) {
        settings = await window.pywebview.api.get_app_settings();
      }
      if (settings) {
        const wwmiEl = document.getElementById('wiz-wwmi-path');
        const d3El = document.getElementById('wiz-3d-status');
        const modsEl = document.getElementById('wiz-mods-status');
        const badgeEl = document.getElementById('wiz-overall-badge');
        
        if (wwmiEl) wwmiEl.innerText = settings.wwmi_path || 'Chưa nhận diện';
        if (d3El) {
          d3El.innerHTML = settings.has_3dmigoto ? '<span style="color: #10b981;">✅ Đã tìm thấy 3DMigoto</span>' : '<span style="color: #f59e0b;">⚠️ Chưa có (Hãy trỏ vào WWMI)</span>';
        }
        if (modsEl) {
          modsEl.innerHTML = settings.has_mods_dir ? '<span style="color: #10b981;">✅ Đã có thư mục Mods</span>' : '<span style="color: var(--accent);">⚡ Sẽ tự động tạo</span>';
        }
        if (badgeEl) {
          if (settings.is_wwmi_valid) {
            badgeEl.className = 'badge-tag green';
            badgeEl.innerText = 'ĐÃ KẾT NỐI SẴN SÀNG';
          } else {
            badgeEl.className = 'badge-tag amber';
            badgeEl.innerText = 'CHƯA TRỎ ĐÚNG THƯ MỤC WWMI';
          }
        }
      }
    } catch(e) {
      console.error(e);
    }
    const modal = document.getElementById('welcome-wizard-modal');
    if (modal) modal.style.display = 'flex';
  }

  function closeWelcomeWizardModal() {
    const modal = document.getElementById('welcome-wizard-modal');
    if (modal) modal.style.display = 'none';
  }

  function completeWelcomeWizard() {
    safeSetStorage('resonamod_setup_completed', 'true');
    closeWelcomeWizardModal();
    appendLog('🎉 Thiết lập hoàn tất! Bạn có thể bắt đầu tải mod và chơi ngay.');
  }

  async function chooseWwmiFolderInWizard() {
    const res = await window.pywebview.api.choose_wwmi_folder();
    if (res && res.success) {
      appendLog(`[Cài Đặt] Đã chuyển thư mục WWMI sang: ${res.path}`);
      await loadCharacters();
      if (currentView === 'installed') loadInstalled(currentCharFolder);
      await openWelcomeWizardModal();
    }
  }

  async function chooseWwmiFolder() {
    const res = await window.pywebview.api.choose_wwmi_folder();
    if (res && res.success) {
      document.getElementById('set-wwmi-path').innerText = res.path;
      appendLog(`[Cài Đặt] Đã chuyển thư mục WWMI sang: ${res.path}`);
      await loadCharacters();
      if (currentView === 'installed') loadInstalled(currentCharFolder);
      alert('Đã cập nhật thư mục WWMI thành công!');
    }
  }

  async function resetWwmiFolder() {
    const res = await window.pywebview.api.reset_wwmi_path();
    if (res && res.success) {
      document.getElementById('set-wwmi-path').innerText = res.path;
      appendLog(`[Cài Đặt] Đã khôi phục thư mục WWMI: ${res.path}`);
      await loadCharacters();
      if (currentView === 'installed') loadInstalled(currentCharFolder);
      alert('Đã khôi phục đường dẫn WWMI mặc định!');
    }
  }

  async function chooseGameExe() {
    const res = await window.pywebview.api.choose_game_exe();
    if (res && res.success) {
      document.getElementById('set-game-exe').innerText = res.path;
      appendLog(`[Cài Đặt] Đã chọn file chạy game: ${res.path}`);
      alert(`Đã chọn file chạy game: ${res.path}`);
    }
  }

  async function ensureApiReady(maxWaitMs = 6000) {
    const start = Date.now();
    while (Date.now() - start < maxWaitMs) {
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_characters === 'function') {
        return true;
      }
      await new Promise(r => setTimeout(r, 40));
    }
    return !!(window.pywebview && window.pywebview.api);
  }

  let isAppInitialized = false;

  async function initApp() {
    if (isAppInitialized) return;
    isAppInitialized = true;
    try { updateSafeModeBtn(); } catch(e){}
    try { renderSidebarList(); } catch(e){}
    try {
      await ensureApiReady();
      loadCharacters();
      loadMods(1);
      checkAppUpdate(true);
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_app_settings) {
        const settings = await window.pywebview.api.get_app_settings();
        const hasCompletedWizard = safeGetStorage('resonamod_setup_completed') === 'true';
        if (!hasCompletedWizard && (!settings || !settings.is_wwmi_valid)) {
          openWelcomeWizardModal(settings);
        }
      }
    } catch(e) {
      console.error('Lỗi initApp:', e);
    }
  }

  window.addEventListener('pywebviewready', initApp);
  window.addEventListener('DOMContentLoaded', () => {
    try { renderSidebarList(); } catch(e){}
    initApp();
  });
  setTimeout(initApp, 200);

  window.appendLog = function(msg) {
    const el = document.getElementById('status-log-text');
    if (el) el.innerText = msg;
  };

  async function loadCharacters() {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_characters) {
        const res = await window.pywebview.api.get_characters();
        if (res && Array.isArray(res.characters) && res.characters.length > 0) {
          allCharactersData = res;
        }
      }
    } catch(e) {
      console.error('Lỗi loadCharacters:', e);
    }
    const filterVal = document.getElementById('sidebar-filter-input') ? document.getElementById('sidebar-filter-input').value : '';
    renderSidebarList(filterVal);
  }

  function filterSidebarList(kw) {
    renderSidebarList((kw || '').trim().toLowerCase());
  }

  function renderSidebarList(filter = '') {
    const list = document.getElementById('char-list');
    if (!list) return;
    list.innerHTML = '';

    const addHeading = (text) => {
      const h = document.createElement('div');
      h.className = 'sidebar-group-title';
      h.innerText = text;
      list.appendChild(h);
    };

    addHeading('👤 Resonators (Nhân Vật)');

    const chars = (allCharactersData && Array.isArray(allCharactersData.characters)) ? allCharactersData.characters : [];
    const filteredChars = chars.filter(c => 
      !filter || (c.name && c.name.toLowerCase().includes(filter)) || (c.query_cn && c.query_cn.toLowerCase().includes(filter))
    );

    filteredChars.forEach(c => {
      const item = document.createElement('div');
      const isAct = currentSelectedItem ? currentSelectedItem.name === c.name : (c.name === 'All Characters' || c.name === 'Tất Cả Nhân Vật');
      item.className = `char-item ${isAct ? 'active' : ''}`;
      item.onclick = () => selectItem(c);
      const iconSrc = c.icon || 'data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'26\\' height=\\'26\\' fill=\\'%23333\\'><rect width=\\'26\\' height=\\'26\\' rx=\\'6\\'/></svg>';
      item.innerHTML = `
        <div class="char-left">
          <img src="${iconSrc}" class="char-avatar" onerror="this.style.opacity=0.3">
          <span class="char-name">${c.name}</span>
        </div>
        ${c.count > 0 ? `<span class="char-badge">${c.count}</span>` : ''}
      `;
      list.appendChild(item);
    });

    addHeading('🏍️ Phương Tiện & Phụ Kiện');

    const cats = (allCharactersData && Array.isArray(allCharactersData.categories)) ? allCharactersData.categories : [];
    const filteredCats = cats.filter(sc => 
      !filter || (sc.name && sc.name.toLowerCase().includes(filter))
    );

    filteredCats.forEach(sc => {
      const item = document.createElement('div');
      const isAct = currentSelectedItem && currentSelectedItem.name === sc.name;
      item.className = `char-item ${isAct ? 'active' : ''}`;
      item.onclick = () => selectItem(sc);
      item.innerHTML = `
        <div class="char-left">
          <span style="font-size: 16px; width: 26px; text-align: center;">${sc.icon || '📦'}</span>
          <span class="char-name">${sc.name}</span>
        </div>
        ${sc.count > 0 ? `<span class="char-badge">${sc.count}</span>` : ''}
      `;
      list.appendChild(item);
    });
  }

  function selectItem(item) {
    currentSelectedItem = item;
    const isAll = !item || item.name === 'All Characters' || item.name === 'Tất Cả Nhân Vật' || !item.folder;
    if (isAll) {
      currentChar = '';
      currentCharFolder = '';
      document.getElementById('context-char-name').innerText = 'All Characters';
    } else {
      currentChar = item.name;
      currentCharFolder = item.folder || '';
      document.getElementById('context-char-name').innerText = item.name;
    }

    renderSidebarList(document.getElementById('sidebar-filter-input').value);
    if (currentView === 'installed') {
      loadInstalled(currentCharFolder);
    } else if (currentView === 'store') {
      loadMods(1);
    }
  }

  function getActiveQuery() {
    if (!currentSelectedItem || currentSelectedItem.name === 'All Characters' || currentSelectedItem.name === 'Tất Cả Nhân Vật') return '';
    if (currentSelectedItem.type === 'category') {
      if (currentSource === 'huihui168') return currentSelectedItem.huihui_kw || '';
      if (currentSource === 'gamebanana') return currentSelectedItem.gb_kw || '';
      return currentSelectedItem.folder || '';
    }
    if (currentSource === 'huihui168' && currentSelectedItem.query_cn) {
      return currentSelectedItem.query_cn;
    }
    return currentSelectedItem.query || currentSelectedItem.name || '';
  }

  function switchStore(src) {
    currentSource = src;
    currentView = 'store';
    ['tab-gb', 'tab-hh', 'tab-nx', 'tab-inst', 'tab-imp'].forEach(id => document.getElementById(id).className = 'nav-item');
    document.getElementById(src === 'gamebanana' ? 'tab-gb' : (src === 'nexus' ? 'tab-nx' : 'tab-hh')).className = 'nav-item active';
    
    document.getElementById('filter-bar').style.display = 'flex';
    document.getElementById('store-bulk-actions').style.display = 'flex';
    document.getElementById('installed-bulk-actions').style.display = 'none';
    document.getElementById('mod-grid').style.display = 'grid';
    document.getElementById('installed-view').style.display = 'none';
    document.getElementById('direct-link-view').style.display = 'none';
    loadMods(1);
  }

  function selectAllCharacters() {
    const allItem = (allCharactersData.characters && allCharactersData.characters[0]) || { name: 'All Characters', folder: '' };
    selectItem(allItem);
  }

  function switchView(view) {
    currentView = view;
    ['tab-gb', 'tab-hh', 'tab-nx', 'tab-inst', 'tab-imp'].forEach(id => document.getElementById(id).className = 'nav-item');
    document.getElementById(view === 'installed' ? 'tab-inst' : 'tab-imp').className = 'nav-item active';
    
    if (view === 'installed') {
      document.getElementById('filter-bar').style.display = 'flex';
      document.getElementById('store-bulk-actions').style.display = 'none';
      document.getElementById('installed-bulk-actions').style.display = 'flex';
      document.getElementById('mod-grid').style.display = 'none';
      document.getElementById('installed-view').style.display = 'flex';
      document.getElementById('direct-link-view').style.display = 'none';
      
      if (!currentSelectedItem || !currentSelectedItem.count || currentSelectedItem.count === 0 || currentCharFolder === '') {
        selectAllCharacters();
      } else {
        loadInstalled(currentCharFolder);
      }
    } else {
      document.getElementById('filter-bar').style.display = 'none';
      document.getElementById('store-bulk-actions').style.display = 'none';
      document.getElementById('installed-bulk-actions').style.display = 'none';
      document.getElementById('mod-grid').style.display = 'none';
      document.getElementById('installed-view').style.display = 'none';
      document.getElementById('direct-link-view').style.display = 'block';
    }
  }

  function reloadCurrentView() {
    if (currentView === 'installed') loadInstalled(currentCharFolder);
    else loadMods(1);
  }

  let currentStoreRequestId = 0;
  const clientStoreCache = new Map();

  async function loadMods(page = 1) {
    currentStorePage = Math.max(1, page);
    const reqId = ++currentStoreRequestId;
    const grid = document.getElementById('mod-grid');
    
    const search = document.getElementById('search-input').value.trim();
    let q = search;
    let catId = null;

    if (currentSource === 'gamebanana') {
      if (currentSelectedItem && currentSelectedItem.name !== 'All Characters' && currentSelectedItem.name !== 'Tất Cả Nhân Vật') {
        catId = currentSelectedItem.gb_cat_id || null;
        if (!catId) {
          const activeQ = getActiveQuery();
          q = (activeQ + ' ' + search).trim();
        }
      }
    } else {
      const activeQ = getActiveQuery();
      q = (activeQ + ' ' + search).trim();
    }

    const cacheKey = `${currentSource}_${q}_${currentStorePage}_${catId}`;
    if (clientStoreCache.has(cacheKey)) {
      const cached = clientStoreCache.get(cacheKey);
      onlineMods = cached.items || [];
      document.getElementById('context-mod-count').innerText = `${onlineMods.length} Mod (Trang ${currentStorePage})`;
      renderGrid();
      return;
    }

    grid.innerHTML = Array(8).fill(0).map(() => `
      <div class="skeleton-card">
        <div class="skeleton-img"></div>
        <div class="skeleton-body">
          <div class="skeleton-line" style="width: 85%;"></div>
          <div class="skeleton-line" style="width: 55%; margin-top: 4px;"></div>
          <div class="skeleton-line" style="width: 100%; height: 28px; margin-top: auto; border-radius: var(--radius-sm);"></div>
        </div>
      </div>
    `).join('');

    try {
      await ensureApiReady();
      if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_online_mods) {
        throw new Error("Chưa kết nối được với dịch vụ backend.");
      }

      const res = await window.pywebview.api.get_online_mods(currentSource, q, currentStorePage, catId);
      if (reqId !== currentStoreRequestId) return;
      
      if (!res || !res.success || !res.items || res.items.length === 0) {
        document.getElementById('context-mod-count').innerText = '0 Mod';
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-muted);">
            <div style="font-size: 24px; margin-bottom: 8px;">📦</div>
            <div>Không tìm thấy bản mod nào ở trang ${currentStorePage}.</div>
            <button class="btn btn-secondary" style="margin-top: 14px;" onclick="loadMods(1)">Quay lại trang 1</button>
          </div>
        `;
        return;
      }
      
      clientStoreCache.set(cacheKey, res);
      onlineMods = res.items;
      document.getElementById('context-mod-count').innerText = `${onlineMods.length} Mod (Trang ${currentStorePage})`;
      renderGrid();
    } catch(err) {
      if (reqId !== currentStoreRequestId) return;
      console.error('Lỗi loadMods:', err);
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-muted);">
          <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
          <div style="font-size: 14px; font-weight: 700; color: #ef4444; margin-bottom: 6px;">Không thể tải danh sách Mod</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 14px;">${err.message || err}</div>
          <button class="btn btn-primary" onclick="loadMods(${currentStorePage})">🔄 Thử Lại Ngay</button>
        </div>
      `;
    }
  }

  function changeStorePage(delta) {
    const target = currentStorePage + delta;
    if (target >= 1) loadMods(target);
  }

  function renderGrid() {
    const grid = document.getElementById('mod-grid');
    grid.innerHTML = '';
    onlineMods.forEach((m, idx) => {
      const modKey = String((m.source || '') + '_' + (m.id || m.link || m.title));
      const isItemBlurred = blurredModIds.has(modKey);
      const isBlurred = isSafeMode || isItemBlurred;
      const card = document.createElement('div');
      card.className = 'mod-card';
      card.id = `mod-card-${idx}`;
      card.innerHTML = `
        <div class="card-img-wrap ${isBlurred ? 'blurred' : ''}" onclick='handleCardImgClick(${JSON.stringify(m)}, ${JSON.stringify(modKey)}, ${idx})' title="${isBlurred ? 'Bấm để mở xem ảnh này' : 'Bấm để phóng to xem ảnh'}">
          <img src="${m.img_url || 'https://via.placeholder.com/215x255'}" class="card-img" loading="lazy" onerror="this.src='https://via.placeholder.com/215x255?text=WuWa+Mod'">
          <div class="blur-overlay">
            <span class="blur-overlay-icon">🙈</span>
            <span class="blur-overlay-text">Đã Làm Mờ</span>
          </div>
          <span class="badge-like">${m.likes}</span>
        </div>
        <div class="card-body">
          <div>
            <div class="card-title" title="${(m.title || '').replace(/"/g, '&quot;')}" onclick='openGalleryModal(${JSON.stringify(m)})'>${m.title}</div>
            <div class="card-author">${m.author}</div>
          </div>
          <div class="card-actions">
            <button class="btn-card-dl" onclick='downloadMod(${JSON.stringify(m)})' title="Tải và cài đặt bản mod này vào game">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>Tải Xuống</span>
            </button>
            <button class="btn-card-blur ${isItemBlurred ? 'active' : ''}" id="blur-btn-${idx}" title="${isItemBlurred ? 'Bỏ làm mờ ảnh này' : 'Làm mờ ảnh xem trước này'}" onclick='toggleBlurMod(${JSON.stringify(modKey)}, ${idx}, event)'>
              ${isItemBlurred ? `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <span>Hiện Ảnh</span>
              ` : `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                <span>Làm Mờ</span>
              `}
            </button>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });

    // PAGINATION
    const pagBar = document.createElement('div');
    pagBar.style = "grid-column: 1/-1; display: flex; justify-content: center; align-items: center; gap: 10px; padding: 24px 0 40px;";
    pagBar.innerHTML = `
      <button class="btn btn-secondary" ${currentStorePage <= 1 ? 'disabled style="opacity: 0.4; pointer-events: none;"' : ''} onclick="changeStorePage(-1)">
        ◀ Trang Trước
      </button>
      <span style="font-size: 13px; font-weight: 700; color: var(--accent); background: var(--bg-surface); border: 1px solid var(--border-subtle); padding: 6px 16px; border-radius: var(--radius-sm);">
        Trang ${currentStorePage}
      </span>
      <button class="btn btn-secondary" onclick="changeStorePage(1)">
        Trang Sau ▶
      </button>
    `;
    grid.appendChild(pagBar);
  }

  /* INSTALLED MANAGER */
  async function loadInstalled(filterFolder = '') {
    const tbody = document.getElementById('installed-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: var(--text-muted);">⏳ Đang đọc danh sách Mod đã cài...</td></tr>';
    
    try {
      await ensureApiReady();
      if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_installed_mods) {
        throw new Error("Chưa kết nối được với dịch vụ backend.");
      }
      installedMods = await window.pywebview.api.get_installed_mods(filterFolder);
    } catch(err) {
      console.error('Lỗi loadInstalled:', err);
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px; color: #ef4444;">⚠️ Lỗi đọc mods đã cài: ${err.message || err}</td></tr>`;
      return;
    }
    
    if (!installedMods || installedMods.length === 0) {
      const countEl = document.getElementById('context-mod-count');
      if (countEl) countEl.innerText = '0 Mod';
      const allItem = (allCharactersData.characters && allCharactersData.characters[0]);
      const totalAll = (allItem && allItem.count) || 0;
      let emptyHtml = `
        <div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 32px; margin-bottom: 10px;">📂</div>
          <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
            Chưa có bản Mod nào được cài trong thư mục <b>${currentChar || filterFolder || 'này'}</b>.
          </div>
          ${totalAll > 0 ? `
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 16px;">
              Hiện đang có <b style="color: var(--accent);">${totalAll}</b> bản Mod trong các nhân vật khác.
            </div>
            <button class="btn btn-primary" onclick="selectAllCharacters()" style="padding: 8px 18px; font-weight: 700; box-shadow: var(--shadow-glow);">
              👁️ Xem Toàn Bộ ${totalAll} Bản Mod Đã Cài (All Characters)
            </button>
          ` : ''}
        </div>
      `;
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 20px;">${emptyHtml}</td></tr>`;
      clearInspector();
      return;
    }

    const countEl = document.getElementById('context-mod-count');
    if (countEl) countEl.innerText = `${installedMods.length} Bản Mod Đã Cài`;
    tbody.innerHTML = '';
    installedMods.forEach((m, idx) => {
      const tr = document.createElement('tr');
      tr.id = `mod-row-${idx}`;
      tr.onclick = (e) => {
        if (e.target.type !== 'checkbox' && !e.target.classList.contains('slider')) {
          inspectMod(m.full_path, idx);
        }
      };
      
      const isEn = m.is_enabled;
      tr.innerHTML = `
        <td style="text-align: center;">
          <label class="switch">
            <input type="checkbox" ${isEn ? 'checked' : ''} onchange="toggleMod('${m.full_path.replace(/\\\\/g, '\\\\\\\\')}', this.checked, ${idx})">
            <span class="slider"></span>
          </label>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: var(--radius-xs); background: rgba(255,255,255,0.04); display: flex; align-items: center; justify-content: center; font-size: 12px; border: 1px solid var(--border-subtle); flex-shrink: 0; color: #94a3b8;">
              ${m.has_cover ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M20.4 14.5L16 10 4 20"/></svg>' : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>'}
            </div>
            <div>
              <div style="font-weight: 600; color: ${isEn ? 'var(--text-primary)' : 'var(--text-muted)'};">${m.name}</div>
              <div style="font-size: 11px; color: var(--text-muted);">${m.char_folder}</div>
            </div>
          </div>
        </td>
        <td style="color: var(--text-secondary); font-size: 12px;">${m.author}</td>
        <td>
          <span style="font-size: 11px; font-weight: 600; color: ${isEn ? '#10b981' : 'var(--text-muted)'};">
            ${isEn ? '● Đang Bật' : '○ Đã Tắt'}
          </span>
        </td>
        <td style="text-align: right;">
          <button class="btn btn-secondary" style="height: 24px; padding: 0 8px; font-size: 11px; margin-right: 4px;" onclick="event.stopPropagation(); inspectMod('${m.full_path.replace(/\\\\/g, '\\\\\\\\')}', ${idx})">Chi Tiết</button>
          <button class="btn btn-secondary" style="height: 24px; padding: 0 6px; font-size: 11px; color: #f87171;" title="Xóa bản mod này" onclick="event.stopPropagation(); deleteInstalledModDirect('${m.full_path.replace(/\\\\/g, '\\\\\\\\')}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    if (installedMods.length > 0) {
      inspectMod(installedMods[0].full_path, 0);
    }
  }

  async function toggleMod(fullPath, isEnable, rowIdx) {
    await window.pywebview.api.toggle_mod(fullPath, isEnable);
    loadInstalled(currentCharFolder);
    loadCharacters();
  }

  async function toggleAllModsForCurrentChar(isEnable) {
    if (!currentCharFolder) {
      alert('Vui lòng chọn một nhân vật cụ thể bên trái để thao tác bật/tắt toàn bộ.');
      return;
    }
    await window.pywebview.api.toggle_all_mods_for_char(currentCharFolder, isEnable);
    loadInstalled(currentCharFolder);
  }

  let activeInspectedImages = [];
  let currentInspectedImgIdx = 0;
  let isCoverContain = false;

  function toggleCoverFit() {
    isCoverContain = !isCoverContain;
    const img = document.getElementById('insp-cover-img');
    const btn = document.getElementById('btn-cover-fit');
    if (!img || !btn) return;
    if (isCoverContain) {
      img.style.objectFit = 'contain';
      img.style.background = '#040508';
      btn.innerText = '🖼️ Đầy Khung';
    } else {
      img.style.objectFit = 'cover';
      img.style.objectPosition = 'top center';
      img.style.background = 'transparent';
      btn.innerText = '📐 Vừa Khung';
    }
  }

  async function inspectMod(fullPath, rowIdx = -1) {
    if (rowIdx >= 0) {
      document.querySelectorAll('#installed-tbody tr').forEach(r => r.className = '');
      const selectedRow = document.getElementById(`mod-row-${rowIdx}`);
      if (selectedRow) selectedRow.className = 'selected';
    }

    selectedModDetail = await window.pywebview.api.get_mod_detail(fullPath);
    if (!selectedModDetail) return;

    document.getElementById('insp-name').value = selectedModDetail.name || '';
    document.getElementById('insp-author').value = selectedModDetail.author || '';
    document.getElementById('insp-note').value = selectedModDetail.note || '';

    // Metadata Badges
    document.getElementById('insp-meta-char').innerText = selectedModDetail.char_folder || 'OTHERS';
    document.getElementById('insp-meta-size').innerText = selectedModDetail.size_mb || '-';
    document.getElementById('insp-meta-date').innerText = selectedModDetail.mod_date || '-';
    const statusEl = document.getElementById('insp-meta-status');
    if (selectedModDetail.is_enabled) {
      statusEl.innerText = '🟢 Đang Bật';
      statusEl.style.color = '#10b981';
    } else {
      statusEl.innerText = '⚪ Đã Tắt';
      statusEl.style.color = 'var(--text-muted)';
    }

    // Images & Gallery
    activeInspectedImages = selectedModDetail.images || [];
    currentInspectedImgIdx = 0;

    const imgEl = document.getElementById('insp-cover-img');
    const noImgEl = document.getElementById('insp-no-cover');
    const zoomHint = document.getElementById('insp-zoom-hint');
    const galWrap = document.getElementById('insp-gallery-wrap');
    const galStrip = document.getElementById('insp-gallery-strip');

    if (activeInspectedImages.length > 0) {
      imgEl.src = activeInspectedImages[0].base64;
      imgEl.style.display = 'block';
      noImgEl.style.display = 'none';
      if (zoomHint) zoomHint.style.display = 'block';
    } else if (selectedModDetail.cover_base64) {
      imgEl.src = selectedModDetail.cover_base64;
      imgEl.style.display = 'block';
      noImgEl.style.display = 'none';
      if (zoomHint) zoomHint.style.display = 'block';
    } else {
      imgEl.style.display = 'none';
      noImgEl.style.display = 'block';
      if (zoomHint) zoomHint.style.display = 'none';
    }

    if (activeInspectedImages.length > 1) {
      galWrap.style.display = 'block';
      document.getElementById('insp-img-count').innerText = activeInspectedImages.length;
      galStrip.innerHTML = '';
      activeInspectedImages.forEach((imgObj, i) => {
        const thumb = document.createElement('img');
        thumb.src = imgObj.base64;
        thumb.className = `gallery-thumb ${i === 0 ? 'active' : ''}`;
        thumb.title = imgObj.name;
        thumb.onclick = (e) => {
          e.stopPropagation();
          currentInspectedImgIdx = i;
          imgEl.src = imgObj.base64;
          document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
          thumb.classList.add('active');
        };
        galStrip.appendChild(thumb);
      });
    } else {
      galWrap.style.display = 'none';
    }

    renderKeybinds(selectedModDetail.keybinds || []);
  }

  function openInspectorFullPreview() {
    if (!activeInspectedImages || activeInspectedImages.length === 0) {
      if (selectedModDetail && selectedModDetail.cover_base64) {
        galleryImages = [selectedModDetail.cover_base64];
        galleryIndex = 0;
        activeGalleryMod = {
          title: selectedModDetail.name,
          author: selectedModDetail.author,
          source: 'local'
        };
        document.getElementById('gal-title').innerText = selectedModDetail.name;
        document.getElementById('gal-author').innerText = `Tác giả: ${selectedModDetail.author} | Nhân vật: ${selectedModDetail.char_folder}`;
        updateGalleryView();
        document.getElementById('gallery-modal').className = 'modal-overlay active';
      }
      return;
    }
    galleryImages = activeInspectedImages.map(img => img.base64);
    galleryIndex = currentInspectedImgIdx;
    activeGalleryMod = {
      title: selectedModDetail.name,
      author: selectedModDetail.author,
      source: 'local'
    };
    document.getElementById('gal-title').innerText = selectedModDetail.name;
    document.getElementById('gal-author').innerText = `Tác giả: ${selectedModDetail.author} | Nhân vật: ${selectedModDetail.char_folder} (${activeInspectedImages.length} ảnh)`;
    updateGalleryView();
    document.getElementById('gallery-modal').className = 'modal-overlay active';
  }

  function renderKeybinds(kbs) {
    const box = document.getElementById('insp-keybinds');
    box.innerHTML = '';
    if (!kbs || kbs.length === 0) {
      box.innerHTML = '<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 10px;">Mod này không có phím tắt phụ kiện.</div>';
      return;
    }

    kbs.forEach((kb, idx) => {
      const row = document.createElement('div');
      row.className = 'keybind-row';
      row.innerHTML = `
        <div class="keybind-name">${kb.display_name}</div>
        <input type="text" class="keybind-input" id="kb-input-${idx}" value="${kb.key}" placeholder="Phím">
      `;
      box.appendChild(row);
    });
  }

  async function saveSelectedModConfig() {
    if (!selectedModDetail) return;
    const newName = document.getElementById('insp-name').value;
    const newAuthor = document.getElementById('insp-author').value;
    const newNote = document.getElementById('insp-note').value;

    const newKbs = (selectedModDetail.keybinds || []).map((kb, idx) => {
      const val = document.getElementById(`kb-input-${idx}`).value.trim();
      return { ...kb, key: val };
    });

    const payload = JSON.stringify({
      full_path: selectedModDetail.full_path,
      name: newName,
      author: newAuthor,
      note: newNote,
      keybinds: newKbs
    });

    const res = await window.pywebview.api.save_mod_detail(payload);
    if (res.success) {
      alert('Đã lưu cấu hình mod thành công!');
      loadInstalled(currentCharFolder);
    } else {
      alert('Lỗi lưu cấu hình: ' + (res.error || 'Không xác định'));
    }
  }

  function openSelectedModFolder() {
    if (selectedModDetail) window.pywebview.api.open_folder(selectedModDetail.full_path);
  }

  function clearInspector() {
    document.getElementById('insp-name').value = '';
    document.getElementById('insp-author').value = '';
    document.getElementById('insp-note').value = '';
    document.getElementById('insp-cover-img').style.display = 'none';
    document.getElementById('insp-no-cover').style.display = 'block';
    const zoomHint = document.getElementById('insp-zoom-hint');
    if (zoomHint) zoomHint.style.display = 'none';
    const galWrap = document.getElementById('insp-gallery-wrap');
    if (galWrap) galWrap.style.display = 'none';
    document.getElementById('insp-meta-char').innerText = '-';
    document.getElementById('insp-meta-size').innerText = '-';
    document.getElementById('insp-meta-date').innerText = '-';
    document.getElementById('insp-meta-status').innerText = '-';
    document.getElementById('insp-keybinds').innerHTML = '';
  }

  async function confirmDeleteMod(fullPath, modName) {
    if (!confirm(`Bạn có chắc chắn muốn XÓA VĨNH VIỄN bản mod:\n"${modName}"\nkhỏi game không?\n\n(Thao tác này sẽ xóa thư mục mod và không thể khôi phục!)`)) {
      return;
    }
    const res = await window.pywebview.api.delete_mod(fullPath);
    if (res && res.success) {
      await loadCharacters();
      loadInstalled(currentCharFolder);
    } else {
      alert('Lỗi xóa bản mod: ' + (res.error || 'Không xác định'));
    }
  }

  function deleteCurrentInspectedMod() {
    if (!selectedModDetail || !selectedModDetail.full_path) {
      alert('Vui lòng chọn một bản mod để xóa.');
      return;
    }
    confirmDeleteMod(selectedModDetail.full_path, selectedModDetail.name || 'Bản mod này');
  }

  /* MOD FIXER MODAL */
  let currentFixerTarget = null;

  function openFixerModal(targetPath = null) {
    currentFixerTarget = targetPath;
    const label = document.getElementById('fixer-target-label');
    if (targetPath) {
      label.innerText = `Bản Mod: ${targetPath.split('\\\\').pop() || targetPath}`;
    } else {
      label.innerText = 'Toàn bộ kho Mod trong WWMI (Tự động quét tất cả nhân vật)';
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
      const res = await window.pywebview.api.run_advanced_fix(currentFixerTarget, derived, stable, mesh, isRollback);
      if (res.success) {
        consoleBox.innerHTML += `<div style="color: #10b981; white-space: pre-wrap;">${res.output || 'Đã hoàn tất thành công!'}</div>`;
        alert(isRollback ? 'Đã khôi phục file gốc từ .BAK thành công!' : 'Đã sửa lỗi thành công!');
        if (selectedModDetail) inspectMod(selectedModDetail.full_path);
      } else {
        consoleBox.innerHTML += `<div style="color: var(--danger);">Lỗi: ${res.msg}</div>`;
      }
    } else {
      consoleBox.innerHTML += `<div style="color: var(--accent);">🚀 Đang quét và sửa lỗi toàn bộ thư mục mod trong nền... Theo dõi thanh trạng thái bên dưới!</div>`;
      await window.pywebview.api.fix_all_installed_mods_advanced(derived, stable, mesh);
      alert('Đang tiến hành sửa lỗi toàn bộ Mod trong nền!');
    }
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  /* GALLERY LIGHTBOX */
  let currentGalleryImages = [];
  let currentGalleryIndex = 0;
  let activeGalleryMod = null;

  async function openGalleryModal(modObj) {
    activeGalleryMod = modObj;
    document.getElementById('gal-title').innerText = modObj.title;
    document.getElementById('gal-author').innerText = `Tác giả: ${modObj.author} | Nguồn: ${modObj.source.toUpperCase()}`;
    document.getElementById('gal-big-img').src = modObj.img_url;
    document.getElementById('gal-counter').innerText = '⏳ Đang nạp toàn bộ album ảnh xem trước...';
    document.getElementById('gal-thumbs').innerHTML = '';
    document.getElementById('gallery-modal').className = 'modal-overlay active';

    currentGalleryImages = [modObj.img_url];
    const res = await window.pywebview.api.get_mod_gallery_images(modObj.source, modObj.id, modObj.link);
    if (res && res.success && res.images && res.images.length > 0) {
      currentGalleryImages = res.images;
    }
    renderGalleryThumbs();
    setGalleryImage(0);
  }

  function renderGalleryThumbs() {
    const thumbsBox = document.getElementById('gal-thumbs');
    if (!thumbsBox) return;
    thumbsBox.innerHTML = '';
    if (currentGalleryImages.length <= 1) {
      thumbsBox.style.display = 'none';
      return;
    }
    thumbsBox.style.display = 'flex';
    currentGalleryImages.forEach((imgUrl, idx) => {
      const thumb = document.createElement('img');
      thumb.src = imgUrl;
      thumb.style = `height: 70px; width: 100px; object-fit: cover; border-radius: var(--radius-xs); cursor: pointer; border: 2px solid ${idx === currentGalleryIndex ? 'var(--accent)' : 'transparent'}; opacity: ${idx === currentGalleryIndex ? '1' : '0.6'}; transition: var(--transition); flex-shrink: 0;`;
      thumb.onclick = () => setGalleryImage(idx);
      thumbsBox.appendChild(thumb);
    });
  }

  function setGalleryImage(idx) {
    if (!currentGalleryImages || currentGalleryImages.length === 0) return;
    if (idx < 0) idx = currentGalleryImages.length - 1;
    if (idx >= currentGalleryImages.length) idx = 0;
    currentGalleryIndex = idx;
    document.getElementById('gal-big-img').src = currentGalleryImages[idx];
    document.getElementById('gal-counter').innerText = `${idx + 1} / ${currentGalleryImages.length}`;
    
    // Update border on thumbs
    const thumbImgs = document.querySelectorAll('#gal-thumbs img');
    thumbImgs.forEach((img, i) => {
      img.style.borderColor = (i === idx) ? 'var(--accent)' : 'transparent';
      img.style.opacity = (i === idx) ? '1' : '0.6';
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


  let dlWidgetTimeout = null;

  function hideDownloadWidget() {
    const w = document.getElementById('dl-widget');
    if (w) w.className = 'corner-dl-widget';
  }

  function showDownloadWidget(title = 'Đang tải bản mod...') {
    if (dlWidgetTimeout) clearTimeout(dlWidgetTimeout);
    const w = document.getElementById('dl-widget');
    if (!w) return;
    w.className = 'corner-dl-widget active';
    document.getElementById('dl-title').innerText = title;
    document.getElementById('dl-subtitle').innerText = 'Đang kết nối máy chủ...';
    document.getElementById('dl-bar').style.width = '0%';
    document.getElementById('dl-pct').innerText = '0%';
    document.getElementById('dl-speed').innerText = 'Đang chuẩn bị...';
  }

  function downloadMod(modObj) {
    const payload = Object.assign({}, modObj, {
      context_folder: currentCharFolder || '',
      context_name: currentChar || ''
    });
    showDownloadWidget(modObj.title);
    window.pywebview.api.download_and_install(JSON.stringify(payload));
  }

  function updateDownloadProgress(pct, cur, tot, speed) {
    const w = document.getElementById('dl-widget');
    if (w && !w.classList.contains('active')) w.className = 'corner-dl-widget active';
    document.getElementById('dl-subtitle').innerText = 'Đang tải xuống dữ liệu...';
    document.getElementById('dl-bar').style.width = pct + '%';
    document.getElementById('dl-pct').innerText = pct + '% (' + cur + '/' + tot + ' MB)';
    document.getElementById('dl-speed').innerText = speed + ' MB/s';
  }

  function finishDownloadSuccess(name, char) {
    const w = document.getElementById('dl-widget');
    if (w) w.className = 'corner-dl-widget active success';
    document.getElementById('dl-bar').style.width = '100%';
    document.getElementById('dl-title').innerText = 'Đã cài đặt thành công';
    document.getElementById('dl-subtitle').innerText = name || 'Hoàn tất giải nén và nạp vào game.';
    document.getElementById('dl-speed').innerText = 'Hoàn tất 100%';
    
    // Auto update background lists without disrupting the user
    loadCharacters();
    if (currentView === 'installed') {
      loadInstalled(currentCharFolder);
    }
    
    if (dlWidgetTimeout) clearTimeout(dlWidgetTimeout);
    dlWidgetTimeout = setTimeout(() => {
      hideDownloadWidget();
    }, 4500);
  }

  function finishDownloadError(err) {
    const w = document.getElementById('dl-widget');
    if (w) w.className = 'corner-dl-widget active error';
    document.getElementById('dl-title').innerText = 'Lỗi cài đặt mod';
    document.getElementById('dl-subtitle').innerText = err || 'Không thể tải hoặc giải nén tệp mod.';
    
    if (dlWidgetTimeout) clearTimeout(dlWidgetTimeout);
    dlWidgetTimeout = setTimeout(() => {
      hideDownloadWidget();
    }, 6000);
  }

  async function submitDirectLink() {
    const link = document.getElementById('direct-link-input').value.trim();
    if (!link) return;
    const res = await window.pywebview.api.import_from_direct_link(link);
    appendLog(res.msg);
  }

  function handleSearchKey(e) {
    if (e.key === 'Enter') reloadCurrentView();
  }
</script>
</body>
</html>
"""

class ResonaServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Tắt log HTTP mặc định để giữ console sạch sẽ

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ('/', '/index.html'):
            rendered = HTML_TEMPLATE.replace("{APP_LOGO_B64}", APP_LOGO_B64).replace("{INITIAL_CHARACTERS_DATA}", INITIAL_CHARACTERS_JSON).replace("{APP_VERSION}", APP_VERSION)
            data = rendered.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif parsed.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                self.wfile.write(b": connected\n\n")
                self.wfile.flush()
            except:
                return

            while True:
                try:
                    js_code = GLOBAL_EVENT_QUEUE.get(timeout=15)
                    payload = json.dumps({"type": "eval", "code": js_code})
                    self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                    self.wfile.flush()
                except queue.Empty:
                    try:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    except:
                        break
                except (BrokenPipeError, ConnectionResetError):
                    break
        elif parsed.path in ('/api/ping', '/api/heartbeat'):
            global LAST_HEARTBEAT, APP_STARTED
            LAST_HEARTBEAT = time.time()
            APP_STARTED = True
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith('/api/'):
            method_name = parsed.path[len('/api/'):]
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length > 0 else "[]"
            try:
                args = json.loads(body) if body else []
            except:
                args = []

            api_instance = getattr(self.server, 'api_instance', None)
            res = None
            if api_instance and hasattr(api_instance, method_name):
                func = getattr(api_instance, method_name)
                try:
                    if isinstance(args, list):
                        res = func(*args)
                    elif isinstance(args, dict):
                        res = func(**args)
                    else:
                        res = func(args)
                except Exception as e:
                    res = {"success": False, "error": str(e)}
            else:
                res = {"success": False, "error": f"Method {method_name} not found"}

            resp_data = json.dumps(res, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(resp_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(resp_data)
        else:
            self.send_response(404)
            self.end_headers()


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def launch_edge_app(url, width=1320, height=880):
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    app_exe = None
    for p in edge_paths:
        if os.path.isfile(p):
            app_exe = p
            break

    profile_dir = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "ResonaMod_App_Profile")
    os.makedirs(profile_dir, exist_ok=True)

    if app_exe:
        cmd = [
            app_exe,
            f"--app={url}",
            f"--window-size={width},{height}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-mode",
            "--disable-extensions"
        ]
        return subprocess.Popen(cmd)
    else:
        webbrowser.open(url)
        return None


def main():
    api = ResonaModAPI()
    win_proxy = WindowProxy()
    api.set_window(win_proxy)

    port = find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), ResonaServerHandler)
    server.api_instance = api

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    app_url = f"http://127.0.0.1:{port}"
    try:
        print(f"ResonaMod Studio v{APP_VERSION} running at: {app_url}")
    except:
        pass

    proc = launch_edge_app(app_url, width=1320, height=880)

    # Giữ tiến trình chạy mượt mà và tự động thoát khi đóng cửa sổ
    start_time = time.time()
    try:
        while True:
            time.sleep(1)
            if APP_STARTED:
                if time.time() - LAST_HEARTBEAT > 6:
                    break
            else:
                if proc and proc.poll() is not None and (time.time() - start_time > 30):
                    break
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
