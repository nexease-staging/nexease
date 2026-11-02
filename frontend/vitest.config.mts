import path from "node:path";
import {fileURLToPath} from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

import {
  defineConfig,
} from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [
      "./src/test/setup.ts",
    ],
    css: true,
  },

  resolve: {
    alias: {
      "@": path.resolve(
        __dirname,
        "./src",
      ),
    },
  },
});