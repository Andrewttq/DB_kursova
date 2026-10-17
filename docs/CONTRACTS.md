# Контракти між сервісами
## Індекс Elasticsearch

Назва індексу: `recipes` (змінна `ES_INDEX` у `.env`).
Id документа = id рецепта, тому повторна індексація перезаписує документ.

| Поле | Тип | Для чого |
|---|---|---|
| title | text (english) | повнотекстовий пошук |
| description | text (english) | повнотекстовий пошук |
| steps | text (english) | повнотекстовий пошук |
| ingredients | text (english) | повнотекстовий пошук |
| cuisine | keyword | фільтр |
| tags | keyword | фільтр |
| cook_time_min | integer | фільтр за діапазоном |
| calories | float | фільтр за діапазоном |


## Ключі Redis

| Ключ | Тип | Хто пише | Хто читає | TTL |
|---|---|---|---|---|
| `ingest:config` | hash (поля `rate`, `running`) | query-service | ingest-service | немає |
| `stats:read` | string (лічильник, INCRBY) | ingest-service | query-service | немає |
| `stats:published` | string (лічильник, INCRBY) | ingest-service | query-service | немає |
| `stats:saved:<роль>` | string (лічильник) | writer-service | query-service | немає |
| `stats:failed:<роль>` | string (лічильник) | writer-service | query-service | немає |
| `stats:saved:mongo:<unix-секунда>` | string (лічильник за секунду) | writer-service | query-service | короткий |
| `search:<sha1>` | string (JSON зі списком результатів) | query-service | query-service | 300 с |
| `search:log` | list (LPUSH + LTRIM до 100) | query-service | query-service | немає |

`<роль>` — одна з `mongo`, `es`, `neo4j` (змінна `WRITER_ROLE`).
`<sha1>` — хеш від рядка «слова|фільтри|сторінка|розмір».