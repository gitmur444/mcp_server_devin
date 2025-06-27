# Интеграция DonutBuffer MCP с OpenAI GPTs через Custom Actions

## 🎯 Обзор

Этот гайд показывает, как подключить ваш OpenAI GPT к DonutBuffer MCP серверу через Custom Actions.

## 📋 Архитектура

```
OpenAI GPT ↔ Custom Actions (REST API) ↔ HTTP Wrapper ↔ MCP Server ↔ DonutBuffer C++
```

## 🚀 Шаг 1: Запуск HTTP Wrapper

### Локальная разработка:
```bash
# Установить зависимости
pip install -r wrapper_requirements.txt

# Запустить wrapper
python mcp_http_wrapper.py

# Сервер доступен на http://localhost:8000
# Документация: http://localhost:8000/docs
```

### Проверка работы:
```bash
# Тест анализа README
curl http://localhost:8000/analyze-readme

# Тест создания конфигурации
curl -X POST http://localhost:8000/configure-buffer \
  -H "Content-Type: application/json" \
  -d '{"requirements": "high performance setup"}'
```

## 🌐 Шаг 2: Деплой на облако

### Heroku:
```bash
# Создать Procfile
echo "web: uvicorn mcp_http_wrapper:app --host 0.0.0.0 --port \$PORT" > Procfile

# Деплой
git add .
git commit -m "Add MCP HTTP wrapper"
git push heroku main
```

### Railway:
```bash
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn mcp_http_wrapper:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Vercel (serverless):
```python
# vercel_app.py
from mcp_http_wrapper import app
handler = app
```

## 🤖 Шаг 3: Создание OpenAI GPT

### A) Создать новый GPT:
1. Перейти в https://chat.openai.com/gpts/editor
2. Нажать "Create a GPT"
3. Заполнить основную информацию:
   - **Name**: DonutBuffer Assistant
   - **Description**: AI assistant for C++ ring buffer analysis and optimization
   - **Instructions**: 
   ```
   You are an expert assistant for DonutBuffer - a C++ ring buffer visualization and testing tool.
   
   Your capabilities:
   - Analyze DonutBuffer documentation and features
   - Generate optimal buffer configurations based on user requirements
   - Run buffer performance tests
   - Interpret results and provide optimization recommendations
   
   Always use the available actions to interact with DonutBuffer. When a user asks about buffer performance, first analyze the documentation, then configure an appropriate buffer, run tests, and interpret the results.
   
   Be technical but accessible in your explanations. Focus on practical performance insights.
   ```

### B) Настроить Custom Actions:

1. Перейти в раздел "Configure" → "Actions"
2. Нажать "Create new action"
3. Вставить OpenAPI схему из файла `openapi_schema.yaml`
4. Обновить URL сервера на ваш деплоенный адрес:
   ```yaml
   servers:
     - url: https://your-app.herokuapp.com
       description: Production server
   ```

### C) Настроить аутентификацию (если нужно):
- **None** - для публичного API
- **API Key** - если добавите аутентификацию в wrapper
- **OAuth** - для продвинутой интеграции

## 📝 Шаг 4: Тестирование GPT

### Примеры запросов к GPT:

**1. Анализ возможностей:**
```
"Что умеет DonutBuffer? Какие типы буферов поддерживает?"
```

**2. Создание конфигурации:**
```
"Настрой высокопроизводительный буфер для обработки видео потока 4K"
```

**3. Запуск тестов:**
```
"Запусти тест производительности с lockfree буфером и 4 производителями"
```

**4. Комплексный анализ:**
```
"Мне нужен буфер для real-time аудио обработки с минимальной задержкой. 
Проанализируй возможности, создай конфигурацию, запусти тест и дай рекомендации."
```

## 🔧 Шаг 5: Расширенная настройка

### Добавление аутентификации:
```python
# В mcp_http_wrapper.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

# Добавить к эндпоинтам:
@app.get("/analyze-readme", dependencies=[Depends(verify_token)])
```

### Логирование и мониторинг:
```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "request_processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    return response
```

### Кэширование результатов:
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
async def cached_analyze_readme():
    return await call_mcp_tool("analyze_readme")
```

## 🎉 Результат

Ваш OpenAI GPT теперь может:

✅ **Анализировать DonutBuffer документацию**
- Извлекать информацию о типах буферов
- Понимать параметры конфигурации
- Объяснять возможности системы

✅ **Создавать оптимальные конфигурации**
- Интерпретировать требования пользователя
- Генерировать подходящие параметры
- Объяснять выбор конфигурации

✅ **Запускать тесты производительности**
- Выполнять DonutBuffer с заданными параметрами
- Обрабатывать ошибки сборки и выполнения
- Возвращать результаты тестирования

✅ **Интерпретировать результаты**
- Анализировать метрики throughput и latency
- Давать рекомендации по оптимизации
- Сравнивать с ожидаемой производительностью

## 🔍 Пример диалога с GPT:

**Пользователь:** "Мне нужен буфер для high-frequency trading системы"

**GPT:** 
1. Анализирует DonutBuffer возможности
2. Создает конфигурацию: lockfree buffer, 8 producers, 4 consumers, 64MB buffer
3. Запускает тест производительности
4. Интерпретирует результаты: "Получен throughput 2.1 GB/s с latency 0.3ms - отлично для HFT. Рекомендую увеличить buffer_size до 128MB для стабильности."

## 🛠️ Troubleshooting

### Проблема: GPT не видит actions
- Проверьте OpenAPI схему на валидность
- Убедитесь что URL сервера доступен
- Проверьте CORS настройки

### Проблема: Timeout ошибки
- Увеличьте timeout в FastAPI
- Оптимизируйте MCP server вызовы
- Добавьте асинхронную обработку

### Проблема: MCP server недоступен
- Проверьте путь к mcp_server_devin_pkg
- Убедитесь что зависимости установлены
- Проверьте логи wrapper'а

## 📚 Дополнительные ресурсы

- [OpenAI GPT Actions Documentation](https://platform.openai.com/docs/actions)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
