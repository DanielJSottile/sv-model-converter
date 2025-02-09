@echo off
setlocal enabledelayedexpansion

:: Define paths for QuickBMS and the .bms script
set QUICKBMS_PATH=%~dp0\quickbms\quickbms.exe
set BMS_SCRIPT=%~dp0\Switch_BNTX.bms
set NOESIS_PATH=%~dp0\noesisv4474\Noesis.exe
set MODELS_DIR=%~dp0\MODELS
set BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.3\blender.exe
set PYTHON_SCRIPT=%~dp0\blender_script.py

for /d %%D in ("%MODELS_DIR%\*") do (
    echo Processing directory: %%D
    
    :: Create a single temporary Output folder in the current subdirectory, it gets unused in the final output -- this is not an output directory for the final fbx
    set "OUTPUT_DIR=%%D\Output"
    if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"

    :: Process all .bntx files in the current subdirectory
    for %%F in ("%%D\*.bntx") do (
        echo Processing file: %%F
        "%QUICKBMS_PATH%" -Y -o -D "%BMS_SCRIPT%" "%%F" "!OUTPUT_DIR!"
    )

    :: Move all .dds files from subdirectories of Output back to the Output folder
    for /d %%G in ("!OUTPUT_DIR!\*") do (
        echo Processing directory: %%G
        for %%H in ("%%G\*.dds") do (
            echo Processing file: %%H
            move "%%H" "!OUTPUT_DIR!\" >nul
        )
        rd "%%G" 2>nul
    )

    :: Process all .dds files in the Output directory via Noesis
    for %%F in ("!OUTPUT_DIR!\*.dds") do (
        echo Processing file: %%F
        set "OUTPUT_FILE=!OUTPUT_DIR!\%%~nF.png"
        "%NOESIS_PATH%" ?cmode "%%F" "!OUTPUT_FILE!"
    )

    :: Move all processed .png files back to the main directory
    move "!OUTPUT_DIR!\*.png" "%%D\" >nul

    :: Extract directory name and check for .trmdl file
    set "DIR_NAME=%%~nD"
    set "TRMDL_FILE=%%D\!DIR_NAME!.trmdl"
    echo Checking file: !TRMDL_FILE!

    :: If .trmdl exists, run Blender to process it into the final fbx model
    if exist "!TRMDL_FILE!" (
        echo Found .trmdl file: !TRMDL_FILE!
        "%BLENDER_PATH%" --background --python "%PYTHON_SCRIPT%" -- "!TRMDL_FILE!"
        echo File processed: !TRMDL_FILE!
    ) else (
        echo No matching .trmdl file found for !DIR_NAME!. Skipping...
    )
)

echo All files processed.
pause
