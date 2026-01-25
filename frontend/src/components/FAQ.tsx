'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const faqs = [
  {
    question: 'How does VexAds find winning ads?',
    answer: 'VexAds analyzes Facebook Ad Library data to identify ads that have been running for a long time. Advertisers don\'t keep running unprofitable ads, so ads running 30+ days are likely winners.',
  },
  {
    question: 'Do I need design skills?',
    answer: 'No! Just upload your product image and logo. Our AI handles all the design work, creating professional ads inspired by proven winners.',
  },
  {
    question: 'What image formats do you support?',
    answer: 'We support JPG, PNG, and WebP formats. Generated ads are delivered in PNG format at 1024x1024 resolution, perfect for Facebook and Instagram.',
  },
  {
    question: 'Is this legal?',
    answer: 'Yes! We only analyze publicly available data from Facebook\'s Ad Library, which is a transparency tool provided by Meta. We don\'t copy ads directly - our AI creates original variations inspired by successful patterns.',
  },
  {
    question: 'Can I cancel anytime?',
    answer: 'Absolutely. No contracts, no commitments. Cancel your subscription anytime from your dashboard.',
  },
  {
    question: 'How fast is ad generation?',
    answer: 'Most ads are generated in under 30 seconds. You can generate multiple variations at once and download them immediately.',
  },
]

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section id="faq" className="py-24 bg-background">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Frequently asked questions
          </h2>
          <p className="text-zinc-400 text-lg">
            Everything you need to know about VexAds
          </p>
        </motion.div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.05 }}
              viewport={{ once: true }}
              className="border border-border rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between p-6 text-left bg-surface hover:bg-zinc-800/50 transition-colors"
              >
                <span className="text-white font-medium">{faq.question}</span>
                <svg
                  className={`w-5 h-5 text-zinc-400 transition-transform ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="p-6 pt-0 text-zinc-400">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
