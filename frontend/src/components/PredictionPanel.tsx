'use client'

import { useState } from 'react'
import { getPrediction, Prediction } from '@/lib/api'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Sparkles, Loader2, TrendingUp, AlertCircle } from 'lucide-react'

interface PredictionPanelProps {
  cardId: string
  cardName: string
  currentPrice: number
}

export default function PredictionPanel({ cardId, cardName, currentPrice }: PredictionPanelProps) {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [yearsAhead, setYearsAhead] = useState(3)

  const handlePredict = async () => {
    setIsLoading(true)
    const result = await getPrediction(cardId, yearsAhead)
    if (result) {
      setPrediction(result)
    }
    setIsLoading(false)
  }

  // Prepare chart data
  const chartData = prediction
    ? [
        { year: 'Now', price: currentPrice, lower: currentPrice, upper: currentPrice },
        ...prediction.timeline.map((item) => ({
          year: `+${item.years_ahead}yr`,
          price: item.predicted_price,
          lower: prediction.confidence_lower,
          upper: prediction.confidence_upper,
        })),
      ]
    : []

  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-6">
        <Sparkles className="w-6 h-6 text-purple-600" />
        <h3 className="text-2xl font-bold text-white">Future Price Prediction</h3>
      </div>

      {/* Prediction Controls */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6 mb-6">
        <label className="block text-sm font-medium text-white mb-3">
          Predict price in how many years?
        </label>
        <div className="flex items-center space-x-3 mb-4">
          {[1, 2, 3, 5].map((year) => (
            <button
              key={year}
              onClick={() => setYearsAhead(year)}
              className={`px-5 py-2.5 rounded-lg font-medium transition-all ${
                yearsAhead === year
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md'
                  : 'bg-white/10 text-white/70 hover:bg-white/20 border border-white/20'
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
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-center">
              <div className="text-sm text-white/70 mb-1">Current Price</div>
              <div className="text-3xl font-bold text-blue-300">
                ${prediction.current_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-center">
              <div className="text-sm text-white/70 mb-1">
                Predicted ({yearsAhead}yr)
              </div>
              <div className="text-3xl font-bold text-purple-300">
                ${prediction.predicted_price.toFixed(2)}
              </div>
            </div>
            <div className="rounded-lg p-4 text-center bg-white/5 border border-white/10">
              <div className="text-sm text-white/70 mb-1">Expected Growth</div>
              <div className={`text-3xl font-bold flex items-center justify-center ${
                prediction.growth_rate >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                <TrendingUp className="w-5 h-5 mr-1" />
                {prediction.growth_rate >= 0 ? '+' : ''}{prediction.growth_rate.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Confidence Range */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-white">Confidence Range</span>
              <AlertCircle className="w-4 h-4 text-gray-400" />
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-white/70 font-medium">
                ${prediction.confidence_lower.toFixed(2)}
              </span>
              <div className="flex-1 h-2 bg-gradient-to-r from-red-300 via-yellow-300 to-green-300 rounded-full"></div>
              <span className="text-white/70 font-medium">
                ${prediction.confidence_upper.toFixed(2)}
              </span>
            </div>
            <div className="text-center mt-2">
              <span className="text-xs text-white/60">
                95% confidence interval
              </span>
            </div>
          </div>

          {/* Timeline Chart */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Price Projection Timeline</h4>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
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
                  formatter={(value: any) => [`$${value.toFixed(2)}`, 'Price']}
                />
                <Area 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#8b5cf6" 
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                  name="Predicted Price"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Investment Insights */}
          {prediction.insights && (
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-4">AI Insights</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-white">Investment Rating</span>
                  <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${
                    prediction.insights.investment_rating === 'Strong Buy' 
                      ? 'bg-green-500/20 text-green-200'
                      : prediction.insights.investment_rating === 'Buy'
                      ? 'bg-blue-500/20 text-blue-200'
                      : prediction.insights.investment_rating === 'Hold'
                      ? 'bg-yellow-500/20 text-yellow-200'
                      : 'bg-red-500/20 text-red-200'
                  }`}>
                    {prediction.insights.investment_rating}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium text-white">Investment Score</span>
                  <span className="font-bold text-purple-600">
                    {prediction.insights.investment_score}/10
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Model Info */}
          <div className="text-xs text-white/60 text-center pt-4 border-t border-white/10">
            Prediction generated using {prediction.model_version} • 
            Target date: {new Date(prediction.target_date).toLocaleDateString()}
          </div>
        </div>
      )}

      {/* Initial State */}
      {!prediction && !isLoading && (
        <div className="text-center py-12 text-white/70">
          <Sparkles className="w-16 h-16 mx-auto mb-4 text-white/40" />
          <p>Select a time frame and generate a prediction to see future price estimates</p>
        </div>
      )}
    </div>
  )
}
