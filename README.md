# Payvast Backend

Django REST Framework backend для краудфандинговой платформы.

## Технологии

- Python 3.14+
- Django 6.x
- Django REST Framework 3.15
- SimpleJWT — JWT аутентификация
- SQLite — база данных (разработка)

## Структура проекта

```
Payvast-Backend/
├── config/               # Конфигурация проекта
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── auth_app/             # Аутентификация (регистрация, вход, JWT)
├── users/                # Кастомная модель пользователя
├── campaigns/            # Кампании сбора средств
├── donations/            # Пожертвования
├── fund_owner/           # Профили владельцев фондов
├── applications/         # Заявки на получение помощи
├── manage.py
└── requirements.txt
```

## Установка

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| POST | `/api/auth/token/refresh/` | Обновление токена |
| GET/PATCH | `/api/users/me/` | Профиль текущего пользователя |
| GET | `/api/campaigns/` | Список активных кампаний |
| POST | `/api/campaigns/create/` | Создать кампанию |
| GET/PUT/DELETE | `/api/campaigns/<id>/` | Детали кампании |
| GET | `/api/donations/` | Мои пожертвования |
| POST | `/api/donations/create/` | Создать пожертвование |
| GET | `/api/fund-owner/` | Список верифицированных фондов |
| GET/PUT | `/api/fund-owner/profile/` | Профиль фонда |
| GET | `/api/applications/` | Мои заявки |
| POST | `/api/applications/` | Создать заявку |
| PATCH | `/api/applications/<id>/review/` | Рассмотреть заявку (admin) |
