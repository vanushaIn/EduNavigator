"""
Утилиты для работы с внешними API
"""
import requests
import time
import re
from bs4 import BeautifulSoup
from django.conf import settings
from typing import Optional, Dict, List


def get_yandex_place_rating(place_name: str, address: str, city: str = None) -> Optional[Dict]:
    """
    Получает рейтинг места из Яндекс Карт по названию и адресу
    
    Использует Search API для организаций (Places API)
    Требуется API ключ от Яндекс.Разработчик
    
    Args:
        place_name: Название места (университета)
        address: Адрес места
        city: Город (опционально)
    
    Returns:
        Dict с ключами: rating, reviews_count, place_id или None при ошибке
    """
    api_key = getattr(settings, 'YANDEX_MAPS_API_KEY', '')
    
    if not api_key:
        return None
    
    try:
        # Используем Geocoder API для получения координат адреса
        geocoder_url = "https://geocode-maps.yandex.ru/1.x/"
        
        # Формируем запрос для поиска адреса
        query = address
        if city:
            query = f"{city}, {address}"
        
        geocoder_params = {
            'apikey': api_key,
            'geocode': query,
            'format': 'json',
            'results': 1
        }
        
        geocoder_response = requests.get(geocoder_url, params=geocoder_params, timeout=10)
        geocoder_response.raise_for_status()
        
        geocoder_data = geocoder_response.json()
        
        # Получаем координаты
        lon, lat = None, None
        if 'response' in geocoder_data and 'GeoObjectCollection' in geocoder_data['response']:
            features = geocoder_data['response']['GeoObjectCollection'].get('featureMember', [])
            if features:
                geo_object = features[0]['GeoObject']
                pos = geo_object['Point']['pos']  # "lon lat"
                lon, lat = pos.split()
        
        # Если не получили координаты из адреса, пробуем по названию
        if not lon or not lat:
            query = place_name
            if city:
                query = f"{place_name}, {city}"
            
            geocoder_params['geocode'] = query
            geocoder_response = requests.get(geocoder_url, params=geocoder_params, timeout=10)
            if geocoder_response.status_code == 200:
                geocoder_data = geocoder_response.json()
                if 'response' in geocoder_data and 'GeoObjectCollection' in geocoder_data['response']:
                    features = geocoder_data['response']['GeoObjectCollection'].get('featureMember', [])
                    if features:
                        geo_object = features[0]['GeoObject']
                        pos = geo_object['Point']['pos']
                        lon, lat = pos.split()
        
        if not lon or not lat:
            return None
        
        # Используем Search API для поиска организации
        search_url = "https://search-maps.yandex.ru/v1/"
        
        search_params = {
            'apikey': api_key,
            'text': place_name,
            'll': f"{lon},{lat}",
            'type': 'biz',
            'lang': 'ru_RU',
            'results': 1,
            'spn': '0.1,0.1'  # Радиус поиска
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=10)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            
            if 'features' in search_data and len(search_data['features']) > 0:
                feature = search_data['features'][0]
                properties = feature.get('properties', {})
                company_meta = properties.get('CompanyMetaData', {})
                
                # Получаем рейтинг и количество отзывов
                rating = company_meta.get('rating', None)
                reviews = company_meta.get('reviews', 0)
                place_id = feature.get('id', '')
                
                if rating is not None:
                    return {
                        'rating': float(rating),
                        'reviews_count': int(reviews) if reviews else 0,
                        'place_id': place_id
                    }
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Яндекс API: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        print(f"Ошибка при обработке ответа Яндекс API: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None


def get_google_place_rating(place_name: str, address: str, city: str = None, verbose: bool = False) -> Optional[Dict]:
    """
    Получает рейтинг места из Google Places API по названию и адресу
    
    Использует Find Place API (более точный) или Text Search API (резервный)
    Требуется API ключ от Google Cloud Platform
    
    Args:
        place_name: Название места (университета)
        address: Адрес места
        city: Город (опционально)
        verbose: Выводить подробную информацию в консоль
    
    Returns:
        Dict с ключами: rating, reviews_count, place_id или None при ошибке
    """
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
    
    if not api_key:
        if verbose:
            print("  [WARN] API ключ не найден")
        return None
    
    try:
        # Сначала пробуем получить координаты адреса для locationbias
        lat, lng = None, None
        
        # Пробуем использовать Find Place API (более точный поиск)
        find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        
        # Формируем запрос для поиска
        input_query = place_name
        if city:
            input_query = f"{place_name} {city}"
        if address:
            input_query = f"{input_query} {address}"
        
        find_params = {
            'input': input_query,
            'inputtype': 'textquery',
            'fields': 'place_id,rating,user_ratings_total,name,geometry',
            'key': api_key,
            'language': 'ru'
        }
        
        # Если есть адрес, пробуем получить координаты для locationbias
        if address or city:
            try:
                geocoder_url = "https://maps.googleapis.com/maps/api/geocode/json"
                geocode_query = address if address else city
                if city and address:
                    geocode_query = f"{city}, {address}"
                
                if verbose:
                    print(f"  [Геокодирование] {geocode_query}")
                
                geocode_params = {
                    'address': geocode_query,
                    'key': api_key,
                    'language': 'ru'
                }
                
                geocode_response = requests.get(geocoder_url, params=geocode_params, timeout=10)
                if geocode_response.status_code == 200:
                    geocode_data = geocode_response.json()
                    if geocode_data.get('status') == 'OK' and geocode_data.get('results'):
                        location = geocode_data['results'][0]['geometry']['location']
                        lat = location['lat']
                        lng = location['lng']
                        # Добавляем locationbias для более точного поиска
                        find_params['locationbias'] = f"circle:5000@{lat},{lng}"
                        if verbose:
                            print(f"  [OK] Координаты получены: {lat}, {lng}")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] Не удалось получить координаты: {e}")
                pass  # Если не получилось получить координаты, продолжаем без locationbias
        
        # Пробуем Find Place API
        if verbose:
            print(f"  [Поиск] Find Place API: {input_query}")
        
        find_response = requests.get(find_place_url, params=find_params, timeout=10)
        find_response.raise_for_status()
        
        find_data = find_response.json()
        
        place_id = None
        rating = None
        reviews_count = 0
        
        # Если Find Place API вернул результат
        if find_data.get('status') == 'OK' and find_data.get('candidates'):
            candidate = find_data['candidates'][0]
            place_id = candidate.get('place_id')
            rating = candidate.get('rating')
            reviews_count = candidate.get('user_ratings_total', 0)
            if verbose:
                print(f"  [OK] Найдено через Find Place API: рейтинг {rating}, отзывов {reviews_count}")
        elif verbose:
            status = find_data.get('status', 'UNKNOWN')
            error_message = find_data.get('error_message', '')
            print(f"  [WARN] Find Place API: {status}")
            if error_message:
                print(f"         Ошибка: {error_message}")
            if status == 'REQUEST_DENIED':
                print(f"         Возможные причины:")
                print(f"         - API ключ неверный или неактивен")
                print(f"         - Places API (New) не включен в Google Cloud Console")
                print(f"         - Ограничения по IP/домену для API ключа")
                print(f"         - Превышен лимит запросов или квота")
                print(f"         Полный ответ API: {find_data}")
        
        # Если Find Place не сработал, используем Text Search как резервный вариант
        if not place_id:
            if verbose:
                print(f"  [Поиск] Резервный поиск через Text Search API: {input_query}")
            
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            
            query = input_query
            search_params = {
                'query': query,
                'key': api_key,
                'language': 'ru'
            }
            
            if lat and lng:
                search_params['location'] = f"{lat},{lng}"
                search_params['radius'] = 5000
            
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            
            search_data = search_response.json()
            
            if search_data.get('status') == 'OK' and search_data.get('results'):
                place = search_data['results'][0]
                place_id = place.get('place_id')
                rating = place.get('rating')
                reviews_count = place.get('user_ratings_total', 0)
                if verbose:
                    print(f"  [OK] Найдено через Text Search API: рейтинг {rating}, отзывов {reviews_count}")
            elif verbose:
                status = search_data.get('status', 'UNKNOWN')
                error_message = search_data.get('error_message', '')
                print(f"  [WARN] Text Search API: {status}")
                if error_message:
                    print(f"         Ошибка: {error_message}")
                if status == 'REQUEST_DENIED':
                    print(f"         Возможные причины:")
                    print(f"         - API ключ неверный или неактивен")
                    print(f"         - Places API (New) не включен в Google Cloud Console")
                    print(f"         - Ограничения по IP/домену для API ключа")
                    print(f"         - Превышен лимит запросов или квота")
                    print(f"         Полный ответ API: {search_data}")
        
        # Если нашли place_id, но нет рейтинга, получаем детали
        if place_id and rating is None:
            if verbose:
                print(f"  [Детали] Получение деталей места (place_id: {place_id})")
            
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place_id,
                'key': api_key,
                'language': 'ru',
                'fields': 'rating,user_ratings_total,place_id,name'
            }
            
            details_response = requests.get(details_url, params=details_params, timeout=10)
            details_response.raise_for_status()
            
            details_data = details_response.json()
            
            if details_data.get('status') == 'OK':
                result = details_data.get('result', {})
                rating = result.get('rating')
                reviews_count = result.get('user_ratings_total', 0)
                if verbose:
                    print(f"  [OK] Детали получены: рейтинг {rating}, отзывов {reviews_count}")
            elif verbose:
                print(f"  [WARN] Place Details API: {details_data.get('status', 'UNKNOWN')}")
        
        if place_id and rating is not None:
            return {
                'rating': float(rating),
                'reviews_count': int(reviews_count) if reviews_count else 0,
                'place_id': place_id
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"  [ERROR] Ошибка при запросе к Google Places API: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        if verbose:
            print(f"  [ERROR] Ошибка при обработке ответа Google Places API: {e}")
        return None
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Неожиданная ошибка: {e}")
        return None


def update_university_yandex_rating(university) -> bool:
    """
    Обновляет рейтинг университета из Яндекс Карт
    
    Args:
        university: Объект University
    
    Returns:
        True если рейтинг успешно обновлен, False в противном случае
    """
    rating_data = get_yandex_place_rating(
        place_name=university.name,
        address=university.address,
        city=university.city
    )
    
    if rating_data:
        university.yandex_rating = rating_data.get('rating')
        university.yandex_reviews_count = rating_data.get('reviews_count', 0)
        university.yandex_place_id = rating_data.get('place_id', '')
        university.save(update_fields=['yandex_rating', 'yandex_reviews_count', 'yandex_place_id'])
        return True
    
    return False


def update_university_google_rating(university, verbose: bool = False) -> bool:
    """
    Обновляет рейтинг университета из Google Places
    
    Args:
        university: Объект University
        verbose: Выводить подробную информацию в консоль
    
    Returns:
        True если рейтинг успешно обновлен, False в противном случае
    """
    rating_data = get_google_place_rating(
        place_name=university.name,
        address=university.address,
        city=university.city,
        verbose=verbose
    )
    
    if rating_data:
        university.google_rating = rating_data.get('rating')
        university.google_reviews_count = rating_data.get('reviews_count', 0)
        university.google_place_id = rating_data.get('place_id', '')
        university.save(update_fields=['google_rating', 'google_reviews_count', 'google_place_id'])
        return True
    
    return False


def get_tabiturient_rating(university_name: str, verbose: bool = False) -> Optional[Dict]:
    """
    Получает рейтинг университета с сайта tabiturient.ru/globalrating/
    
    Args:
        university_name: Название университета
        verbose: Выводить подробную информацию в консоль
    
    Returns:
        Dict с ключами: rating, rank, category или None при ошибке
    """
    try:
        url = "https://tabiturient.ru/globalrating/"
        
        if verbose:
            print(f"  [Запрос] Получение рейтинга с tabiturient.ru")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ищем таблицу с рейтингом
        rating_data = None
        
        # Пробуем найти данные в таблице
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Ищем название университета в ячейках
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        # Проверяем, содержит ли ячейка название университета
                        if university_name.lower() in cell_text.lower() or cell_text.lower() in university_name.lower():
                            # Пытаемся извлечь рейтинг из соседних ячеек
                            try:
                                rating_match = None
                                rank_match = None
                                category_match = None
                                
                                # Ищем в текущей строке
                                for cell in cells:
                                    cell_text = cell.get_text(strip=True)
                                    # Рейтинг обычно число типа 158.75
                                    if re.match(r'^\d+\.?\d*$', cell_text):
                                        if rating_match is None:
                                            rating_match = float(cell_text)
                                    # Категория типа A+, A, B
                                    elif re.match(r'^[A-Z][\+\-]?$', cell_text):
                                        category_match = cell_text
                                    # Место в рейтинге (просто число)
                                    elif cell_text.isdigit() and int(cell_text) < 1000:
                                        rank_match = int(cell_text)
                                
                                if rating_match or rank_match:
                                    rating_data = {
                                        'rating': rating_match,
                                        'rank': rank_match,
                                        'category': category_match
                                    }
                                    if verbose:
                                        print(f"  [OK] Найден рейтинг: {rating_data}")
                                    break
                            except (ValueError, AttributeError) as e:
                                if verbose:
                                    print(f"  [WARN] Ошибка при парсинге строки: {e}")
                                continue
                    
                    if rating_data:
                        break
            
            if rating_data:
                break
        
        return rating_data
        
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"  [ERROR] Ошибка при запросе к tabiturient.ru: {e}")
        return None
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Неожиданная ошибка при парсинге: {e}")
        return None


def parse_tabiturient_ratings_page(verbose: bool = False) -> List[Dict]:
    """
    Парсит всю страницу рейтинга tabiturient.ru и возвращает список всех рейтингов
    
    Args:
        verbose: Выводить подробную информацию в консоль
    
    Returns:
        List[Dict] со списком всех рейтингов: [{'name': str, 'rating': float, 'rank': int, 'category': str}, ...]
    """
    try:
        url = "https://tabiturient.ru/globalrating/"
        
        if verbose:
            print(f"  [Запрос] Парсинг всей страницы рейтинга tabiturient.ru")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        ratings_list = []
        
        # Ищем таблицы с классом listtop100 (структура: <table class="listtop100">)
        rating_tables = soup.find_all('table', class_='listtop100')
        
        if verbose:
            print(f"  [INFO] Найдено таблиц с классом listtop100: {len(rating_tables)}")
        
        for table in rating_tables:
            # Каждая таблица содержит одну строку с данными университета
            rows = table.find_all('tr')
            if not rows:
                continue
            
            row = rows[0]  # Первая (и обычно единственная) строка
            # Ищем только прямые дочерние td с классом tdtop100 (без вложенных)
            cells = [td for td in row.find_all('td', class_='tdtop100', recursive=False)]
            
            if len(cells) < 3:
                continue
            
            name = None
            rating = None
            rank = None
            category = None
            
            # Извлекаем данные из ячеек
            # Структура: [rank+change, logo, name, rating, category, arrow]
            for i, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                
                # Ищем ранг (#1, #2, etc.) - обычно в первой ячейке
                if i == 0:
                    # Ищем #N в <span class="font2"><b>#N</b></span>
                    rank_elem = cell.find('span', class_='font2')
                    if rank_elem:
                        rank_bold = rank_elem.find('b')
                        if rank_bold:
                            rank_text = rank_bold.get_text(strip=True)
                            rank_match = re.search(r'#(\d+)', rank_text)
                            if rank_match:
                                try:
                                    rank = int(rank_match.group(1))
                                except ValueError:
                                    pass
                
                # Ищем название университета - обычно в третьей ячейке (индекс 2)
                # Название находится в <span class="font2"><b>...</b></span>
                # В ячейке может быть несколько span с font2 (первый для mobile с #N, второй с названием)
                if i == 2:
                    # Ищем все span с классом font2
                    name_spans = cell.find_all('span', class_='font2')
                    for name_span in name_spans:
                        name_bold = name_span.find('b')
                        if name_bold:
                            name_text = name_bold.get_text(strip=True)
                            # Пропускаем span с #N (ранг для mobile)
                            if not re.match(r'^#\d+$', name_text) and len(name_text) > 1:
                                name = name_text
                                break
                    # Если не нашли в font2, пробуем весь текст ячейки
                    if not name:
                        # Берем первую строку текста (короткое название)
                        lines = [line.strip() for line in cell_text.split('\n') if line.strip() and not line.strip().startswith('#')]
                        if lines:
                            # Пропускаем строки с числами или символами
                            for line in lines:
                                if len(line) > 2 and not re.match(r'^[#\+\-]\d+$', line) and not re.match(r'^\d+\.?\d*$', line):
                                    name = line
                                    break
                
                # Ищем рейтинг - обычно в четвертой ячейке (индекс 3)
                if i == 3:
                    rating_elem = cell.find('span', class_='font2')
                    if rating_elem:
                        rating_bold = rating_elem.find('b')
                        if rating_bold:
                            rating_text = rating_bold.get_text(strip=True)
                        else:
                            rating_text = rating_elem.get_text(strip=True)
                        
                        try:
                            rating_val = float(rating_text)
                            if 10 <= rating_val <= 200:  # Разумный диапазон для рейтинга
                                rating = rating_val
                        except ValueError:
                            pass
                
                # Ищем категорию (A+, A, B, etc.) - обычно в пятой ячейке (индекс 4)
                if i == 4:
                    category_elem = cell.find('span', class_='font2')
                    if category_elem:
                        category_bold = category_elem.find('b')
                        if category_bold:
                            category_text = category_bold.get_text(strip=True)
                            # Проверяем, что это категория (A+, A, B, etc.), а не рейтинг
                            if re.match(r'^[A-Z][\+\-]?$', category_text):
                                category = category_text
                        else:
                            category_text = category_elem.get_text(strip=True)
                            if re.match(r'^[A-Z][\+\-]?$', category_text):
                                category = category_text
            
            # Если не нашли ранг из #N, пробуем найти в тексте первой ячейки
            if not rank and cells:
                first_cell = cells[0].get_text(strip=True)
                rank_match = re.search(r'#(\d+)', first_cell)
                if rank_match:
                    try:
                        rank = int(rank_match.group(1))
                    except ValueError:
                        pass
            
            # Если нашли хотя бы название и рейтинг или ранг, добавляем в список
            if name and (rating or rank):
                ratings_list.append({
                    'name': name,
                    'rating': rating,
                    'rank': rank,
                    'category': category
                })
        
        if verbose:
            print(f"  [OK] Найдено {len(ratings_list)} рейтингов")
        
        return ratings_list
        
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"  [ERROR] Ошибка при запросе к tabiturient.ru: {e}")
        return []
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Неожиданная ошибка при парсинге: {e}")
        return []


def update_university_tabiturient_rating(university, verbose: bool = False) -> bool:
    """
    Обновляет рейтинг университета из tabiturient.ru
    
    Args:
        university: Объект University
        verbose: Выводить подробную информацию в консоль
    
    Returns:
        True если рейтинг успешно обновлен, False в противном случае
    """
    rating_data = get_tabiturient_rating(
        university_name=university.name,
        verbose=verbose
    )
    
    if rating_data:
        university.tabiturient_rating = rating_data.get('rating')
        university.tabiturient_rank = rating_data.get('rank')
        university.tabiturient_category = rating_data.get('category', '')
        university.save(update_fields=['tabiturient_rating', 'tabiturient_rank', 'tabiturient_category'])
        return True
    
    return False

