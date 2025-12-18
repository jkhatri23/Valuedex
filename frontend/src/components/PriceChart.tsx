'use client'

import { useEffect, useState } from 'react'
import { getPriceHistory, PriceHistory, CardCondition } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react'

interface PriceChartProps {
  cardId: string
}

export default function PriceChart({ cardId }: PriceChartProps) {
  const [priceData, setPriceData] = useState<PriceHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [condition, setCondition] = useState<CardCondition>('Near Mint')

  useEffect(() => {
    const fetchPrices = async () => {
      setIsLoading(true)
      const data = await getPriceHistory(cardId, condition)
      setPriceData(data)
      setIsLoading(false)
    }

    fetchPrices()
  }, [cardId, condition])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  // If there's no data for this selection, show a friendly message instead of
  // trying to reuse loose history.
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
            Try a different condition, or select All / Loose.
          </p>
        </div>
      </div>
    )
  }

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
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-6">
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
              return (
                <div className="p-3">
                  <div className="text-sm font-semibold text-gray-900">Price: ${point.price?.toFixed(2)}</div>
                  <div className="text-xs text-gray-600">{point.dateLabel}</div>
                  <div className="text-xs text-gray-600">Source: {point.source}</div>
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
