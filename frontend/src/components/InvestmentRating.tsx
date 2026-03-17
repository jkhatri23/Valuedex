'use client'


interface InvestmentRatingProps {
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
}

export default function InvestmentRating({ features }: InvestmentRatingProps) {
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
  
  const getScoreColor = (_score: number) => {
    return 'text-gray-900 dark:text-white'
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
              className="bg-blue-500 rounded-full h-2 transition-all duration-500"
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
              className="bg-gray-500 rounded-full h-2 transition-all duration-500"
              style={{ width: `${features.artist_score * 10}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Market Trends */}
      <div className="pt-6 border-t border-gray-200 dark:border-white/10">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Market Trends</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="text-center p-3 bg-gray-50/50 border border-gray-100/50 rounded-lg dark:bg-white/[0.02] dark:border-white/[0.04]">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {features.trend_30d >= 0 ? '+' : ''}{features.trend_30d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">30 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50/50 border border-gray-100/50 rounded-lg dark:bg-white/[0.02] dark:border-white/[0.04]">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {features.trend_90d >= 0 ? '+' : ''}{features.trend_90d.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">90 Days</div>
          </div>
          <div className="text-center p-3 bg-gray-50/50 border border-gray-100/50 rounded-lg dark:bg-white/[0.02] dark:border-white/[0.04]">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {features.trend_1y >= 0 ? '+' : ''}{features.trend_1y.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 dark:text-white/60 mt-1">1 Year</div>
          </div>
        </div>
      </div>

      {/* Volatility */}
      <div className="mt-4 p-4 bg-blue-50/50 border border-blue-100/50 rounded-lg dark:bg-white/[0.02] dark:border-white/[0.04]">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-900 dark:text-white">Price Volatility</span>
          <span className="text-sm font-semibold text-gray-900 dark:text-white">
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
