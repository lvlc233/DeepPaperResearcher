/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['reagraph', 'troika-worker-utils', 'troika-three-text', 'three'],
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    config.resolve.alias.encoding = false;
    return config;
  },
};

export default nextConfig;
