import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

export type CardCondition =
  | 'Near Mint'
  | 'PSA 6'
  | 'PSA 7'
  | 'PSA 8'
  | 'PSA 9'
  | 'PSA 10'

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
  
  // Multiple scenarios
  scenarios: {
    conservative: number
    moderate: number
    aggressive: number
  }
  
  // Comprehensive risk assessment
  risk_assessment: {
    risk_level: 'low' | 'moderate' | 'high'
    volatility: number
    downside_risk_pct: number
    upside_potential_pct: number
    reward_risk_ratio: number
  }
  
  // Market factors
  market_factors: {
    sentiment_multiplier: number
    popularity_score: number
    market_sentiment: number | null
    current_trend: number
  }
  
  // Investment recommendation
  recommendation: 'strong_buy' | 'buy' | 'hold' | 'consider_selling' | 'sell'
  
  // Timeline with scenarios
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

export const searchCards = async (query: string): Promise<Card[]> => {
  try {
    const response = await api.get(`/api/cards/search?q=${encodeURIComponent(query)}`)
    console.log('API Response:', response.data)
    const cards = response.data.cards || response.data || []
    console.log('Parsed cards:', cards)
    return cards
  } catch (error: any) {
    console.error('Error searching cards:', error)
    if (error.response) {
      console.error('Response error:', error.response.data)
    }
    return []
  }
}

export const getCardDetails = async (cardId: string): Promise<CardDetails | null> => {
  try {
    const response = await api.get(`/api/cards/${cardId}`)
    return response.data
  } catch (error) {
    console.error('Error fetching card details:', error)
    return null
  }
}

export const getPriceHistory = async (
  cardId: string,
  condition?: CardCondition
): Promise<PriceHistory[]> => {
  try {
    const response = await api.get(`/api/cards/${cardId}/prices`, {
      params: condition ? { grade: condition } : {},
    })
    return response.data.prices
  } catch (error) {
    console.error('Error fetching price history:', error)
    return []
  }
}

export const getPrediction = async (cardId: string, yearsAhead: number = 3): Promise<Prediction | null> => {
  try {
    const response = await api.post('/api/predict', {
      card_id: cardId,
      years_ahead: yearsAhead,
    })
    return response.data
  } catch (error) {
    console.error('Error getting prediction:', error)
    return null
  }
}

export const getInvestmentRating = async (cardId: string) => {
  try {
    const response = await api.get(`/api/cards/${cardId}/rating`)
    return response.data
  } catch (error) {
    console.error('Error fetching investment rating:', error)
    return null
  }
}

export default api

