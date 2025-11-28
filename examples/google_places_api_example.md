# Примеры использования Google Places API

## 1. Find Place API - Точный поиск места (рекомендуется)

### Запрос:
```http
GET https://maps.googleapis.com/maps/api/place/findplacefromtext/json
?input=МГУ+Москва+Ленинские+горы
&inputtype=textquery
&fields=place_id,rating,user_ratings_total,name,geometry
&locationbias=circle:5000@55.7031,37.5307
&key=YOUR_API_KEY
&language=ru
```

### Ответ:
```json
{
  "candidates": [
    {
      "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "name": "Московский государственный университет имени М.В. Ломоносова",
      "rating": 4.5,
      "user_ratings_total": 1234,
      "geometry": {
        "location": {
          "lat": 55.7031,
          "lng": 37.5307
        }
      }
    }
  ],
  "status": "OK"
}
```

**Преимущества Find Place API:**
- Более быстрый поиск
- Может возвращать рейтинг сразу (без дополнительного запроса)
- Поддержка locationbias для более точного поиска
- Экономит квоту API (меньше запросов)

## 2. Text Search API - Поиск места по тексту (резервный вариант)

### Запрос:
```http
GET https://maps.googleapis.com/maps/api/place/textsearch/json?query=МГУ+Москва&key=YOUR_API_KEY&language=ru
```

### Ответ:
```json
{
  "results": [
    {
      "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "name": "Московский государственный университет имени М.В. Ломоносова",
      "formatted_address": "Ленинские горы, 1, Москва, 119991",
      "geometry": {
        "location": {
          "lat": 55.7031,
          "lng": 37.5307
        }
      },
      "rating": 4.5,
      "user_ratings_total": 1234,
      "types": ["university", "establishment"],
      "photos": [
        {
          "photo_reference": "CmRaAAAA...",
          "height": 3024,
          "width": 4032
        }
      ]
    }
  ],
  "status": "OK"
}
```

## 2. Place Details API - Детальная информация о месте

### Запрос:
```http
GET https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4&key=YOUR_API_KEY&language=ru&fields=rating,user_ratings_total,place_id,name,formatted_address,reviews
```

### Ответ:
```json
{
  "result": {
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "name": "Московский государственный университет имени М.В. Ломоносова",
    "formatted_address": "Ленинские горы, 1, Москва, 119991",
    "rating": 4.5,
    "user_ratings_total": 1234,
    "reviews": [
      {
        "author_name": "Иван Иванов",
        "author_url": "https://www.google.com/maps/contrib/...",
        "language": "ru",
        "profile_photo_url": "https://lh3.googleusercontent.com/...",
        "rating": 5,
        "relative_time_description": "2 месяца назад",
        "text": "Отличный университет с богатой историей. Преподаватели высокого уровня.",
        "time": 1698765432
      },
      {
        "author_name": "Мария Петрова",
        "author_url": "https://www.google.com/maps/contrib/...",
        "language": "ru",
        "profile_photo_url": "https://lh3.googleusercontent.com/...",
        "rating": 4,
        "relative_time_description": "3 месяца назад",
        "text": "Хороший вуз, но инфраструктура требует обновления.",
        "time": 1696087032
      }
    ]
  },
  "status": "OK"
}
```

## 3. Пример использования в Python (улучшенная версия)

```python
import requests

def get_google_place_rating(place_name, address, city=None, api_key=None):
    """
    Получает рейтинг места из Google Places API
    Использует Find Place API с locationbias для более точного поиска
    """
    # Шаг 1: Получаем координаты адреса для locationbias (опционально)
    lat, lng = None, None
    if address or city:
        geocoder_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geocode_query = address if address else city
        if city and address:
            geocode_query = f"{city}, {address}"
        
        geocode_params = {
            'address': geocode_query,
            'key': api_key,
            'language': 'ru'
        }
        
        geocode_response = requests.get(geocoder_url, params=geocode_params)
        if geocode_response.status_code == 200:
            geocode_data = geocode_response.json()
            if geocode_data.get('status') == 'OK' and geocode_data.get('results'):
                location = geocode_data['results'][0]['geometry']['location']
                lat = location['lat']
                lng = location['lng']
    
    # Шаг 2: Поиск места через Find Place API (более точный)
    find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
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
    
    # Добавляем locationbias для более точного поиска
    if lat and lng:
        find_params['locationbias'] = f"circle:5000@{lat},{lng}"
    
    find_response = requests.get(find_place_url, params=find_params)
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
    
    # Если Find Place не сработал, используем Text Search как резерв
    if not place_id:
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            'query': input_query,
            'key': api_key,
            'language': 'ru'
        }
        
        if lat and lng:
            search_params['location'] = f"{lat},{lng}"
            search_params['radius'] = 5000
        
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        if search_data.get('status') == 'OK' and search_data.get('results'):
            place = search_data['results'][0]
            place_id = place.get('place_id')
            rating = place.get('rating')
            reviews_count = place.get('user_ratings_total', 0)
    
    # Если нашли place_id, но нет рейтинга, получаем детали
    if place_id and rating is None:
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            'place_id': place_id,
            'key': api_key,
            'language': 'ru',
            'fields': 'rating,user_ratings_total,place_id,name'
        }
        
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()
        
        if details_data.get('status') == 'OK':
            result = details_data.get('result', {})
            rating = result.get('rating')
            reviews_count = result.get('user_ratings_total', 0)
    
    if place_id and rating is not None:
        return {
            'place_id': place_id,
            'rating': rating,
            'reviews_count': reviews_count
        }
    
    return None

# Пример использования
api_key = "YOUR_API_KEY"
rating_data = get_google_place_rating(
    place_name="МГУ",
    address="Ленинские горы, 1",
    city="Москва",
    api_key=api_key
)

if rating_data:
    print(f"Название: {rating_data['name']}")
    print(f"Рейтинг: {rating_data['rating']}/5.0")
    print(f"Отзывов: {rating_data['reviews_count']}")
    print(f"Адрес: {rating_data['address']}")
    print(f"\nПоследние отзывы:")
    for review in rating_data['reviews'][:3]:
        print(f"  - {review['author_name']}: {review['rating']} звезд")
        print(f"    {review['text'][:100]}...")
```

## 4. Возможные статусы ответа

- `OK` - Запрос успешно выполнен
- `ZERO_RESULTS` - Не найдено результатов
- `OVER_QUERY_LIMIT` - Превышен лимит запросов
- `REQUEST_DENIED` - Запрос отклонен (неверный API ключ или не включен API)
- `INVALID_REQUEST` - Неверный запрос
- `UNKNOWN_ERROR` - Неизвестная ошибка

## 5. Важные поля в ответе

### Основные поля:
- `place_id` - Уникальный идентификатор места
- `name` - Название места
- `rating` - Средний рейтинг (от 1.0 до 5.0)
- `user_ratings_total` - Общее количество отзывов
- `formatted_address` - Форматированный адрес
- `geometry.location` - Координаты (lat, lng)

### Дополнительные поля (требуют отдельного запроса):
- `reviews` - Список отзывов пользователей
- `photos` - Фотографии места
- `opening_hours` - Часы работы
- `phone_number` - Телефон
- `website` - Веб-сайт
- `price_level` - Уровень цен (для ресторанов и т.д.)

## 6. Лимиты и квоты

- **Text Search**: до 10 запросов в секунду
- **Place Details**: до 10 запросов в секунду
- **Бесплатный тариф**: $200 кредитов в месяц
- **Text Search**: $32 за 1000 запросов
- **Place Details**: $17 за 1000 запросов

## 7. Пример полного ответа с отзывами

```json
{
  "result": {
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "name": "Московский государственный университет имени М.В. Ломоносова",
    "formatted_address": "Ленинские горы, 1, Москва, 119991",
    "rating": 4.5,
    "user_ratings_total": 1234,
    "reviews": [
      {
        "author_name": "Иван Иванов",
        "rating": 5,
        "relative_time_description": "2 месяца назад",
        "text": "Отличный университет с богатой историей. Преподаватели высокого уровня, современное оборудование.",
        "time": 1698765432
      },
      {
        "author_name": "Мария Петрова",
        "rating": 4,
        "relative_time_description": "3 месяца назад",
        "text": "Хороший вуз, но инфраструктура требует обновления. Образование качественное.",
        "time": 1696087032
      }
    ],
    "geometry": {
      "location": {
        "lat": 55.7031,
        "lng": 37.5307
      }
    },
    "types": ["university", "establishment", "point_of_interest"]
  },
  "status": "OK"
}
```

## 8. Рекомендации по использованию

1. **Кэширование**: Сохраняйте `place_id` для избежания повторных запросов
2. **Задержки**: Добавляйте задержки между запросами (1-2 секунды)
3. **Обработка ошибок**: Всегда проверяйте статус ответа
4. **Лимиты полей**: Используйте параметр `fields` для экономии квоты
5. **Язык**: Указывайте `language=ru` для русскоязычных результатов

