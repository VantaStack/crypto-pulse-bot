require('dotenv').config();
const { startBot } = require('./src/bot');

(async () => {
  try {
    await startBot();
    console.log('Crypto Pulse Bot is up and running.');
  } catch (error) {
    console.error('Error starting the bot:', error);
    process.exit(1);
  }
})();
