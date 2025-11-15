"""
Команда для обновления рейтингов университетов с сайта tabiturient.ru
"""
from django.core.management.base import BaseCommand
from universities.models import University
from universities.utils import parse_tabiturient_ratings_page, update_university_tabiturient_rating
import time
from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    """Вычисляет схожесть двух строк"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class Command(BaseCommand):
    help = 'Обновляет рейтинги университетов с сайта tabiturient.ru'

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
            default=0.5,
            help='Задержка между запросами в секундах (по умолчанию 0.5)',
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
            help='Выводить подробную информацию о запросах',
        )
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Использовать пакетный режим: загрузить все рейтинги сразу и сопоставить',
        )

    def handle(self, *args, **options):
        delay = options['delay']
        limit = options.get('limit')
        university_id = options.get('university_id')
        verbose = options.get('verbose', False)
        batch_mode = options.get('batch', False)
        
        if batch_mode:
            # Пакетный режим: загружаем все рейтинги сразу
            self.stdout.write('Загрузка всех рейтингов с tabiturient.ru...')
            ratings_list = parse_tabiturient_ratings_page(verbose=verbose)
            
            if not ratings_list:
                self.stdout.write(
                    self.style.ERROR('Не удалось загрузить рейтинги с tabiturient.ru')
                )
                return
            
            self.stdout.write(f'Загружено {len(ratings_list)} рейтингов')
            
            if university_id:
                universities = University.objects.filter(id=university_id)
            else:
                universities = University.objects.all()
            
            if limit:
                universities = universities[:limit]
            
            updated = 0
            matched = 0
            not_found = 0
            
            for university in universities:
                # Ищем наиболее похожее название
                best_match = None
                best_similarity = 0.0
                
                for rating_item in ratings_list:
                    sim = similarity(university.name, rating_item['name'])
                    if sim > best_similarity and sim > 0.7:  # Минимальная схожесть 70%
                        best_similarity = sim
                        best_match = rating_item
                
                if best_match:
                    university.tabiturient_rating = best_match.get('rating')
                    university.tabiturient_rank = best_match.get('rank')
                    university.tabiturient_category = best_match.get('category', '')
                    university.save(update_fields=['tabiturient_rating', 'tabiturient_rank', 'tabiturient_category'])
                    
                    if verbose:
                        self.stdout.write(
                            f'  [OK] {university.name} -> {best_match["name"]} '
                            f'(схожесть: {best_similarity:.2f}, рейтинг: {best_match.get("rating")}, место: {best_match.get("rank")})'
                        )
                    updated += 1
                    matched += 1
                else:
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f'  [FAIL] Не найдено совпадение для: {university.name}')
                        )
                    not_found += 1
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nИтоги:\n'
                    f'  Обновлено: {updated}\n'
                    f'  Найдено совпадений: {matched}\n'
                    f'  Не найдено: {not_found}\n'
                    f'  Всего обработано: {universities.count()}'
                )
            )
        else:
            # Поштучный режим: запрашиваем рейтинг для каждого университета отдельно
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
                
                # Пропускаем, если уже есть рейтинг
                if university.tabiturient_rating and university.tabiturient_rank:
                    self.stdout.write(
                        self.style.WARNING(f'  Пропущен (уже есть рейтинг: {university.tabiturient_rating}, место: {university.tabiturient_rank})')
                    )
                    skipped += 1
                    continue
                
                try:
                    success = update_university_tabiturient_rating(university, verbose=verbose)
                    
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [OK] Обновлен: рейтинг {university.tabiturient_rating}, '
                                f'место {university.tabiturient_rank}, категория {university.tabiturient_category}'
                            )
                        )
                        updated += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING('  [FAIL] Рейтинг не найден на tabiturient.ru')
                        )
                        failed += 1
                    
                    # Задержка между запросами
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

