import { useState, useCallback, useRef } from 'react'
import { OrderBook } from './components/OrderBook'
import { PriceChart } from './components/PriceChart'
import { TradeTape } from './components/TradeTape'
import { OrderEntry } from './components/OrderEntry'
import { useWebSocket } from './hooks/useWebSocket'
import type { PriceLevel, TradeEvent, StreamEvent } from './types'

const FLASH_MS = 400

export default function App() {
  const [bids, setBids]       = useState<PriceLevel[]>([])
  const [asks, setAsks]       = useState<PriceLevel[]>([])
  const [spread, setSpread]   = useState<number | null>(null)
  const [midPrice, setMid]    = useState<number | null>(null)
  const [trades, setTrades]   = useState<TradeEvent[]>([])
  const [flashSet, setFlash]  = useState<Set<string>>(new Set())
  const chartTrades = trades.map(t => ({ price: t.price, timestamp: t.timestamp }))

  const flashKeys = useRef<Set<string>>(new Set())

  const triggerFlash = useCallback((keys: string[]) => {
    keys.forEach(k => flashKeys.current.add(k))
    setFlash(new Set(flashKeys.current))
    setTimeout(() => {
      keys.forEach(k => flashKeys.current.delete(k))
      setFlash(new Set(flashKeys.current))
    }, FLASH_MS)
  }, [])

  const onMessage = useCallback((event: StreamEvent) => {
    if (event.type === 'order_book_update') {
      const newBidKeys = event.bids.map(b => `bid-${b.price}`)
      const newAskKeys = event.asks.map(a => `ask-${a.price}`)

      setBids(prev => {
        const changed = newBidKeys.filter((k, i) => {
          const p = event.bids[i]
          const old = prev.find(b => b.price === p.price)
          return !old || old.quantity !== p.quantity
        })
        if (changed.length) triggerFlash(changed)
        return event.bids
      })
      setAsks(prev => {
        const changed = newAskKeys.filter((k, i) => {
          const p = event.asks[i]
          const old = prev.find(a => a.price === p.price)
          return !old || old.quantity !== p.quantity
        })
        if (changed.length) triggerFlash(changed)
        return event.asks
      })
      setSpread(event.spread)
      setMid(event.mid_price)
    } else if (event.type === 'trade_executed') {
      setTrades(prev => {
        if (prev.some(t => t.id === event.id)) return prev
        return [...prev.slice(-499), event]
      })
    }
  }, [triggerFlash])

  useWebSocket(onMessage)

  return (
    <div style={{ minHeight: '100vh', padding: 16 }}>
      {/* Header */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>Order Book Simulator</span>
        {midPrice != null && (
          <span style={{ fontSize: 14, color: '#58a6ff', background: '#388bfd26', padding: '2px 10px', borderRadius: 20, border: '1px solid #388bfd' }}>
            {midPrice.toFixed(2)}
          </span>
        )}
        {spread != null && (
          <span style={{ fontSize: 12, color: '#8b949e' }}>spread {spread.toFixed(2)}</span>
        )}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, alignItems: 'start' }}>
        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <OrderBook bids={bids} asks={asks} spread={spread} mid_price={midPrice} flashSet={flashSet} />
          <OrderEntry />
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <PriceChart trades={chartTrades} />
          <TradeTape trades={trades} />
        </div>
      </div>
    </div>
  )
}
