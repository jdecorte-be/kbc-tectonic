import { getRequestURL, proxyRequest } from 'h3'

export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event)
  const requestURL = getRequestURL(event)
  // The destination is server configuration, never a user-supplied host.
  const target = `${config.apiBase.replace(/\/$/, '')}${requestURL.pathname}${requestURL.search}`
  return proxyRequest(event, target)
})
