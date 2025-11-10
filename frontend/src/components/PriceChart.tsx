'use client'

import { useEffect, useState } from 'react'
import { getPriceHistory, PriceHistory } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react'

interface PriceChartProps {
  cardId: string
}

export default function PriceChart({ cardId }: PriceChartProps) {
  const [priceData, setPriceData] = useState<PriceHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchPrices = async () => {
      setIsLoading(true)
      const data = await getPriceHistory(cardId)
      setPriceData(data)
      setIsLoading(false)
    }

    fetchPrices()
  }, [cardId])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  // Format data for chart
  const chartData = priceData.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    price: item.price,
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
          <h3 className="text-2xl font-bold text-gray-900">Price History</h3>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {priceChange >= 0 ? '+' : ''}{priceChangePercent.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">12 Month Change</div>
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

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">${firstPrice.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">12 Months Ago</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">${lastPrice.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">Current Price</div>
          </div>
          <div>
            <div className={`text-2xl font-bold ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {priceChange >= 0 ? '+' : ''}${Math.abs(priceChange).toFixed(2)}
            </div>
            <div className="text-sm text-gray-500 mt-1">Change</div>
          </div>
        </div>
      </div>
    </div>
  )
}
