# Espresso Physics Dial-In — AI Agent Skill

Навык для работы с параметрами эспрессо **по проверенным материалам книги** Jonathan Gagné, *The Physics of Espresso* (Scott Rao Coffee Books, 2025), ISBN 9798350747737.

> **Уровень достоверности:** на 28.10.2026 прочитаны два разрешенных к публикации фрагмента — **с. 85–89 и 163–174 (17 страниц)**. **Вся книга пока не прочитана.**

## Первичный источник

- Книга у издателя: https://www.scottrao.com/products/poe
- Официально опубликованный PDF — глава 9 «Beverage Types and Recipes»: https://decentespresso.com/img/f/gagne_chapter_vevs.pdf
- Подтверждение разрешения издателя: https://decentespresso.com/blog/gagne_espresso_book_excerpt_beverage_types_and_recipes
- Второй проверенный PDF — shower screens / headspace (с. 85–89): https://fast.decentespresso.com/f/0/gagne_espresso_shower_screens.pdf
- Подтверждение разрешения автора: https://decentespresso.com/blog/free_book_extract_from_the_physics_of_espresso_shower_screens_and_headspace

## Содержимое репозитория

- [SKILL.md](SKILL.md) — правила работы агента: не выдумывать источники и EY, различать эксперимент и вывод книги.
- [references/profiles-and-recipes.md](references/profiles-and-recipes.md) — проверенный пересказ главы 9: Traditional, Preinfused, Flow-Controlled, Blooming, Rao Allongé, Turbo, Adaptive, Extractamundo!, Filter Brewing, Nomacano.
- [references/puck-physics-and-prep.md](references/puck-physics-and-prep.md) — подтвержденные эксперименты по headspace и puck resistance (с. 85–89) и предсмачиванию (с. 165–169).
- [references/water-and-burr-geometry.md](references/water-and-burr-geometry.md) — точные границы подтвержденного по воде и жерновам; без выдуманных рецептов минерализации.
- [references/source-audit.md](references/source-audit.md) — таблица достоверности, страниц и исправленных ошибок.
- [scripts/shot_analyzer.py](scripts/shot_analyzer.py) — **самостоятельный** CLI-калькулятор для наблюдаемых метрик шота; не является программой из книги.

## Использование Skill

Для среды с поддержкой \`SKILL.md\` установите репозиторий как папку навыка согласно требованиям вашей IDE/агента. Наличие этого файла само по себе не гарантирует автоматического обнаружения во всех перечисленных приложениях.

Агент должен:
1. Сначала сверить физические утверждения с [source-audit.md](references/source-audit.md).
2. Учитывать возможности машины: настоящий blooming требует остановки подачи **без сброса давления**.
3. Считать Ratio и среднюю гравиметрическую скорость по измерениям, а **EY — только при известной TDS**.
4. Предлагать по одной экспериментальной правке, не выдавая ее за цитату из книги.

## Запуск калькулятора

\`\`\`bash
python3 scripts/shot_analyzer.py \
  --dose 18 --yield_g 36 --time 29 \
  --preinfusion 6 --pressure 9 --temp 93 --taste "sour+dry"

# С измеренной TDS:
python3 scripts/shot_analyzer.py \
  --dose 18 --yield_g 36 --time 29 --tds 10.5 --json
\`\`\`

**Важно:** давление, температура и средние скорости не дают достаточных данных для достоверного диагноза каналов или степени экстракции. Истинный профиль давления/потока изменяется в течение шота; число в CLI служит сравнительным ориентиром, а не прямым измерением проницаемости.

## Научная добросовестность и авторские права

Это **неофициальный** вспомогательный проект, не утвержденный автором и издателем. Материалы написаны заново, без воспроизведения текста книги целыми главами, защищенных иллюстраций и графиков. Чтобы завершить строго книжную версию по остальным темам, нужны соответствующие страницы оригинала: полный PDF или фото отдельных разделов.
