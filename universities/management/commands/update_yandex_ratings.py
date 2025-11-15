"""
Команда для обновления рейтингов университетов из Яндекс Карт
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from universities.models import University
from universities.utils import update_university_yandex_rating
import time


class Command(BaseCommand):
    help = 'Обновляет рейтинги университетов из Яндекс Карт'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Ограничить количество обновляемых университетов',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Задержка между запросами в секундах (по умолчанию 1.0)',
        )
        parser.add_argument(
            '--university-id',
            type=int,
            default=None,
            help='Обновить рейтинг только для конкретного университета',
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, 'YANDEX_MAPS_API_KEY', '')
        
        if not api_key:
            self.stdout.write(
                self.style.WARNING(
                    'ВНИМАНИЕ: YANDEX_MAPS_API_KEY не установлен в настройках.\n'
                    'Добавьте YANDEX_MAPS_API_KEY=ваш_ключ в файл .env\n'
                    'Получить ключ можно на https://developer.tech.yandex.ru/\n'
                    'Или используйте Google Places API: python manage.py update_google_ratings'
                )
            )
            return
        
        delay = options['delay']
        limit = options.get('limit')
        university_id = options.get('university_id')
        
        if university_id:
            universities = University.objects.filter(id=university_id)
        else:
            universities = University.objects.all()
        
        if limit:
            universities = universities[:limit]
        
        total = universities.count()
        self.stdout.write(f'Найдено {total} университетов для обновления')
        
        updated = 0
        failed = 0
        skipped = 0
        
        for index, university in enumerate(universities, 1):
            self.stdout.write(
                f'\n[{index}/{total}] Обработка: {university.name}'
            )
            
            # Пропускаем, если уже есть рейтинг и place_id
            if university.yandex_rating and university.yandex_place_id:
                self.stdout.write(
                    self.style.WARNING(f'  Пропущен (уже есть рейтинг: {university.yandex_rating})')
                )
                skipped += 1
                continue
            
            try:
                success = update_university_yandex_rating(university)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Обновлен: рейтинг {university.yandex_rating}, '
                            f'отзывов {university.yandex_reviews_count}'
                        )
                    )
                    updated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING('  ✗ Рейтинг не найден в Яндекс Картах')
                    )
                    failed += 1
                
                # Задержка между запросами, чтобы не превысить лимиты API
                if index < total:
                    time.sleep(delay)
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Ошибка: {str(e)}')
                )
                failed += 1
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'\nИтоги:\n'
                f'  Обновлено: {updated}\n'
                f'  Не найдено: {failed}\n'
                f'  Пропущено: {skipped}\n'
                f'  Всего: {total}'
            )
        )

