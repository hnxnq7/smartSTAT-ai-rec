/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
  // If your repo name is not the root (e.g., username.github.io/repo-name)
  // Uncomment and set the basePath:
  // basePath: '/smartSTAT',
  // assetPrefix: '/smartSTAT',
}

module.exports = nextConfig

