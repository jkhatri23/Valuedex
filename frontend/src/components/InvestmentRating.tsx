'use client'

import { Award, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface InvestmentRatingProps {
  cardId: string
  features: {
    investment_score: number
    investment_rating: string
    popularity_score: number
    rarity_score: number
    artist_score: number
    trend_30d: number
    trend_90d: number
    trend_1y: number
    volatility: number
  } | null
}

export default function InvestmentRating({ features }: InvestmentRatingProps) {
  // Handle null/undefined features
  if (!features) {
    return (
      <div className="card">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800 font-semibold mb-2">Investment Rating Not Available</p>
          <p className="text-sm text-yellow-600">
            Features are being calculated. Please check back later or refresh the page.
          </p>
        </div>
      </div>
    )
  }

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'Strong Buy':
        return 'from-green-500 to-green-600'
      case 'Buy':
        return 'from-blue-500 to-blue-600'
      case 'Hold':
        return 'from-yellow-500 to-yellow-600'
      case 'Underperform':
        return 'from-orange-500 to-orange-600'
      case 'Sell':
        return 'from-red-500 to-red-600'
      default:
        return 'from-gray-500 to-gray-600'
    }
  }

  const getRatingIcon = (rating: string) => {
    if (rating.includes('Buy')) return <TrendingUp className="w-6 h-6" />
    if (rating === 'Sell') return <TrendingDown className="w-6 h-6" />
    return <Minus className="w-6 h-6" />
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-blue-600'
    if (score >= 4) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="card">
      {/* Rating Header */}
      <div className={`bg-gradient-to-r ${getRatingColor(features.investment_rating)} rounded-lg p-6 text-white mb-6`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Award className="w-8 h-8" />
            <div>
              <div className="text-sm opacity-90">Investment Rating</div>
              <div className="text-2xl font-bold">{features.investment_rating}</div>
            </div>
          </div>
          {getRatingIcon(features.investment_rating)}
        </div>
        
        {/* Score Bar */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Investment Score</span>
            <span className="font-bold">{features.investment_score}/10</span>
          </div>
          <div className="w-full bg-white bg-opacity-30 rounded-full h-2">
            <div
              className="bg-white rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.investment_score * 10}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Rating Explanation */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">What This Means</h4>
        <p className="text-sm text-gray-600">
          {features.investment_rating === 'Strong Buy' && 
            'This card shows exceptional growth potential with strong fundamentals across multiple factors.'}
          {features.investment_rating === 'Buy' && 
            'This card demonstrates good investment potential with positive market trends.'}
          {features.investment_rating === 'Hold' && 
            'This card is fairly valued at current prices. Consider holding or monitoring closely.'}
          {features.investment_rating === 'Underperform' && 
            'This card may underperform the market. Exercise caution when investing.'}
          {features.investment_rating === 'Sell' && 
            'This card shows weak fundamentals and may decline in value. Consider selling.'}
        </p>
      </div>

      {/* Key Factors */}
      <div className="space-y-4 mb-6">
        <h4 className="text-sm font-semibold text-gray-700">Key Factors</h4>
        
        {/* Popularity */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">Popularity</span>
            <span className={`font-semibold ${getScoreColor(features.popularity_score / 10)}`}>
              {features.popularity_score.toFixed(0)}/100
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-400 to-purple-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.popularity_score}%` }}
            ></div>
          </div>
        </div>

        {/* Rarity */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">Rarity</span>
            <span className={`font-semibold ${getScoreColor(features.rarity_score)}`}>
              {features.rarity_score.toFixed(1)}/10
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.rarity_score * 10}%` }}
            ></div>
          </div>
        </div>

        {/* Artist */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">Artist Reputation</span>
            <span className={`font-semibold ${getScoreColor(features.artist_score)}`}>
              {features.artist_score.toFixed(1)}/10
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-pink-400 to-purple-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.artist_score * 10}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Market Trends */}
      <div className="pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-4">Market Trends</h4>
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className={`text-lg font-bold ${features.trend_30d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {features.trend_30d >= 0 ? '+' : ''}{features.trend_30d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">30 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className={`text-lg font-bold ${features.trend_90d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {features.trend_90d >= 0 ? '+' : ''}{features.trend_90d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">90 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className={`text-lg font-bold ${features.trend_1y >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {features.trend_1y >= 0 ? '+' : ''}{features.trend_1y.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">1 Year</div>
          </div>
        </div>
      </div>

      {/* Volatility */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-700">Price Volatility</span>
          <span className="text-sm font-semibold text-blue-600">
            {features.volatility.toFixed(1)}%
          </span>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          {features.volatility < 10 && 'Low volatility - stable investment'}
          {features.volatility >= 10 && features.volatility < 25 && 'Moderate volatility - balanced risk/reward'}
          {features.volatility >= 25 && 'High volatility - higher risk but potential for gains'}
        </p>
      </div>
    </div>
  )
}
