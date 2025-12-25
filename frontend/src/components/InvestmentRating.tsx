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
    market_sentiment?: number
  } | null
  prediction?: {
    recommendation: string
    risk_assessment: {
      risk_level: string
      reward_risk_ratio: number
      volatility: number
      upside_potential_pct: number
      downside_risk_pct: number
    }
    scenarios: {
      conservative: number
      moderate: number
      aggressive: number
    }
    growth_rate: number
    market_factors: {
      sentiment_multiplier: number
      popularity_score: number
      current_trend: number
    }
  } | null
}

export default function InvestmentRating({ features, prediction }: InvestmentRatingProps) {
  // Handle null/undefined features
  if (!features) {
    return (
      <div className="card">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center dark:bg-white/5 dark:border-white/10">
          <p className="text-yellow-800 font-semibold mb-2 dark:text-white">Investment Rating Not Available</p>
          <p className="text-sm text-yellow-700 dark:text-white/70">
            Features are being calculated. Please check back later or refresh the page.
          </p>
        </div>
      </div>
    )
  }
  
  // Generate AI-powered explanation using prediction data
  const getAIExplanation = () => {
    if (!prediction) {
      // Fallback to feature-based explanations
      if (features.investment_rating === 'Strong Buy') 
        return 'This card shows exceptional growth potential with strong fundamentals across multiple factors.'
      if (features.investment_rating === 'Buy') 
        return 'This card demonstrates good investment potential with positive market trends.'
      if (features.investment_rating === 'Hold') 
        return 'This card is fairly valued at current prices. Consider holding or monitoring closely.'
      if (features.investment_rating === 'Underperform') 
        return 'This card may underperform the market. Exercise caution when investing.'
      return 'This card shows weak fundamentals and may decline in value. Consider selling.'
    }
    
    const { recommendation, risk_assessment, growth_rate, market_factors } = prediction
    const riskLevel = risk_assessment.risk_level
    const rewardRisk = risk_assessment.reward_risk_ratio
    const upside = risk_assessment.upside_potential_pct
    const downside = Math.abs(risk_assessment.downside_risk_pct)
    
    // AI-generated explanation based on prediction model
    let explanation = ''
    
    if (recommendation === 'strong_buy') {
      explanation = `Exceptional investment opportunity with a ${rewardRisk.toFixed(1)}x reward-risk ratio. `
      explanation += `Upside potential of +${upside.toFixed(0)}% significantly outweighs the ${downside.toFixed(0)}% downside risk. `
      explanation += `${riskLevel === 'low' ? 'Low risk profile makes this ideal for conservative portfolios.' : ''}`
    } else if (recommendation === 'buy') {
      explanation = `Strong buy signal with ${growth_rate.toFixed(1)}% expected growth. `
      explanation += `Reward-risk ratio of ${rewardRisk.toFixed(1)}x indicates good potential. `
      explanation += `Market sentiment (${market_factors.sentiment_multiplier.toFixed(2)}x) supports upward momentum.`
    } else if (recommendation === 'hold') {
      explanation = `Balanced risk-reward profile (${rewardRisk.toFixed(1)}x ratio). `
      explanation += `Current valuation is fair with ${Math.abs(growth_rate).toFixed(1)}% expected movement. `
      explanation += `${riskLevel === 'high' ? 'High volatility suggests monitoring closely before additional investment.' : 'Suitable for patient investors.'}`
    } else if (recommendation === 'consider_selling') {
      explanation = `Risk outweighs reward with only ${rewardRisk.toFixed(1)}x ratio. `
      explanation += `Downside risk of ${downside.toFixed(0)}% is concerning given ${upside.toFixed(0)}% upside. `
      explanation += `Consider reducing position or setting stop-loss orders.`
    } else {
      explanation = `Poor investment profile with ${downside.toFixed(0)}% downside risk. `
      explanation += `Reward-risk ratio of ${rewardRisk.toFixed(1)}x indicates unfavorable conditions. `
      explanation += `Market trends suggest considering exit strategy.`
    }
    
    return explanation
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

      {/* Key Factors */}
      <div className="space-y-4 mb-6">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Key Factors</h4>
        
        {/* Popularity */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-white/70">Popularity</span>
            <span className={`font-semibold ${getScoreColor(features.popularity_score / 10)}`}>
              {features.popularity_score.toFixed(0)}/100
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-white/20 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-400 to-purple-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.popularity_score}%` }}
            ></div>
          </div>
        </div>

        {/* Rarity */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-white/70">Rarity</span>
            <span className={`font-semibold ${getScoreColor(features.rarity_score)}`}>
              {features.rarity_score.toFixed(1)}/10
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-white/20 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.rarity_score * 10}%` }}
            ></div>
          </div>
        </div>

        {/* Artist */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-white/70">Artist Reputation</span>
            <span className={`font-semibold ${getScoreColor(features.artist_score)}`}>
              {features.artist_score.toFixed(1)}/10
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-white/20 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-pink-400 to-purple-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.artist_score * 10}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Market Trends */}
      <div className="pt-6 border-t border-gray-200 dark:border-white/10">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Market Trends</h4>
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-gray-50 border border-gray-200 rounded-lg dark:bg-white/5 dark:border-white/10">
            <div className={`text-lg font-bold ${features.trend_30d >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {features.trend_30d >= 0 ? '+' : ''}{features.trend_30d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">30 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50 border border-gray-200 rounded-lg dark:bg-white/5 dark:border-white/10">
            <div className={`text-lg font-bold ${features.trend_90d >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {features.trend_90d >= 0 ? '+' : ''}{features.trend_90d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">90 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50 border border-gray-200 rounded-lg dark:bg-white/5 dark:border-white/10">
            <div className={`text-lg font-bold ${features.trend_1y >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {features.trend_1y >= 0 ? '+' : ''}{features.trend_1y.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">1 Year</div>
          </div>
        </div>
      </div>

      {/* Volatility */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-lg dark:bg-white/5 dark:border-white/10">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-900 dark:text-white">Price Volatility</span>
          <span className="text-sm font-semibold text-blue-600 dark:text-blue-300">
            {features.volatility.toFixed(1)}%
          </span>
        </div>
        <p className="text-xs text-gray-600 dark:text-white/70 mt-2">
          {features.volatility < 10 && 'Low volatility - stable investment'}
          {features.volatility >= 10 && features.volatility < 25 && 'Moderate volatility - balanced risk/reward'}
          {features.volatility >= 25 && 'High volatility - higher risk but potential for gains'}
        </p>
      </div>
    </div>
  )
}
