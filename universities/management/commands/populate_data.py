from django.core.management.base import BaseCommand
from universities.models import Region, UniversityType, University, Faculty, Program, News
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Заполняет базу данных примерами российских университетов'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы данных...')
        
        # Создаем регионы
        regions_data = [
            {'name': 'Москва', 'code': '77'},
            {'name': 'Санкт-Петербург', 'code': '78'},
            {'name': 'Московская область', 'code': '50'},
            {'name': 'Краснодарский край', 'code': '23'},
            {'name': 'Свердловская область', 'code': '66'},
            {'name': 'Новосибирская область', 'code': '54'},
            {'name': 'Республика Татарстан', 'code': '16'},
            {'name': 'Нижегородская область', 'code': '52'},
            {'name': 'Самарская область', 'code': '63'},
            {'name': 'Ростовская область', 'code': '61'},
        ]
        
        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                code=region_data['code'],
                defaults={'name': region_data['name']}
            )
            if created:
                self.stdout.write(f'Создан регион: {region.name}')
        
        # Создаем типы университетов
        university_types_data = [
            'Университет',
            'Институт',
            'Академия',
            'Консерватория',
            'Технический университет',
            'Медицинский университет',
            'Педагогический университет',
        ]
        
        for type_name in university_types_data:
            university_type, created = UniversityType.objects.get_or_create(name=type_name)
            if created:
                self.stdout.write(f'Создан тип университета: {university_type.name}')
        
        # Создаем университеты
        universities_data = [
            {
                'name': 'Московский государственный университет имени М.В. Ломоносова',
                'short_name': 'МГУ',
                'description': 'Старейший и крупнейший университет России, основанный в 1755 году. Ведущий центр образования, науки и культуры.',
                'founded_year': 1755,
                'region': 'Москва',
                'city': 'Москва',
                'address': 'Ленинские горы, д. 1, Москва, 119991',
                'website': 'https://www.msu.ru',
                'email': 'rector@msu.ru',
                'phone': '+7 (495) 939-10-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2025 года',
                'license': 'Лицензия № 001234 от 01.01.2020',
            },
            {
                'name': 'Санкт-Петербургский государственный университет',
                'short_name': 'СПбГУ',
                'description': 'Один из старейших университетов России, основанный в 1724 году. Ведущий научно-образовательный центр.',
                'founded_year': 1724,
                'region': 'Санкт-Петербург',
                'city': 'Санкт-Петербург',
                'address': 'Университетская наб., д. 7-9, Санкт-Петербург, 199034',
                'website': 'https://spbu.ru',
                'email': 'rector@spbu.ru',
                'phone': '+7 (812) 328-20-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2026 года',
                'license': 'Лицензия № 001235 от 01.01.2020',
            },
            {
                'name': 'Московский физико-технический институт',
                'short_name': 'МФТИ',
                'description': 'Ведущий технический университет России, известный своими исследованиями в области физики и математики.',
                'founded_year': 1951,
                'region': 'Московская область',
                'city': 'Долгопрудный',
                'address': 'Институтский пер., д. 9, Долгопрудный, 141701',
                'website': 'https://mipt.ru',
                'email': 'rector@mipt.ru',
                'phone': '+7 (495) 408-48-00',
                'university_type': 'Технический университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2024 года',
                'license': 'Лицензия № 001236 от 01.01.2020',
            },
            {
                'name': 'Новосибирский государственный университет',
                'short_name': 'НГУ',
                'description': 'Ведущий университет Сибири, основанный в 1959 году. Центр науки и образования в Новосибирском Академгородке.',
                'founded_year': 1959,
                'region': 'Новосибирская область',
                'city': 'Новосибирск',
                'address': 'ул. Пирогова, д. 2, Новосибирск, 630090',
                'website': 'https://www.nsu.ru',
                'email': 'rector@nsu.ru',
                'phone': '+7 (383) 363-40-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2025 года',
                'license': 'Лицензия № 001237 от 01.01.2020',
            },
            {
                'name': 'Казанский федеральный университет',
                'short_name': 'КФУ',
                'description': 'Один из старейших университетов России, основанный в 1804 году. Ведущий центр образования в Поволжье.',
                'founded_year': 1804,
                'region': 'Республика Татарстан',
                'city': 'Казань',
                'address': 'ул. Кремлевская, д. 18, Казань, 420008',
                'website': 'https://kpfu.ru',
                'email': 'rector@kpfu.ru',
                'phone': '+7 (843) 233-70-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2026 года',
                'license': 'Лицензия № 001238 от 01.01.2020',
            },
            {
                'name': 'Уральский федеральный университет имени первого Президента России Б.Н. Ельцина',
                'short_name': 'УрФУ',
                'description': 'Крупнейший университет Урала, образованный в 2010 году путем слияния УГТУ-УПИ и УрГУ.',
                'founded_year': 2010,
                'region': 'Свердловская область',
                'city': 'Екатеринбург',
                'address': 'ул. Мира, д. 19, Екатеринбург, 620002',
                'website': 'https://urfu.ru',
                'email': 'rector@urfu.ru',
                'phone': '+7 (343) 375-44-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2025 года',
                'license': 'Лицензия № 001239 от 01.01.2020',
            },
            {
                'name': 'Нижегородский государственный университет имени Н.И. Лобачевского',
                'short_name': 'ННГУ',
                'description': 'Ведущий университет Поволжья, основанный в 1916 году. Центр науки и образования в Нижнем Новгороде.',
                'founded_year': 1916,
                'region': 'Нижегородская область',
                'city': 'Нижний Новгород',
                'address': 'пр. Гагарина, д. 23, Нижний Новгород, 603950',
                'website': 'https://www.unn.ru',
                'email': 'rector@unn.ru',
                'phone': '+7 (831) 465-60-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2024 года',
                'license': 'Лицензия № 001240 от 01.01.2020',
            },
            {
                'name': 'Самарский национальный исследовательский университет имени академика С.П. Королева',
                'short_name': 'СамГУ',
                'description': 'Ведущий университет в области авиации и космонавтики, основанный в 1942 году.',
                'founded_year': 1942,
                'region': 'Самарская область',
                'city': 'Самара',
                'address': 'Московское ш., д. 34, Самара, 443086',
                'website': 'https://www.ssau.ru',
                'email': 'rector@ssau.ru',
                'phone': '+7 (846) 267-40-00',
                'university_type': 'Университет',
                'is_public': True,
                'accreditation': 'Аккредитован до 2025 года',
                'license': 'Лицензия № 001241 от 01.01.2020',
            },
        ]
        
        for uni_data in universities_data:
            region = Region.objects.get(name=uni_data['region'])
            university_type = UniversityType.objects.get(name=uni_data['university_type'])
            
            university, created = University.objects.get_or_create(
                short_name=uni_data['short_name'],
                defaults={
                    'name': uni_data['name'],
                    'description': uni_data['description'],
                    'founded_year': uni_data['founded_year'],
                    'region': region,
                    'city': uni_data['city'],
                    'address': uni_data['address'],
                    'website': uni_data['website'],
                    'email': uni_data['email'],
                    'phone': uni_data['phone'],
                    'university_type': university_type,
                    'is_public': uni_data['is_public'],
                    'accreditation': uni_data['accreditation'],
                    'license': uni_data['license'],
                }
            )
            if created:
                self.stdout.write(f'Создан университет: {university.name}')
        
        # Создаем факультеты для МГУ
        mgu = University.objects.get(short_name='МГУ')
        faculties_data = [
            {
                'name': 'Механико-математический факультет',
                'university': mgu,
                'description': 'Один из ведущих математических факультетов мира',
                'dean': 'А.А. Шабат',
            },
            {
                'name': 'Физический факультет',
                'university': mgu,
                'description': 'Центр физического образования и исследований',
                'dean': 'Н.Н. Сысоев',
            },
            {
                'name': 'Химический факультет',
                'university': mgu,
                'description': 'Ведущий центр химического образования',
                'dean': 'С.Н. Калмыков',
            },
            {
                'name': 'Биологический факультет',
                'university': mgu,
                'description': 'Центр биологического образования и исследований',
                'dean': 'М.П. Кирпичников',
            },
        ]
        
        for faculty_data in faculties_data:
            faculty, created = Faculty.objects.get_or_create(
                name=faculty_data['name'],
                university=faculty_data['university'],
                defaults={
                    'description': faculty_data['description'],
                    'dean': faculty_data['dean'],
                }
            )
            if created:
                self.stdout.write(f'Создан факультет: {faculty.name}')
        
        # Создаем программы
        programs_data = [
            {
                'name': 'Математика',
                'faculty': Faculty.objects.get(name='Механико-математический факультет'),
                'degree_level': 'Бакалавриат',
                'duration_years': 4,
                'tuition_fee': 400000,
                'description': 'Фундаментальная математика и прикладная математика',
            },
            {
                'name': 'Физика',
                'faculty': Faculty.objects.get(name='Физический факультет'),
                'degree_level': 'Бакалавриат',
                'duration_years': 4,
                'tuition_fee': 400000,
                'description': 'Теоретическая и экспериментальная физика',
            },
            {
                'name': 'Химия',
                'faculty': Faculty.objects.get(name='Химический факультет'),
                'degree_level': 'Бакалавриат',
                'duration_years': 4,
                'tuition_fee': 400000,
                'description': 'Органическая, неорганическая и физическая химия',
            },
            {
                'name': 'Биология',
                'faculty': Faculty.objects.get(name='Биологический факультет'),
                'degree_level': 'Бакалавриат',
                'duration_years': 4,
                'tuition_fee': 400000,
                'description': 'Общая биология, генетика, экология',
            },
        ]
        
        for program_data in programs_data:
            program, created = Program.objects.get_or_create(
                name=program_data['name'],
                faculty=program_data['faculty'],
                defaults={
                    'degree_level': program_data['degree_level'],
                    'duration_years': program_data['duration_years'],
                    'tuition_fee': program_data['tuition_fee'],
                    'description': program_data['description'],
                }
            )
            if created:
                self.stdout.write(f'Создана программа: {program.name}')
        
        # Создаем суперпользователя
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Администратор',
                last_name='Системы'
            )
            self.stdout.write('Создан суперпользователь: admin/admin123')
        
        self.stdout.write(
            self.style.SUCCESS('База данных успешно заполнена!')
        )
