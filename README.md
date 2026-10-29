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
