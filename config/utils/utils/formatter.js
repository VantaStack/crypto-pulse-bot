function formatPrice(num) {
  if (num === null || num === undefined || Number.isNaN(num)) return 'N/A';
  if (num >= 1) return Number(num).toLocaleString(undefined, { maximumFractionDigits: 6 });
  return Number(num).toPrecision(6);
}

module.exports = { formatPrice };
