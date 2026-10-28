# Espresso Physics Dial-In (AI Agent Skill)

Инженерно-физический навык (Skill) для ИИ-агентов (Gemini, Claude Code, Google Antigravity IDE, Cursor) по книге астрофизика **Джонатана Ганье (Jonathan Gagné) — «The Physics of Espresso»**.

## Структура репозитория
- `SKILL.md` — ядро навыка: уравнение фильтрации Дарси, защита от пороупругого сжатия («Вулкан Ганье»), стандарты Puck Prep и пошаговая матрица доводки (Dial-In Matrix).
- `references/profiles-and-recipes.md` — точные карты профилей (Classic Lever, Turbo Shot, Blooming Espresso, Extractamundo Dos!, Allongé) и адаптация под машины с фиксированной помпой 9 бар.
- `references/puck-physics-and-prep.md` — гидродинамика таблетки, статистика по методам распределения (WDT vs Blind Shaker vs Levelers), физика корзин и бумажных фильтров.
- `references/water-and-burr-geometry.md` — химия воды (рецепты KH/GH в ppm без накипи), бимодальное и унимодальное распределение частиц, заморозка зерна и дегазация CO2.
- `scripts/shot_analyzer.py` — CLI-калькулятор для расчета Brew Ratio, EY%, динамической вязкости воды по Фогелю и индекса сопротивления Дарси.

## Быстрый запуск анализатора шота
    python3 scripts/shot_analyzer.py --dose 18.0 --yield_g 36.0 --time 29 --preinfusion 6 --pressure 9 --temp 93 --taste "sour+dry"
