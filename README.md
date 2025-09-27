# Crypto Pulse Bot (Refactor)

This is a refactored version of the Crypto Pulse Telegram bot with:
- safer input validation
- multi-exchange price aggregation (CoinGecko + Binance)
- in-memory caching with TTL
- graceful shutdown and structured logging (pino)

## Run
1. Copy `.env.example` to `.env` and set `TELEGRAM_TOKEN`.
2. `npm install`
3. `npm start`

Commands:
- `/price SYMBOL [vs]` e.g. `/price btc usd`
- `/convert AMOUNT FROM to TO` e.g. `/convert 2 btc to usd`
