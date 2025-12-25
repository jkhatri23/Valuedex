'use client'

import { useState } from 'react'
import Image from 'next/image'
import SearchBar from '@/components/SearchBar'
import CardDisplay from '@/components/CardDisplay'
import PriceChart from '@/components/PriceChart'
import PredictionPanel from '@/components/PredictionPanel'
import InvestmentRating from '@/components/InvestmentRating'
import ThemeToggle from '@/components/ThemeToggle'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { TrendingUp, Search, Brain, Database, LineChart, Target } from 'lucide-react'

export default function Home() {
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [cardDetails, setCardDetails] = useState<any>(null)
  const [latestPrediction, setLatestPrediction] = useState<any>(null)
  
  // Scroll animation hooks for different sections
  const statsAnimation = useScrollAnimation({ threshold: 0.2 })
  const featuresAnimation = useScrollAnimation({ threshold: 0.15 })
  const techStackAnimation = useScrollAnimation({ threshold: 0.2 })
  const footerAnimation = useScrollAnimation({ threshold: 0.3 })

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-[#0a0a0a] dark:via-[#0d0d0d] dark:to-[#0a0a0a] relative">
      {/* Full-Width Background Image and Gradient - Only shown when no card is selected */}
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
          {/* Gradient Overlay */}
          <div className="absolute inset-0 w-full h-full bg-gradient-to-b from-white/80 via-white/60 to-white/90 dark:from-[#0a0a0a]/80 dark:via-[#0a0a0a]/60 dark:to-[#0a0a0a]/90" />
        </div>
      )}

      {/* Header */}
      <header className="bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-gray-200 dark:border-white/10 sticky top-0 z-50 animate-slide-up relative" style={{ animationDelay: '0ms', opacity: 0, animationFillMode: 'forwards' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-black p-3 rounded-xl hover:scale-110 transition-transform duration-300">
                <Image 
                  src="/logo.png" 
                  alt="Valuedex Logo" 
                  width={32} 
                  height={32}
                  className="w-8 h-8"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
                  Valuedex
                </h1>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

         

      {/* Hero Section */}
      {!selectedCard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative" style={{ zIndex: 1 }}>
          {/* Decorative Background Elements */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
          
          {/* Main Hero */}
          <div className="text-center mb-16 animate-fade-in relative z-10">
            <h2 className="text-6xl md:text-7xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
              <span className="inline-block animate-slide-up" style={{ animationDelay: '100ms', opacity: 0, animationFillMode: 'forwards' }}>
                Predict Your Card's
              </span>
              <br />
              <span className="inline-block bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent animate-slide-up" style={{ animationDelay: '300ms', opacity: 0, animationFillMode: 'forwards' }}>
                Future Value
              </span>
            </h2>
            <p className="text-xl md:text-2xl text-gray-600 dark:text-white/70 mb-12 max-w-3xl mx-auto font-light animate-slide-up" style={{ animationDelay: '500ms', opacity: 0, animationFillMode: 'forwards' }}>
              Advanced forecasting meets Pokémon TCG. 
              Discover what your cards could be worth tomorrow.
            </p>
          </div>

          {/* Search Section */}
          <div className="max-w-3xl mx-auto mb-12 animate-slide-up relative z-10" style={{ animationDelay: '200ms', opacity: 0, animationFillMode: 'forwards' }}>
            <SearchBar onSelectCard={(card) => setSelectedCard(card)} />
          </div>

          {/* Scroll Indicator */}
          <div className="flex justify-center mb-20 animate-bounce">
            <div className="flex flex-col items-center text-gray-400 dark:text-gray-600 animate-fade-in" style={{ animationDelay: '1s', opacity: 0, animationFillMode: 'forwards' }}>
              <span className="text-sm font-medium mb-2">Scroll to explore</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
          </div>

          {/* Stats Section */}
          <div 
            ref={statsAnimation.ref}
            className={`max-w-5xl mx-auto mb-20 transition-all duration-1000 ${
              statsAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden'
            }`}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="group text-center p-6 bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md hover:scale-105 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-lg transition-all duration-300 cursor-default">
                <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-blue-500 transition-colors">
                  1,000+
                </div>
                <div className="text-sm text-gray-600 dark:text-white/60 font-medium">
                  Simulations per Prediction
                </div>
              </div>
              <div className="group text-center p-6 bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md hover:scale-105 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-lg transition-all duration-300 cursor-default" style={{ transitionDelay: '100ms' }}>
                <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-purple-500 transition-colors">
                  3
                </div>
                <div className="text-sm text-gray-600 dark:text-white/60 font-medium">
                  Scenario Forecasts
                </div>
              </div>
              <div className="group text-center p-6 bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md hover:scale-105 hover:border-green-400 dark:hover:border-green-500 hover:shadow-lg transition-all duration-300 cursor-default" style={{ transitionDelay: '200ms' }}>
                <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-green-500 transition-colors">
                  5
                </div>
                <div className="text-sm text-gray-600 dark:text-white/60 font-medium">
                  Years Ahead
                </div>
              </div>
              <div className="group text-center p-6 bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md hover:scale-105 hover:border-orange-400 dark:hover:border-orange-500 hover:shadow-lg transition-all duration-300 cursor-default" style={{ transitionDelay: '300ms' }}>
                <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-orange-500 transition-colors">
                  Live
                </div>
                <div className="text-sm text-gray-600 dark:text-white/60 font-medium">
                  Market Data
                </div>
              </div>
            </div>
          </div>

          
          {/* How We Predict Section */}
          <div 
            ref={featuresAnimation.ref}
            className={`transition-all duration-1000 ${
              featuresAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden'
            }`}
          >
            <div className="text-center mb-12">
              <h3 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">How We Predict</h3>
              <p className="text-gray-600 dark:text-white/70 text-lg font-light max-w-2xl mx-auto">
                Advanced crypto-style forecasting with comprehensive risk analysis
              </p>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div 
                className={`group bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-all duration-500 ${
                  featuresAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden-scale'
                }`}
                style={{ transitionDelay: '100ms' }}
              >
                <div className="bg-blue-500/10 dark:bg-blue-400/10 w-16 h-16 rounded-md flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <LineChart className="w-8 h-8 text-blue-500 dark:text-blue-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-semibold text-lg mb-2">Exponential Smoothing</h4>
                <p className="text-gray-600 dark:text-white/70 text-sm font-light">Holt's method for advanced trend detection</p>
              </div>

              <div 
                className={`group bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8 text-center hover:border-purple-500 dark:hover:border-purple-400 transition-all duration-500 ${
                  featuresAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden-scale'
                }`}
                style={{ transitionDelay: '200ms' }}
              >
                <div className="bg-purple-500/10 dark:bg-purple-400/10 w-16 h-16 rounded-md flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Brain className="w-8 h-8 text-purple-500 dark:text-purple-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-semibold text-lg mb-2">Monte Carlo Simulation</h4>
                <p className="text-gray-600 dark:text-white/70 text-sm font-light">1,000 simulations for risk assessment</p>
              </div>

              <div 
                className={`group bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8 text-center hover:border-green-500 dark:hover:border-green-400 transition-all duration-500 ${
                  featuresAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden-scale'
                }`}
                style={{ transitionDelay: '300ms' }}
              >
                <div className="bg-green-500/10 dark:bg-green-400/10 w-16 h-16 rounded-md flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Database className="w-8 h-8 text-green-500 dark:text-green-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-semibold text-lg mb-2">VWAP Analysis</h4>
                <p className="text-gray-600 dark:text-white/70 text-sm font-light">Volume-weighted market insights</p>
              </div>

              <div 
                className={`group bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8 text-center hover:border-orange-500 dark:hover:border-orange-400 transition-all duration-500 ${
                  featuresAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden-scale'
                }`}
                style={{ transitionDelay: '400ms' }}
              >
                <div className="bg-orange-500/10 dark:bg-orange-400/10 w-16 h-16 rounded-md flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Target className="w-8 h-8 text-orange-500 dark:text-orange-400" />
                </div>
                <h4 className="text-gray-900 dark:text-white font-semibold text-lg mb-2">Multi-Scenario</h4>
                <p className="text-gray-600 dark:text-white/70 text-sm font-light">Conservative to aggressive forecasts</p>
              </div>
            </div>

            {/* Tech Stack Display */}
            <div 
              ref={techStackAnimation.ref}
              className={`bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8 transition-all duration-1000 ${
                techStackAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden'
              }`}
            >
              <div className="flex flex-col md:flex-row items-center justify-center gap-4 text-gray-900 dark:text-white flex-wrap">
                <div className="text-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 px-6 py-3 rounded-md border border-blue-200 dark:border-blue-500/30 hover:scale-105 transition-transform">
                  <p className="text-xs text-gray-600 dark:text-white/60 mb-1 font-semibold uppercase tracking-wide">Step 1</p>
                  <p className="font-semibold text-sm">Exponential Smoothing</p>
                </div>
                <div className="text-gray-400">→</div>
                <div className="text-center bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 px-6 py-3 rounded-md border border-purple-200 dark:border-purple-500/30 hover:scale-105 transition-transform">
                  <p className="text-xs text-gray-600 dark:text-white/60 mb-1 font-semibold uppercase tracking-wide">Step 2</p>
                  <p className="font-semibold text-sm">Monte Carlo (GBM)</p>
                </div>
                <div className="text-gray-400">→</div>
                <div className="text-center bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 px-6 py-3 rounded-md border border-green-200 dark:border-green-500/30 hover:scale-105 transition-transform">
                  <p className="text-xs text-gray-600 dark:text-white/60 mb-1 font-semibold uppercase tracking-wide">Step 3</p>
                  <p className="font-semibold text-sm">Market Factors</p>
                </div>
                <div className="text-gray-400">→</div>
                <div className="text-center bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-md shadow-lg hover:scale-105 transition-transform">
                  <p className="text-xs mb-1 font-semibold uppercase tracking-wide opacity-90">Result</p>
                  <p className="font-bold text-sm">ML Prediction</p>
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
              className="text-gray-600 hover:text-purple-600 dark:text-white/70 dark:hover:text-purple-400 font-medium flex items-center space-x-2 transition-colors"
            >
              <span>← Back to Search</span>
            </button>
          </div>
          
          <div className="bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-md p-8">

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column - Card Info */}
              <div className="lg:col-span-1 space-y-6">
                <CardDisplay 
                  card={selectedCard} 
                  onDetailsLoaded={setCardDetails}
                />
                {cardDetails && cardDetails.features && (
                  <InvestmentRating 
                    cardId={selectedCard.id}
                    features={cardDetails.features}
                    prediction={latestPrediction}
                  />
                )}
              </div>

              {/* Right Column - Charts and Predictions */}
              <div className="lg:col-span-2 space-y-6">
                {cardDetails && (
                  <>
                    <PriceChart cardId={selectedCard.id} />
                    <PredictionPanel 
                      cardId={selectedCard.id}
                      cardName={selectedCard.name}
                      currentPrice={cardDetails.current_price}
                      onPredictionGenerated={setLatestPrediction}
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer 
        ref={footerAnimation.ref}
        className={`bg-white/50 dark:bg-[#0a0a0a]/50 backdrop-blur-sm border-t border-gray-200 dark:border-white/10 mt-32 transition-all duration-1000 ${
          footerAnimation.isVisible ? 'scroll-visible' : 'scroll-hidden'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <p className="text-gray-600 dark:text-white/70 mb-3 font-light">
              Data powered by PriceCharting API • Predictions by Advanced ML Models
            </p>
            <p className="text-sm text-gray-500 dark:text-white/50 font-light max-w-3xl mx-auto">
              For entertainment and educational purposes only. Not financial advice. 
              This site is not affiliated with, endorsed, or sponsored by The Pokémon Company International, Nintendo, or Game Freak.
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}

