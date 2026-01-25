import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'VexAds - AI Ad Generator',
  description: 'Generate winning Facebook ads in seconds using AI.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
