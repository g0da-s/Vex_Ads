'use client'

import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'

type Step = 'upload' | 'analyze' | 'generate' | 'results'

interface GeneratedAd {
  id: string
  download_url: string
  competitor_ad_id: string
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState<Step>('upload')

  // Form state
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [productImage, setProductImage] = useState<File | null>(null)
  const [logoImage, setLogoImage] = useState<File | null>(null)
  const [competitorUrl, setCompetitorUrl] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [competitorAds, setCompetitorAds] = useState<any[]>([])
  const [generatedAds, setGeneratedAds] = useState<GeneratedAd[]>([])
  const [error, setError] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const checkUser = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        router.push('/login')
      } else {
        setUser(user)
        setLoading(false)
      }
    }
    checkUser()
  }, [router])

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/')
  }

  const handleUpload = async () => {
    if (!productImage || !logoImage) {
      setError('Please select both product image and logo')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('product_image', productImage)
      formData.append('logo', logoImage)

      const response = await fetch(`${API_URL}/api/assets/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const data = await response.json()
      setSessionId(data.session_id)
      setCurrentStep('analyze')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!sessionId || !competitorUrl) {
      setError('Please enter a Facebook Ad Library URL')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/competitors/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          ad_library_url: competitorUrl,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Analysis failed')
      }

      const data = await response.json()
      setCompetitorAds(data.competitor_ads || [])
      setCurrentStep('generate')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerate = async () => {
    if (!sessionId) return

    setIsGenerating(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          num_variations: 1,
          max_winners: 3,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Generation failed')
      }

      const data = await response.json()
      setGeneratedAds(data.generated_ads)
      setCurrentStep('results')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-surface border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">V</span>
              </div>
              <span className="text-xl font-bold text-white">VexAds</span>
            </Link>

            <div className="flex items-center space-x-4">
              <span className="text-zinc-400 text-sm">{user?.email}</span>
              <button
                onClick={handleSignOut}
                className="text-zinc-400 hover:text-white text-sm transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-12">
          {['upload', 'analyze', 'generate', 'results'].map((step, index) => (
            <div key={step} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-medium ${
                  currentStep === step
                    ? 'bg-primary text-white'
                    : index < ['upload', 'analyze', 'generate', 'results'].indexOf(currentStep)
                    ? 'bg-primary/20 text-primary'
                    : 'bg-zinc-800 text-zinc-500'
                }`}
              >
                {index + 1}
              </div>
              {index < 3 && (
                <div
                  className={`w-24 h-0.5 mx-2 ${
                    index < ['upload', 'analyze', 'generate', 'results'].indexOf(currentStep)
                      ? 'bg-primary'
                      : 'bg-zinc-800'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-error/10 border border-error/20 rounded-xl p-4 mb-6">
            <p className="text-error">{error}</p>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-surface border border-border rounded-2xl p-8">
          {currentStep === 'upload' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Upload Your Assets</h2>
              <p className="text-zinc-400 mb-8">Upload your product image and logo to get started</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Product Image */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Product Image
                  </label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                      productImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('product-input')?.click()}
                  >
                    {productImage ? (
                      <div>
                        <p className="text-primary font-medium">{productImage.name}</p>
                        <p className="text-zinc-500 text-sm mt-1">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-12 h-12 text-zinc-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-zinc-400">Click to upload product image</p>
                      </div>
                    )}
                  </div>
                  <input
                    id="product-input"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => setProductImage(e.target.files?.[0] || null)}
                  />
                </div>

                {/* Logo */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Logo
                  </label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                      logoImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('logo-input')?.click()}
                  >
                    {logoImage ? (
                      <div>
                        <p className="text-primary font-medium">{logoImage.name}</p>
                        <p className="text-zinc-500 text-sm mt-1">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-12 h-12 text-zinc-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-zinc-400">Click to upload logo</p>
                      </div>
                    )}
                  </div>
                  <input
                    id="logo-input"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => setLogoImage(e.target.files?.[0] || null)}
                  />
                </div>
              </div>

              <button
                onClick={handleUpload}
                disabled={!productImage || !logoImage || isUploading}
                className="w-full bg-primary hover:bg-primary-hover disabled:bg-zinc-700 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Continue'}
              </button>
            </div>
          )}

          {currentStep === 'analyze' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Analyze Competitors</h2>
              <p className="text-zinc-400 mb-8">Paste a Facebook Ad Library URL to analyze competitor ads</p>

              <div className="mb-8">
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Facebook Ad Library URL
                </label>
                <input
                  type="url"
                  placeholder="https://www.facebook.com/ads/library/?view_all_page_id=..."
                  value={competitorUrl}
                  onChange={(e) => setCompetitorUrl(e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors"
                />
                <p className="text-zinc-500 text-sm mt-2">
                  Go to Facebook Ad Library, search for a competitor, and copy the URL
                </p>
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!competitorUrl || isAnalyzing}
                className="w-full bg-primary hover:bg-primary-hover disabled:bg-zinc-700 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition-colors"
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Ads'}
              </button>
            </div>
          )}

          {currentStep === 'generate' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Found {competitorAds?.length || 0} Ads</h2>
              <p className="text-zinc-400 mb-8">Our AI identified the top winners. Ready to generate your ads?</p>

              {/* Winner ads preview */}
              <div className="grid grid-cols-3 gap-4 mb-8">
                {(competitorAds || []).slice(0, 3).map((ad, i) => (
                  <div key={ad.id || i} className="bg-zinc-800 rounded-lg p-3">
                    <div className="aspect-square bg-zinc-700 rounded mb-2 flex items-center justify-center overflow-hidden">
                      {ad.image_url ? (
                        <img src={ad.image_url} alt="Ad" className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-zinc-500">No image</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                        Winner
                      </span>
                      <span className="text-xs text-zinc-500">{ad.days_running || 0} days</span>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full bg-primary hover:bg-primary-hover disabled:bg-zinc-700 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition-colors"
              >
                {isGenerating ? 'Generating... (this may take a minute)' : 'Generate My Ads'}
              </button>
            </div>
          )}

          {currentStep === 'results' && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Your Ads Are Ready!</h2>
              <p className="text-zinc-400 mb-8">Generated {generatedAds.length} ads. Click to download.</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {generatedAds.map((ad) => (
                  <div key={ad.id} className="bg-zinc-800 rounded-xl p-4 border border-primary/30">
                    <div className="aspect-square bg-zinc-700 rounded-lg mb-4 overflow-hidden">
                      <img
                        src={ad.download_url}
                        alt="Generated ad"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <a
                      href={ad.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg font-medium text-center transition-colors"
                    >
                      Download
                    </a>
                  </div>
                ))}
              </div>

              <button
                onClick={() => {
                  setCurrentStep('upload')
                  setSessionId(null)
                  setProductImage(null)
                  setLogoImage(null)
                  setCompetitorUrl('')
                  setCompetitorAds([])
                  setGeneratedAds([])
                }}
                className="w-full bg-zinc-800 hover:bg-zinc-700 text-white py-3 rounded-xl font-medium transition-colors"
              >
                Create More Ads
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
