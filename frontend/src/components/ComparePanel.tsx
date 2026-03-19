'use client'

import { useState, useEffect, useRef } from 'react'
import { searchCards, getCardDetails, getPrediction, getPriceHistory, Card, CardDetails, CardCondition, Prediction } from '@/lib/api'
import { GitCompareArrows, Search, Loader2, Sparkles, X } from 'lucide-react'

const GRADE_OPTIONS: CardCondition[] = ['Ungraded', 'PSA 6', 'PSA 7', 'PSA 8', 'PSA 9', 'PSA 10']

interface ComparePanelProps {
  primaryCard: {
    id: string
    name: string
    set_name: string
    image_url?: string
    current_price: number
    features?: CardDetails['features']
  }
  primaryPrediction: Prediction | null
  primaryGrade?: string
  primaryGradePrice?: number
}

function RatingBadge({ rating }: { rating: string }) {
  const colorClass = (() => {
    switch (rating) {
      case 'Strong Buy': return 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-200'
      case 'Buy': return 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200'
      case 'Hold': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-200'
      case 'Underperform': return 'bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-200'
      case 'Sell': return 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-500/20 dark:text-gray-200'
    }
  })()
  return <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${colorClass}`}>{rating}</span>
}

function formatRecommendation(rec: string) {
  return rec.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function RecommendationBadge({ rec }: { rec: string }) {
  const colorClass = (() => {
    switch (rec) {
      case 'strong_buy': return 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-200'
      case 'buy': return 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200'
      case 'hold': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-200'
      case 'consider_selling': return 'bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-200'
      case 'sell': return 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-500/20 dark:text-gray-200'
    }
  })()
  return <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${colorClass}`}>{formatRecommendation(rec)}</span>
}

interface CardColumnProps {
  label: string
  name: string
  setName: string
  imageUrl?: string
  price: number
  grade?: string
  features?: CardDetails['features']
  prediction: Prediction | null
}

function CardColumn({ label, name, setName, imageUrl, price, grade, features, prediction }: CardColumnProps) {
  return (
    <div className="flex-1 min-w-0 space-y-4">
      <div className="text-xs font-medium text-gray-500 dark:text-white/50 uppercase tracking-wider">{label}</div>

      {/* Card identity */}
      <div className="flex items-center space-x-3">
        {imageUrl ? (
          <img src={imageUrl} alt={name} className="w-16 h-22 object-contain rounded-lg shadow-sm flex-shrink-0" />
        ) : (
          <div className="w-16 h-22 bg-gray-100 dark:bg-white/10 rounded-lg flex items-center justify-center text-gray-400 text-xs flex-shrink-0">
            No img
          </div>
        )}
        <div className="min-w-0">
          <div className="font-semibold text-gray-900 dark:text-white truncate">{name}</div>
          <div className="text-sm text-gray-500 dark:text-white/60 truncate">{setName}</div>
        </div>
      </div>

      {/* Current price */}
      <div className="bg-white/30 dark:bg-white/[0.02] border border-gray-100/50 dark:border-white/[0.04] rounded-lg p-4">
        <div className="text-xs text-gray-500 dark:text-white/60 mb-1">
          Current Price{grade ? ` (${grade})` : ''}
        </div>
        {price === -1 ? (
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            <span className="text-sm text-gray-400">Loading price...</span>
          </div>
        ) : price > 0 ? (
          <div className="text-2xl font-bold text-gray-900 dark:text-white">${price.toFixed(2)}</div>
        ) : (
          <div className="text-lg font-semibold text-gray-400 dark:text-white/40 italic">Not available</div>
        )}
      </div>

      {/* Investment rating */}
      <div className="bg-white/30 dark:bg-white/[0.02] border border-gray-100/50 dark:border-white/[0.04] rounded-lg p-4">
        <div className="text-xs text-gray-500 dark:text-white/60 mb-2">Investment Rating</div>
        {features ? (
          <div className="space-y-2">
            <RatingBadge rating={features.investment_rating} />
            <div className="text-lg font-bold text-gray-900 dark:text-white">{features.investment_score.toFixed(1)}/10</div>
          </div>
        ) : (
          <div className="text-sm text-gray-400 dark:text-white/40 italic">Not available</div>
        )}
      </div>

      {/* Prediction results */}
      <div className="bg-white/30 dark:bg-white/[0.02] border border-gray-100/50 dark:border-white/[0.04] rounded-lg p-4">
        <div className="text-xs text-gray-500 dark:text-white/60 mb-2">Prediction</div>
        {prediction ? (
          <div className="space-y-3">
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                ${prediction.predicted_price.toFixed(2)}
              </div>
              <div className={`text-sm font-medium ${prediction.growth_rate >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {prediction.growth_rate >= 0 ? '+' : ''}{prediction.growth_rate.toFixed(1)}% growth
              </div>
            </div>
            <RecommendationBadge rec={prediction.recommendation} />
            <div className="text-xs text-gray-500 dark:text-white/60">
              Risk: {prediction.risk_assessment.risk_level.toUpperCase()}
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-400 dark:text-white/40 italic">Generate below</div>
        )}
      </div>
    </div>
  )
}

export default function ComparePanel({ primaryCard, primaryPrediction, primaryGrade, primaryGradePrice }: ComparePanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Card[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  const [compCard, setCompCard] = useState<Card | null>(null)
  const [compDetails, setCompDetails] = useState<CardDetails | null>(null)
  const [compLoading, setCompLoading] = useState(false)

  const [compGrade, setCompGrade] = useState<CardCondition>('Ungraded')
  const [compGradePrice, setCompGradePrice] = useState<number>(0)
  const [gradePriceLoading, setGradePriceLoading] = useState(false)

  const [yearsAhead, setYearsAhead] = useState(3)
  const [compPrediction, setCompPrediction] = useState<Prediction | null>(null)
  const [predLoading, setPredLoading] = useState(false)

  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
        setIsSearching(true)
        const results = await searchCards(query)
        setSearchResults(results.filter(c => c.id !== primaryCard.id))
        setIsSearching(false)
        setShowDropdown(true)
      } else {
        setSearchResults([])
        setShowDropdown(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, primaryCard.id])

  // Fetch comparison card details when selected
  useEffect(() => {
    if (!compCard) return
    let cancelled = false
    setCompLoading(true)
    setCompPrediction(null)
    getCardDetails(compCard.id).then(details => {
      if (!cancelled && details) setCompDetails(details)
      setCompLoading(false)
    })
    return () => { cancelled = true }
  }, [compCard])

  // Fetch grade-specific price when comparison card grade changes
  useEffect(() => {
    if (!compCard || !compDetails) return
    setCompPrediction(null)

    if (compGrade === 'Ungraded') {
      setCompGradePrice(compDetails.current_price)
      return
    }

    let cancelled = false
    setGradePriceLoading(true)
    getPriceHistory(compCard.id, compGrade, compCard.name, compCard.set_name).then(history => {
      if (cancelled) return
      const lastPrice = history.length > 0 ? history[history.length - 1].price : 0
      setCompGradePrice(lastPrice > 0 ? lastPrice : compDetails.current_price)
      setGradePriceLoading(false)
    })
    return () => { cancelled = true }
  }, [compGrade, compCard, compDetails])

  const handleSelectComp = (card: Card) => {
    setCompCard(card)
    setQuery('')
    setSearchResults([])
    setShowDropdown(false)
  }

  const handleRemoveComp = () => {
    setCompCard(null)
    setCompDetails(null)
    setCompPrediction(null)
    setCompGrade('Ungraded')
    setCompGradePrice(0)
  }

  const handleGenerate = async () => {
    if (!compCard) return
    setPredLoading(true)
    const effectivePrice = compGradePrice > 0 ? compGradePrice : compDetails?.current_price || 0
    const result = await getPrediction(compCard.id, yearsAhead, compCard.name, compGrade, effectivePrice)
    if (result) setCompPrediction(result)
    setPredLoading(false)
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full btn-secondary flex items-center justify-center space-x-2 py-4"
      >
        <GitCompareArrows className="w-5 h-5" />
        <span>Compare with another card</span>
      </button>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <GitCompareArrows className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">Compare Cards</h3>
        </div>
        <button onClick={() => { setIsOpen(false); handleRemoveComp() }} title="Close comparison" className="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Search for comparison card */}
      {!compCard && (
        <div ref={dropdownRef} className="relative mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              {isSearching ? (
                <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
              ) : (
                <Search className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search for a card to compare..."
              autoFocus
              className="w-full pl-12 pr-4 py-3 text-sm border border-gray-200 dark:border-white/10 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-gray-900 placeholder:text-gray-400 bg-white dark:bg-[#1a1a1a] dark:text-white dark:placeholder:text-gray-500"
            />
          </div>

          {showDropdown && searchResults.length > 0 && (
            <div className="absolute w-full mt-2 bg-white/95 dark:bg-[#0a0a0a]/95 backdrop-blur-md rounded-lg shadow-xl border border-gray-200 dark:border-white/10 max-h-72 overflow-y-auto z-50">
              {searchResults.map(card => (
                <button
                  key={card.id}
                  onClick={() => handleSelectComp(card)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-white/5 border-b border-gray-100 dark:border-white/5 last:border-b-0 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {card.image_url && (
                      <img src={card.image_url} alt={card.name} className="w-10 h-14 object-contain rounded" />
                    )}
                    <div className="min-w-0">
                      <div className="font-medium text-gray-900 dark:text-white truncate">{card.name}</div>
                      <div className="text-xs text-gray-500 dark:text-white/60">{card.set_name}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading comparison card details */}
      {compCard && compLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400 mr-3" />
          <span className="text-gray-500 dark:text-white/60">Loading card details...</span>
        </div>
      )}

      {/* Side-by-side comparison */}
      {compCard && compDetails && !compLoading && (
        <div className="space-y-6">
          {/* Controls row */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700 dark:text-white/70">Predict:</span>
              {[1, 2, 3, 5].map(year => (
                <button
                  key={year}
                  onClick={() => { setYearsAhead(year); setCompPrediction(null) }}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    yearsAhead === year
                      ? 'bg-gray-800 dark:bg-gray-600 text-white'
                      : 'bg-gray-50/50 text-gray-700 hover:bg-gray-100/50 border border-gray-200/50 dark:bg-white/[0.03] dark:text-white/70 dark:hover:bg-white/[0.06] dark:border-white/[0.04]'
                  }`}
                >
                  {year}yr
                </button>
              ))}
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500 dark:text-white/60">Comparison Grade:</span>
                <select
                  value={compGrade}
                  aria-label="Select comparison card grade"
                  onChange={e => { setCompGrade(e.target.value as CardCondition) }}
                  className="text-sm px-2 py-1.5 rounded-lg border border-gray-200/50 bg-white/50 dark:bg-white/5 dark:border-white/10 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                >
                  {GRADE_OPTIONS.map(g => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <button onClick={handleGenerate} disabled={predLoading || gradePriceLoading} className="btn-primary flex items-center space-x-2 text-sm py-2 px-4">
                {predLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>{predLoading ? 'Analyzing...' : 'Generate Prediction'}</span>
              </button>
              <button onClick={handleRemoveComp} className="btn-secondary text-sm py-2 px-3">
                Change card
              </button>
            </div>
          </div>

          {/* Two columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <CardColumn
              label="Your card"
              name={primaryCard.name}
              setName={primaryCard.set_name}
              imageUrl={primaryCard.image_url}
              price={primaryGradePrice && primaryGradePrice > 0 ? primaryGradePrice : primaryCard.current_price}
              grade={primaryGrade || 'Ungraded'}
              features={primaryCard.features}
              prediction={primaryPrediction}
            />
            <CardColumn
              label="Comparison"
              name={compDetails.name}
              setName={compDetails.set_name}
              imageUrl={compDetails.image_url}
              price={gradePriceLoading ? -1 : compGradePrice}
              grade={compGrade}
              features={compDetails.features}
              prediction={compPrediction}
            />
          </div>
        </div>
      )}
    </div>
  )
}
