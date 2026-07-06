// Обмен authorization code → access_token
// Принимает: POST { code, code_verifier, redirect_uri, device_id }
// Возвращает: { access_token, refresh_token, expires_in, user_id, email? }

export default async function handler(req, res) {
  // CORS — чтобы лендинг на github.io мог дёргать эту функцию
  res.setHeader('Access-Control-Allow-Origin', 'https://tonalion07-ui.github.io')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }

  const { code, code_verifier, redirect_uri, device_id } = req.body || {}

  if (!code || !code_verifier || !redirect_uri || !device_id) {
    return res.status(400).json({
      error: 'missing_params',
      message: 'code, code_verifier, redirect_uri, device_id are required'
    })
  }

  const clientId = process.env.VK_CLIENT_ID
  const clientSecret = process.env.VK_CLIENT_SECRET

  if (!clientId || !clientSecret) {
    return res.status(500).json({ error: 'env_not_configured' })
  }

  // PKCE + code_verifier обязателен для публичных клиентов
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    code_verifier,
    redirect_uri,
    client_id: clientId,
    client_secret: clientSecret,    // PKCE-flow всё равно требует secret для Standalone
    device_id,
    v: '5.199'
  })

  try {
    const r = await fetch('https://id.vk.ru/oauth2/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    })

    const data = await r.json()

    if (!r.ok || data.error) {
      return res.status(400).json({
        error: 'vk_error',
        vk_response: data
      })
    }

    // Возвращаем токен на лендинг
    return res.status(200).json(data)
  } catch (err) {
    return res.status(500).json({
      error: 'fetch_failed',
      message: err.message
    })
  }
}

Структура после создания
    return res.status(200).json(data)
  } catch (err) {
    return res.status(500).json({
      error: 'fetch_failed',
      message: err.message
    })
  }
}