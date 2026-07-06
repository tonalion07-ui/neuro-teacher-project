
const TOKEN = process.env.VK_ACCESS_TOKEN;
const GROUP_ID = process.env.VK_GROUP_ID;

async function testPost() {
  try {
    const response = await fetch(`https://api.vk.com/method/wall.get?owner_id=-${GROUP_ID}&count=1&access_token=${TOKEN}&v=5.199`);
    const data = await response.json();
    console.log('Полный ответ VK:', JSON.stringify(data, null, 2));
    if (data.response?.items?.[0]) {
      console.log('✅ Последний пост:', data.response.items[0].text);
    } else {
      console.log('❌ Постов нет или response пустой');
    }
  } catch (error) {
    console.log('❌ Ошибка:', error);
  }
}

testPost();