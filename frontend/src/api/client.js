import axios from 'axios'

const apiClient = axios.create({
  baseURL: `${import.meta.env.BASE_URL}api`,
  timeout: 30000,
})

/**
 * SSE 流式请求封装
 * @param {string} url - 请求 URL
 * @param {object} body - 请求体
 * @param {object} callbacks - 事件回调
 * @param {function} [callbacks.onThinking] - 思考过程回调
 * @param {function} [callbacks.onIntent] - 意图识别回调
 * @param {function} [callbacks.onToolCall] - 工具调用回调
 * @param {function} [callbacks.onToolResult] - 工具结果回调
 * @param {function} [callbacks.onToken] - Token 回调
 * @param {function} [callbacks.onDone] - 完成回调
 * @param {function} [callbacks.onError] - 错误回调
 */
export async function streamChat(url, body, callbacks = {}) {
  const response = await fetch(`${import.meta.env.BASE_URL}api${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          const callbackKey = 'on' + currentEvent.charAt(0).toUpperCase() + currentEvent.slice(1)
          if (callbacks[callbackKey]) {
            callbacks[callbackKey](data)
          }
        } catch (e) {
          // JSON 解析失败，忽略
        }
      }
    }
  }
}

export default apiClient
