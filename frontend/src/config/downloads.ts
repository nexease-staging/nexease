/** Public download links. Both are GitHub releases that the build workflows replace on every build. */
const RELEASES = "https://github.com/nexease-staging/nexease/releases";

export const downloads = {
  connector: {
    url: `${RELEASES}/download/tally-connector/NexEase-Tally-Connector.exe`,
    checksum: `${RELEASES}/download/tally-connector/NexEase-Tally-Connector.exe.sha256`,
    file: "NexEase-Tally-Connector.exe",
    size: "12 MB",
    needs: "Windows 10 or 11 with TallyPrime",
  },
  android: {
    url: `${RELEASES}/download/android-latest/NexEase.apk`,
    file: "NexEase.apk",
    size: "40 MB",
    needs: "Android 8 or later",
  },
} as const;
