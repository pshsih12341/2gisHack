#!/usr/bin/env python3
"""
Скрипт для запуска Map Assistant без базы данных.

Использование:
python run_dev.py
"""

import uvicorn
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

if __name__ == "__main__":
    # Проверяем наличие обязательных переменных
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Ошибка: GROQ_API_KEY не установлен")
        print("Установите переменную окружения или добавьте в .env файл")
        exit(1)
    
    if not os.getenv("DGIS_API_KEY"):
        print("❌ Ошибка: DGIS_API_KEY не установлен")
        print("Установите переменную окружения или добавьте в .env файл")
        exit(1)
    
    print("🚀 Запуск Map Assistant...")
    print("📝 API документация: http://localhost:8000/docs")
    print("🗺️ Map API: http://localhost:8000/api/map/plan-route")
    print("🏥 Health check: http://localhost:8000/api/map/health")
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
