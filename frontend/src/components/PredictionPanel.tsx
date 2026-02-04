'use client'

import { useState } from 'react'
import { getPrediction, Prediction } from '@/lib/api'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Sparkles, Loader2, TrendingUp, AlertCircle, Shield, Target, Activity, BarChart3 } from 'lucide-react'

interface PredictionPanelProps {
  cardId: string
  cardName: string
  currentPrice: number
  onPredictionGenerated?: (prediction: Prediction | null) => void
}

export default function PredictionPanel({ cardId, cardName, currentPrice, onPredictionGenerated }: PredictionPanelProps) {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [yearsAhead, setYearsAhead] = useState(3)

  const handlePredict = async () => {
    console.log('handlePredict called with cardId:', cardId, 'cardName:', cardName, 'yearsAhead:', yearsAhead)
    setIsLoading(true)
    try {
      const result = await getPrediction(cardId || '', yearsAhead, cardName || '')
      console.log('Prediction result:', result)
      if (result) {
        setPrediction(result)
        onPredictionGenerated?.(result)
      }
    } catch (error) {
      console.error('Prediction failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Prepare chart data with multiple scenarios
  const chartData = prediction
    ? [
        { 
          year: 'Now', 
          moderate: currentPrice, 
          conservative: currentPrice, 
          aggressive: currentPrice,
          lower: currentPrice, 
          upper: currentPrice 
        },
        ...prediction.timeline.map((item) => ({
          year: `+${item.years_ahead}yr`,
          moderate: item.moderate,
          conservative: item.conservative,
          aggressive: item.aggressive,
          lower: item.confidence_lower,
          upper: item.confidence_upper,
        })),
      ]
    : []
  
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'strong_buy': return 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-200'
      case 'buy': return 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200'
      case 'hold': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-200'
      case 'consider_selling': return 'bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-200'
      case 'sell': return 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-500/20 dark:text-gray-200'
    }
  }
  
  const getRiskLevelColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 dark:text-green-400'
      case 'moderate': return 'text-yellow-600 dark:text-yellow-400'
      case 'high': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }
  
  const formatRecommendation = (rec: string) => {
    return rec.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-6">
        <Sparkles className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white">Future Price Prediction</h3>
      </div>

      {/* Prediction Controls */}
      <div className="bg-white/30 border border-gray-100/50 rounded-lg p-6 mb-6 dark:bg-white/[0.02] dark:border-white/[0.04]">
        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-3">
          Predict price in how many years?
        </label>
        <div className="flex items-center space-x-3 mb-4">
          {[1, 2, 3, 5].map((year) => (
              <button
                key={year}
                onClick={() => setYearsAhead(year)}
                className={`px-5 py-2.5 rounded-lg font-medium transition-all ${
                  yearsAhead === year
                    ? 'bg-gray-800 dark:bg-gray-600 text-white'
                    : 'bg-gray-50/50 text-gray-700 hover:bg-gray-100/50 border border-gray-200/50 dark:bg-white/[0.03] dark:text-white/70 dark:hover:bg-white/[0.06] dark:border-white/[0.04]'
                }`}
              >
              {year} {year === 1 ? 'Year' : 'Years'}
            </button>
          ))}
        </div>
        <button
          onClick={handlePredict}
          disabled={isLoading}
          className="w-full btn-primary flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Generate Prediction</span>
            </>
          )}
        </button>
      </div>

      {/* Prediction Results */}
      {prediction && (
        <div className="space-y-6 animate-fade-in">
          {/* Recommendation Badge */}
          <div className="bg-gray-50/50 border border-gray-200/50 rounded-lg p-6 dark:bg-white/[0.02] dark:border-white/[0.05]">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-white/70 mb-2">Investment Recommendation</div>
                <span className={`inline-block px-6 py-2 rounded-full text-lg font-bold ${getRecommendationColor(prediction.recommendation)}`}>
                  {formatRecommendation(prediction.recommendation)}
                </span>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Risk Level</div>
                <div className={`text-2xl font-bold ${getRiskLevelColor(prediction.risk_assessment.risk_level)}`}>
                  {prediction.risk_assessment.risk_level.toUpperCase()}
                </div>
              </div>
            </div>
          </div>

          {/* Price Scenarios */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Target className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
              Price Scenarios ({yearsAhead} Year{yearsAhead > 1 ? 's' : ''})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50/50 border border-blue-100/50 rounded-lg p-4 text-center dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Current</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-300">
                  ${prediction.current_price.toFixed(2)}
                </div>
              </div>
              <div className="bg-orange-50/50 border border-orange-100/50 rounded-lg p-4 text-center dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Conservative</div>
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-300">
                  ${prediction.scenarios.conservative.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">25th percentile</div>
              </div>
              <div className="bg-gray-50/50 border border-gray-200/50 rounded-lg p-4 text-center dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Moderate</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${prediction.scenarios.moderate.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">Most likely</div>
              </div>
              <div className="bg-green-50/50 border border-green-100/50 rounded-lg p-4 text-center dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Aggressive</div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-300">
                  ${prediction.scenarios.aggressive.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">75th percentile</div>
              </div>
            </div>
            <div className={`mt-4 p-3 rounded-lg ${
              prediction.growth_rate >= 0 
                ? 'bg-green-50 border border-green-100 dark:bg-green-900/20 dark:border-green-500/30' 
                : 'bg-red-50 border border-red-100 dark:bg-red-900/20 dark:border-red-500/30'
            }`}>
              <div className="flex items-center justify-center">
                <TrendingUp className={`w-5 h-5 mr-2 ${prediction.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Expected Growth: 
                  <span className={`ml-2 text-lg font-bold ${
                    prediction.growth_rate >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {prediction.growth_rate >= 0 ? '+' : ''}{prediction.growth_rate.toFixed(1)}%
                  </span>
                </span>
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Shield className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
              Risk Assessment
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white/30 border border-gray-100/50 rounded-lg p-4 dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">Reward-Risk Ratio</span>
                  <BarChart3 className="w-4 h-4 text-gray-400" />
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">
                  {prediction.risk_assessment.reward_risk_ratio.toFixed(2)}x
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">
                  {prediction.risk_assessment.reward_risk_ratio > 2.5 ? 'Excellent' : 
                   prediction.risk_assessment.reward_risk_ratio > 1.5 ? 'Good' :
                   prediction.risk_assessment.reward_risk_ratio > 1.0 ? 'Fair' : 'Poor'}
                </div>
              </div>
              <div className="bg-white/30 border border-gray-100/50 rounded-lg p-4 dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">Volatility</span>
                  <Activity className="w-4 h-4 text-gray-400" />
                </div>
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-300">
                  {(prediction.risk_assessment.volatility * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">Price stability</div>
              </div>
              <div className="bg-red-50/50 border border-red-100/50 rounded-lg p-4 dark:bg-white/[0.02] dark:border-white/[0.04]">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Downside Risk</div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-300">
                  {prediction.risk_assessment.downside_risk_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">Potential loss (10th percentile)</div>
              </div>
              <div className="bg-green-50 border border-green-100 rounded-lg p-4 dark:bg-white/5 dark:border-white/10">
                <div className="text-sm text-gray-600 dark:text-white/70 mb-1">Upside Potential</div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-300">
                  +{prediction.risk_assessment.upside_potential_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 dark:text-white/60 mt-1">Potential gain (90th percentile)</div>
              </div>
            </div>
          </div>

          {/* Confidence Range */}
          <div className="bg-gray-50/50 border border-gray-100/50 rounded-lg p-4 dark:bg-white/[0.02] dark:border-white/[0.04]">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-900 dark:text-white">10-90% Confidence Range</span>
              <AlertCircle className="w-4 h-4 text-gray-400" />
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-700 dark:text-white/70 font-medium">
                ${prediction.confidence_lower.toFixed(2)}
              </span>
              <div className="flex-1 h-2 bg-gradient-to-r from-red-300 via-yellow-300 to-green-300 rounded-full"></div>
              <span className="text-gray-700 dark:text-white/70 font-medium">
                ${prediction.confidence_upper.toFixed(2)}
              </span>
            </div>
            <div className="text-center mt-2">
              <span className="text-xs text-gray-500 dark:text-white/60">
                80% of outcomes fall within this range
              </span>
            </div>
          </div>

          {/* Timeline Chart with Multiple Scenarios */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Price Projection Timeline</h4>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorModerate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="year" 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value: any, name: string) => {
                    const label = name === 'conservative' ? 'Conservative' : 
                                 name === 'moderate' ? 'Moderate' :
                                 name === 'aggressive' ? 'Aggressive' : name
                    return [`$${typeof value === 'number' ? value.toFixed(2) : value}`, label]
                  }}
                />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="conservative" 
                  stroke="#f97316" 
                  strokeWidth={2}
                  fillOpacity={0.1}
                  fill="#f97316"
                  name="Conservative"
                  strokeDasharray="5 5"
                />
                <Area 
                  type="monotone" 
                  dataKey="moderate" 
                  stroke="#8b5cf6" 
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorModerate)"
                  name="Moderate"
                />
                <Area 
                  type="monotone" 
                  dataKey="aggressive" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fillOpacity={0.1}
                  fill="#10b981"
                  name="Aggressive"
                  strokeDasharray="5 5"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Market Factors */}
          <div className="bg-white/30 border border-gray-100/50 rounded-lg p-6 dark:bg-white/[0.02] dark:border-white/[0.04]">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Market Factors</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600 dark:text-white/70">Popularity Score</span>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {prediction.market_factors.popularity_score.toFixed(0)}/100
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-600 dark:text-white/70">Sentiment Multiplier</span>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-300">
                  {prediction.market_factors.sentiment_multiplier.toFixed(2)}x
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-600 dark:text-white/70">Current Trend</span>
                <div className="text-2xl font-bold text-green-600 dark:text-green-300">
                  {prediction.market_factors.current_trend >= 0 ? '+' : ''}
                  {prediction.market_factors.current_trend.toFixed(2)}
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-600 dark:text-white/70">Market Sentiment</span>
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-300">
                  {prediction.market_factors.market_sentiment ? 
                    `${prediction.market_factors.market_sentiment.toFixed(0)}/100` : 
                    'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Investment Insights */}
          {prediction.insights && (
            <div className="bg-gray-50/50 border border-gray-200/50 rounded-lg p-6 dark:bg-white/[0.02] dark:border-white/[0.05]">
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white/60 rounded-lg p-4 dark:bg-black/20">
                  <span className="text-sm text-gray-600 dark:text-white/70">Investment Rating</span>
                  <div className={`mt-2 inline-block px-4 py-1.5 rounded-full text-sm font-semibold ${
                    prediction.insights.investment_rating === 'Strong Buy' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-200'
                      : prediction.insights.investment_rating === 'Buy'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200'
                      : prediction.insights.investment_rating === 'Hold'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200'
                  }`}>
                    {prediction.insights.investment_rating}
                  </div>
                </div>
                <div className="bg-white/60 rounded-lg p-4 dark:bg-black/20">
                  <span className="text-sm text-gray-600 dark:text-white/70">Investment Score</span>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                    {prediction.insights.investment_score.toFixed(1)}/10
                  </div>
                </div>
                <div className="bg-white/60 rounded-lg p-4 dark:bg-black/20">
                  <span className="text-sm text-gray-600 dark:text-white/70">Time Series Weight</span>
                  <div className="text-xl font-bold text-blue-600 dark:text-blue-300 mt-2">
                    ${prediction.insights.time_series_contribution.toFixed(2)}
                  </div>
                </div>
                <div className="bg-white/60 rounded-lg p-4 dark:bg-black/20">
                  <span className="text-sm text-gray-600 dark:text-white/70">Feature Weight</span>
                  <div className="text-xl font-bold text-green-600 dark:text-green-300 mt-2">
                    ${prediction.insights.feature_contribution.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Model Info */}
          <div className="text-xs text-gray-500 dark:text-white/60 text-center pt-4 border-t border-gray-200 dark:border-white/10 space-y-1">
            <div>
              Prediction generated using <span className="font-semibold">{prediction.model_version}</span> •
              Target date: {new Date(prediction.target_date).toLocaleDateString()}
            </div>
            <div>
              Uses crypto/financial forecasting techniques: Exponential Smoothing + Monte Carlo (1,000 simulations)
            </div>
          </div>
        </div>
      )}

      {/* Initial State */}
      {!prediction && !isLoading && (
        <div className="text-center py-12 text-gray-500 dark:text-white/70">
          <Sparkles className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-white/40" />
          <p>Select a time frame and generate a prediction to see future price estimates</p>
        </div>
      )}
    </div>
  )
}
