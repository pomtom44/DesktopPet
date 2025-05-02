@echo off
echo Building DesktopPet...

:: Check for required files
if not exist "duck.ico" (
    echo Error: Icon file not found at duck.ico
    pause
    exit /b 1
)

if not exist "config.ini" (
    echo Error: Config file not found at config.ini
    pause
    exit /b 1
)

if not exist "DesktopPet.py" (
    echo Error: Main script not found at DesktopPet.py
    pause
    exit /b 1
)

:: Remove existing build files
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "DesktopPet.spec" del "DesktopPet.spec"

:: Run PyInstaller with all required files
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --icon=duck.ico ^
    --add-data "images;images" ^
    --add-data "config.ini;." ^
    --name "DesktopPet" ^
    DesktopPet.py

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Build complete!
pause