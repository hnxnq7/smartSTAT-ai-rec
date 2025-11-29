/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Set base path for GitHub Pages subdirectory deployment
  basePath: '/smartSTAT-ai-rec',
  assetPrefix: '/smartSTAT-ai-rec',
}

module.exports = nextConfig

