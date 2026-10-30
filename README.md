# Конфигурационное управление — вариант 16

Практические работы на Python. В `main` лежат готовые версии:

| Папка | Работа |
| --- | --- |
| [PR_1](PR_1) | Эмулятор оболочки с виртуальной файловой системой |
| [PR_2](PR_2) | Анализатор зависимостей Python-пакетов, D2 и ASCII |

В каждой папке свой README, исходники, тесты и скрипт запуска.

## Запуск

Python 3.10+. Для ПР №1 также нужен tkinter.
Каждый пример запускайте из корня репозитория.

ПР №1:

```sh
cd PR_1
python3 -B scripts/generate_vfs.py data
./run.sh --vfs data/nested.zip
```

ПР №2:

```sh
cd PR_2
./run.sh --package requests --version 2.32.3 --ascii-tree
```

Тесты запускаются из папки нужной практики:

```sh
python3 -B -m unittest discover -s tests -v
```

## Сохранённые этапы

Каждый этап сохранён тегом с прежним именем ветки.
Ссылки открывают те же версии, которые были представлены на защите.

| Этап | ПР №1 | ПР №2 |
| --- | --- | --- |
| 1 | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/stage-1) | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/pr2-stage-1) |
| 2 | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/stage-2) | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/pr2-stage-2) |
| 3 | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/stage-3) | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/pr2-stage-3) |
| 4 | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/stage-4) | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/pr2-stage-4) |
| 5 | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/stage-5) | [Открыть](https://github.com/segeitsi/konf-upr-variant16/tree/pr2-stage-5) |
