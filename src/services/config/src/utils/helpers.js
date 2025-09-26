function prettyNumber(n) {
  if (n === undefined || n === null || isNaN(n)) return '-';
  if (n < 0.0001) return n.toPrecision(4);
  return Number(n.toFixed(6)).toString().replace(/\.0+$/, '');
}

module.exports = { prettyNumber };
