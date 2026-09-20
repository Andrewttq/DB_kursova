# Роадмап курсовой + видеокурс

Команда из трёх человек, ~8 недель до готовой системы и отчёта, ещё неделя на подготовку к защите.
После каждого этапа система рабочая: если время закончится, можно остановиться на том, что есть.

Ссылки на видео ведут на поиск YouTube — нужное видео первое или среди первых.
**[RU]** — на русском, остальные на английском (Настройки → Субтитры → Перевести).

**Зоны ответственности** (распределите между собой):

| Зона | Сервис | Технологии |
|---|---|---|
| A | ingest-service + UI | CSV, RabbitMQ (publisher), HTMX, Locust |
| B | writer-service | RabbitMQ (consumer), MongoDB + шардинг, Neo4j |
| C | query-service | Elasticsearch, Redis-кэш, REST API, тесты поиска |

Правило: каждый делает свою зону, но **ревьюит PR остальных**. На защите вопросы задают каждому по всем темам.

---

## Этап 0. Репозиторий и каркас — ✅ сделано

- [x] Каркас трёх сервисов на GitHub (задание 4)
- [x] Раздел отчёта «Архитектура» (задание 3)
- [ ] Репозиторий публичный (или Student Pack), напарники добавлены, правила для `main` включены
- [ ] Задания 3 и 4 сданы в Classroom
- [ ] Проект перенесён из OneDrive, у всех выполнено `uv sync --all-packages` и `uv run pre-commit install`

**Видео (все трое):**
1. Git с нуля **[RU]** — https://www.youtube.com/results?search_query=Гоша+Дударь+git+для+начинающих
2. Ветки и Pull Request **[RU]** — https://www.youtube.com/results?search_query=git+ветки+pull+request+командная+работа
3. uv — менеджер пакетов Python — https://www.youtube.com/results?search_query=uv+python+package+manager+tutorial
4. ruff и pre-commit — https://www.youtube.com/results?search_query=ruff+pre-commit+python+tutorial

---

## Этап 1. Окружение и основы — неделя 1 · все вместе

**Сделать:**
- [ ] Установить Docker Desktop (Windows: с WSL2)
- [ ] `docker-compose.yml` с MongoDB и Redis (одна нода, без шардинга)
- [ ] Эндпоинт `/health` в query-service, который проверяет связь с Mongo и Redis

**Готово, когда:** `docker compose up -d` поднимает базы, `/health` отвечает `ok`.

**Видео (все трое):**
5. REST API простыми словами **[RU]** — https://www.youtube.com/results?search_query=REST+API+простыми+словами
6. ООП и абстрактные классы **[RU]** — https://www.youtube.com/results?search_query=selfedu+ООП+python+абстрактные+классы
7. Type hints **[RU]** — https://www.youtube.com/results?search_query=Диджитализируй+type+hints+python
8. Docker за 100 секунд — https://www.youtube.com/results?search_query=Fireship+Docker+in+100+seconds
9. Docker для начинающих — https://www.youtube.com/results?search_query=TechWorld+with+Nana+Docker+Tutorial+for+Beginners
10. Docker Compose — https://www.youtube.com/results?search_query=TechWorld+with+Nana+Ultimate+Docker+Compose+Tutorial

---

## Этап 2. Первый вертикальный срез — неделя 2 · все вместе

**Сделать:**
- [ ] `MongoRecipeReadRepository.find_by_id` и `get_recipe_card` через фасад — первая реальная цепочка controller → facade → service → port → adapter
- [ ] Временный скрипт, который кладёт 10 рецептов в Mongo
- [ ] Первый pytest-тест фасада с фейковым репозиторием (без БД)
- [ ] В CI добавить шаг `uv run pytest`

**Готово, когда:** `GET /api/recipes/{id}` возвращает карточку, тест зелёный в Actions.

**Спросят:** зачем порт, если можно сразу вызвать Mongo; что такое DI.

**Видео (все трое):**
11. asyncio **[RU]** — https://www.youtube.com/results?search_query=Олег+Молчанов+asyncio
12. Курс FastAPI **[RU]** — https://www.youtube.com/results?search_query=Артём+Шумейко+FastAPI+курс
13. Гексагональная архитектура — https://www.youtube.com/results?search_query=ArjanCodes+hexagonal+architecture
14. CQRS — https://www.youtube.com/results?search_query=CodeOpinion+CQRS+explained
15. SQL vs NoSQL — https://www.youtube.com/results?search_query=Fireship+SQL+vs+NoSQL
16. Как работают индексы — https://www.youtube.com/results?search_query=Hussein+Nasser+database+indexing+explained

---

## Этапы 3–5. Параллельная работа по зонам — недели 3–5

### Зона A: ingest-service + UI

**Сделать:**
- [ ] Скачать Food.com `RAW_recipes.csv` в `data/`, `CsvRecipeSource` (разбор списков через `ast.literal_eval`)
- [ ] `RateLimiter`, `IngestScheduler`, `IngestService.run_tick`
- [ ] RabbitMQ в compose, `RabbitRecipePublisher`
- [ ] Redis: `RedisIngestConfigRepository`, `RedisIngestStatsRepository`
- [ ] UI: слайдер 10–5000, кнопка Старт/Стоп, блок статистики с `hx-trigger="every 1s"`

**Готово, когда:** двигаешь слайдер — счётчик «прочитано» растёт с этой скоростью, очередь в RabbitMQ наполняется.

**Видео:**
17. RabbitMQ за 100 секунд — https://www.youtube.com/results?search_query=Fireship+RabbitMQ+in+100+seconds
18. RabbitMQ Crash Course — https://www.youtube.com/results?search_query=Hussein+Nasser+RabbitMQ+crash+course
19. aio-pika — https://www.youtube.com/results?search_query=aio-pika+rabbitmq+python+asyncio
20. HTMX за 100 секунд — https://www.youtube.com/results?search_query=Fireship+htmx+in+100+seconds
21. HTMX + FastAPI — https://www.youtube.com/results?search_query=htmx+fastapi+jinja+tutorial

### Зона B: writer-service + MongoDB

**Сделать:**
- [ ] `RabbitRecipeConsumer`: пачки, `prefetch_count`, ack только после записи
- [ ] `mappers`, `RecipeCommandFacade.save_batch`
- [ ] `MongoRecipeRepository.upsert_many` (bulk, `ordered=False`), `MongoChefRepository`
- [ ] `RedisWriteStatsRepository` (счётчик по секундам для write RPS)

**Готово, когда:** при запущенном ingest счётчик «сохранено» растёт, очередь не копится на малых скоростях.

**Спросят:** что будет, если writer упадёт посреди пачки; почему запись идемпотентна.

**Видео:**
22. MongoDB за 100 секунд — https://www.youtube.com/results?search_query=Fireship+MongoDB+in+100+seconds
23. MongoDB Crash Course — https://www.youtube.com/results?search_query=Web+Dev+Simplified+MongoDB+crash+course
24. PyMongo Async — https://www.youtube.com/results?search_query=pymongo+async+AsyncMongoClient+tutorial
25. Bulk write в Mongo — https://www.youtube.com/results?search_query=mongodb+bulk+write+performance

### Зона C: query-service + Elasticsearch + Redis

**Сделать:**
- [ ] Elasticsearch в compose, `ElasticRecipeIndexRepository` в writer-service (mapping + bulk) — вместе с зоной B
- [ ] `ElasticRecipeSearchRepository`: bool-запрос, фильтры, highlight
- [ ] `QueryNormalizer`, `RedisSearchCache`, `SearchFacade`
- [ ] `RedisSearchLogRepository`, блок «Последние запросы» на UI
- [ ] Страница результатов поиска (HTMX), `/api/search` в JSON

**Готово, когда:** «Chicken Garlic Pasta» и «pasta, garlic chicken» дают попадание в кэш, ответ быстрее 100 мс.

**Спросят:** как работает инвертированный индекс; почему не `LIKE`; что такое cache-aside и TTL.

**Видео:**
26. Инвертированный индекс — https://www.youtube.com/results?search_query=inverted+index+explained+full+text+search
27. Elasticsearch с нуля — https://www.youtube.com/results?search_query=Elasticsearch+tutorial+for+beginners
28. Elasticsearch из Python — https://www.youtube.com/results?search_query=elasticsearch+python+tutorial+bulk+search
29. Redis за 100 секунд — https://www.youtube.com/results?search_query=Fireship+Redis+in+100+seconds
30. Redis Crash Course — https://www.youtube.com/results?search_query=Traversy+Media+Redis+crash+course
31. Стратегии кэширования — https://www.youtube.com/results?search_query=ByteByteGo+caching+strategies

**Видео для всех (чтобы понимать чужие зоны на ревью):**
32. Микросервисы простыми словами — https://www.youtube.com/results?search_query=TechWorld+with+Nana+microservices+explained

---

## Этап 6. Шардинг MongoDB — неделя 6 · зона B, остальные помогают

**Сделать:**
- [ ] В compose: config server, 3 шарда, `mongos`; скрипт инициализации
- [ ] `sh.shardCollection("recipes.recipes", { _id: "hashed" })`
- [ ] Индекс `{ cuisine: 1, cook_time_min: 1 }`
- [ ] Скриншот `db.recipes.getShardDistribution()` для отчёта

**Готово, когда:** данные распределены примерно по трети на шард, код сервисов не менялся (только адрес подключения на `mongos`).

**Спросят:** почему hashed, а не `cuisine`; targeted vs scatter-gather; зачем config server.

**Видео:**
33. Шардинг как концепция — https://www.youtube.com/results?search_query=Hussein+Nasser+database+sharding
34. Шардированный Mongo в Docker — https://www.youtube.com/results?search_query=MongoDB+sharded+cluster+docker+compose
35. План запроса `explain()` — https://www.youtube.com/results?search_query=MongoDB+explain+query+plan

---

## Этап 7. Neo4j — неделя 7 · зона B + C

**Сделать:**
- [ ] Neo4j в compose, constraints на `Recipe.id`, `Chef.id`, `Ingredient.name`
- [ ] `Neo4jRecipeGraphRepository.merge_many` через `UNWIND` (writer)
- [ ] Рекомендации и «другие рецепты шефа» (query), блоки на UI

**Готово, когда:** у рецепта есть «похожие», у шефа — список рецептов.

**Спросят:** почему граф, а не JOIN в SQL; что делает `MERGE`.

**Видео:**
36. Neo4j и Cypher — https://www.youtube.com/results?search_query=Neo4j+Cypher+crash+course+beginners

---

## Этап 8. Качество и измерения — неделя 8 · все

**Сделать:**
- [ ] Тест записи через шард-ключ (зона B)
- [ ] Позитивный и негативный тест поиска (зона C)
- [ ] Логи INFO / DEBUG / ERROR, скриншоты для отчёта (все)
- [ ] Locust: нагрузка от 10 RPS, графики RPS и latency (зона A)
- [ ] Замер пропускной способности каждого слоя, диаграмма-воронка
- [ ] Отчёт по всем 9 разделам методички (каждый пишет раздел про свою зону)

**Видео:**
37. pytest **[RU]** — https://www.youtube.com/results?search_query=pytest+для+начинающих
38. Логирование — https://www.youtube.com/results?search_query=Corey+Schafer+python+logging
39. Locust — https://www.youtube.com/results?search_query=Locust+load+testing+python+tutorial

---

## Этап 9. Подготовка к защите — неделя 9 · все

- [ ] Прогон демо: слайдер вверх → очередь и счётчики растут → слайдер вниз → система успокаивается
- [ ] Внутренний прогон: каждый объясняет **чужую** зону
- [ ] Теория ниже — каждый должен уметь ответить на всё
- [ ] Бонус, если есть время: replica sets для Mongo (+10)

**Видео (обязательно всем):**
40. CAP-теорема — https://www.youtube.com/results?search_query=ByteByteGo+CAP+theorem
41. Репликация — https://www.youtube.com/results?search_query=Hussein+Nasser+database+replication
42. Replica set в Mongo — https://www.youtube.com/results?search_query=MongoDB+replica+set+election+explained
43. Eventual consistency — https://www.youtube.com/results?search_query=ByteByteGo+eventual+consistency

**Вопросы, которые точно зададут:**
- Почему именно такой набор БД и за что отвечает каждая
- CAP: куда попадают Mongo, Elasticsearch, Neo4j, Redis и почему
- Как устроен шардинг, почему выбран такой ключ
- Что такое репликация, почему минимум 3 ноды, синхронная и асинхронная
- Где в системе eventual consistency и почему это допустимо
- Где узкое место системы и как его расширить
- Как читать план запроса
