
const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Puppeteer server is running.');
});

app.get('/generate', async (req, res) => {
  const query = req.query.query || 'пицца';
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  try {
    await page.goto('https://eda.yandex.ru');
    await page.waitForTimeout(3000); // ждём загрузку
    await browser.close();
    res.send(`🔍 Запрос получен: ${query}. (Обработка пока тестовая)`);
  } catch (err) {
    await browser.close();
    res.status(500).send('Ошибка при открытии сайта');
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
