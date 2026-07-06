# Состояние проекта на 26.06.2026 и план дальнейших действий

> Документ-памятка. Написан в конце рабочей сессии, чтобы утром быстро
> войти в контекст и продолжить с того же места.

---

## 1. Что сделано сегодня

### 1.1. Лендинг «Нейроучитель» опубликован

| Артефакт | Где | Статус |
|---|---|---|
| Репозиторий | https://github.com/tonalion07-ui/neuro-teacher-site | ✅ Public, 1 коммит `cf78268` |
| GitHub Pages | https://tonalion07-ui.github.io/neuro-teacher-site/ | ✅ работает |
| Главная | `/index.html` | ✅ «Нейроучитель — методички…» |
| Политика | `/privacy.html` | ✅ для модерации VK |
| OAuth-callback | `/oauth-callback.html` | ✅ обработчик `?code=…` от VK ID |

### 1.2. Файлы, которые лежат в репо

```
.gitignore       ← исключает .env, .env.local, .vercel
auth.js          ← PKCE + кнопка «Войти через VK ID» (clientId = [TODO])
index.html       ← главная, бренд «Нейроучитель», email vtab3@yandex.ru
oauth-callback.html
privacy.html
script.js        ← копия из content-agent-site (без правок)
styles.css       ← копия из content-agent-site (без правок)
vercel.json      ← конфиг для будущего Functions
```

### 1.3. Скрипты для автопостинга (локально, не в репо)

| Скрипт | Что делает | Статус |
|---|---|---|
| `vk_poster.py` | публикация текста в ВК через `VK_ACCESS_TOKEN` | ✅ работает (service token) |
| `tg_poster.py` | публикация текста+картинки в Telegram-канал `@neuro_uchitel` | ⚠️ 403 — бот не админ канала |

### 1.4. Telegram-бот — что не работает и почему

| Проверка | Результат |
|---|---|
| Токен бота валиден | ✅ `NeuroUchitelBot` (`neuro_uchitel_content_bot`) |
| Канал существует | ✅ id `-1004318421364`, `@neuro_uchitel` |
| Бот добавлен в админы канала | ❌ **нет** → `403 Forbidden` на `sendPhoto` |

**Завтра**: добавить `@neuro_uchitel_content_bot` в админы канала
`@neuro_uchitel` (Настройки канала → Администраторы → Добавить администратора)
с правом «Публикация сообщений». После этого `tg_poster.py` заработает.

### 1.5. Анализ PDF-учебников по вайб-кодингу

Прочитаны `docs/Modul2_Less_4_5_6_7_Modul3_Less_8_9.pdf` (93 стр.)
и `docs/Modul4_Less_10_11_12.pdf` (61 стр.). Текстовые расшифровки сохранены
рядом с PDF (`.txt`, можно удалить если не нужны).

**Найдено устаревшее** в `Modul2`, урок 4.2 (стр. 88–90):

| Утверждение в учебнике | Реальность |
|---|---|
| «Управление → Работа с API → Создать ключ» | ❌ даёт `vk1.a.`, отклоняется после 21.03.2022 |
| `oauth.vk.com/authorize?response_type=token&v=5.199` | ❌ Implicit Flow deprecated, endpoint `oauth.vk.com` заменён на `id.vk.ru` |
| `scope=wall,groups,photos,offline` через стандартный OAuth | ❌ выдаются только через «Подключение сообществ» |
| «Для фото нужен отдельный токен» | ⚠️ устарело, сейчас — единый community token |

**Что подтвердилось** (актуально):

- GitHub Pages — бесплатный хостинг для HTML/CSS/JS
- Vercel — managed для фронтенда и Next.js
- `.env` — никогда не коммитить, держать в секрете
- Telegram-бот должен быть админом канала для публикации

---

## 2. Текущее состояние VK ID Cabinet

| Приложение | ID | client_secret | Статус |
|---|---|---|---|
| NeuroUchitel AutoPost | `54654398` (из `.env`) | `v7MBfspwKJ6i8wSN80ws` | не опубликовано, модерация отклонена |
| NeuroUchitel AutoPost1 | `54654398` (?) | — | не опубликовано, «Подключение сообществ» отклонено |
| NeuroUchitel AutoPost1-2 | — | — | не опубликовано, «Подключение сообществ» отклонено |

**Вывод**: оба приложения бесполезны для автопубликации с картинкой, потому
что **Standalone нельзя использовать без публикации в каталоге VK** + отдельно
нужно «Подключение сообществ» (2 ступени модерации, 4–10 дней).

Скриншоты отказов лежат в `docs/2026-06-26_*.png`.

---

## 3. Что готово к публикации прямо сейчас

| Материал | Где | Что нужно |
|---|---|---|
| Пост 26.06 ВК | `posts/2026-06-26_mozgovoy-shturm.md` | опубликовать вручную в группе `vk.com/club239683607` |
| Пост 26.06 ТГ | `posts/2026-06-26_mozgovoy-shturm-tg.md` | опубликовать вручную в `@neuro_uchitel` (или через `tg_poster.py` после добавления бота) |
| Картинка 26.06 | `assets/2026-06/2026-06-26_mozgovoy-shturm/2026-06-26_mozgovoy-shturm.png` (1.4 МБ) | прикрепить к обоим постам |

---

## 4. План на завтра (27.06) и далее

### 4.1. Прямо сейчас утром (10 минут)

| # | Действие | Где | Зачем |
|---|---|---|---|
| 1 | Опубликовать пост 26.06 в ВК (текст + картинка, вручную) | https://vk.com/club239683607 | не отставать от контент-плана |
| 2 | Добавить `@neuro_uchitel_content_bot` в админы `@neuro_uchitel` | Telegram → Настройки канала | чтобы `tg_poster.py` заработал |
| 3 | Протестировать `python tg_poster.py posts/2026-06-26_mozgovoy-shturm-tg.md assets/2026-06/2026-06-26_mozgovoy-shturm/2026-06-26_mozgovoy-shturm.png` | локально | убедиться, что публикация работает |

### 4.2. Standalone в VK ID Cabinet (30 минут, в любой день)

| # | Действие | Где | Зачем |
|---|---|---|---|
| 1 | Создать новое Standalone-приложение (или переиспользовать `54654398`) | https://id.vk.ru → Standalone | нужен `client_id` для OAuth |
| 2 | Базовый домен = `tonalion07-ui.github.io` | VK ID Cabinet | требование модерации |
| 3 | Доверенный Redirect URL = `https://tonalion07-ui.github.io/neuro-teacher-site/oauth-callback.html` | VK ID Cabinet | куда VK ID вернёт `?code=…` |
| 4 | Скопировать `client_id` и `client_secret` | VK ID Cabinet | для auth.js и Vercel env |
| 5 | Заменить `[TODO-VK-CLIENT-ID]` в `site/auth.js` на реальный `client_id` | локально → push | кнопка заработает |
| 6 | Подать Standalone на публикацию в каталоге VK | VK ID Cabinet | 3–7 дней модерации |
| 7 | После одобрения → подать «Подключение сообществ» | VK ID Cabinet | 1–3 дня модерации |
| 8 | Добавить приложение в группу `239683607` | Управление → Работа с API | получить community token |

### 4.3. Vercel Functions (20 минут, после п. 4.2.4)

| # | Действие | Где | Зачем |
|---|---|---|---|
| 1 | Зарегистрироваться на vercel.com через GitHub | vercel.com | бесплатный tier |
| 2 | Импортировать репо `neuro-teacher-site` | vercel.com | автодеплой при push |
| 3 | Добавить env: `VK_CLIENT_ID` и `VK_CLIENT_SECRET` | Vercel Project Settings | секреты для обмена `code → token` |
| 4 | Создать `site/api/vk-token.js` (черновик уже есть в памяти агента) | локально → push | серверная функция обмена |
| 5 | Проверить: открыть `https://neuro-teacher-site.vercel.app/api/vk-token` (должен вернуть ошибку без параметров) | браузер | sanity-check |

### 4.4. После одобрения модерации (1–2 недели)

| # | Действие | Что это даст |
|---|---|---|
| 1 | Получить community token из ВК | для `vk_poster.py` с правами на стену + фото |
| 2 | Вписать `VK_COMMUNITY_TOKEN=…` в `.env` | автоматическая публикация с картинкой |
| 3 | Тест: `python vk_poster.py posts/2026-06-XX_…md assets/…/…png` | проверка полного цикла |

### 4.5. Регулярные задачи (каждую неделю)

| # | Задача | Ответственный |
|---|---|---|
| 1 | Готовить 2–3 поста в `posts/` по контент-плану | ты |
| 2 | Публиковать вручную в ВК + Telegram (пока нет автопубликации) | ты |
| 3 | Когда модерация пройдёт — переключить на `vk_poster.py` + `tg_poster.py` | мы вместе |

---

## 5. Секреты, которые нужно отозвать / перезаписать

| Секрет | Где | Что сделать |
|---|---|---|
| `github_pat_11CAOOCAQ0…` | история чата + `.git/config` (был) | **отозвать** на https://github.com/settings/tokens → Delete, создать новый |
| `vk1.a.YPdtK_…` (старый) | `.env` | проверить, что он не используется, можно удалить |
| `client_secret=v7MBfspwKJ6i8wSN80ws` | `.env` (NeuroUchitel AutoPost) | **не используется** — Standalone не опубликован |
| `ID_приложения=54654398` | `.env` | переиспользовать, когда создашь Standalone с этим ID |

**Рекомендация**: настроить `git config credential.helper store` — тогда PAT
не придётся вводить каждый раз.

---

## 6. Чек-лист на утро

```
[ ] Открыть этот файл
[ ] Вспомнить: лендинг работает на https://tonalion07-ui.github.io/neuro-teacher-site/
[ ] Шаг 1: опубликовать пост 26.06 вручную в ВК
[ ] Шаг 2: добавить @neuro_uchitel_content_bot в админы @neuro_uchitel
[ ] Шаг 3: протестировать tg_poster.py
[ ] Шаг 4 (если есть время): создать Standalone в VK ID Cabinet
[ ] Шаг 5 (если есть время): зарегистрироваться на vercel.com
[ ] Отозвать старый GitHub PAT
```

---

## 7. Полезные ссылки

| Что | URL |
|---|---|
| Лендинг | https://tonalion07-ui.github.io/neuro-teacher-site/ |
| Репо на GitHub | https://github.com/tonalion07-ui/neuro-teacher-site |
| Группа ВК | https://vk.com/club239683607 |
| Telegram-канал | https://t.me/neuro_uchitel |
| VK ID Cabinet | https://id.vk.ru/ |
| Vercel | https://vercel.com/ |
| GitHub Pages | https://github.com/tonalion07-ui/neuro-teacher-site/settings/pages |
| GitHub PAT | https://github.com/settings/tokens |

---

## 8. Что лежит в проекте сейчас (дерево)

```
D:\LearnVibeCOD\vibe-workspace\neuro-teacher-project\
├── .env                                ← токены, НЕ в git
├── .git/                               ← репо нейроучитель-контента
├── tg_poster.py                        ← Telegram-публикатор
├── vk_poster.py                        ← ВК-публикатор
├── posts\
│   ├── 2026-06-26_mozgovoy-shturm.md
│   ├── 2026-06-26_mozgovoy-shturm-tg.md
│   └── (будущие посты)
├── assets\
│   ├── 2026-06\
│   │   ├── 2026-06-26_mozgovoy-shturm\2026-06-26_mozgovoy-shturm.png
│   │   └── 2026-06-29_biologia\
│   ├── 2026-07\
│   └── templates\
├── scripts\
│   └── extract_pdf_text.py             ← утилита для чтения PDF
├── site\                               ← лендинг, ОТДЕЛЬНЫЙ git-репо
│   ├── .git\
│   ├── .gitignore
│   ├── auth.js
│   ├── index.html
│   ├── oauth-callback.html
│   ├── privacy.html
│   ├── script.js
│   ├── styles.css
│   └── vercel.json
└── docs\
    ├── Modul2_Less_4_5_6_7_Modul3_Less_8_9.pdf
    ├── Modul2_Less_4_5_6_7_Modul3_Less_8_9.txt     ← извлечённый текст
    ├── Modul4_Less_10_11_12.pdf
    ├── Modul4_Less_10_11_12.txt                    ← извлечённый текст
    ├── gaidVK1.pdf
    ├── vk-auth-methods.pdf
    ├── vk-auth-methods1.pdf
    ├── 2026-06-26_*.png                             ← скриншоты VK ID Cabinet
    ├── 2026-06-26_22-08-00GitHub_screen.png        ← подтверждение публикации
    └── 2026-06-26-current-state-and-next-steps.md  ← ЭТОТ ФАЙЛ
```

---

## 9. Концепции на заметку (для роста)

| Концепция | Где встретилась сегодня | Зачем |
|---|---|---|
| **OAuth 2.1 + PKCE** | VK ID авторизация | современный стандарт, защита от перехвата `code` |
| **Implicit Flow (deprecated)** | `Modul2.pdf`, стр. 90 | устарел, в VK ID больше не работает |
| **Service token (vk1.a.)** | `.env`, `vk-auth-methods1.pdf` | не выдаётся новым приложениям с 21.03.2022 |
| **client_secret** | `auth.js` (не хранится), `/api/vk-token.js` (хранится на сервере) | «мастер-пароль» приложения, никогда в JS |
| **Vercel Functions** | `vercel.json`, `/api/vk-token.js` | бессерверные функции для хранения секретов |
| **GitHub Pages** | репо `neuro-teacher-site` | бесплатный статический хостинг с HTTPS |
| **Standalone vs Mini App** | `docs/gaidVK1.pdf` | Standalone — полноценный сервис с модерацией |
| **«Подключение сообществ»** | `docs/vk-auth-methods1.pdf` | обязательный шаг для прав на стену и фото |

---

*Документ создан 26.06.2026 в конце рабочей сессии. Утром 27.06 — открыть и начать с чек-листа в разделе 6.*
