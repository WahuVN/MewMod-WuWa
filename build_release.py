import os, sys, subprocess, shutil
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

print("=== BAT DAU DONG GOI BUILD BAN STANDALONE MEWMOD WUWA ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
ICON_ICO = os.path.join(BASE_DIR, "app_icon.ico")

# 1. Create .ico icon
all_png = os.path.join(AVATARS_DIR, "All.png")
if os.path.exists(all_png):
    try:
        im = Image.open(all_png)
        im.save(ICON_ICO, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"✅ Da tao Icon: {ICON_ICO}")
    except Exception as e:
        print(f"⚠️ Khong the tao ico: {e}")

# 2. Run PyInstaller
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "MewModWuWa",
    "--add-data", f"{AVATARS_DIR};avatars",
]

if os.path.exists(TOOLS_DIR):
    cmd.extend(["--add-data", f"{TOOLS_DIR};tools"])

if os.path.exists(ICON_ICO):
    cmd.extend(["--icon", ICON_ICO])

cmd.append(os.path.join(BASE_DIR, "MewModWuWa.py"))

print("Dang chay PyInstaller...")
res = subprocess.run(cmd, cwd=BASE_DIR)

if res.returncode == 0:
    print("\n🎉 BUILD THANH CONG!")
    print(f"📁 Thu muc phat hanh: {os.path.join(BASE_DIR, 'dist', 'MewModWuWa')}")
else:
    print(f"\n❌ Loi khi dong goi: {res.returncode}")
