// config/config.js
require("dotenv").config();

module.exports = {
  botToken: process.env.BOT_TOKEN || "",
  defaultCurrency: process.env.DEFAULT_CURRENCY || "usd",
  logLevel: process.env.LOG_LEVEL || "info",
};
