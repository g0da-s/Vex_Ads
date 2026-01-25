'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-background to-background" />

      {/* Animated background orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center space-x-2 bg-surface/50 backdrop-blur-sm border border-border rounded-full px-4 py-2 mb-8 mt-8"
        >
          <div className="flex items-center space-x-1">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <span className="text-zinc-400 text-sm">4.9</span>
          <span className="text-zinc-500">|</span>
          <span className="text-zinc-400 text-sm">Trusted by 500+ marketers</span>
        </motion.div>

        {/* Main headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight"
        >
          Create winning ads
          <br />
          <span className="gradient-text">in seconds</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto mb-8"
        >
          Analyze competitor Facebook ads, identify winners, and generate
          high-converting creatives with AI. No design skills needed.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <Link
            href="/login"
            className="w-full sm:w-auto bg-primary hover:bg-primary-hover text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all hover:scale-105 glow-sm"
          >
            Start Free Trial
          </Link>
          <Link
            href="#demo"
            className="w-full sm:w-auto bg-surface hover:bg-zinc-800 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-colors border border-border"
          >
            Watch Demo
          </Link>
        </motion.div>

        {/* Product preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="relative max-w-5xl mx-auto"
        >
          <div className="bg-surface border border-border rounded-2xl p-2 glow">
            <div className="bg-zinc-900 rounded-xl overflow-hidden">
              {/* Mock dashboard header */}
              <div className="flex items-center space-x-2 px-4 py-3 border-b border-border">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="ml-4 text-zinc-500 text-sm">VexAds Dashboard</span>
              </div>

              {/* Mock dashboard content */}
              <div className="p-6 min-h-[400px] flex items-center justify-center">
                <div className="grid grid-cols-3 gap-6 w-full">
                  {/* Competitor Ad Card */}
                  <div className="bg-zinc-800 rounded-lg p-4">
                    <div className="text-xs text-zinc-500 mb-2">Competitor Ad</div>
                    <div className="aspect-square bg-zinc-700 rounded-lg mb-3 flex items-center justify-center">
                      <svg className="w-12 h-12 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">Winner</span>
                      <span className="text-xs text-zinc-500">45 days</span>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center justify-center">
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mb-2">
                        <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                      <span className="text-xs text-zinc-500">AI Magic</span>
                    </div>
                  </div>

                  {/* Generated Ad Card */}
                  <div className="bg-zinc-800 rounded-lg p-4 border border-primary/30">
                    <div className="text-xs text-primary mb-2">Generated Ad</div>
                    <div className="aspect-square bg-gradient-to-br from-primary/20 to-accent/20 rounded-lg mb-3 flex items-center justify-center">
                      <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">Ready</span>
                      <span className="text-xs text-zinc-500">Download</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
