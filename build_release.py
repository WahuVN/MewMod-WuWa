import os, sys, subprocess, shutil
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

print("=== BAT DAU DONG GOI BUILD BAN STANDALONE RESONAMOD STUDIO ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
ICON_ICO = os.path.join(BASE_DIR, "app_icon.ico")

# 1. Create .ico icon from app_icon.png
app_png = os.path.join(BASE_DIR, "app_icon.png")
if os.path.exists(app_png):
    try:
        im = Image.open(app_png).convert('RGBA')
        im.save(ICON_ICO, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"✅ Da tao Icon tu app_icon.png: {ICON_ICO}")
    except Exception as e:
        print(f"⚠️ Khong the tao ico: {e}")

# 2. Run PyInstaller
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "ResonaMod",
    "--add-data", f"{AVATARS_DIR};avatars",
]

logo_png = os.path.join(BASE_DIR, "logo.png")
if os.path.exists(logo_png):
    cmd.extend(["--add-data", f"{logo_png};."])

if os.path.exists(app_png):
    cmd.extend(["--add-data", f"{app_png};."])

if os.path.exists(TOOLS_DIR):
    cmd.extend(["--add-data", f"{TOOLS_DIR};tools"])

if os.path.exists(ICON_ICO):
    cmd.extend(["--icon", ICON_ICO])

cmd.append(os.path.join(BASE_DIR, "ResonaMod.py"))

print("Dang chay PyInstaller...")
res = subprocess.run(cmd, cwd=BASE_DIR)

if res.returncode == 0:
    import re
    with open(os.path.join(BASE_DIR, "ResonaMod.py"), "r", encoding="utf-8") as f:
        m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', f.read())
        APP_VERSION = m.group(1) if m else "1.0.1"
    
    dist_dir = os.path.join(BASE_DIR, 'dist', 'ResonaMod')
    zip_path = os.path.join(BASE_DIR, 'dist', f'ResonaMod-v{APP_VERSION}-Standalone.zip')
    print("\n📦 Dang nen thu muc phat hanh thanh file .zip...")
    try:
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', os.path.join(BASE_DIR, 'dist'), 'ResonaMod')
        zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"✅ Da tao ban .zip phat hanh: {zip_path} ({zip_size_mb:.1f} MB)")
    except Exception as e:
        print(f"⚠️ Khong the tao file zip: {e}")

    print("\n🎉 BUILD & DONG GOI HOAN TAT!")
    print(f"📁 Thu muc chay truc tiep: {dist_dir}")
    print(f"📦 File zip de chia se:    {zip_path}")
else:
    print(f"\n❌ Loi khi dong goi: {res.returncode}")
