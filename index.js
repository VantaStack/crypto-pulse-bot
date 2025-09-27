const { startBot } = require('./src/bot');
const logger = require('./config/logger');

(async () => {
  try {
    await startBot();
  } catch (err) {
    logger.error({msg:'Failed starting bot', err: err.message || err});
    process.exit(1);
  }
})();
