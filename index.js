require('dotenv').config();
const bot = require('./src/bot');

bot.launch().then(() => {
  console.log('🤖 Bot is running...');
}).catch(err => {
  console.error('❌ Failed to start bot:', err);
});
