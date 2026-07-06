// api/oauth-callback.js
export default async function handler(req, res) {
  // Проверяем, что это GET запрос с кодом авторизации
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { code, state, device_id } = req.query;

  // Проверяем наличие обязательных параметров
  if (!code || !state || !device_id) {
    return res.status(400).json({ 
      error: 'Missing required parameters',
      received: { code: !!code, state: !!state, device_id: !!device_id }
    });
  }

  try {
    // Обмениваем code на токены
    const tokenResponse = await fetch('https://id.vk.ru/oauth2/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: code,
        client_id: process.env.VK_CLIENT_ID,
        client_secret: process.env.VK_CLIENT_SECRET,
        redirect_uri: process.env.VK_REDIRECT_URI,
        device_id: device_id,
        state: state,
      }),
    });

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.json();
      console.error('Token exchange error:', errorData);
      return res.status(400).json({ 
        error: 'Failed to exchange code for tokens',
        details: errorData 
      });
    }

    const tokens = await tokenResponse.json();

    // Здесь можно сохранить токены в базу данных или сессию
    // Например: await saveTokensToDatabase(tokens);

    // Возвращаем успешный ответ
    return res.status(200).json({
      success: true,
      message: 'Authorization successful',
      // НЕ возвращаем токены клиенту для безопасности!
      // tokens: tokens, // <-- НИКОГДА не делай так в production
    });

  } catch (error) {
    console.error('OAuth callback error:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
}