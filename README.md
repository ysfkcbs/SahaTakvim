# SahaTakvim

Flask tabanlı halı saha rezervasyon, haftalık takvim, gün sonu kapanışı, finans ve rapor uygulaması.

## Docker ile Çalıştırma

Bu repo artık Docker üzerinden çalıştırılacak şekilde düzenlenmiştir.

```bash
docker compose build
docker compose up -d
```

Uygulama:

```text
http://127.0.0.1:8000
```

İlk açılışta container şunları otomatik çalıştırır:

```bash
flask db upgrade
flask seed-admin
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

Varsayılan local Docker kullanıcı bilgileri `docker-compose.yml` içindedir:

```text
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=Admin123!
```

## Docker Dosyaları

```text
Dockerfile
docker-compose.yml
.dockerignore
```

`docker-compose.yml` PostgreSQL bağlantısını `.env` içindeki `DATABASE_URL` değerinden okur. Docker içinden Windows host üzerindeki PostgreSQL'e bağlanmak için host değeri genellikle `host.docker.internal` olmalıdır.

```text
DATABASE_URL=postgresql://postgres:your-password@host.docker.internal:5432/SahaTakvim
```

`.env` dosyası Git'e eklenmez; yerel şifre ve bağlantı bilgileri bu dosyada tutulur.

## Faydalı Docker Komutları

```bash
docker compose ps
docker compose logs -f web
docker compose down
docker compose up -d --build
```

Veritabanı volume’unu sıfırlamak için:

```bash
docker compose down -v
```

## Mimari

- Flask app factory: `app/__init__.py`
- Blueprints: `auth`, `main`, `calendar`, `fields`, `finance`, `reports`
- ORM: Flask-SQLAlchemy
- Migration: Flask-Migrate/Alembic
- Auth: Flask-Login
- Production server: Gunicorn

## Modüller

- Haftalık saha takvimi ve rezervasyon modalı
- Saha yönetimi
- Gün sonu kapanış tablosu ve modal giriş/düzeltme akışı
- Finans gelir/gider ve bilanço ekranları
- Kullanıcı yönetimi
- Rezervasyon raporları

## Ortam Değişkenleri

Local Docker ortamı için temel değişkenler `.env` dosyasında tanımlıdır.

```text
FLASK_ENV=production
SECRET_KEY=change-this-secret
DATABASE_URL=postgresql://postgres:your-password@host.docker.internal:5432/SahaTakvim
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=Admin123!
```

## Lokal Python ile Çalıştırma

Ana çalışma yöntemi Docker’dır. Yine de ihtiyaç olursa:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade
flask seed-admin
flask run
```
