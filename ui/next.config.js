/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/kalavai/:path*',
        destination: `${process.env.NEXT_PUBLIC_KALAVAI_API_URL || 'http://0.0.0.0:49152'}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
