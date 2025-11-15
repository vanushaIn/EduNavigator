"""
Команда для обновления рейтингов университетов из Google Places API
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from universities.models import University
from universities.utils import update_university_google_rating
import time


class Command(BaseCommand):
    help = 'Обновляет рейтинги университетов из Google Places API'

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
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Выводить подробную информацию о запросах к API',
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
        
        if not api_key:
            self.stdout.write(
                self.style.WARNING(
                    'ВНИМАНИЕ: GOOGLE_PLACES_API_KEY не установлен в настройках.\n'
                    'Добавьте GOOGLE_PLACES_API_KEY=ваш_ключ в файл .env\n'
                    'Получить ключ можно на https://console.cloud.google.com/\n'
                    'Включите Places API в Google Cloud Console'
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
            if university.google_rating and university.google_place_id:
                self.stdout.write(
                    self.style.WARNING(f'  Пропущен (уже есть рейтинг: {university.google_rating})')
                )
                skipped += 1
                continue
            
            try:
                success = update_university_google_rating(university, verbose=options.get('verbose', False))
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [OK] Обновлен: рейтинг {university.google_rating}, '
                            f'отзывов {university.google_reviews_count}'
                        )
                    )
                    updated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING('  [FAIL] Рейтинг не найден в Google Places')
                    )
                    failed += 1
                
                # Задержка между запросами, чтобы не превысить лимиты API
                if index < total:
                    time.sleep(delay)
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  [ERROR] Ошибка: {str(e)}')
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

