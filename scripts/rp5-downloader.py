#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Массовая загрузка архивов погоды с RP5 для всех станций из wmo-mapping.js
Использует Selenium для автоматизации браузера с параллельной загрузкой
"""

import os
import re
import time
import gzip
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Директория для сохранения CSV файлов
OUTPUT_DIR = Path(__file__).parent / 'data' / 'rp5-csv'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Период данных
START_DATE = '01.04.2016'  # С какой даты скачивать
END_DATE = datetime.now().strftime('%d.%m.%Y')  # До сегодняшнего дня

# Количество параллельных браузеров
NUM_WORKERS = 5  # Можно увеличить до 10 для еще большей скорости

# Lock для безопасного логирования из разных потоков
log_lock = Lock()

def load_wmo_stations():
    """Загружает список WMO станций из wmo-mapping.js"""
    wmo_file = Path(__file__).parent / 'data' / 'wmo-mapping.js'
    
    if not wmo_file.exists():
        logging.error(f"Файл {wmo_file} не найден")
        return {}
    
    with open(wmo_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем все пары geonameId: 'wmoId'
    pattern = r'(\d+):\s*["\'](\d+)["\']'
    matches = re.findall(pattern, content)
    
    stations = {}
    for geoname_id, wmo_id in matches:
        if wmo_id != '0':  # Пропускаем станции без данных
            stations[geoname_id] = wmo_id
    
    logging.info(f"Загружено {len(stations)} станций из wmo-mapping.js")
    return stations

def is_already_downloaded(wmo_id):
    """Проверяет, скачан ли уже файл для станции"""
    csv_file = OUTPUT_DIR / f'{wmo_id}.csv'
    return csv_file.exists()

def safe_log(level, message):
    """Потокобезопасное логирование"""
    with log_lock:
        if level == 'info':
            logging.info(message)
        elif level == 'error':
            logging.error(message)

def create_driver():
    """Создает новый экземпляр WebDriver"""
    chrome_options = Options()
    
    # Headless режим для сервера
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def download_station_archive(wmo_id, start_date, end_date):
    """
    Скачивает архив погоды для одной станции
    
    Args:
        wmo_id: ID метеостанции WMO
        start_date: Начальная дата (формат: DD.MM.YYYY)
        end_date: Конечная дата (формат: DD.MM.YYYY)
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    driver = None
    try:
        driver = create_driver()
        url = f'https://rp5.ru/archive.php?wmo_id={wmo_id}&lang=ru'
        safe_log('info', f"[{wmo_id}] Открываем страницу: {url}")
        driver.get(url)
        
        # Ждём загрузки страницы
        time.sleep(5)
        
        # Переключаемся на вкладку "Скачать архив погоды"
        safe_log('info', f"[{wmo_id}] Переключаемся на вкладку 'Скачать архив'")
        download_tab = driver.find_element(By.ID, 'tabSynopDLoad')
        download_tab.click()
        time.sleep(3)
        
        # Заполняем даты
        safe_log('info', f"[{wmo_id}] Заполняем даты: {start_date} - {end_date}")
        driver.execute_script(f"""
            document.getElementById('calender_dload').value = '{start_date}';
            document.getElementById('calender_dload2').value = '{end_date}';
        """)
        time.sleep(1)
        
        # Выбираем формат CSV
        safe_log('info', f"[{wmo_id}] Выбираем формат CSV")
        driver.execute_script("""
            var csvRadio = document.querySelector('input[name="format"][value="f_csv"]');
            if (csvRadio) csvRadio.click();
        """)
        time.sleep(3)
        
        # Выбираем кодировку UTF-8
        safe_log('info', f"[{wmo_id}] Выбираем кодировку UTF-8")
        driver.execute_script("""
            var utf8Radio = document.getElementById('coding2');
            if (utf8Radio) utf8Radio.click();
        """)
        time.sleep(2)
        
        # Нажимаем кнопку "Выбрать в файл GZ"
        safe_log('info', f"[{wmo_id}] Нажимаем 'Выбрать в файл GZ'")
        driver.execute_script("""
            var buttons = document.querySelectorAll('.archButton');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent || '';
                if (text.includes('Выбрать') && text.includes('файл')) {
                    buttons[i].click();
                    break;
                }
            }
        """)
        time.sleep(10)  # Увеличено с 7 до 10 секунд
        
        # Кликаем по ссылке "Скачать"
        safe_log('info', f"[{wmo_id}] Кликаем по ссылке 'Скачать'")
        download_link = driver.execute_script("""
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var text = links[i].textContent || '';
                if (text.includes('Скачать')) {
                    return links[i].href;
                }
            }
            return null;
        """)
        
        if not download_link:
            safe_log('error', f"[{wmo_id}] ❌ Ссылка 'Скачать' не найдена")
            return False
        
        # Ждём генерации файла (для больших архивов может потребоваться больше времени)
        safe_log('info', f"[{wmo_id}] Ожидание генерации файла (10 сек)...")
        time.sleep(10)
        
        # Скачиваем файл через requests с cookies из браузера
        safe_log('info', f"[{wmo_id}] Скачивание файла...")
        cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Добавляем заголовки для имитации браузера
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Пробуем скачать с retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = session.get(download_link, timeout=180, stream=True)
                
                if response.status_code == 200:
                    # Скачиваем по частям
                    gz_data = b''
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            gz_data += chunk
                    
                    gz_size = len(gz_data)
                    safe_log('info', f"[{wmo_id}] Скачано: {gz_size} байт (сжато)")
                    
                    # Распаковываем GZ
                    csv_data = gzip.decompress(gz_data)
                    csv_size = len(csv_data)
                    
                    # Сохраняем CSV
                    output_file = OUTPUT_DIR / f'{wmo_id}.csv'
                    with open(output_file, 'wb') as f:
                        f.write(csv_data)
                    
                    safe_log('info', f"[{wmo_id}] ✅ Успешно: {gz_size} байт → {csv_size} байт → {output_file.name}")
                    return True
                else:
                    safe_log('error', f"[{wmo_id}] ❌ HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        safe_log('info', f"[{wmo_id}] Повтор через 5 сек...")
                        time.sleep(5)
                    continue
                    
            except Exception as e:
                safe_log('error', f"[{wmo_id}] ❌ Попытка {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    safe_log('info', f"[{wmo_id}] Повтор через 5 сек...")
                    time.sleep(5)
                else:
                    return False
        
        return False
            
    except Exception as e:
        safe_log('error', f"[{wmo_id}] ❌ Ошибка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def main():
    """Основная функция"""
    logging.info("=" * 70)
    logging.info("МАССОВАЯ ЗАГРУЗКА АРХИВОВ ПОГОДЫ С RP5")
    logging.info("=" * 70)
    
    # Загружаем список станций
    stations = load_wmo_stations()
    
    if not stations:
        logging.error("Нет станций для загрузки")
        return
    
    # Фильтруем уже скачанные
    to_download = {gid: wid for gid, wid in stations.items() if not is_already_downloaded(wid)}
    already_downloaded = len(stations) - len(to_download)
    
    logging.info(f"Всего станций: {len(stations)}")
    logging.info(f"Уже скачано: {already_downloaded}")
    logging.info(f"К загрузке: {len(to_download)}")
    
    if not to_download:
        logging.info("Все архивы уже скачаны!")
        return
    
    # Параллельная загрузка
    logging.info(f"Запуск {NUM_WORKERS} параллельных браузеров...")
    
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Создаем задачи для всех станций
        futures = {
            executor.submit(download_station_archive, wmo_id, START_DATE, END_DATE): (geoname_id, wmo_id)
            for geoname_id, wmo_id in to_download.items()
        }
        
        # Обрабатываем результаты по мере завершения
        for idx, future in enumerate(as_completed(futures), 1):
            geoname_id, wmo_id = futures[future]
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                safe_log('error', f"[{wmo_id}] ❌ Исключение: {e}")
                fail_count += 1
            
            # Прогресс
            if idx % 10 == 0:
                logging.info(f"Прогресс: {idx}/{len(to_download)} ({success_count} успешно, {fail_count} ошибок)")
    
    logging.info("\n" + "=" * 70)
    logging.info("ИТОГИ ЗАГРУЗКИ")
    logging.info("=" * 70)
    logging.info(f"Успешно: {success_count}")
    logging.info(f"Ошибок: {fail_count}")
    logging.info(f"Всего обработано: {success_count + fail_count}")

if __name__ == '__main__':
    main()
