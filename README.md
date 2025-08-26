# Flask Blog

Учебный проект: блог на Flask с регистрацией пользователей, постами и комментариями.

## 🚀 Возможности
- Регистрация и вход пользователей
- Создание, редактирование и удаление постов
- Публичные и приватные записи
- Комментарии
- Теги для сортировки

## 🔧 Установка и запуск
```bash
# Клонировать репозиторий
git clone https://github.com/saida2347g/flask-blog.git
cd flask-blog

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate   # для Windows
# или source venv/bin/activate   # для Linux/Mac

# Установить зависимости
pip install flask flask_sqlalchemy werkzeug

# Запустить приложение
python app.py
