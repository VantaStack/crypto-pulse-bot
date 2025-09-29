# Crypto Pulse Bot

A privacy-first Telegram bot for real-time crypto/fiat conversion using CoinGecko.
Clean architecture, safe parsing (AST), resilient networking (retry/backoff), multi-language (EN/FA),
inline mode, and simple rate limiting. No user data is stored.

## Features
- Real-time prices via CoinGecko with retry/backoff
- Safe arithmetic in queries: `2.5 BTC to USD`, `(1.2 ETH + 0.3 ETH) to EUR`
- Inline queries and standard messages
- Smart defaults for missing quote (crypto→USD, fiat→BTC)
- In-memory caching to reduce API calls
- Simple per-chat rate limiting and optional access control
- Multi-language responses (English/Persian)
- Docker support

## Quick start
1. Create `.env`:
