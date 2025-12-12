@echo off
chcp 65001 >nul
title Video Factory - Установка

echo ========================================
echo    🎬 Video Factory - Установка
echo ========================================
echo.

REM Проверка Python
echo [1/4] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo.
    echo Установи Python 3.10+ с https://python.org
    echo ВАЖНО: При установке поставь галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo ✅ Python найден

REM Проверка pip
echo [2/4] Проверка pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip не найден!
    echo Попробуй: python -m ensurepip --upgrade
    pause
    exit /b 1
)
echo ✅ pip найден

REM Установка зависимостей
echo [3/4] Установка зависимостей...
echo Это может занять 2-5 минут...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ Ошибка установки зависимостей
    echo Попробуй запустить от имени администратора
    pause
    exit /b 1
)
echo.
echo ✅ Зависимости установлены

REM Проверка FFmpeg
echo [4/4] Проверка FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️ FFmpeg не найден!
    echo.
    echo Установи FFmpeg:
    echo   winget install ffmpeg
    echo.
    echo Или скачай с https://ffmpeg.org/download.html
    echo и добавь в PATH
    echo.
) else (
    echo ✅ FFmpeg найден
)

REM Проверка .env
echo.
if not exist ".env" (
    echo ⚠️ Файл .env не найден!
    echo Скопируй .env файл с API ключами с основного ПК
) else (
    echo ✅ Файл .env найден
)

echo.
echo ========================================
echo    ✅ Установка завершена!
echo ========================================
echo.
echo Для запуска используй: run_windows.bat
echo Или: python main.py
echo.
pause
