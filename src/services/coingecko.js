const axios = require('axios');

async function fetchCoinPrice(symbol, vsCurrency) {
  const { data } = await axios.get('https://api.coingecko.com/api/v3/simple/price', {
    params: {
      ids: symbol,
      vs_currencies: vsCurrency
    }
  });
  return data[symbol] ? data[symbol][vsCurrency] : 'قیمت پیدا نشد';
}

async function convertCrypto(input) {
  const parts = input.match(/([0-9\.]+)\s*(\w+)\s*(?:to|->|\s)\s*(\w+)/i);
  if (!parts) throw new Error('فرمت درست نیست. مثال: /convert 2 BTC to USD');

  const amount = parseFloat(parts[1]);
  const from = parts[2];
  const to = parts[3];

  const fromPrice = await fetchCoinPrice(from, 'usd');
  const toPrice = await fetchCoinPrice(to, 'usd');

  if (!fromPrice || !toPrice) throw new Error('قیمت‌ها پیدا نشدند');

  const result = amount * (fromPrice / toPrice);
  return `${amount} ${from.toUpperCase()} ≈ ${result.toFixed(6)} ${to.toUpperCase()}`;
}

module.exports = { fetchCoinPrice, convertCrypto };
