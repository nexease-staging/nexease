import type {
  NextConfig,
} from "next";

const nextConfig: NextConfig = {
  ...(process.env.NEXEASE_MOBILE === "true" ? { output: "export" as const, trailingSlash: true, images: { unoptimized: true } } : {}),
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "172.20.10.7",
  ],
};

export default nextConfig;