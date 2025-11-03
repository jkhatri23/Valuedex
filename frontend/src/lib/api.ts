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

export interface PriceHistory {
  date: string
  price: number
  volume?: number
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
  timeline: Array<{
    predicted_price: number
    years_ahead: number
    target_date: string
  }>
  insights?: {
    investment_rating: string
    investment_score: number
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

export const getPriceHistory = async (cardId: string): Promise<PriceHistory[]> => {
  try {
    const response = await api.get(`/api/cards/${cardId}/prices`)
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

