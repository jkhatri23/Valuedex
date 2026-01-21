'use client'

import { useEffect, useState } from 'react'
import { getPriceHistory, getAllGradesHistory, PriceHistory, CardCondition, AllGradesHistory, GradeAnalysis } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Loader2, BarChart3, Award, Scale } from 'lucide-react'

interface PriceChartProps {
  cardId: string
  cardName?: string
  setName?: string
}

// Colors for different grades
const GRADE_COLORS: Record<string, string> = {
  'Near Mint': '#6366f1',
  'PSA 1': '#ef4444',
  'PSA 2': '#f97316',
  'PSA 3': '#f59e0b',
  'PSA 4': '#eab308',
  'PSA 5': '#84cc16',
  'PSA 6': '#22c55e',
  'PSA 7': '#10b981',
  'PSA 8': '#14b8a6',
  'PSA 9': '#06b6d4',
  'PSA 10': '#8b5cf6',
}

// Helper to prepare chart data for all grades
function _prepareAllGradesChartData(data: AllGradesHistory): any[] {
  const dateMap: Record<string, any> = {}
  
  // Collect all dates and prices by grade
  Object.entries(data.grades).forEach(([grade, gradeData]) => {
    gradeData.history.forEach((point) => {
      const dateKey = point.date.substring(0, 7) // YYYY-MM
      if (!dateMap[dateKey]) {
        dateMap[dateKey] = { date: dateKey }
      }
      dateMap[dateKey][grade] = point.price
    })
  })
  
  // Sort by date and return
  return Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date))
}

export default function PriceChart({ cardId, cardName, setName }: PriceChartProps) {
  const [priceData, setPriceData] = useState<PriceHistory[]>([])
  const [allGradesData, setAllGradesData] = useState<AllGradesHistory | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [condition, setCondition] = useState<CardCondition>('Near Mint')
  const [viewMode, setViewMode] = useState<'single' | 'all'>('single')  // Default to ungraded view

  useEffect(() => {
    const fetchPrices = async () => {
      setIsLoading(true)
      
      if (viewMode === 'all' && cardName) {
        // Fetch all grades history
        const allData = await getAllGradesHistory(cardId, cardName, setName)
        setAllGradesData(allData)
        setPriceData([])
      } else {
        // Fetch single grade
        const data = await getPriceHistory(cardId, condition, cardName, setName)
        setPriceData(data)
        setAllGradesData(null)
      }
      
      setIsLoading(false)
    }

    fetchPrices()
  }, [cardId, condition, cardName, setName, viewMode])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  // All grades view
  if (viewMode === 'all' && allGradesData) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <BarChart3 className="w-6 h-6 text-purple-500" />
            <div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                All PSA Grades Analysis
              </h3>
              <p className="text-xs text-gray-500 dark:text-white/60">
                12-month price history for all grades • eBay data
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('single')}
              className="text-sm px-3 py-1.5 rounded-md border border-gray-300 bg-white dark:bg-[#111] dark:border-white/20 dark:text-white hover:bg-gray-50 dark:hover:bg-white/10"
            >
              Single Grade
            </button>
            <button
              className="text-sm px-3 py-1.5 rounded-md bg-purple-600 text-white"
            >
              All Grades
            </button>
          </div>
        </div>

        {/* Recommendations Banner */}
        {allGradesData.recommendations && (
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/20">
            <div className="flex items-center space-x-2 mb-3">
              <Award className="w-5 h-5 text-purple-500" />
              <span className="font-semibold text-gray-900 dark:text-white">Investment Recommendations</span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-white/60">Best Value:</span>
                <span className="ml-2 font-semibold text-purple-600 dark:text-purple-400">
                  {allGradesData.recommendations.best_value || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-white/60">Best Growth:</span>
                <span className="ml-2 font-semibold text-green-600 dark:text-green-400">
                  {allGradesData.recommendations.best_growth || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-white/60">Most Liquid:</span>
                <span className="ml-2 font-semibold text-blue-600 dark:text-blue-400">
                  {allGradesData.recommendations.most_liquid || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Multi-line chart for all grades */}
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={_prepareAllGradesChartData(allGradesData)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '11px' }} />
            <YAxis stroke="#9ca3af" style={{ fontSize: '11px' }} tickFormatter={(v) => `$${v >= 1000 ? (v/1000).toFixed(0) + 'k' : v}`} />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(0,0,0,0.9)', border: 'none', borderRadius: '8px' }}
              labelStyle={{ color: '#fff' }}
              formatter={(value: any, name: string) => [`$${Number(value).toLocaleString()}`, name]}
            />
            <Legend />
            {Object.keys(allGradesData.grades).map((grade) => (
              <Line
                key={grade}
                type="monotone"
                dataKey={grade}
                stroke={GRADE_COLORS[grade] || '#888'}
                strokeWidth={grade === 'PSA 10' || grade === 'PSA 9' ? 2.5 : 1.5}
                dot={false}
                name={grade}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* PriceCharting Comparison */}
        {allGradesData.pricecharting_comparison && (
          <div className="mt-6 p-4 bg-gradient-to-r from-amber-500/10 to-orange-500/10 rounded-lg border border-amber-500/20">
            <div className="flex items-center space-x-2 mb-3">
              <Scale className="w-5 h-5 text-amber-500" />
              <span className="font-semibold text-gray-900 dark:text-white">PriceCharting Comparison</span>
              <span className="text-xs text-gray-500 dark:text-white/50 ml-2">
                ({allGradesData.pricecharting_comparison.product_name})
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-white/60">Loose (Raw):</span>
                <span className="ml-2 font-semibold text-amber-600 dark:text-amber-400">
                  ${allGradesData.pricecharting_comparison.loose_price.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-white/60">CIB (Graded):</span>
                <span className="ml-2 font-semibold text-orange-600 dark:text-orange-400">
                  ${allGradesData.pricecharting_comparison.cib_price.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-white/60">New (Sealed):</span>
                <span className="ml-2 font-semibold text-red-600 dark:text-red-400">
                  ${allGradesData.pricecharting_comparison.new_price.toLocaleString()}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-white/40 mt-2">
              {allGradesData.pricecharting_comparison.description}
            </p>
          </div>
        )}

        {/* Grade Analysis Table */}
        {allGradesData.recommendations?.analysis && (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-white/10">
                  <th className="text-left py-2 px-2 text-gray-600 dark:text-white/70">Grade</th>
                  <th className="text-right py-2 px-2 text-gray-600 dark:text-white/70">Price</th>
                  <th className="text-right py-2 px-2 text-gray-600 dark:text-white/70">12M Change</th>
                  <th className="text-right py-2 px-2 text-gray-600 dark:text-white/70">Rating</th>
                </tr>
              </thead>
              <tbody>
                {allGradesData.recommendations.analysis.map((item: GradeAnalysis) => (
                  <tr key={item.grade} className="border-b border-gray-100 dark:border-white/5">
                    <td className="py-2 px-2 font-medium" style={{ color: GRADE_COLORS[item.grade] }}>
                      {item.grade}
                    </td>
                    <td className="text-right py-2 px-2 text-gray-900 dark:text-white">
                      ${item.current_price.toLocaleString()}
                    </td>
                    <td className={`text-right py-2 px-2 font-medium ${item.growth_12m >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {item.growth_12m >= 0 ? '+' : ''}{item.growth_12m.toFixed(1)}%
                    </td>
                    <td className="text-right py-2 px-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        item.rating === 'Strong Buy' ? 'bg-green-500/20 text-green-600' :
                        item.rating === 'Buy' ? 'bg-emerald-500/20 text-emerald-600' :
                        item.rating === 'Hold' ? 'bg-yellow-500/20 text-yellow-600' :
                        item.rating === 'Underperform' ? 'bg-orange-500/20 text-orange-600' :
                        'bg-red-500/20 text-red-600'
                      }`}>
                        {item.rating}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  // If there's no data for this selection, show a friendly message
  if (!isLoading && priceData.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              Price History
            </h3>
            <p className="text-xs text-gray-500 dark:text-white/60">
              Condition: {condition}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium text-gray-600 dark:text-white/70">
              Condition
            </span>
            <select
              value={condition}
              aria-label="Select card condition"
              onChange={(e) =>
                setCondition(e.target.value as CardCondition)
              }
              className="text-sm px-3 py-1.5 rounded-md border border-gray-300 bg-white dark:bg-[#111] dark:border-white/20 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Near Mint">Near Mint</option>
              <option value="PSA 6">PSA 6</option>
              <option value="PSA 7">PSA 7</option>
              <option value="PSA 8">PSA 8</option>
              <option value="PSA 9">PSA 9</option>
              <option value="PSA 10">PSA 10</option>
            </select>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-gray-600 dark:text-white/70 font-medium mb-2">
            No price data available for this condition yet.
          </p>
          <p className="text-sm text-gray-500 dark:text-white/60">
            Try a different condition, or select Near Mint.
          </p>
        </div>
      </div>
    )
  }

  // Check data source for display
  const hasEstimatedData = priceData.some((p: any) => p.source === 'ebay_estimated')
  const hasHistoricalData = priceData.some((p: any) => p.source === 'ebay_historical')

  // Format data for chart
  const chartData = priceData.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    dateLabel: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    isoDate: item.date,
    price: item.price,
    source: item.source || 'unknown',
  }))

  // Calculate price change
  const firstPrice = priceData[0]?.price || 0
  const lastPrice = priceData[priceData.length - 1]?.price || 0
  const priceChange = lastPrice - firstPrice
  const priceChangePercent = firstPrice > 0 ? (priceChange / firstPrice) * 100 : 0

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          {priceChange >= 0 ? (
            <TrendingUp className="w-6 h-6 text-green-600" />
          ) : (
            <TrendingDown className="w-6 h-6 text-red-600" />
          )}
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              Price History
            </h3>
            <p className="text-xs text-gray-500 dark:text-white/60">
              {condition === 'All'
                ? 'Loose / market price trend'
                : `Condition: ${condition}`}
              {hasHistoricalData && ' • eBay sold data'}
              {hasEstimatedData && !hasHistoricalData && ' • Estimated trend'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="hidden sm:block text-right">
            <div
              className={`text-2xl font-bold ${
                priceChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {priceChange >= 0 ? '+' : ''}
              {priceChangePercent.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 dark:text-white/70">
              12 Month Change
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={condition}
              aria-label="Select card condition"
              onChange={(e) =>
                setCondition(e.target.value as CardCondition)
              }
              className="text-sm px-3 py-1.5 rounded-md border border-gray-300 bg-white dark:bg-[#111] dark:border-white/20 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Near Mint">Near Mint</option>
              <option value="PSA 6">PSA 6</option>
              <option value="PSA 7">PSA 7</option>
              <option value="PSA 8">PSA 8</option>
              <option value="PSA 9">PSA 9</option>
              <option value="PSA 10">PSA 10</option>
            </select>
            {cardName && (
              <button
                onClick={() => setViewMode('all')}
                className="text-sm px-3 py-1.5 rounded-md bg-purple-600 text-white hover:bg-purple-700"
              >
                All Grades
              </button>
            )}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
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
            labelFormatter={() => ''}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null
              const point = payload[0].payload as any
              const sourceLabel = point.source === 'ebay_historical' ? 'eBay Sold' 
                : point.source === 'ebay_estimated' ? 'Estimated'
                : point.source === 'database' ? 'Historical'
                : 'Market';
              return (
                <div className="p-3">
                  <div className="text-sm font-semibold text-gray-900">Price: ${point.price?.toFixed(2)}</div>
                  <div className="text-xs text-gray-600">{point.dateLabel}</div>
                  <div className="text-xs text-gray-500">{sourceLabel}</div>
                </div>
              )
            }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5 }}
            name="Market Price"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-white/10">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${firstPrice.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 dark:text-white/70 mt-1">
              12 Months Ago
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              ${lastPrice.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 dark:text-white/70 mt-1">
              Current Price
            </div>
          </div>
          <div>
            <div
              className={`text-2xl font-bold ${
                priceChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {priceChange >= 0 ? '+' : ''}
              ${Math.abs(priceChange).toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 dark:text-white/70 mt-1">
              Change
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
