# SYNOP Weather Data

Автоматически обновляемые архивы погоды с метеостанций SYNOP (RP5).

## 📊 Данные

- **Формат**: CSV (UTF-8, разделитель `;`)
- **Период**: с 01.04.2016 по текущую дату
- **Обновление**: 
  - Избранные станции: каждые 3 часа
  - Остальные станции: раз в день в 02:00 UTC

## 🚀 Использование

### Прямые ссылки на CSV файлы

```
https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/{WMO_ID}.csv
```

**Примеры:**
- Тюмень (28367): `https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/28367.csv`
- Ишим (28573): `https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/28573.csv`

### JavaScript

```javascript
const wmoId = '28367';
const url = `https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/${wmoId}.csv`;

fetch(url)
  .then(res => res.text())
  .then(csv => console.log(csv));
```

### Python

```python
import requests

wmo_id = '28367'
url = f'https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/{wmo_id}.csv'

response = requests.get(url)
csv_data = response.text
```

## 📁 Структура данных

Каждый CSV файл содержит:

| Столбец | Описание |
|---------|----------|
| Местное время | Дата и время наблюдения |
| T | Температура воздуха (°C) |
| Po | Давление на уровне станции (мм рт.ст.) |
| Pa | Давление приведенное (мм рт.ст.) |
| U | Относительная влажность (%) |
| DD | Направление ветра |
| Ff | Скорость ветра (м/с) |
| ff10 | Порыв ветра за 10 мин (м/с) |
| ff3 | Порыв ветра между сроками (м/с) |
| N | Общая облачность (%) |
| WW | Текущая погода |
| W1, W2 | Прошедшая погода |
| Tn, Tx | Мин/макс температура (°C) |
| VV | Видимость (км) |
| Td | Точка росы (°C) |
| RRR | Осадки (мм) |
| tR | Период осадков (ч) |
| sss | Высота снега (см) |

## 🤖 Автоматическое обновление

Данные обновляются автоматически через GitHub Actions:

- **Частые станции** (каждые 3 часа): см. `scripts/update-frequent.py`
- **Остальные станции** (раз в день): автоматически определяются

## 📋 Список станций

См. директорию `data/` для полного списка доступных станций.

## 📜 Лицензия

Данные предоставлены [RP5.ru](https://rp5.ru)

## 🔗 Связанные проекты

- [WeatherWebsite](https://github.com/ladnoladno213/WeatherWebsite) - сайт погоды использующий эти данные
