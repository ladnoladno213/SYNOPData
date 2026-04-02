# Инструкция по настройке SYNOPData репозитория

## Шаг 1: Инициализация Git

```bash
cd synop-data-repo

# Инициализируем Git
git init

# Добавляем remote
git remote add origin https://github.com/ladnoladno213/SYNOPData.git

# Добавляем все файлы
git add .

# Первый коммит
git commit -m "Initial setup: automated SYNOP data updates"

# Пушим в GitHub
git branch -M main
git push -u origin main
```

## Шаг 2: Проверка

После пуша проверьте:

1. **Файлы загружены**: https://github.com/ladnoladno213/SYNOPData
2. **Actions включены**: Settings → Actions → Allow all actions
3. **Workflows видны**: Actions tab

## Шаг 3: Тестовый запуск

Запустите workflow вручную:

1. Перейдите в Actions
2. Выберите "Update Frequent Stations"
3. Нажмите "Run workflow"
4. Дождитесь завершения (5-10 минут)

## Шаг 4: Проверка данных

Проверьте что CSV доступны:

```bash
curl https://raw.githubusercontent.com/ladnoladno213/SYNOPData/main/data/28367.csv
```

## Готово!

Теперь данные будут обновляться автоматически:
- Каждые 3 часа: избранные станции
- Раз в день в 02:00 UTC: остальные станции

## Добавление станций в частое обновление

Отредактируйте `scripts/update-frequent.py`:

```python
FREQUENT_STATIONS = [
    '28367',  # Тюмень
    '28573',  # Ишим
    '27612',  # Москва (пример)
    # Добавьте другие
]
```

Закоммитьте изменения:

```bash
git add scripts/update-frequent.py
git commit -m "Add more frequent stations"
git push
```
