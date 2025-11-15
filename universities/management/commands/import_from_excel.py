from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from universities.models import (
    Region, UniversityType, University, Faculty, Program,
    UniversityRating, UniversityComparison, News
)
from django.contrib.auth.models import User
import os
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None


class Command(BaseCommand):
    help = 'Импортирует вузы и специальности из Excel файла. Удаляет все существующие вузы.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='postupi_detailed_20251019_225218.xlsx',
            help='Путь к Excel файлу'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Проверяем наличие файла
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден!')
            )
            return
        
        # Проверяем наличие необходимых библиотек
        if pd is None:
            self.stdout.write(
                self.style.ERROR(
                    'ОШИБКА: pandas не установлен!\n'
                    'Установите его командой: pip install pandas openpyxl'
                )
            )
            return
        
        self.stdout.write('Начинаем импорт данных из Excel...')
        
        try:
            # Читаем Excel файл
            self.stdout.write(f'Читаем файл: {file_path}')
            
            # Читаем первый лист (вузы)
            df_universities = pd.read_excel(file_path, sheet_name=0)
            self.stdout.write(f'Загружено {len(df_universities)} записей вузов')
            
            # Читаем второй лист (специальности)
            df_programs = pd.read_excel(file_path, sheet_name=1)
            self.stdout.write(f'Загружено {len(df_programs)} записей специальностей')
            
            # Выводим структуру для отладки
            self.stdout.write('\nКолонки первого листа (вузы):')
            for col in df_universities.columns:
                self.stdout.write(f'  - {col}')
            
            self.stdout.write('\nКолонки второго листа (специальности):')
            for col in df_programs.columns:
                self.stdout.write(f'  - {col}')
            
            # Удаляем все существующие данные
            self.stdout.write('\nУдаляем существующие данные...')
            with transaction.atomic():
                # Удаляем связанные данные
                UniversityRating.objects.all().delete()
                UniversityComparison.objects.all().delete()
                News.objects.all().delete()
                Program.objects.all().delete()
                Faculty.objects.all().delete()
                University.objects.all().delete()
                
            self.stdout.write(self.style.SUCCESS('Все существующие вузы удалены'))
            
            # Импортируем данные
            self.stdout.write('\nИмпортируем вузы...')
            universities_created = self.import_universities(df_universities)
            self.stdout.write(
                self.style.SUCCESS(f'Создано {universities_created} вузов')
            )
            
            self.stdout.write('\nИмпортируем специальности...')
            programs_created = self.import_programs(df_programs)
            self.stdout.write(
                self.style.SUCCESS(f'Создано {programs_created} специальностей')
            )
            
            self.stdout.write(
                self.style.SUCCESS('\nИмпорт завершен успешно!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при импорте: {str(e)}')
            )
            import traceback
            traceback.print_exc()
    
    def import_universities(self, df):
        """Импортирует вузы из DataFrame"""
        universities_created = 0
        skipped = 0
        
        # Получаем или создаем дефолтные значения
        default_region, _ = Region.objects.get_or_create(
            code='00',
            defaults={'name': 'Не указан'}
        )
        
        default_type, _ = UniversityType.objects.get_or_create(
            name='Университет'
        )
        
        # Сначала создаем все уникальные регионы
        self.stdout.write('Создаем регионы...')
        unique_cities = df['city'].dropna().unique()
        region_cache = {}
        
        # Получаем максимальный код один раз
        max_code_obj = Region.objects.aggregate(max_code=Max('code'))['max_code']
        if max_code_obj:
            try:
                next_code = int(max_code_obj) + 1
            except (ValueError, TypeError):
                next_code = Region.objects.count() + 1
        else:
            next_code = 1
        
        for city in unique_cities:
            city_str = str(city).strip()
            if city_str and city_str != 'Не указан':
                if city_str not in region_cache:
                    # Пытаемся найти существующий регион
                    region = Region.objects.filter(name=city_str).first()
                    if not region:
                        # Убеждаемся, что код уникален
                        while Region.objects.filter(code=f'{next_code:02d}').exists():
                            next_code += 1
                        
                        try:
                            region = Region.objects.create(
                                name=city_str,
                                code=f'{next_code:02d}'
                            )
                            next_code += 1
                        except Exception as e:
                            # Если ошибка (например, дубликат), пытаемся найти регион снова
                            region = Region.objects.filter(name=city_str).first()
                            if not region:
                                # Пробуем следующий код
                                next_code += 1
                                while Region.objects.filter(code=f'{next_code:02d}').exists():
                                    next_code += 1
                                region = Region.objects.create(
                                    name=city_str,
                                    code=f'{next_code:02d}'
                                )
                                next_code += 1
                    region_cache[city_str] = region
        
        self.stdout.write(f'Создано/найдено {len(region_cache)} регионов')
        
        for index, row in df.iterrows():
            try:
                # Извлекаем данные из строки (используем реальные названия колонок)
                name = row.get('name') if 'name' in row.index else None
                if name is None or pd.isna(name) or not str(name).strip():
                    skipped += 1
                    continue
                name = str(name).strip()
                
                # Краткое название - первые 50 символов полного названия
                short_name = name[:50] if name else ''
                
                # Город
                city = row.get('city') if 'city' in row.index else None
                if city is None or pd.isna(city) or not str(city).strip():
                    city = 'Не указан'
                    region = default_region
                else:
                    city = str(city).strip()
                    region = region_cache.get(city, default_region)
                
                # Адрес - используем город
                address = city
                
                # Сайт
                website = row.get('detail_url') if 'detail_url' in row.index else ''
                if website is None or pd.isna(website):
                    website = ''
                else:
                    website = str(website).strip()
                
                # Тип вуза (Государственный/Частный)
                university_type_str = row.get('type') if 'type' in row.index else None
                if university_type_str is None or pd.isna(university_type_str):
                    is_public = True
                else:
                    university_type_str = str(university_type_str).lower()
                    is_public = 'государственный' in university_type_str or 'state' in university_type_str
                
                # Год основания - по умолчанию
                founded_year = 2000
                
                # Описание - можно использовать directions или оставить пустым
                description = row.get('directions') if 'directions' in row.index else ''
                if description is None or pd.isna(description):
                    description = ''
                else:
                    description = str(description)[:500].strip()  # Ограничиваем длину
                
                # Создаем университет
                university = University.objects.create(
                    name=name,
                    short_name=short_name,
                    description=description,
                    founded_year=founded_year,
                    region=region,
                    city=city,
                    address=address,
                    website=website,
                    email='',
                    phone='',
                    university_type=default_type,
                    is_public=is_public,
                    accreditation='',
                    license=''
                )
                
                universities_created += 1
                
                if universities_created % 100 == 0:
                    self.stdout.write(f'  Обработано {universities_created} вузов...')
                    
            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'Ошибка при импорте вуза на строке {index + 2}: {str(e)}')
                )
                continue
        
        self.stdout.write(f'Пропущено {skipped} вузов (уже существуют или ошибки)')
        return universities_created
    
    def import_programs(self, df):
        """Импортирует специальности из DataFrame"""
        programs_created = 0
        skipped_no_university = 0
        skipped_errors = 0
        
        # Создаем кеш университетов для быстрого поиска
        self.stdout.write('Создаем кеш университетов...')
        universities_cache = {}
        for univ in University.objects.all():
            universities_cache[univ.name] = univ
            # Также добавляем варианты с обрезанными названиями для частичного поиска
            if len(univ.name) > 30:
                universities_cache[univ.name[:30]] = univ
        
        self.stdout.write(f'В кеше {len(universities_cache)} записей университетов')
        
        for index, row in df.iterrows():
            try:
                # Извлекаем данные (используем реальные названия колонок)
                university_name = row.get('university_name') if 'university_name' in row.index else None
                if university_name is None or pd.isna(university_name) or not str(university_name).strip():
                    skipped_no_university += 1
                    continue
                university_name = str(university_name).strip()
                
                program_name = row.get('name') if 'name' in row.index else None
                if program_name is None or pd.isna(program_name) or not str(program_name).strip():
                    skipped_no_university += 1
                    continue
                program_name = str(program_name).strip()
                
                # Ищем университет
                university = None
                
                # 1. Точное совпадение
                university = universities_cache.get(university_name)
                
                # 2. Поиск в базе данных (на случай если не в кеше)
                if not university:
                    university = University.objects.filter(name=university_name).first()
                
                # 3. Поиск по частичному совпадению
                if not university:
                    for cached_name, cached_univ in universities_cache.items():
                        if cached_name in university_name or university_name in cached_name:
                            university = cached_univ
                            break
                
                # 4. Поиск в БД по частичному совпадению
                if not university:
                    university = University.objects.filter(name__icontains=university_name[:50]).first()
                
                # 5. Поиск по началу названия
                if not university and len(university_name) > 20:
                    university = University.objects.filter(name__istartswith=university_name[:20]).first()
                
                if not university:
                    skipped_no_university += 1
                    if skipped_no_university <= 10 or skipped_no_university % 500 == 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Вуз "{university_name[:50]}..." не найден (пропущено всего: {skipped_no_university})'
                            )
                        )
                    continue
                
                # Получаем или создаем факультет (используем форму обучения или создаем общий)
                education_form = row.get('education_form') if 'education_form' in row.index else None
                if education_form is None or pd.isna(education_form) or not str(education_form).strip():
                    faculty_name = 'Общий факультет'
                else:
                    faculty_name = str(education_form).strip()[:200]
                
                faculty, _ = Faculty.objects.get_or_create(
                    name=faculty_name,
                    university=university,
                    defaults={
                        'description': '',
                        'dean': ''
                    }
                )
                
                # Описание программы
                description = row.get('description') if 'description' in row.index else None
                if description is None or pd.isna(description) or str(description).strip() == 'Не указано':
                    description = ''
                else:
                    description = str(description).strip()[:1000]  # Ограничиваем длину
                
                # Уровень образования - по умолчанию бакалавриат
                degree_level = 'Бакалавриат'
                
                # Срок обучения - по умолчанию 4 года
                duration = 4
                
                # Стоимость обучения
                tuition_fee = row.get('price') if 'price' in row.index else None
                if tuition_fee is None or pd.isna(tuition_fee):
                    tuition_fee = None
                else:
                    try:
                        # Преобразуем цену (может быть в тысячах рублей)
                        tuition_fee = float(tuition_fee)
                        # Если цена меньше 1000, вероятно это уже в рублях, иначе умножаем на 1000
                        if tuition_fee < 1000:
                            tuition_fee = int(tuition_fee * 1000)
                        else:
                            tuition_fee = int(tuition_fee)
                    except (ValueError, TypeError):
                        tuition_fee = None
                
                # Создаем программу
                program = Program.objects.create(
                    name=program_name[:200],
                    faculty=faculty,
                    degree_level=degree_level,
                    duration_years=duration,
                    description=description,
                    tuition_fee=tuition_fee
                )
                
                programs_created += 1
                
                if programs_created % 1000 == 0:
                    self.stdout.write(f'  Обработано {programs_created} специальностей...')
                    
            except Exception as e:
                skipped_errors += 1
                if skipped_errors <= 10 or skipped_errors % 500 == 0:
                    self.stdout.write(
                        self.style.WARNING(f'Ошибка при импорте специальности на строке {index + 2}: {str(e)}')
                    )
                continue
        
        self.stdout.write(f'Пропущено {skipped_no_university} специальностей (не найден вуз)')
        self.stdout.write(f'Пропущено {skipped_errors} специальностей (ошибки)')
        return programs_created
    
    def detect_column_mapping(self, columns, data_type):
        """Определяет маппинг колонок автоматически"""
        mapping = {}
        columns_lower = [col.lower() if isinstance(col, str) else str(col).lower() for col in columns]
        
        if data_type == 'universities':
            # Ищем колонки для вузов
            name_keywords = ['название', 'name', 'вуз', 'university']
            short_name_keywords = ['краткое', 'short', 'сокращ']
            city_keywords = ['город', 'city']
            region_keywords = ['регион', 'region']
            address_keywords = ['адрес', 'address']
            website_keywords = ['сайт', 'website', 'url']
            email_keywords = ['email', 'e-mail', 'почта']
            phone_keywords = ['телефон', 'phone', 'тел']
            year_keywords = ['год', 'year', 'основания']
            public_keywords = ['государственный', 'public', 'тип']
            desc_keywords = ['описание', 'description', 'опис']
            
            for i, col in enumerate(columns_lower):
                if any(kw in col for kw in name_keywords) and 'краткое' not in col:
                    mapping['name'] = columns[i]
                elif any(kw in col for kw in short_name_keywords):
                    mapping['short_name'] = columns[i]
                elif any(kw in col for kw in city_keywords):
                    mapping['city'] = columns[i]
                elif any(kw in col for kw in region_keywords):
                    mapping['region'] = columns[i]
                elif any(kw in col for kw in address_keywords):
                    mapping['address'] = columns[i]
                elif any(kw in col for kw in website_keywords):
                    mapping['website'] = columns[i]
                elif any(kw in col for kw in email_keywords):
                    mapping['email'] = columns[i]
                elif any(kw in col for kw in phone_keywords):
                    mapping['phone'] = columns[i]
                elif any(kw in col for kw in year_keywords):
                    mapping['founded_year'] = columns[i]
                elif any(kw in col for kw in public_keywords):
                    mapping['is_public'] = columns[i]
                elif any(kw in col for kw in desc_keywords):
                    mapping['description'] = columns[i]
        
        elif data_type == 'programs':
            # Ищем колонки для специальностей
            university_keywords = ['вуз', 'university', 'университет']
            program_keywords = ['специальность', 'program', 'спец', 'название', 'name']
            faculty_keywords = ['факультет', 'faculty']
            degree_keywords = ['уровень', 'degree', 'степень', 'level']
            duration_keywords = ['срок', 'duration', 'лет', 'year']
            tuition_keywords = ['стоимость', 'tuition', 'цена', 'price', 'руб']
            desc_keywords = ['описание', 'description']
            
            for i, col in enumerate(columns_lower):
                if any(kw in col for kw in university_keywords):
                    mapping['university'] = columns[i]
                elif any(kw in col for kw in program_keywords):
                    mapping['program'] = columns[i]
                elif any(kw in col for kw in faculty_keywords):
                    mapping['faculty'] = columns[i]
                elif any(kw in col for kw in degree_keywords):
                    mapping['degree_level'] = columns[i]
                elif any(kw in col for kw in duration_keywords):
                    mapping['duration'] = columns[i]
                elif any(kw in col for kw in tuition_keywords):
                    mapping['tuition_fee'] = columns[i]
                elif any(kw in col for kw in desc_keywords):
                    mapping['description'] = columns[i]
        
        return mapping
    
    def get_value(self, row, possible_keys):
        """Получает значение из строки по возможным ключам"""
        if isinstance(possible_keys, str):
            possible_keys = [possible_keys]
        
        for key in possible_keys:
            if key in row.index:
                value = row[key]
                if not pd.isna(value):
                    return value
        
        return None

