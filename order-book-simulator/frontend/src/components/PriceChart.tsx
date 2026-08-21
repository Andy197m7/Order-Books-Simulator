import { useEffect, useRef } from 'react'
import { createChart, type IChartApi, type ISeriesApi, type Time } from 'lightweight-charts'

interface Props {
  trades: Array<{ price: number; timestamp: number }>
}

export function PriceChart({ trades }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 260,
      layout: { background: { color: '#161b22' }, textColor: '#8b949e' },
      grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#30363d' },
      timeScale: { borderColor: '#30363d', timeVisible: true },
    })

    const series = chart.addLineSeries({
      color: '#58a6ff',
      lineWidth: 2,
      crosshairMarkerVisible: true,
    })

    chartRef.current = chart
    seriesRef.current = series

    const ro = new ResizeObserver(() => {
      if (containerRef.current) chart.resize(containerRef.current.clientWidth, 260)
    })
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!seriesRef.current || trades.length === 0) return
    const data = trades.map(t => ({
      time: Math.floor(t.timestamp) as Time,
      value: t.price,
    }))
    // dedupe by time (lightweight-charts requires strictly ascending time)
    const seen = new Map<number, number>()
    data.forEach(d => seen.set(d.time as number, d.value))
    const sorted = Array.from(seen.entries())
      .sort(([a], [b]) => a - b)
      .map(([time, value]) => ({ time: time as Time, value }))
    seriesRef.current.setData(sorted)
  }, [trades])

  return (
    <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #30363d', fontWeight: 700, fontSize: 13, color: '#8b949e', letterSpacing: 1 }}>
        PRICE CHART
      </div>
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  )
}
