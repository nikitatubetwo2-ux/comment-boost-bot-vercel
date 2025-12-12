#!/bin/bash
# Скрипт запуска Video Factory

cd "$(dirname "$0")"

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активация
source venv/bin/activate

# Установка зависимостей
pip install -q -r requirements.txt

# Запуск
python main.py
