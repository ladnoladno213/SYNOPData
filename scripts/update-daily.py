#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление остальных станций (раз в день)
"""

import sys
import importlib.util
from pathlib import Path

# Загружаем модули
spec = importlib.util.spec_from_file_location(
    "downloader",
    Path(__file__).parent / "rp5-downloader.py"
)
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)

from update_frequent import FREQUENT_STATIONS

def main():
    print("=" * 70)
    print("ЕЖЕДНЕВНОЕ ОБНОВЛЕНИЕ")
    print("=" * 70)
    
    # Загружаем все станции
    all_stations = downloader.load_wmo_stations()
    
    # Исключаем частые станции
    daily_stations = {
        gid: wid for gid, wid in all_stations.items()
        if wid not in FREQUENT_STATIONS
    }
    
    print(f"Всего станций: {len(all_stations)}")
    print(f"Частых станций (пропускаем): {len(FREQUENT_STATIONS)}")
    print(f"К обновлению: {len(daily_stations)}")
    
    # Ограничение для GitHub Actions
    MAX_STATIONS = 50
    
    if len(daily_stations) > MAX_STATIONS:
        print(f"\nОграничение: обновляем только {MAX_STATIONS} станций")
        daily_stations = dict(list(daily_stations.items())[:MAX_STATIONS])
    
    success = 0
    failed = 0
    
    for idx, (geoname_id, wmo_id) in enumerate(daily_stations.items(), 1):
        print(f"\n[{idx}/{len(daily_stations)}] [{wmo_id}] Обновление...")
        
        # Удаляем старый файл
        csv_file = downloader.OUTPUT_DIR / f'{wmo_id}.csv'
        if csv_file.exists():
            csv_file.unlink()
        
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
