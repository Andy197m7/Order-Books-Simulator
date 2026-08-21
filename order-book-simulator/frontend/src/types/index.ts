export interface PriceLevel {
  price: number
  quantity: number
}

export interface OrderBookSnapshot {
  bids: PriceLevel[]
  asks: PriceLevel[]
  spread: number | null
  mid_price: number | null
}

export interface TradeEvent {
  type: 'trade_executed'
  id: string
  buyer_id: string
  seller_id: string
  price: number
  quantity: number
  timestamp: number
  aggressor_side: 'buy' | 'sell'
}

export interface OrderBookUpdateEvent {
  type: 'order_book_update'
  bids: PriceLevel[]
  asks: PriceLevel[]
  spread: number | null
  mid_price: number | null
}

export interface OrderStatusEvent {
  type: 'order_status'
  id: string
  status: 'open' | 'filled' | 'partial' | 'cancelled' | 'rejected'
  remaining: number
  client_id: string
}

export type StreamEvent = TradeEvent | OrderBookUpdateEvent | OrderStatusEvent
