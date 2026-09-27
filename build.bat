@echo off
REM Compila LECTOR.exe localmente (requer Python 3.10+ instalado). Duplo clique.
cd /d %~dp0
python -m pip install pymupdf==1.28.2 pyinstaller || goto erro
if not exist tessdata mkdir tessdata
for %%L in (por eng) do if not exist tessdata\%%L.traineddata curl -sSL -o tessdata\%%L.traineddata https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/%%L.traineddata
python -m PyInstaller --onefile --windowed --name LECTOR --add-data "tessdata;tessdata" lector.py || goto erro
certutil -hashfile dist\LECTOR.exe SHA256 > dist\LECTOR.exe.sha256.txt
echo. & echo Pronto: dist\LECTOR.exe & pause & exit /b
:erro
echo Falha na compilacao. & pause
