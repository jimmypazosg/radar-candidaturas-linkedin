@echo off
setlocal EnableExtensions

REM Uso:
REM   compilar_pdf.bat [ruta_html_entrada] [ruta_pdf_salida]
REM Sin argumentos, compila plantilla_cv.html -> CV_Jimmy_Pazos.pdf en el directorio actual.

set "INPUT_HTML=%~1"
if "%INPUT_HTML%"=="" set "INPUT_HTML=%cd%\plantilla_cv.html"

set "OUTPUT_PDF=%~2"
if "%OUTPUT_PDF%"=="" set "OUTPUT_PDF=%~dp1CV_Jimmy_Pazos.pdf"
if "%~1"=="" set "OUTPUT_PDF=%cd%\CV_Jimmy_Pazos.pdf"

if not exist "%INPUT_HTML%" (
  echo [ERROR] No se encuentra el HTML de entrada: "%INPUT_HTML%"
  exit /b 1
)

for %%I in ("%INPUT_HTML%") do set "ABS_HTML=%%~fI"
for %%O in ("%OUTPUT_PDF%") do (
  set "ABS_PDF=%%~fO"
  set "OUT_DIR=%%~dpO"
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "BROWSER="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "BROWSER=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "BROWSER=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "BROWSER=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" set "BROWSER=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "BROWSER=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not defined BROWSER (
  for /f "delims=" %%B in ('where chrome.exe 2^>nul') do if not defined BROWSER set "BROWSER=%%B"
)
if not defined BROWSER (
  for /f "delims=" %%B in ('where msedge.exe 2^>nul') do if not defined BROWSER set "BROWSER=%%B"
)

if not defined BROWSER (
  echo [ERROR] No se encontro Google Chrome ni Microsoft Edge instalado.
  exit /b 2
)

set "FILE_URI=%ABS_HTML:\=/%"
set "FILE_URI=file:///%FILE_URI%"

echo Compilando PDF con: "%BROWSER%"
echo   Entrada: "%ABS_HTML%"
echo   Salida:  "%ABS_PDF%"

"%BROWSER%" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="%ABS_PDF%" "%FILE_URI%"
if errorlevel 1 (
  echo [ERROR] Fallo la generacion del PDF.
  exit /b 3
)

if not exist "%ABS_PDF%" (
  echo [ERROR] No se genero el archivo PDF en "%ABS_PDF%".
  exit /b 4
)

echo [OK] PDF generado correctamente: "%ABS_PDF%"
exit /b 0
