#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление избранных станций (каждые 3 часа)
"""

import sys
import importlib.util
from pathlib import Path

# Загружаем основной модуль
spec = importlib.util.spec_from_file_location(
    "downloader",
    Path(__file__).parent / "rp5-downloader.py"
)
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)

# СПИСОК СТАНЦИЙ ДЛЯ ЧАСТОГО ОБНОВЛЕНИЯ
# Добавьте сюда WMO ID станций которые нужно обновлять каждые 3 часа
FREQUENT_STATIONS = [
    '28367',  # Тюмень
    '28573',  # Ишим
    # Добавьте другие станции по необходимости
]

def main():
    print("=" * 70)
    print("ЧАСТОЕ ОБНОВЛЕНИЕ (каждые 3 часа)")
    print("=" * 70)
    print(f"Станций к обновлению: {len(FREQUENT_STATIONS)}")
    
    success = 0
    failed = 0
    
    for wmo_id in FREQUENT_STATIONS:
        print(f"\n[{wmo_id}] Обновление...")
        
        # Удаляем старый файл
        csv_file = downloader.OUTPUT_DIR / f'{wmo_id}.csv'
        if csv_file.exists():
            csv_file.unlink()
            print(f"[{wmo_id}] Удален старый файл")
        
        # Скачиваем свежие данные
        if downloader.download_station(wmo_id):
            success += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    print(f"Успешно: {success}")
    print(f"Ошибок: {failed}")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
