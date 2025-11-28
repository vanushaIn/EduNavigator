# Быстрый деплой UniGuide

## 🚀 Самый простой способ: Railway или Render

### Railway (рекомендуется)

1. Зайдите на [railway.app](https://railway.app) и войдите через GitHub
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Railway автоматически определит Django
5. Добавьте переменные окружения:
   - `SECRET_KEY` - сгенерируйте: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.railway.app`
   - `YANDEX_MAPS_API_KEY` (опционально)
   - `GOOGLE_PLACES_API_KEY` (опционально)
6. Готово! Сайт будет доступен по адресу `https://your-app.railway.app`

### Render.com

1. Зайдите на [render.com](https://render.com) и войдите через GitHub
2. Нажмите "New +" → "Web Service"
3. Подключите ваш репозиторий
4. Настройки:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn university_aggregator.wsgi:application`
5. Добавьте переменные окружения (как в Railway)
6. Готово!

## 📝 Локальный запуск для тестирования

```bash
# Установите зависимости
pip install -r requirements.txt

# Создайте .env файл
cp .env.example .env
# Отредактируйте .env и добавьте SECRET_KEY

# Настройте базу данных
python manage.py migrate
python manage.py collectstatic

# Запустите сервер
python manage.py runserver
```

## 🔧 Для VPS (продвинутый вариант)

Смотрите подробную инструкцию в `DEPLOYMENT.md`

## ⚠️ Важно перед деплоем

1. ✅ Сгенерируйте новый `SECRET_KEY`
2. ✅ Установите `DEBUG=False`
3. ✅ Укажите правильный `ALLOWED_HOSTS`
4. ✅ Настройте базу данных (PostgreSQL для production)
5. ✅ Выполните `python manage.py collectstatic`

## 📚 Подробная документация

Смотрите `DEPLOYMENT.md` для детальных инструкций по деплою на различные платформы.

