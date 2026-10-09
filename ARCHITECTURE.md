# EduOsh — Architecture

## Репозитории
- Web frontend: https://github.com/Amange1di/frontend (Next.js App Router, React, TypeScript, Redux Toolkit, i18n).
- Backend: https://github.com/Amange1di/backend1 (Django, Django REST Framework, ORM).
- Mobile: https://github.com/Amange1di/edoush_mobile (Flutter/Dart).

## Границы
Browser/Flutter -> API -> DRF permissions/business services -> ORM -> database. Frontend отвечает за отображение и UX, backend — за авторизацию, бизнес-инварианты и изоляцию данных.

## Данные
Company -> Branch -> Courses/Groups/Students/Teachers/Schedules/Payments (точные связи подтвердить по моделям). Все branch-scoped запросы должны фильтроваться на backend, включая detail, update, delete, exports и статистику. Запрещено полагаться только на фильтр UI.

## Авторизация
Сверять фактический механизм token/session с кодом. 401/403 обрабатывать раздельно; не сохранять секреты в репозитории; роли и разрешения проверять на каждом API endpoint.

## Интеграции
Frontend обращается к Django API через текущую инфраструктуру/proxy. Не внедрять Supabase без отдельного архитектурного решения: текущий backend — Django. Развертывание Vercel и БД требуют отдельной проверки миграций, env и конфигурации.

## Принципы
Не ломать API-контракты, применять миграции безопасно, избегать дублирования бизнес-логики, использовать типизированные DTO, поддерживать ky/ru/en, тестировать права и критические потоки.
