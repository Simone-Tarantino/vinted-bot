# Vinted Deal Agent

Servizio hostabile su VPS Docker che monitora annunci su Vinted, confronta i prezzi con eBay venduti e invia alert Telegram quando trova offerte interessanti. Il matching prodotto usa Gemini tramite `GEMINI_API_KEY`.

## Funzionalità MVP

- Ricerche monitorate via API REST
- Worker Playwright per Vinted con sessione cifrata
- Benchmark prezzi da eBay sold
- Matching AI con Gemini
- Alert Telegram con anti-spam
- Scheduler periodico
- Dashboard web read-only

## Requisiti

- Docker + Docker Compose
- `GEMINI_API_KEY` (obbligatoria)
- Token Telegram (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) per notifiche

## Avvio rapido

```bash
cp .env.example .env
# imposta GEMINI_API_KEY e credenziali Telegram
docker compose up --build
```

Servizi:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000`
- Reverse proxy: `http://localhost`

Healthcheck:

```bash
curl http://localhost:8000/health
```

## API principali

- `GET /health`
- `GET /searches`
- `POST /searches`
- `GET /deals`
- `GET /listings`
- `GET /jobs`
- `POST /scan/run`

Esempio creazione ricerca:

```bash
curl -X POST http://localhost:8000/searches \
  -H "Content-Type: application/json" \
  -d '{
    "query": "nike air max 90",
    "brand": "Nike",
    "max_price": 80,
    "discount_threshold_percent": 25
  }'
```

## Sessione Vinted

La sessione viene salvata cifrata in `VINTED_SESSION_FILE`. Per il primo setup:

1. Effettua login su Vinted nel browser controllato dal worker
2. Salva i cookie tramite endpoint/worker di import sessione
3. I job successivi riutilizzano la sessione

## Sviluppo locale backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
export DATABASE_URL=sqlite:///./vinted_bot.db
export DISABLE_SCHEDULER=true
pytest
uvicorn app.main:app --reload
```

## Deploy VPS (runbook)

1. Clona repo sul VPS
2. Configura `.env` con segreti produzione
3. Avvia `docker compose up -d --build`
4. Configura DNS + HTTPS (consigliato Certbot davanti a nginx)
5. Verifica `GET /health` e crea almeno una ricerca monitorata
6. Controlla log job con `GET /jobs`

## Note operative

- Nessun acquisto automatico: solo segnalazioni
- `GEMINI_API_KEY` non viene mai salvata su database
- In caso captcha/login scaduto, aggiorna sessione Vinted
- Aumenta `SCAN_INTERVAL_MINUTES` se riscontri rate limit
