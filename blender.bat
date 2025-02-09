@echo off
setlocal enabledelayedexpansion

:: Define paths for QuickBMS and the .bms script
set QUICKBMS_PATH=%~dp0\quickbms\quickbms.exe
set BMS_SCRIPT=%~dp0\Switch_BNTX.bms
:: Define the Noesis path for the executable
set NOESIS_PATH=%~dp0\noesisv4474\Noesis.exe

:: Define the parent directory containing all the subdirectories
set MODELS_DIR=%~dp0\MODELS

:: Define the path to the Blender executable
set BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 4.3\blender.exe

:: Define the path to the Python script
set PYTHON_SCRIPT=%~dp0\blender_script.py


:: Loop through each subdirectory in MODELS
for /d %%D in ("%MODELS_DIR%\*") do (
    echo Processing directory: %%D

    :: Create a single Output folder in the current subdirectory
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
            move "%%H" "!OUTPUT_DIR!\"
        )
        :: Remove the empty subdirectory
        rd "%%G" 2>nul  
    )

    :: Process all .dds files in the Output directory via the noesis executable
    for %%F in ("!OUTPUT_DIR!\*.dds") do (
        echo Processing file: %%F
        :: Define output file name by changing the extension to .png
        set "OUTPUT_FILE=!OUTPUT_DIR!\%%~nF.png"
        :: Call Noesis to convert the .dds file to .png
        "%NOESIS_PATH%" ?cmode "%%F" "!OUTPUT_FILE!"
    )

    :: Move all processed .png files back to the main directory
    echo Moving processed files to main directory: %%D
    move "!OUTPUT_DIR!\*.png" "%%D\"

   :: Extract the directory name
    set "DIR_NAME=%%~nD"
    echo Directory name: !DIR_NAME!

    :: Set the full path to the .trmdl file
    set "TRMDL_FILE=%%D\!DIR_NAME!.trmdl"
    echo Checking file: !TRMDL_FILE!

    :: Debugging - print the absolute path to make sure it’s correct
    for %%I in ("!TRMDL_FILE!") do (
        echo Absolute path: %%~fI
    )

    :: Check if the .trmdl file exists before processing (no delayed expansion inside the condition)
    setlocal enabledelayedexpansion
    if exist "!TRMDL_FILE!" (
        echo Found .trmdl file: !TRMDL_FILE!
        
        :: Re-enable delayed expansion for the blender call
        endlocal
        setlocal enabledelayedexpansion

        :: Call Blender with the Python script and the .trmdl file as an argument
        echo Running Blender: "%BLENDER_PATH%" --background --python "%PYTHON_SCRIPT%" -- "!TRMDL_FILE!"
        "%BLENDER_PATH%" --background --python "%PYTHON_SCRIPT%" -- "!TRMDL_FILE!"
        echo File processed: !TRMDL_FILE!
    ) else (
        echo No matching .trmdl file found for !DIR_NAME!. Skipping...
        endlocal
    )
)

echo All files processed.
pause
