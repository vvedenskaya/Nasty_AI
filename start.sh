#!/bin/bash

# Активация виртуальной среды
poetry run python app.py

# Установка переменных окружения
export MAIL_USERNAME="promptgramm.app@gmail.com"
export MAIL_PASSWORD="ishe wxdz jzqh vbtz"

# Запуск приложения
python app.py
