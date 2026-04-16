# SignAI — Распознавание языка жестов

Приложение состоит из двух частей:
- **backend/** — Python сервер (FastAPI + MediaPipe + твоя модель)
- **frontend/** — PWA веб-сайт (открывается в браузере телефона)

---

## Структура

```
sign-language-app/
├── backend/
│   ├── main.py              ← FastAPI сервер
│   ├── requirements.txt
│   └── models/
│       ├── model.p          ← СКОПИРУЙ СЮДА
│       └── data.pickle      ← СКОПИРУЙ СЮДА
└── frontend/
    ├── index.html           ← PWA сайт
    └── manifest.json
```

---

## Шаг 1 — Скопируй модели

```bash
cp "Code for Nabi/models/model.p"      sign-language-app/backend/models/
cp "Code for Nabi/models/data.pickle"  sign-language-app/backend/models/
```

---

## Шаг 2 — Запусти бэкенд

```bash
cd sign-language-app/backend

# Создай виртуальное окружение
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Установи зависимости
pip install -r requirements.txt

# Запусти сервер
python main.py
```

Сервер будет работать на: `http://localhost:8000`

---

## Шаг 3 — Запусти фронтенд

```bash
cd sign-language-app/frontend

# Нужен любой HTTP сервер. Например:
python3 -m http.server 3000
# или
npx serve .
```

Открой в браузере: `http://localhost:3000`

---

## Шаг 4 — Открыть на телефоне

Телефон и компьютер должны быть в одной Wi-Fi сети.

1. Узнай IP компьютера:
   - Mac: `ipconfig getifaddr en0`
   - Linux: `hostname -I`
   - Windows: `ipconfig` → IPv4

2. Открой на телефоне: `http://192.168.X.X:3000`

3. При подключении введи адрес сервера: `ws://192.168.X.X:8000`

4. **Добавить на рабочий стол** (iPhone: кнопка "Поделиться" → "На экран Домой")

---

## Деплой в интернет (опционально)

### Бэкенд — Railway.app (бесплатно)
```bash
# Установи Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### Фронтенд — Netlify (бесплатно)
Просто перетащи папку `frontend/` на netlify.com/drop

---

## Что умеет приложение

- 📷 Захват камеры в реальном времени
- 🤖 Распознавание 31 жеста через WebSocket
- 🔊 Озвучивание жестов (Web Speech API)
- 📜 История распознанных жестов
- 📱 PWA — добавляется на рабочий стол как приложение
- 🌐 Работает на Android и iPhone

---

## Распознаваемые жесты

Yes, No, OK, Stop, I, You, We, Friend, Hello, Goodbye, Love,
Help, Thank you, Please, Want, Can, Sorry, Cannot, Eat,
Work, Study, Watch, Listen, Speak, Understand,
Question, Answer, Good, Bad,
How are you, What are you doing, See you
