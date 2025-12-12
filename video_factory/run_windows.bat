@echo off
chcp 65001 >nul
title Video Factory

echo ========================================
echo    🎬 Video Factory - Запуск
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установи Python 3.10+ с https://python.org
    echo При установке поставь галочку "Add Python to PATH"
    pause
    exit /b 1
)

REM Проверка зависимостей
echo Проверка зависимостей...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
)

REM Проверка .env
if not exist ".env" (
    echo ❌ Файл .env не найден!
    echo Скопируй .env файл с API ключами
    pause
    exit /b 1
)

echo.
echo ✅ Всё готово! Запускаю Video Factory...
echo.

REM Запуск
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска. Проверь логи выше.
    pause
)
