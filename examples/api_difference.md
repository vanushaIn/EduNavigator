# Разница между Google Maps JavaScript API и Places API (REST)

## 1. Google Maps JavaScript API (для карт на странице)

**URL:** `https://maps.googleapis.com/maps/api/js?key=YOUR_KEY&callback=iniciarMap`

**Назначение:** Встраивание интерактивных карт на веб-страницу

**Пример использования:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap"></script>
</head>
<body>
    <div id="map" style="height: 400px;"></div>
    <script>
        function initMap() {
            const map = new google.maps.Map(document.getElementById("map"), {
                center: { lat: 55.7558, lng: 37.6173 },
                zoom: 10
            });
            
            // Добавление маркера
            const marker = new google.maps.Marker({
                position: { lat: 55.7031, lng: 37.5307 },
                map: map,
                title: "МГУ"
            });
        }
    </script>
</body>
</html>
```

**Особенности:**
- Работает только в браузере (JavaScript)
- Требует загрузки на клиентской стороне
- Не подходит для серверных запросов Django

## 2. Google Places API (REST) - для получения данных

**URL:** `https://maps.googleapis.com/maps/api/place/textsearch/json`

**Назначение:** Получение данных о местах через HTTP-запросы (серверная сторона)

**Пример использования (наш код):**
```python
import requests

def get_google_place_rating(place_name, address, city=None, api_key=None):
    # Шаг 1: Поиск места
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    query = f"{place_name} {city} {address}"
    params = {
        'query': query,
        'key': api_key,
        'language': 'ru'
    }
    
    response = requests.get(search_url, params=params)
    data = response.json()
    
    if data.get('status') != 'OK':
        return None
    
    place = data['results'][0]
    place_id = place['place_id']
    
    # Шаг 2: Получение деталей (рейтинг)
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        'place_id': place_id,
        'key': api_key,
        'language': 'ru',
        'fields': 'rating,user_ratings_total,place_id,name'
    }
    
    details_response = requests.get(details_url, params=details_params)
    details_data = details_response.json()
    
    result = details_data.get('result', {})
    return {
        'rating': result.get('rating'),
        'reviews_count': result.get('user_ratings_total', 0),
        'place_id': place_id
    }
```

**Особенности:**
- Работает на сервере (Python/Django)
- HTTP GET/POST запросы
- Возвращает JSON данные
- Идеально для нашего случая

## 3. Сравнение

| Характеристика | JavaScript API | Places API (REST) |
|----------------|----------------|-------------------|
| **Где работает** | Браузер (клиент) | Сервер (Django) |
| **Тип запросов** | JavaScript функции | HTTP GET/POST |
| **Использование** | Отображение карт | Получение данных |
| **Наш случай** | ❌ Не подходит | ✅ Используем |

## 4. Почему мы используем REST API

1. **Серверная обработка:** Django работает на сервере, не в браузере
2. **Безопасность:** API ключ хранится на сервере, не виден пользователям
3. **Кэширование:** Можем сохранять данные в базе
4. **Автоматизация:** Команды управления обновляют рейтинги автоматически

## 5. Пример полного запроса REST API

### Text Search Request:
```http
GET https://maps.googleapis.com/maps/api/place/textsearch/json?query=МГУ+Москва&key=YOUR_API_KEY&language=ru
```

### Text Search Response:
```json
{
  "results": [
    {
      "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "name": "Московский государственный университет",
      "rating": 4.5,
      "user_ratings_total": 1234
    }
  ],
  "status": "OK"
}
```

### Place Details Request:
```http
GET https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4&key=YOUR_API_KEY&fields=rating,user_ratings_total
```

### Place Details Response:
```json
{
  "result": {
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "rating": 4.5,
    "user_ratings_total": 1234
  },
  "status": "OK"
}
```

## 6. Важно!

**JavaScript API ключ ≠ Places API ключ**

Оба используют один и тот же API ключ из Google Cloud Console, но:
- JavaScript API требует настройки ограничений по HTTP referrer
- Places API (REST) требует настройки ограничений по IP или без ограничений для серверных запросов

**Для нашего проекта:**
- Используем **Places API (REST)** ✅
- Ключ настраиваем без ограничений или с ограничением по IP сервера
- НЕ используем JavaScript API для получения данных

