// utils/formatter.js
function formatPrice(price, currency = "usd") {
  return `${price.toFixed(2)} ${currency.toUpperCase()}`;
}

function formatChange(change) {
  const sign = change >= 0 ? "+" : "-";
  return `${sign}${Math.abs(change).toFixed(2)}%`;
}

module.exports = { formatPrice, formatChange };
