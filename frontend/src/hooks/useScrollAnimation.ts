import { useEffect, useRef, useState } from 'react'

interface UseScrollAnimationOptions {
  threshold?: number
  rootMargin?: string
  triggerOnce?: boolean
}

export function useScrollAnimation(options: UseScrollAnimationOptions = {}) {
  const {
    threshold = 0.1,
    rootMargin = '0px 0px -50px 0px',
    triggerOnce = true,
  } = options

  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    // Immediately check if in viewport
    const checkVisibility = () => {
      const rect = element.getBoundingClientRect()
      const windowHeight = window.innerHeight
      if (rect.top < windowHeight + 100 && rect.bottom > -100) {
        setIsVisible(true)
        return true
      }
      return false
    }

    // Check immediately
    if (checkVisibility() && triggerOnce) {
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          if (triggerOnce) {
            observer.unobserve(element)
          }
        } else if (!triggerOnce) {
          setIsVisible(false)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(element)

    // Fallback: always show after 800ms to prevent blank sections
    const fallback = setTimeout(() => {
      setIsVisible(true)
    }, 800)

    return () => {
      observer.unobserve(element)
      clearTimeout(fallback)
    }
  }, [threshold, rootMargin, triggerOnce])

  return { ref, isVisible }
}
