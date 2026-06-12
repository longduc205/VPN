import './globals.css'

export const metadata = {
  title: 'Secure VPN Portal',
  description: 'Secure Web-Based VPN Management Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
