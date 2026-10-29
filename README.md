# ПР 2 — граф зависимостей, вариант 16

Python 3.10+, только стандартная библиотека. Сборка и установка не нужны.

## Этап 1

```sh
./run.sh --stage 1 --package requests --version 2.32.3
./run.sh --stage 1 --test --repository examples/diamond.json --package A --version 1.0
```

Параметры: `--package` — имя, `--version` — версия,
`--repository` — URL репозитория (по умолчанию `https://pypi.org`)
или путь к тестовому JSON, `--test` — тестовый режим,
`--ascii-tree` — ASCII-дерево, `--stage` — этап (1–5).
На этапе 1 параметры выводятся как `ключ=значение`.
Неверные параметры завершают программу с сообщением об ошибке.

Точка входа: `python3 -B src/__main__.py` с теми же параметрами.
Тесты: `python3 -B -m unittest discover -s tests -v`.

## Этап 2

```sh
./run.sh --stage 2 --package requests --version 2.32.3
```

Данные читаются из PyPI JSON API `/pypi/имя/версия/json`,
поле `requires_dist`. Версия корневого пакета не заменяется на последнюю.
Условия среды проверяются для текущего Python и ОС. Неактивные extras
пропускаются. Ошибки HTTP, JSON и несовместимого Python выводятся явно.
`pip`, `packaging` и другие готовые средства в программе не используются.

## Этап 3

```sh
./run.sh --stage 3 --test --repository examples/diamond.json --package A --version 1.0
./run.sh --stage 3 --test --repository examples/cycle.json --package A --version 1.0
./run.sh --stage 3 --package requests --version 2.32.3
```

Граф строится BFS через очередь, без рекурсии. Циклические рёбра сохраняются,
повторный обход узлов не зацикливает программу. Недостижимые пакеты исключены.
Тестовый JSON: объект `{"A": ["B"], "B": []}`; имена — заглавные A–Z.
Все упомянутые узлы должны быть объявлены. `--version` задаёт общую
версию узлов тестового графа. Примеры: цепочка, ромб, цикл и одиночный узел.

Для зависимостей выбирается последняя стабильная версия, удовлетворяющая
ограничению и текущему Python. Общий пакет представлен одним узлом.
При несовместимости уже выбранной версии программа сообщает конфликт.
Полного перебора вариантов, как у решателя pip, нет: допустимый набор
иногда потребует ручного выбора другой версии корневого пакета.
Прямые URL зависимостей и динамические метаданные отклоняются явно.

## Этап 4

```sh
./run.sh --stage 4 --test --repository examples/diamond.json --package A --version 1.0
./run.sh --stage 4 --package requests --version 2.32.3
```

Алгоритм Кана выдаёт зависимости раньше пакетов, которым они нужны.
Общие зависимости выводятся один раз. При цикле линейного порядка нет:
программа сообщает ошибку, а не печатает выдуманный порядок.
Порядок независимых пакетов может отличаться от pip.

## Этап 5

```sh
./run.sh --package requests --version 2.32.3 --ascii-tree
./run.sh --package flask --version 3.0.3
./run.sh --package rich --version 13.9.4 > graph.d2
./scripts/demo.sh
```

По умолчанию включён этап 5. D2 выводится в терминал, `--ascii-tree`
добавляет дерево. `[cycle]` отмечает цикл, `[already shown]` — общий узел.
D2-текст можно открыть в D2 Playground или обработать внешним `d2`.
Рендерер не требуется для запуска этой работы.

В `examples/` сохранены D2, ASCII и результаты сравнения для трёх пакетов.
Версии и рёбра совпали с `pip inspect`, порядок установки соблюдает те же
зависимости. Pip не выводит D2/ASCII-граф штатной командой; сравнивались
его метаданные, план и фактическая последовательность установки.
Различия порядка независимых пакетов описаны в `*-comparison.md`.
Подробное повторение проверки: [сравнение](examples/COMPARISON.md).

## Основные функции

| Модуль | Функции |
| --- | --- |
| `config.py`, `cli.py` | `parse_config`, проверка параметров, выбор этапа |
| `repository.py` | `metadata`, `dependencies`, `resolve`: PyPI и выбор версии |
| `requirements.py`, `markers.py`, `versions.py` | Разбор условий и версий |
| `test_repository.py` | Чтение и проверка тестового графа |
| `graph.py` | `build_graph`: BFS; `describe_graph`: список рёбер |
| `order.py` | `dependency_order`: зависимости перед потребителями |
| `render.py` | `to_d2`, `to_ascii`: представления графа |

Основа форматов: [PyPI JSON API](https://docs.pypi.org/api/json/),
[PEP 508](https://packaging.python.org/en/latest/specifications/dependency-specifiers/),
[D2](https://d2lang.com/tour/connections).
