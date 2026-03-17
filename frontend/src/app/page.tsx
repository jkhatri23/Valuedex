'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import Image from 'next/image'
import { useRouter, useSearchParams } from 'next/navigation'
import SearchBar from '@/components/SearchBar'
import CardDisplay from '@/components/CardDisplay'
import PriceChart from '@/components/PriceChart'
import PredictionPanel from '@/components/PredictionPanel'
import InvestmentRating from '@/components/InvestmentRating'
import ComparePanel from '@/components/ComparePanel'
import ThemeToggle from '@/components/ThemeToggle'
import { getCardDetails } from '@/lib/api'
import { Brain, Database, LineChart, Target } from 'lucide-react'

function CardIdListener({ onCardId }: { onCardId: (id: string) => void }) {
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    const cardId = searchParams.get('cardId')
    if (cardId) {
      onCardId(cardId)
      router.replace('/', { scroll: false })
    }
  }, [searchParams, router, onCardId])

  return null
}

function HomeContent() {
  const router = useRouter()
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [cardDetails, setCardDetails] = useState<any>(null)
  const [latestPrediction, setLatestPrediction] = useState<any>(null)
  const [featuredCards, setFeaturedCards] = useState<any[] | null>(null)

  const handleCardIdFromUrl = useCallback((cardId: string) => {
    getCardDetails(cardId).then((details) => {
      if (details) {
        setSelectedCard({
          id: details.id ?? details.external_id ?? cardId,
          name: details.name,
          set_name: details.set_name,
          current_price: details.current_price,
          image_url: details.image_url,
        })
      }
    })
  }, [])

  useEffect(() => {
    const fetchFeaturedCards = async () => {
      try {
        const cardIds = [
          'gym2-2',
          'base1-4',
          'base1-15',
          'neo1-4',
          'base1-2'
        ]
        
        const cardPromises = cardIds.map(id => 
          fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/cards/${id}`)
            .then(res => res.ok ? res.json() : null)
            .catch(() => null)
        )
        
        const cards = await Promise.all(cardPromises)
        const validCards = cards.filter(card => card !== null)
        
        if (validCards.length > 0) {
          setFeaturedCards(validCards)
        } else {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/cards/search?q=charizard&limit=5`)
          if (response.ok) {
            const data = await response.json()
            setFeaturedCards(data.slice(0, 5))
          } else {
            setFeaturedCards([])
          }
        }
      } catch (error) {
        console.error('Error fetching featured cards:', error)
        setFeaturedCards([])
      }
    }

    fetchFeaturedCards()
  }, [])

  const handleDetailsLoaded = useCallback((details: any) => {
    setCardDetails(details)
    if (details.current_price > 0) {
      setFeaturedCards((prev) =>
        prev
          ? prev.map((c) =>
              (c.id === selectedCard?.id || c.external_id === selectedCard?.id || c.id === selectedCard?.external_id)
                ? { ...c, current_price: details.current_price }
                : c
            )
          : prev
      )
    }
  }, [selectedCard?.id, selectedCard?.external_id])

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-[#0a0a0a] dark:via-[#0d0d0d] dark:to-[#0a0a0a] relative">
      {/* Isolated Suspense for useSearchParams - prevents entire page bailout */}
      <Suspense fallback={null}>
        <CardIdListener onCardId={handleCardIdFromUrl} />
      </Suspense>

      {/* Background - only on home */}
      {!selectedCard && (
        <div className="fixed inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
          <div 
            className="absolute inset-0 w-full h-full bg-cover bg-center bg-no-repeat opacity-40 dark:opacity-15"
            style={{ 
              backgroundImage: 'url(/hero-background.png)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: 'blur(2px)'
            }}
          />
          <div className="absolute inset-0 w-full h-full bg-gradient-to-b from-white/80 via-white/60 to-white/90 dark:from-[#0a0a0a]/80 dark:via-[#0a0a0a]/60 dark:to-[#0a0a0a]/90" />
        </div>
      )}

      {/* Header */}
      <header className="bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-gray-200 dark:border-white/10 sticky top-0 z-50 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <div className="flex items-center justify-between">
            {selectedCard ? (
              <button
                onClick={() => {
                  setSelectedCard(null)
                  setCardDetails(null)
                  setLatestPrediction(null)
                }}
                className="flex items-center space-x-2 cursor-pointer"
              >
                <div className="bg-black p-2 rounded-lg hover:scale-110 transition-transform duration-300">
                  <Image 
                    src="/logo.png" 
                    alt="Valuedex Logo" 
                    width={24} 
                    height={24}
                    className="w-6 h-6"
                  />
                </div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
                  Valuedex
                </h1>
              </button>
            ) : (
              <div className="flex items-center space-x-2">
                <div className="bg-black p-2 rounded-lg">
                  <Image 
                    src="/logo.png" 
                    alt="Valuedex Logo" 
                    width={24} 
                    height={24}
                    className="w-6 h-6"
                  />
                </div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
                  Valuedex
                </h1>
              </div>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {!selectedCard && (
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 pt-24 pb-16 md:pt-32 md:pb-20 relative" style={{ zIndex: 1 }}>
          {/* Decorative blurs */}
          <div className="hidden sm:block absolute top-20 left-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="hidden sm:block absolute bottom-20 right-10 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
          
          {/* Hero Text */}
          <div className="text-center mb-20 md:mb-24 relative z-10">
            <h2 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-gray-900 dark:text-white mb-8 md:mb-10 leading-[1.1] tracking-tight">
              <span className="inline-block">
                Predict Your Card&#39;s
              </span>
              <br />
              <span className="inline-block text-blue-500 dark:text-blue-400">
                Future Value
              </span>
            </h2>
          </div>

          {/* Search */}
          <div className="max-w-2xl mx-auto mb-16 md:mb-20">
            <SearchBar
              onSelectCard={(card) => setSelectedCard(card)}
              onSearch={(q) => router.push(`/search?q=${encodeURIComponent(q)}`)}
            />
          </div>

          {/* Featured Cards Gallery */}
          <div className="mb-20 md:mb-28">
            <div className="text-center mb-10">
              <h3 className="text-2xl sm:text-3xl font-medium text-gray-900 dark:text-white tracking-tight mb-2">Popular cards</h3>
              <p className="text-gray-500 dark:text-white/50 text-base">Click any card to see predictions</p>
            </div>

            {featuredCards === null ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
                {[0, 1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-white/60 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg p-5">
                    <div className="mb-4 rounded-lg bg-gray-200 dark:bg-white/10 aspect-[2.5/3.5] animate-pulse" />
                    <div className="h-4 bg-gray-200 dark:bg-white/10 rounded animate-pulse mb-2" />
                    <div className="h-3 bg-gray-200 dark:bg-white/10 rounded animate-pulse w-2/3 mb-3" />
                    <div className="h-5 bg-gray-200 dark:bg-white/10 rounded animate-pulse w-1/3" />
                  </div>
                ))}
              </div>
            ) : featuredCards.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
                {featuredCards.map((card, index) => (
                  <button
                    key={card.id}
                    onClick={() => setSelectedCard(card)}
                    className={`group bg-white/60 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-lg p-5 hover:scale-105 hover:border-gray-300 dark:hover:border-white/20 hover:shadow-xl transition-all duration-300 ${
                      index === featuredCards.length - 1 && featuredCards.length % 2 === 1 ? 'col-span-2 max-w-[calc(50%-0.75rem)] mx-auto md:col-span-1 md:max-w-none' : ''
                    }`}
                  >
                    {card.image_url && (
                      <div className="mb-4 rounded-lg overflow-hidden bg-gray-100 dark:bg-white/5 aspect-[2.5/3.5]">
                        <img
                          src={card.image_url}
                          alt={card.name}
                          className="w-full h-full object-contain"
                        />
                      </div>
                    )}
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors min-h-[2.5rem]">
                      {card.name}
                    </h4>
                    <p className="text-xs text-gray-500 dark:text-white/60 mb-3">{card.set_name}</p>
                    {card.current_price > 0 ? (
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        ${card.current_price.toFixed(2)}
                      </div>
                    ) : (
                      <div className="text-sm font-semibold text-gray-400 dark:text-white/40 italic">
                        Price Coming Soon
                      </div>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-white/50">
                <p className="mb-2">Unable to load featured cards</p>
                <p className="text-sm">Try searching for cards above</p>
              </div>
            )}
          </div>

          {/* How We Predict Section */}
          <div className="mb-20 md:mb-28">
            <div className="text-center mb-10">
              <h3 className="text-2xl sm:text-3xl font-medium text-gray-900 dark:text-white mb-2">How We Predict</h3>
              <p className="text-gray-500 dark:text-white/50 text-base max-w-xl mx-auto">
                Advanced forecasting with comprehensive risk analysis
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 md:gap-10 mb-14">
              <div className="bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md p-6 text-center">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mx-auto mb-3">
                  <LineChart className="w-6 h-6 text-blue-500 dark:text-blue-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-medium text-sm mb-1">Exponential Smoothing</h4>
                <p className="text-gray-500 dark:text-white/50 text-xs">Holt&#39;s method for trend detection</p>
              </div>

              <div className="bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md p-6 text-center">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mx-auto mb-3">
                  <Brain className="w-6 h-6 text-gray-500 dark:text-gray-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-medium text-sm mb-1">Monte Carlo Simulation</h4>
                <p className="text-gray-500 dark:text-white/50 text-xs">1,000 simulations for risk assessment</p>
              </div>

              <div className="bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md p-6 text-center">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mx-auto mb-3">
                  <Database className="w-6 h-6 text-green-500 dark:text-green-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-medium text-sm mb-1">VWAP Analysis</h4>
                <p className="text-gray-500 dark:text-white/50 text-xs">Volume-weighted market insights</p>
              </div>

              <div className="bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md p-6 text-center">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mx-auto mb-3">
                  <Target className="w-6 h-6 text-orange-500 dark:text-orange-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-medium text-sm mb-1">Multi-Scenario</h4>
                <p className="text-gray-500 dark:text-white/50 text-xs">Conservative to aggressive forecasts</p>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 mb-10">
              <div className="text-center p-5 bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md">
                <div className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">1,000+</div>
                <div className="text-xs text-gray-500 dark:text-white/50">Simulations</div>
              </div>
              <div className="text-center p-5 bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md">
                <div className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">3</div>
                <div className="text-xs text-gray-500 dark:text-white/50">Scenarios</div>
              </div>
              <div className="text-center p-5 bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md">
                <div className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">5 Years</div>
                <div className="text-xs text-gray-500 dark:text-white/50">Forecast</div>
              </div>
              <div className="text-center p-5 bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md">
                <div className="text-2xl font-semibold text-gray-900 dark:text-white mb-1">Live</div>
                <div className="text-xs text-gray-500 dark:text-white/50">Market Data</div>
              </div>
            </div>

            {/* Pipeline */}
            <div className="bg-white/50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-md p-6">
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 text-gray-900 dark:text-white flex-wrap">
                <div className="w-full sm:w-auto text-center bg-gray-100 dark:bg-white/5 px-5 py-2.5 rounded-md border border-gray-200 dark:border-white/10">
                  <p className="text-xs text-gray-500 dark:text-white/50 mb-0.5 uppercase tracking-wide">Step 1</p>
                  <p className="font-medium text-sm">Exponential Smoothing</p>
                </div>
                <div className="text-gray-400 hidden sm:block">&rarr;</div>
                <div className="w-full sm:w-auto text-center bg-gray-100 dark:bg-white/5 px-5 py-2.5 rounded-md border border-gray-200 dark:border-white/10">
                  <p className="text-xs text-gray-500 dark:text-white/50 mb-0.5 uppercase tracking-wide">Step 2</p>
                  <p className="font-medium text-sm">Monte Carlo (GBM)</p>
                </div>
                <div className="text-gray-400 hidden sm:block">&rarr;</div>
                <div className="w-full sm:w-auto text-center bg-gray-100 dark:bg-white/5 px-5 py-2.5 rounded-md border border-gray-200 dark:border-white/10">
                  <p className="text-xs text-gray-500 dark:text-white/50 mb-0.5 uppercase tracking-wide">Step 3</p>
                  <p className="font-medium text-sm">Market Factors</p>
                </div>
                <div className="text-gray-400 hidden sm:block">&rarr;</div>
                <div className="w-full sm:w-auto text-center bg-green-500 text-white px-5 py-2.5 rounded-md">
                  <p className="text-xs mb-0.5 uppercase tracking-wide opacity-80">Result</p>
                  <p className="font-medium text-sm">ML Prediction</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Card Details Section */}
      {selectedCard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative" style={{ zIndex: 1 }}>
          <div className="mb-6">
            <button
              onClick={() => {
                setSelectedCard(null)
                setCardDetails(null)
                setLatestPrediction(null)
              }}
              className="text-gray-600 hover:text-gray-900 dark:text-white/70 dark:hover:text-white font-medium flex items-center space-x-2 transition-colors min-h-[44px] py-2"
            >
              <span>&larr; Back to Search</span>
            </button>
          </div>
          
          <div className="bg-black/[0.02] dark:bg-white/[0.02] rounded-2xl p-4 sm:p-8 border border-black/[0.03] dark:border-white/[0.03]">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8 items-stretch">
              <div className="lg:col-span-1 flex">
                <div className="w-full">
                  <CardDisplay 
                    card={selectedCard} 
                    onDetailsLoaded={handleDetailsLoaded}
                  />
                </div>
              </div>

              <div className="lg:col-span-2 flex">
                {cardDetails && (
                  <div className="w-full [&>.card]:h-full">
                    <PriceChart 
                      cardId={selectedCard.id} 
                      cardName={selectedCard.name}
                      setName={selectedCard.set_name}
                    />
                  </div>
                )}
              </div>
            </div>

            {cardDetails && cardDetails.features && (
              <div className="mt-8">
                <InvestmentRating features={cardDetails.features} />
              </div>
            )}

            {cardDetails && (
              <div className="mt-8">
                <PredictionPanel 
                  cardId={selectedCard.id}
                  cardName={selectedCard.name}
                  currentPrice={cardDetails.current_price}
                  onPredictionGenerated={setLatestPrediction}
                />
              </div>
            )}

            {cardDetails && (
              <div className="mt-8">
                <ComparePanel
                  primaryCard={{
                    id: selectedCard.id,
                    name: cardDetails.name || selectedCard.name,
                    set_name: cardDetails.set_name || selectedCard.set_name,
                    image_url: cardDetails.image_url || selectedCard.image_url,
                    current_price: cardDetails.current_price,
                    features: cardDetails.features,
                  }}
                  primaryPrediction={latestPrediction}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white/50 dark:bg-[#0a0a0a]/50 backdrop-blur-sm border-t border-gray-200 dark:border-white/10 mt-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <p className="text-gray-600 dark:text-white/70 mb-3 font-light">
              Data powered by eBay API &amp; Pokemon TCG API &bull; Predictions by Advanced ML Models
            </p>
            <p className="text-sm text-gray-500 dark:text-white/50 font-light max-w-3xl mx-auto mb-6">
              For entertainment and educational purposes only. Not financial advice. 
              This site is not affiliated with, endorsed, or sponsored by The Pok&eacute;mon Company International, Nintendo, or Game Freak.
            </p>
            <div className="flex items-center justify-center space-x-1 text-sm text-gray-500 dark:text-white/50 font-light">
              <span>Follow us on Twitter</span>
              <a href="https://twitter.com/jordankhatri23" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 font-medium">@jordankhatri23</a>
              <span>&amp;</span>
              <a href="https://twitter.com/joeylu06" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 font-medium">@joeylu06</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}

export default function Home() {
  return <HomeContent />
}
