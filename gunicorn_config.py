"""
Конфигурация Gunicorn для production сервера
"""
import multiprocessing

# Биндинг
bind = "0.0.0.0:8000"

# Количество воркеров (рекомендуется: количество CPU * 2 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Количество потоков на воркер
threads = 2

# Таймауты
timeout = 120
keepalive = 5

# Логирование
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# Процесс
daemon = False
pidfile = "gunicorn.pid"

# Перезапуск при изменении кода (только для разработки)
reload = False

# Имя приложения
proc_name = "uniguide"

# Пользователь и группа (раскомментируйте для production)
# user = "www-data"
# group = "www-data"

# Максимальное количество запросов на воркер перед перезапуском
max_requests = 1000
max_requests_jitter = 50

