# Crosspenis

Минимальный сервис с командой `!help`.

## Структура

```
Crosspenis/
├── app.py
├── requirements.txt
├── .env.example
├── run.ps1
├── run.bat
├── start.bat
├── deploy/
└── README.md
```

## Запуск

```bash
cp .env.example .env
# заполни TOKEN

pip install -r requirements.txt
python app.py
```

Windows: `.\run.ps1 start` или `start.bat`.

## Команды

| Команда | Описание |
|---------|----------|
| `!help` | Справка |

## Конфиг

| Переменная | Описание |
|------------|----------|
| `TOKEN` | Ключ доступа (обязателен) |

## Linux

`deploy/crosspenis.service` — unit для systemd.
