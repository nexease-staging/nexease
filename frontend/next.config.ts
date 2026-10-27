import type {
  NextConfig,
} from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "172.20.10.7",
  ],
};

export default nextConfig;