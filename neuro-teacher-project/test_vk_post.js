// Smoke-test: публикация одного поста в группу через wall.post
// Токен и GROUP_ID берём из process.env (задаются в PowerShell перед запуском).

const TOKEN = process.env.VK_ACCESS_TOKEN;
const GROUP_ID = process.env.VK_GROUP_ID;

const message = [
  '🔧 Технический пост: проверка работы VK API (smoke-test).',
  '',
  'Этот пост создан автоматически из node-скрипта для подтверждения,',
  'что групповой токен и доступ к wall.post работают. Можно удалить.',
  '',
  '#нейроучитель'
].join('\n');

async function main() {
  if (!TOKEN || !GROUP_ID) {
    console.log('❌ Не заданы VK_ACCESS_TOKEN / VK_GROUP_ID');
    process.exit(1);
  }

  const params = new URLSearchParams({
    owner_id: `-${GROUP_ID}`,
    from_group: '1',
    message,
    access_token: TOKEN,
    v: '5.199'
  });

  const url = `https://api.vk.com/method/wall.post?${params.toString()}`;
  console.log('📡 POST →', url.replace(TOKEN, 'TOKEN_HIDDEN'));

  const r = await fetch(url, { method: 'POST' });
  const data = await r.json();
  console.log('\n=== Ответ VK ===');
  console.log(JSON.stringify(data, null, 2));
  console.log('================\n');

  if (data.response?.post_id) {
    console.log(`✅ Пост опубликован. owner_id=-${GROUP_ID}, post_id=${data.response.post_id}`);
    console.log(`   Прямая ссылка: https://vk.com/wall-${GROUP_ID}_${data.response.post_id}`);
    console.log('   Для удаления: wall.delete c post_id=' + data.response.post_id);
  } else if (data.error) {
    console.log(`❌ VK ошибка: ${data.error.error_code} — ${data.error.error_msg}`);
  } else {
    console.log('⚠️ Неожиданный ответ');
  }
}

main().catch(e => {
  console.log('❌ Сетевая ошибка:', e.message);
  process.exit(1);
});
