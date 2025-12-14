# ImageForge

Локальная платформа для генерации изображений на базе FLUX Dev.
Качество уровня Grok/Aurora с безлимитной генерацией на своём железе.

## Возможности

- 🎨 FLUX Dev — максимальное качество генерации
- 🖥️ Распределённая генерация на нескольких устройствах
- 🔗 REST API для интеграции с Video Factory
- 🌐 Веб-интерфейс в стиле Grok
- 📊 Очередь задач с приоритетами
- 🖼️ Галерея и история генераций

## Архитектура

```
┌─────────────────┐     ┌─────────────────┐
│   Web UI        │     │  Video Factory  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │ API
         ┌───────────▼───────────┐
         │     Master Server     │
         │   (очередь, API)      │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
   │ Worker  │  │ Worker  │  │ Worker  │
   │ 3060 Ti │  │ MacBook │  │  ...    │
   └─────────┘  └─────────┘  └─────────┘
```

## Требования

### Master Server (любое устройство)
- Python 3.10+
- 4GB RAM

### Worker (устройство с GPU)
- NVIDIA GPU 8GB+ VRAM или Apple Silicon
- Python 3.10+
- 16GB+ RAM

## Установка

```bash
cd image_forge
pip install -r requirements.txt
```

## Запуск

### Master Server
```bash
python -m image_forge.master
```

### Worker
```bash
python -m image_forge.worker --master http://master-ip:8000
```

## API

```
POST /api/generate
{
  "prompt": "описание изображения",
  "width": 1024,
  "height": 1024,
  "steps": 28,
  "guidance": 3.5
}
```

## Интеграция с Video Factory

В настройках Video Factory указать:
```
IMAGE_FORGE_URL=http://master-ip:8000
```
