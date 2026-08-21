import { useEffect, useRef, useCallback } from 'react'
import type { StreamEvent } from '../types'

type Handler = (event: StreamEvent) => void

export function useWebSocket(onMessage: Handler) {
  const wsRef = useRef<WebSocket | null>(null)
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const ws = new WebSocket(`${protocol}//${host}:8000/stream`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as StreamEvent
        handlerRef.current(event)
      } catch (_) {}
    }

    ws.onclose = () => {
      // Reconnect after 1 second
      setTimeout(connect, 1000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
}
