# flask==3.0.3

Проверено 2026-10-29, Python 3.14.3, pip 26.0.

Узлов: 7. Версии и рёбра совпали с планом pip и метаданными `pip inspect`.

Наш порядок: blinker → click → itsdangerous → markupsafe → werkzeug → jinja2 → flask.

Порядок установки pip: markupsafe → itsdangerous → click → blinker → werkzeug → jinja2 → flask.

В обоих порядках зависимости идут раньше зависящих от них пакетов. Порядок независимых узлов может различаться.
