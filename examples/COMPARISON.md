# Сравнение с pip

Проверено 29.10.2026 на macOS, Python 3.14.3, pip 26.0.

| Корневой пакет | Узлов | Версии и рёбра | Порядок зависимостей |
| --- | --- | --- | --- |
| requests 2.32.3 | 5 | Совпали | Соблюдён |
| flask 3.0.3 | 7 | Совпали | Соблюдён |
| rich 13.9.4 | 4 | Совпали | Соблюдён |

Результаты: [requests](requests-comparison.md),
[flask](flask-comparison.md), [rich](rich-comparison.md).
В D2 стрелка идёт от пакета к его зависимости. В дереве повторное
использование пакета не создаёт новую установленную копию.

Pip не имеет встроенного D2-рендерера или команды ASCII-дерева.
Для сравнения использованы штатные `pip inspect`, отчёт установки
и строка `Installing collected packages` из фактической установки.
Метаданные и версии проверены; равенство картинок не заявляется.

Наш алгоритм начинает с листьев в алфавитном порядке, pip использует
собственный обход. Поэтому порядок независимых пакетов различается.
Зависимости во всех трёх примерах идут раньше потребителей.
Для циклического тестового графа наш инструмент отклоняет линейный
порядок; pip может разорвать цикл при установке. D2 сохраняет цикл.

Это снимки: новые релизы на PyPI и другая ОС/Python могут изменить граф.
Повторить для одного примера, выполняя из папки проекта:

```sh
mkdir -p output/reference
python3 -m pip install --target output/reference/packages \
  --ignore-installed --only-binary=:all: --no-compile \
  --report output/reference/report.json requests==2.32.3 \
  > output/reference/install.log 2>&1
python3 -m pip inspect --path output/reference/packages \
  > output/reference/inspect.json
python3 -B scripts/compare_pip.py --package requests --version 2.32.3 \
  --report output/reference/report.json \
  --inspect output/reference/inspect.json \
  --log output/reference/install.log --output output/comparison
```

Для других пакетов используйте отдельные папки и соответствующие версии.
Pip применяется только при независимом сравнении; приложение его
не запускает и не импортирует. Установка для сравнения идёт в отдельную
папку, а не в системное окружение.

[Документация порядка установки pip](https://pip.pypa.io/en/stable/cli/pip_install/#installation-order)
