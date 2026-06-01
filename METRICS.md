# Метрики Prometheus и дашборд Grafana

## Эндпоинт /metrics

Эндпоинт `/metrics` доступен по адресу `http://localhost:8000/metrics` и возвращает метрики в формате Prometheus.

### Доступные метрики

#### HTTP метрики
- `http_requests_total` (Counter) - общее количество HTTP-запросов с labels: method, endpoint, status
- `http_request_duration_seconds` (Histogram) - время обработки HTTP-запросов с labels: method, endpoint

#### Events Provider метрики
- `events_provider_requests_total` (Counter) - количество запросов к Events Provider API с labels: endpoint, status
- `events_provider_request_duration_seconds` (Histogram) - время ответа Events Provider API с labels: endpoint

#### Бизнес-метрики
- `events_total` (Gauge) - текущее количество событий в БД
- `tickets_created_total` (Gauge) - общее количество созданных билетов в БД
- `tickets_cancelled_total` (Gauge) - количество отменённых билетов в БД

#### Кэш метрики
- `cache_hits_total` (Counter) - количество попаданий в кэш
- `cache_misses_total` (Counter) - количество промахов кэша

## Импорт дашборда в Grafana

### Шаг 1: Авторизация в Grafana

1. Перейдите на страницу Grafana
2. Используйте ссылку со страницы профиля (раздел связанных аккаунтов) для авторизации

### Шаг 2: Проверка Datasource

1. Перейдите в Configuration → Data Sources
2. Убедитесь, что Prometheus datasource уже настроен
3. Если нет, создайте новый Prometheus datasource с URL вашего Prometheus сервера

### Шаг 3: Импорт дашборда

1. Перейдите в Dashboards → Import
2. Нажмите "Upload JSON file"
3. Выберите файл `grafana-dashboard.json`
4. Выберите Prometheus datasource
5. Нажмите "Import"

### Шаг 4: Проверка дашборда

После импорта дашборд будет содержать следующие панели:

1. **Requests per minute (RPM)** - количество HTTP-запросов в минуту по подам
2. **Latency p95** - 95-й процентиль времени ответа
3. **Error rate (%)** - процент ошибок 5xx
4. **Билеты** - график созданных и отменённых билетов
5. **События** - текущее количество событий (stat panel)
6. **Events Provider RPM** - количество запросов к внешнему API в минуту
7. **Events Provider latency p95** - время ответа внешнего API
8. **Cache hit rate (%)** - процент попаданий в кэш

## Примечания

### Агрегация метрик

Все панели с rate/increase используют агрегацию `sum by (pod)` для группировки метрик по подам. Это необходимо, так как Prometheus собирает метрики с каждого пода отдельно.

Для Gauge-метрик из БД (events_total, tickets_created_total, tickets_cancelled_total) используется `max()`, так как значения одинаковы на всех подах.

### Масштаб времени

Все панели со скоростью событий (RPM) умножают результат `rate()` на 60 для отображения в запросах в минуту вместо запросов в секунду.

### Обновление метрик

Prometheus опрашивает эндпоинт `/metrics` каждые 15-30 секунд (зависит от конфигурации). Бизнес-метрики из БД обновляются при каждом запросе к `/metrics`.

## Проверка работы метрик

Для проверки работы метрик выполните несколько запросов к API:

```bash
# Проверить эндпоинт метрик
curl http://localhost:8000/metrics

# Сделать запрос к API
curl http://localhost:8000/api/events

# Проверить, что метрики обновились
curl http://localhost:8000/metrics | grep http_requests_total
```

## Troubleshooting

### Метрики не появляются в Grafana

1. Проверьте, что Prometheus успешно собирает метрики с вашего сервиса
2. Убедитесь, что в Prometheus targets ваш сервис отображается как UP
3. Проверьте, что datasource в Grafana настроен правильно

### Пустые графики

1. Убедитесь, что есть трафик к API (метрики собираются только при наличии запросов)
2. Проверьте временной диапазон на дашборде
3. Убедитесь, что label `pod` присутствует в метриках Prometheus
