'use client'

import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'

type Step = 'input' | 'generating' | 'results'
type QuestionStep = 1 | 2 | 3 | 4 | 5 | 6

interface GeneratedAd {
  hook: string
  body: string
  cta: string
  visual_concept: string
  image_url?: string
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
  const [questionStep, setQuestionStep] = useState<QuestionStep>(1)

  // Form state
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [brandName, setBrandName] = useState('')
  const [logoImage, setLogoImage] = useState<File | null>(null)
  const [productImage, setProductImage] = useState<File | null>(null)
  const [brandImages, setBrandImages] = useState<File[]>([])
  const [product, setProduct] = useState('')
  const [targetCustomer, setTargetCustomer] = useState('')

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

  const handleNextQuestion = () => {
    setError(null)

    // Validate current step before advancing
    if (questionStep === 1 && !brandName.trim()) {
      setError('Please enter your brand name')
      return
    }
    if (questionStep === 2 && !logoImage) {
      setError('Please upload your logo')
      return
    }
    if (questionStep === 3 && !productImage) {
      setError('Please upload your product image')
      return
    }
    if (questionStep === 4 && brandImages.length < 3) {
      setError('Please upload at least 3 brand images (3-5 recommended)')
      return
    }
    if (questionStep === 5 && !product.trim()) {
      setError('Please describe your product')
      return
    }
    if (questionStep === 6 && !targetCustomer.trim()) {
      setError('Please describe your target customer')
      return
    }

    if (questionStep < 6) {
      setQuestionStep((questionStep + 1) as QuestionStep)
    }
  }

  const handlePreviousQuestion = () => {
    setError(null)
    if (questionStep > 1) {
      setQuestionStep((questionStep - 1) as QuestionStep)
    }
  }

  const handleGenerate = async () => {
    // Validate all required inputs
    if (!brandName.trim() || !logoImage || !productImage || brandImages.length < 3 || !product.trim() ||
        !targetCustomer.trim()) {
      setError('Please complete all required fields')
      return
    }

    setIsGenerating(true)
    setError(null)
    setCurrentStep('generating')

    try {
      // Step 1: Upload assets
      const formData = new FormData()

      // Upload logo
      formData.append('logo', logoImage)

      // Upload product image
      formData.append('product_image', productImage)

      // Upload multiple brand images
      brandImages.forEach((image, index) => {
        formData.append('brand_image', image)
      })

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

      // Step 2: Generate ads with Visual Bible workflow
      const generateResponse = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: newSessionId,
          brand_name: brandName.trim(),
          product: product.trim(),
          target_customer: targetCustomer.trim(),
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
      setQuestionStep(1)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleStartOver = () => {
    setCurrentStep('input')
    setQuestionStep(1)
    setSessionId(null)
    setBrandName('')
    setLogoImage(null)
    setProductImage(null)
    setBrandImages([])
    setProduct('')
    setTargetCustomer('')
    setGeneratedAds([])
    setGenerationTime(0)
    setError(null)
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
            {/* Progress indicator */}
            <div className="mb-8">
              <div className="flex items-center justify-center gap-2 mb-4">
                {[1, 2, 3, 4, 5, 6].map((step) => (
                  <div
                    key={step}
                    className={`h-2 rounded-full transition-all ${
                      step < questionStep
                        ? 'w-8 bg-primary'
                        : step === questionStep
                        ? 'w-12 bg-primary'
                        : 'w-8 bg-zinc-700'
                    }`}
                  />
                ))}
              </div>
              <p className="text-center text-zinc-500 text-sm">
                Step {questionStep} of 6
              </p>
            </div>

            <div className="bg-surface border border-border rounded-2xl p-8 min-h-[400px] flex flex-col">
              {/* Question 1: Brand Name */}
              {questionStep === 1 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">What's your brand name?</h2>
                  <p className="text-zinc-400 mb-8">This will appear on your ads</p>
                  <input
                    type="text"
                    placeholder="e.g., FitFuel, Nike, Apple"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleNextQuestion()}
                    autoFocus
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-6 py-4 text-white text-lg placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              )}

              {/* Question 2: Logo Upload */}
              {questionStep === 2 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">Upload your logo</h2>
                  <p className="text-zinc-400 mb-8">This helps establish brand identity in your ads</p>
                  <div
                    className={`flex-1 border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center ${
                      logoImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('logo-input')?.click()}
                  >
                    {logoImage ? (
                      <div>
                        <svg className="w-16 h-16 text-primary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-primary font-semibold text-lg mb-1">{logoImage.name}</p>
                        <p className="text-zinc-500 text-sm">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-16 h-16 text-zinc-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-white font-medium text-lg mb-2">Click to upload logo</p>
                        <p className="text-zinc-500 text-sm">PNG, JPG, or SVG</p>
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
              )}

              {/* Question 3: Product Image Upload */}
              {questionStep === 3 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">Upload your product image</h2>
                  <p className="text-zinc-400 mb-8">This will be featured in all your ads</p>
                  <div
                    className={`flex-1 border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center ${
                      productImage ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('product-input')?.click()}
                  >
                    {productImage ? (
                      <div>
                        <svg className="w-16 h-16 text-primary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-primary font-semibold text-lg mb-1">{productImage.name}</p>
                        <p className="text-zinc-500 text-sm">Click to change</p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-16 h-16 text-zinc-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-white font-medium text-lg mb-2">Click to upload product image</p>
                        <p className="text-zinc-500 text-sm">PNG or JPG - clear photo of your product</p>
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
              )}

              {/* Question 4: Brand Images Upload (3-5 images) */}
              {questionStep === 4 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">Upload 3-5 brand images</h2>
                  <p className="text-zinc-400 mb-8">These will define your brand's visual style</p>
                  <div
                    className={`flex-1 border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center ${
                      brandImages.length > 0 ? 'border-primary bg-primary/5' : 'border-zinc-700 hover:border-zinc-600'
                    }`}
                    onClick={() => document.getElementById('brand-images-input')?.click()}
                  >
                    {brandImages.length > 0 ? (
                      <div>
                        <svg className="w-16 h-16 text-primary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-primary font-semibold text-lg mb-1">{brandImages.length} images selected</p>
                        <p className="text-zinc-500 text-sm">Click to change (3-5 images)</p>
                        <div className="flex flex-wrap gap-2 justify-center mt-4">
                          {brandImages.map((img, i) => (
                            <span key={i} className="text-xs bg-zinc-800 px-2 py-1 rounded">{img.name}</span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-16 h-16 text-zinc-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <p className="text-white font-medium text-lg mb-2">Click to upload 3-5 brand images</p>
                        <p className="text-zinc-500 text-sm">Product photos, lifestyle shots, brand aesthetics</p>
                      </div>
                    )}
                  </div>
                  <input
                    id="brand-images-input"
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || [])
                      if (files.length < 3 || files.length > 5) {
                        setError('Please select 3-5 images')
                      } else {
                        setBrandImages(files)
                        setError(null)
                      }
                    }}
                  />
                </div>
              )}

              {/* Question 5: Product Description */}
              {questionStep === 5 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">What's your product?</h2>
                  <p className="text-zinc-400 mb-8">Describe it in one clear sentence</p>
                  <textarea
                    placeholder="e.g., Organic plant-based protein powder with 25g protein per serving"
                    value={product}
                    onChange={(e) => setProduct(e.target.value)}
                    autoFocus
                    rows={3}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-6 py-4 text-white text-lg placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors resize-none"
                  />
                </div>
              )}

              {/* Question 6: Target Customer */}
              {questionStep === 6 && (
                <div className="flex-1 flex flex-col">
                  <h2 className="text-3xl font-bold text-white mb-3">Who is it for?</h2>
                  <p className="text-zinc-400 mb-8">Describe your ideal customer</p>
                  <textarea
                    placeholder="e.g., Busy professionals who work out but struggle to get enough protein"
                    value={targetCustomer}
                    onChange={(e) => setTargetCustomer(e.target.value)}
                    autoFocus
                    rows={3}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-6 py-4 text-white text-lg placeholder-zinc-500 focus:outline-none focus:border-primary transition-colors resize-none"
                  />
                </div>
              )}

              {/* Navigation buttons */}
              <div className="flex gap-3 mt-8">
                {questionStep > 1 && (
                  <button
                    onClick={handlePreviousQuestion}
                    className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl font-medium transition-colors"
                  >
                    Back
                  </button>
                )}

                {questionStep < 6 && (
                  <button
                    onClick={handleNextQuestion}
                    className="flex-1 bg-primary hover:bg-primary-hover text-white py-3 rounded-xl font-semibold text-lg transition-colors"
                  >
                    Continue
                  </button>
                )}

                {questionStep === 6 && (
                  <button
                    onClick={handleGenerate}
                    className="flex-1 bg-primary hover:bg-primary-hover text-white py-3 rounded-xl font-semibold text-lg transition-colors"
                  >
                    Generate Ads
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Generating Step */}
        {currentStep === 'generating' && (
          <div className="max-w-md mx-auto text-center py-20">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-white mb-2">Generating Your Ads</h2>
            <p className="text-zinc-400 mb-8">Creating 10 unique ad concepts...</p>

            <div className="space-y-3 text-left max-w-xs mx-auto">
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse" />
                Analyzing brand visual style...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-300" />
                Generating creative concepts...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-500" />
                Creating on-brand images...
              </div>
              <div className="flex items-center text-zinc-400">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse delay-700" />
                Compositing final ads...
              </div>
            </div>
          </div>
        )}

        {/* Results Step */}
        {currentStep === 'results' && (
          <div>
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Your 10 Ads</h1>
              <p className="text-zinc-400">
                Generated in {(generationTime / 1000).toFixed(1)} seconds using diverse marketing frameworks
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
              {generatedAds.map((ad, index) => {
                return (
                  <div
                    key={index}
                    className="bg-surface border border-zinc-800 rounded-2xl overflow-hidden flex flex-col"
                  >
                    {/* Ad Image Preview */}
                    {ad.image_url ? (
                      <div className="relative w-full aspect-square bg-zinc-900">
                        <img
                          src={ad.image_url}
                          alt={`Ad ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="w-full aspect-square bg-gradient-to-br from-zinc-800 to-zinc-900 flex items-center justify-center">
                        <div className="text-center">
                          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                          <p className="text-zinc-500">Generating image...</p>
                        </div>
                      </div>
                    )}

                    <div className="p-4">
                      {/* Download button */}
                      {ad.image_url && (
                        <a
                          href={`${API_URL}/api/generate/download/${sessionId}/${index + 1}`}
                          download
                          className="block w-full text-center bg-primary hover:bg-primary-hover text-white px-4 py-3 rounded-xl font-semibold transition-colors"
                        >
                          <svg className="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download Ad
                        </a>
                      )}
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
