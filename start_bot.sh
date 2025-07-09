#!/bin/bash

# Проверка операционной системы
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Запуск бота на Linux..."
    # Команда для запуска бота на Linux
    python3 src/bot.py

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Запуск бота на macOS..."
    # Команда для запуска бота на macOS
    python3 src/bot.py

else
    echo "Неизвестная операционная система. Поддерживаются только Linux и macOS."
fi
