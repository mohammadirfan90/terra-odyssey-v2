/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === "development";

const nextConfig = {
  reactStrictMode: true,
  ...(isDev
    ? {
        async rewrites() {
          return [
            {
              source: "/api/:path*",
              destination: "http://127.0.0.1:8005/:path*",
            },
          ];
        },
      }
    : {
        output: "export",
        images: {
          unoptimized: true,
        },
      }),
};

export default nextConfig;
