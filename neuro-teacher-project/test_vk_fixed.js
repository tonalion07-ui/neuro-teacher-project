// Проверяем переменные окружения
const TOKEN = process.env.VK_ACCESS_TOKEN;
const GROUP_ID = process.env.VK_GROUP_ID;

console.log('=== Диагностика ===');
console.log('VK_ACCESS_TOKEN:', TOKEN ? `${TOKEN.substring(0, 10)}...` : 'НЕ УСТАНОВЛЕН');
console.log('VK_GROUP_ID:', GROUP_ID || 'НЕ УСТАНОВЛЕН');
console.log('==================\n');

if (!TOKEN || !GROUP_ID) {
  console.log('❌ Ошибка: переменные окружения не установлены!');
  console.log('\nВарианты решения:');
  console.log('1. Установить через PowerShell:');
  console.log('   $env:VK_ACCESS_TOKEN="ваш_токен"');
  console.log('   $env:VK_GROUP_ID="239683607"');
  console.log('\n2. Или передать напрямую в коде (только для теста!):');
  console.log('   const TOKEN = "ваш_токен_здесь";');
  console.log('   const GROUP_ID = "239683607";');
  process.exit(1);
}

async function testPost() {
  try {
    console.log(`📡 Запрос к VK API: wall.get для группы -${GROUP_ID}`);
    
    const url = `https://api.vk.com/method/wall.get?owner_id=-${GROUP_ID}&count=1&access_token=${TOKEN}&v=5.199`;
    const response = await fetch(url);
    const data = await response.json();
    
    console.log('\n=== Ответ VK API ===');
    console.log(JSON.stringify(data, null, 2));
    console.log('====================\n');
    
    if (data.error) {
      console.log('❌ Ошибка VK API:');
      console.log(`   Код: ${data.error.error_code}`);
      console.log(`   Сообщение: ${data.error.error_msg}`);
      
      // Расшифровка частых ошибок
      const errorCodes = {
        5: 'User authorization failed — неверный токен',
        27: 'Group authorization failed — токен не от админа сообщества',
        15: 'Access denied — нет прав на стену',
        100: 'One of the parameters specified was missing or invalid — проверь GROUP_ID'
      };
      
      if (errorCodes[data.error.error_code]) {
        console.log(`   Расшифровка: ${errorCodes[data.error.error_code]}`);
      }
    } else if (data.response?.items?.[0]) {
      console.log('✅ Успех! Последний пост:');
      console.log(`   ${data.response.items[0].text.substring(0, 100)}...`);
    } else {
      console.log('⚠️ Ответ получен, но постов нет (возможно, стена пустая)');
    }
  } catch (error) {
    console.log('❌ Сетевая ошибка:', error.message);
  }
}

testPost();