# Сравнение с pip

Проверено 29.10.2026, Python 3.14.3, pip 26.0.

| Пакет | Узлов | Версии и рёбра | Порядок зависимостей |
| --- | --- | --- | --- |
| requests 2.32.3 | 5 | Совпали | Соблюдён |
| flask 3.0.3 | 7 | Совпали | Соблюдён |
| rich 13.9.4 | 4 | Совпали | Соблюдён |

Подробности: [requests](requests-comparison.md),
[flask](flask-comparison.md), [rich](rich-comparison.md).
Алгоритм Кана начинает с листьев в алфавитном порядке. Pip использует
свой обход, поэтому порядок независимых узлов может различаться.
Зависимости в обоих случаях предшествуют своим потребителям.
При цикле наш инструмент сообщает невозможность линейного порядка.

Повторение для requests в отдельной папке, без изменения системного Python:

```sh
mkdir -p output/reference
./run.sh --package requests --version 2.32.3
python3 -m pip install --target output/reference/packages \
  --ignore-installed --only-binary=:all: --no-compile \
  --report output/reference/report.json requests==2.32.3
python3 -m pip inspect --path output/reference/packages
```

В выводе pip строка `Installing collected packages` показывает порядок
установки. `pip inspect` содержит версии и `requires_dist` каждого пакета.
Для остальных примеров используйте отдельные папки и их версии.
Приложение pip не запускает и не импортирует; он нужен только для сравнения.
Новые релизы, версия Python и ОС могут изменить результаты.
