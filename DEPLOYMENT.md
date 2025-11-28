# Инструкция по деплою UniGuide

## Варианты хостинга

### 1. Railway (Рекомендуется - простой и быстрый)

1. Зарегистрируйтесь на [Railway.app](https://railway.app)
2. Создайте новый проект
3. Подключите GitHub репозиторий
4. Добавьте переменные окружения из `.env.example`
5. Railway автоматически определит Django и запустит проект

**Создайте файл `Procfile` в корне проекта:**
```
web: gunicorn university_aggregator.wsgi:application --bind 0.0.0.0:$PORT
```

### 2. Render.com

1. Зарегистрируйтесь на [Render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите GitHub репозиторий
4. Настройки:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn university_aggregator.wsgi:application`
5. Добавьте переменные окружения
6. Выберите PostgreSQL в качестве базы данных (опционально)

### 3. PythonAnywhere (Бесплатный вариант)

1. Зарегистрируйтесь на [PythonAnywhere.com](https://www.pythonanywhere.com)
2. Откройте Bash консоль
3. Клонируйте репозиторий:
   ```bash
   git clone <your-repo-url>
   cd agregator
   ```
4. Создайте виртуальное окружение:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Настройте базу данных:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```
6. Создайте файл `.env` с переменными окружения
7. В разделе Web настройте WSGI файл:
   ```python
   import os
   import sys
   
   path = '/home/yourusername/agregator'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   os.environ['DJANGO_SETTINGS_MODULE'] = 'university_aggregator.settings_production'
   
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

### 4. VPS (DigitalOcean, Hetzner, AWS EC2)

#### Установка на Ubuntu/Debian

1. **Подключитесь к серверу по SSH**

2. **Установите зависимости:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib git
   ```

3. **Клонируйте репозиторий:**
   ```bash
   cd /var/www
   sudo git clone <your-repo-url> uniguide
   sudo chown -R $USER:$USER /var/www/uniguide
   cd uniguide
   ```

4. **Создайте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn psycopg2-binary
   ```

5. **Настройте базу данных PostgreSQL:**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE uniguide_db;
   CREATE USER uniguide_user WITH PASSWORD 'your-password';
   ALTER ROLE uniguide_user SET client_encoding TO 'utf8';
   ALTER ROLE uniguide_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE uniguide_user SET timezone TO 'Europe/Moscow';
   GRANT ALL PRIVILEGES ON DATABASE uniguide_db TO uniguide_user;
   \q
   ```

6. **Создайте файл `.env`:**
   ```bash
   nano .env
   ```
   Добавьте все переменные из `.env.example`

7. **Обновите `settings_production.py`** для использования PostgreSQL

8. **Выполните миграции:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

9. **Создайте systemd сервис для Gunicorn:**
   ```bash
   sudo nano /etc/systemd/system/uniguide.service
   ```
   
   Добавьте:
   ```ini
   [Unit]
   Description=UniGuide Gunicorn daemon
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/uniguide
   ExecStart=/var/www/uniguide/venv/bin/gunicorn \
       --config /var/www/uniguide/gunicorn_config.py \
       university_aggregator.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

10. **Запустите сервис:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start uniguide
    sudo systemctl enable uniguide
    ```

11. **Настройте Nginx:**
    ```bash
    sudo nano /etc/nginx/sites-available/uniguide
    ```
    
    Добавьте:
    ```nginx
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        location /static/ {
            alias /var/www/uniguide/staticfiles/;
        }

        location /media/ {
            alias /var/www/uniguide/media/;
        }

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

12. **Активируйте сайт:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/uniguide /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

13. **Настройте SSL с Let's Encrypt:**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    ```

## Общие шаги для всех вариантов

### 1. Подготовка кода

```bash
# Соберите статические файлы
python manage.py collectstatic --noinput

# Выполните миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser
```

### 2. Переменные окружения

Создайте файл `.env` на сервере с:
- `SECRET_KEY` - сгенерируйте новый ключ
- `DEBUG=False` - обязательно для production
- `ALLOWED_HOSTS` - ваш домен
- API ключи для Яндекс и Google

### 3. Безопасность

- ✅ Используйте сильный `SECRET_KEY`
- ✅ Установите `DEBUG=False`
- ✅ Настройте `ALLOWED_HOSTS`
- ✅ Используйте HTTPS (SSL сертификат)
- ✅ Регулярно обновляйте зависимости
- ✅ Используйте PostgreSQL вместо SQLite для production

### 4. Мониторинг

- Настройте логирование
- Используйте мониторинг (Sentry, Rollbar)
- Настройте резервное копирование базы данных

## Проверка после деплоя

1. Откройте сайт в браузере
2. Проверьте статические файлы (CSS, JS)
3. Проверьте загрузку изображений
4. Протестируйте основные функции
5. Проверьте админ-панель

## Обновление сайта

```bash
# На VPS
cd /var/www/uniguide
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart uniguide
```

## Резервное копирование

```bash
# Бэкап базы данных (PostgreSQL)
pg_dump -U uniguide_user uniguide_db > backup_$(date +%Y%m%d).sql

# Бэкап медиа файлов
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

