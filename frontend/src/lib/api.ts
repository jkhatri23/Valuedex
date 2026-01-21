import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

export interface Card {
  id: string
  name: string
  set_name: string
  current_price: number
  image_url?: string
}

export interface CardDetails {
  id: number
  external_id: string
  name: string
  set_name: string
  rarity: string
  artist: string
  release_year: number
  card_number?: string
  current_price: number
  image_url?: string
  tcgplayer_url?: string
  ebay_url?: string
  features?: {
    popularity_score: number
    rarity_score: number
    artist_score: number
    trend_30d: number
    trend_90d: number
    trend_1y: number
    volatility: number
    investment_score: number
    investment_rating: string
  }
}

export type CardCondition = 'Near Mint' | 'PSA 6' | 'PSA 7' | 'PSA 8' | 'PSA 9' | 'PSA 10'

export interface PriceHistory {
  date: string
  price: number
  volume?: number
  grade?: string | null
  source?: string
}

export interface Prediction {
  card_id: string
  card_name: string
  current_price: number
  predicted_price: number
  confidence_lower: number
  confidence_upper: number
  years_ahead: number
  target_date: string
  growth_rate: number
  model_version: string
  scenarios: {
    conservative: number
    moderate: number
    aggressive: number
  }
  risk_assessment: {
    risk_level: 'low' | 'moderate' | 'high'
    volatility: number
    downside_risk_pct: number
    upside_potential_pct: number
    reward_risk_ratio: number
  }
  market_factors: {
    sentiment_multiplier: number
    popularity_score: number
    market_sentiment: number | null
    current_trend: number
  }
  recommendation: 'strong_buy' | 'buy' | 'hold' | 'consider_selling' | 'sell'
  timeline: Array<{
    predicted_price: number
    years_ahead: number
    target_date: string
    conservative: number
    moderate: number
    aggressive: number
    confidence_lower: number
    confidence_upper: number
    risk_level: string
    recommendation: string
  }>
  insights?: {
    investment_rating: string
    investment_score: number
    time_series_contribution: number
    feature_contribution: number
    volatility: number
    reward_risk_ratio: number
  }
}

export async function searchCards(query: string): Promise<Card[]> {
  try {
    const { data } = await api.get(`/api/cards/search?q=${encodeURIComponent(query)}`)
    return data.cards || data || []
  } catch {
    return []
  }
}

export async function getCardDetails(cardId: string): Promise<CardDetails | null> {
  try {
    const { data } = await api.get(`/api/cards/${cardId}`)
    return data
  } catch {
    return null
  }
}

export async function getPriceHistory(
  cardId: string, 
  condition?: CardCondition,
  cardName?: string,
  setName?: string
): Promise<PriceHistory[]> {
  try {
    const params: Record<string, string> = {}
    if (condition) params.grade = condition
    if (cardName) params.card_name = cardName
    if (setName) params.set_name = setName
    
    const { data } = await api.get(`/api/cards/${cardId}/prices`, { params })
    return data.prices
  } catch {
    return []
  }
}

export async function getPrediction(cardId: string, yearsAhead: number = 3, cardName?: string): Promise<Prediction | null> {
  try {
    console.log('Predicting for cardId:', cardId, 'cardName:', cardName, 'years:', yearsAhead)
    const { data } = await api.post('/api/predict', { 
      card_id: cardId || '', 
      card_name: cardName || '',
      years_ahead: yearsAhead 
    })
    console.log('Prediction response:', data)
    return data
  } catch (error: any) {
    console.error('Prediction error:', error?.response?.data || error?.message || error)
    return null
  }
}

export async function getInvestmentRating(cardId: string) {
  try {
    const { data } = await api.get(`/api/cards/${cardId}/rating`)
    return data
  } catch {
    return null
  }
}

export interface GradeAnalysis {
  grade: string
  current_price: number
  growth_12m: number
  liquidity_score: number
  rating: string
}

export interface PriceChartingComparison {
  product_name: string
  loose_price: number
  cib_price: number
  new_price: number
  source: string
  description: string
}

export interface AllGradesHistory {
  card_id: string
  card_name: string
  set_name: string
  grades: Record<string, {
    history: PriceHistory[]
    current_price: number
    price_12m_ago: number
    change_pct: number
    data_points: number
  }>
  recommendations: {
    best_value: string | null
    best_growth: string | null
    most_liquid: string | null
    analysis: GradeAnalysis[]
  }
  pricecharting_comparison?: PriceChartingComparison | null
}

export async function getAllGradesHistory(
  cardId: string,
  cardName?: string,
  setName?: string
): Promise<AllGradesHistory | null> {
  try {
    const params: Record<string, string> = {}
    if (cardName) params.card_name = cardName
    if (setName) params.set_name = setName
    
    const { data } = await api.get(`/api/cards/${cardId}/all-grades-history`, { params })
    return data
  } catch {
    return null
  }
}

export default api
