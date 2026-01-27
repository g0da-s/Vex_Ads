'use client'

import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'

type Step = 'input' | 'generating' | 'results'

interface GeneratedAd {
  framework: string
  hook: string
  body: string
  cta: string
  visual_concept: string
}

interface GenerateResponse {
  session_id: string
  product: string
  ads: GeneratedAd[]
  generation_time_ms: number
  message: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState<Step>('input')

  // Form state
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [productImage, setProductImage] = useState<File | null>(null)
  const [logoImage, setLogoImage] = useState<File | null>(null)
  const [product, setProduct] = useState('')
  const [targetCustomer, setTargetCustomer] = useState('')
  const [mainBenefit, setMainBenefit] = useState('')

  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedAds, setGeneratedAds] = useState<GeneratedAd[]>([])
  const [generationTime, setGenerationTime] = useState<number>(0)
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

  const handleGenerate = async () => {
    // Validate inputs
    if (!productImage) {
      setError('Please upload a product image')
      return
    }
    if (!product.trim()) {
      setError('Please describe what you sell')
      return
    }
    if (!targetCustomer.trim()) {
      setError('Please describe your target customer')
      return
    }
    if (!mainBenefit.trim()) {
      setError('Please describe the main benefit')
      return
    }

    setIsGenerating(true)
    setError(null)
    setCurrentStep('generating')

    try {
      // Step 1: Upload assets
      const formData = new FormData()
      formData.append('product_image', productImage)
      if (logoImage) {
        formData.append('logo', logoImage)
      }

      const uploadResponse = await fetch(`${API_URL}/api/assets/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        const error = await uploadResponse.json()
        throw new Error(error.detail || 'Failed to upload images')
      }

      const uploadData = await uploadResponse.json()
      const newSessionId = uploadData.session_id
      setSessionId(newSessionId)

      // Step 2: Generate ads
      const generateResponse = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: newSessionId,
          product: product.trim(),
          target_customer: targetCustomer.trim(),
          main_benefit: mainBenefit.trim(),
        }),
      })

      if (!generateResponse.ok) {
        const error = await generateResponse.json()
        throw new Error(error.detail || 'Failed to generate ads')
      }

      const generateData: GenerateResponse = await generateResponse.json()
      setGeneratedAds(generateData.ads)
      setGenerationTime(generateData.generation_time_ms)
      setCurrentStep('results')
    } catch (err: any) {
      setError(err.message)
      setCurrentStep('input')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleStartOver = () => {
    setCurrentStep('input')
    setSessionId(null)
    setProductImage(null)
    setLogoImage(null)
    setProduct('')
    setTargetCustomer('')
    setMainBenefit('')
    setGeneratedAds([])
    setGenerationTime(0)
    setError(null)
  }

  const getFrameworkColor = (framework: string) => {
    if (framework.includes('Problem') || framework.includes('PAS')) {
      return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' }
    }
    if (framework.includes('Social')) {
      return { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' }
    }
    return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' }
  }

  const getFrameworkIcon = (framework: string) => {
    if (framework.includes('Problem') || framework.includes('PAS')) {
      return (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      )
    }
    if (framework.includes('Social')) {
      return (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    }
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    )
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
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-white">AdAngle</span>
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

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Error display */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Input Step */}
        {currentStep === 'input' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Generate 3 Ad Angles</h1>
              <p className="text-zinc-400">Tell us about your product and we'll create 3 psychologically different ad concepts</p>
            </div>

            <div className="bg-surface border border-border rounded-2xl p-8">
              {/* Product Description */}
              <div className="space-y-6 mb-8">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    What do you sell?
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Organic protein powder, Online yoga classes, Project management SaaS"
                    value={product}
                    onChange={(e) => setProduct(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Who buys it?
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Busy professionals who want to stay fit, Small business owners"
                    value={targetCustomer}
                    onChange={(e) => setTargetCustomer(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    What problem does it solve?
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Build muscle without spending hours cooking, Save 10 hours/week on admin"
                    value={mainBenefit}
                    onChange={(e) => setMainBenefit(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>

              {/* Image uploads */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Product Image */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Product Image <span className="text-red-400">*</span>
                  </label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                      productImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('product-input')?.click()}
                  >
                    {productImage ? (
                      <div>
                        <p className="text-primary font-medium truncate">{productImage.name}</p>
                        <p className="text-zinc-500 text-sm mt-1">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-10 h-10 text-zinc-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-zinc-400 text-sm">Upload product image</p>
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

                {/* Logo (optional) */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Logo <span className="text-zinc-500">(optional)</span>
                  </label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                      logoImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('logo-input')?.click()}
                  >
                    {logoImage ? (
                      <div>
                        <p className="text-primary font-medium truncate">{logoImage.name}</p>
                        <p className="text-zinc-500 text-sm mt-1">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-10 h-10 text-zinc-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-zinc-400 text-sm">Upload logo (optional)</p>
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
                onClick={handleGenerate}
                disabled={!productImage || !product || !targetCustomer || !mainBenefit}
                className="w-full bg-primary hover:bg-primary-hover disabled:bg-zinc-700 disabled:cursor-not-allowed text-white py-4 rounded-xl font-semibold text-lg transition-colors"
              >
                Generate 3 Ad Angles
              </button>
            </div>
          </div>
        )}

        {/* Generating Step */}
        {currentStep === 'generating' && (
          <div className="max-w-md mx-auto text-center py-20">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-white mb-2">Generating Your Ads</h2>
            <p className="text-zinc-400 mb-8">Applying marketing psychology frameworks...</p>

            <div className="space-y-3 text-left max-w-xs mx-auto">
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse" />
                Analyzing your product...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-300" />
                Applying PAS framework...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-500" />
                Crafting social proof angle...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-700" />
                Building transformation story...
              </div>
            </div>
          </div>
        )}

        {/* Results Step */}
        {currentStep === 'results' && (
          <div>
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Your 3 Ad Angles</h1>
              <p className="text-zinc-400">
                Generated in {(generationTime / 1000).toFixed(1)} seconds using different psychological frameworks
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {generatedAds.map((ad, index) => {
                const colors = getFrameworkColor(ad.framework)
                return (
                  <div
                    key={index}
                    className={`bg-surface border ${colors.border} rounded-2xl p-6 flex flex-col`}
                  >
                    {/* Framework badge */}
                    <div className={`inline-flex items-center ${colors.bg} ${colors.text} px-3 py-1.5 rounded-lg text-sm font-medium mb-4 self-start`}>
                      {getFrameworkIcon(ad.framework)}
                      <span className="ml-2">{ad.framework}</span>
                    </div>

                    {/* Hook */}
                    <div className="mb-4">
                      <label className="text-xs text-zinc-500 uppercase tracking-wider mb-1 block">Hook</label>
                      <p className="text-xl font-bold text-white leading-tight">{ad.hook}</p>
                    </div>

                    {/* Body */}
                    <div className="mb-4 flex-grow">
                      <label className="text-xs text-zinc-500 uppercase tracking-wider mb-1 block">Body</label>
                      <p className="text-zinc-300 leading-relaxed">{ad.body}</p>
                    </div>

                    {/* CTA */}
                    <div className="mb-4">
                      <label className="text-xs text-zinc-500 uppercase tracking-wider mb-1 block">Call to Action</label>
                      <p className={`font-semibold ${colors.text}`}>{ad.cta}</p>
                    </div>

                    {/* Visual Concept */}
                    <div className="pt-4 border-t border-zinc-800">
                      <label className="text-xs text-zinc-500 uppercase tracking-wider mb-1 block">Visual Concept</label>
                      <p className="text-zinc-400 text-sm italic">{ad.visual_concept}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleGenerate}
                className="bg-zinc-800 hover:bg-zinc-700 text-white px-8 py-3 rounded-xl font-medium transition-colors"
              >
                Regenerate
              </button>
              <button
                onClick={handleStartOver}
                className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-xl font-medium transition-colors"
              >
                Create New Ads
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
