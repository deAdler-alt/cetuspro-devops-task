# CetusPro — DevOps: Deploy & Observe

Zadanie rekrutacyjne (staże/praktyki 2026), ścieżka **DevOps**. Prosta aplikacja
webowa (FastAPI + Redis) opakowana w powtarzalne środowisko kontenerowe z CI,
healthcheckami i podstawową obserwowalnością.

Zgodnie z opisem zadania: sama aplikacja jest celowo minimalna — ocenie podlega
build, uruchomienie i diagnostyka, nie złożoność aplikacji.

## Architektura

- **app** — FastAPI (Python 3.12): strona główna z licznikiem odwiedzin
(zapisywanym w Redisie) oraz endpoint `/health`
- **redis** — Redis 7 (alpine) jako realna zależność aplikacji
- Oba serwisy spina Docker Compose; kolejność startu wymusza
`depends_on: condition: service_healthy`



## Uruchomienie (jedna komenda)

Wymagania: Docker + Docker Compose.

```bash
cp .env.example .env   # opcjonalnie: dostosuj port/nazwę
docker compose up --build
```

- Aplikacja: [http://localhost:8000](http://localhost:8000)
- Healthcheck: [http://localhost:8000/health](http://localhost:8000/health)



## Konfiguracja

Przez zmienne środowiskowe (patrz `.env.example`):


| Zmienna                     | Domyślnie              | Opis                     |
| --------------------------- | ---------------------- | ------------------------ |
| `APP_PORT`                  | `8000`                 | Port aplikacji na hoście |
| `APP_NAME`                  | `cetuspro-devops-demo` | Nazwa aplikacji w logach |
| `REDIS_HOST` / `REDIS_PORT` | ustawiane w Compose    | Adres Redisa             |




## CI (GitHub Actions)

Pipeline uruchamia się przy każdym pushu:

1. **lint-and-test** — ruff (jakość kodu) + pytest (3 testy logiki `/health`
  z mockowanym Redisem — testy są szybkie i niezależne od środowiska)
2. **docker-build** — build obrazu + smoke test: kontener z aplikacją i
  prawdziwym Redisem, weryfikacja `curl /health`



## Diagnostyka

**Status kontenerów** (healthchecki wbudowane w Compose):

```bash
docker ps                          # kolumna STATUS: (healthy)/(unhealthy)
docker compose logs -f app         # logi aplikacji (strukturalny JSON)
```

**Scenariusz awarii — symulacja padu zależności:**

```bash
docker compose stop redis
```

- `/health` zwraca `503 {"status": "degraded", "redis": "unreachable"}`
- w logach pojawia się `Health check FAILED: cannot reach Redis`
- po ~45 s (3 nieudane próby co 15 s) kontener `app` przechodzi w stan
`(unhealthy)` w `docker ps`
- strona główna dalej działa (graceful degradation) — licznik pokazuje
`N/A (Redis down)`

**Przywrócenie:**

```bash
docker compose start redis         # /health wraca do 200 OK
```



## Decyzje projektowe

- **Multi-stage build** — mniejszy obraz końcowy, bez narzędzi budowania
- **Non-root user** w kontenerze — ograniczenie skutków ewentualnego włamania
- **Logi JSON na stdout** — gotowe pod agregację (np. Loki/ELK)
- **Graceful degradation** — awaria Redisa degraduje funkcję, nie ubija aplikacji
- **Testy na mockach** — CI nie wymaga stawiania Redisa do testów jednostkowych;
integrację end-to-end pokrywa smoke test w jobie `docker-build`



## Wykorzystanie AI

Projekt powstał we współpracy z modelem Fable 5 (Anthropic): koncepcja architektury, generowanie konfiguracji (Dockerfile, Compose, CI) i kodu aplikacji, analiza błędu lintera w CI. Decyzje projektowe, weryfikacja działania (uruchomienie, scenariusz awarii) i finalna ocena rozwiązania były wykonane po mojej stronie.