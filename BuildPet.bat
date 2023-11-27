python -m pip install --upgrade pip
python -m pip install PyInstaller psutil Pillow
python -m PyInstaller --noconfirm --onefile --windowed --icon "icon.ico" "DesktopPet.py"
pause