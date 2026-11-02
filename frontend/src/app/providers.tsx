"use client";
import MobileGate from "@/components/mobile/mobile-gate";
import NativeStart from "@/components/mobile/native-start";
import DeviceNotifications from "@/components/mobile/device-notifications";
import MobileRuntime from "@/components/mobile/mobile-runtime";

import {NumberDialog} from "@/features/business/numbering-ui";
import { ThemeProvider } from "@/components/theme-provider";

import {
  useState,
  type ReactNode,
} from "react";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import {
  APIRequestError,
} from "@/lib/api/client";

import {
  AuthProvider,
} from "@/features/auth/auth-context";

export default function Providers({
  children,
}: {
  children: ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,

            refetchOnWindowFocus:
              false,

            retry: (
              failureCount,
              error,
            ) => {
              if (
                error
                instanceof
                APIRequestError
                &&
                (
                  error.status === 401
                  ||
                  error.status === 403
                )
              ) {
                return false;
              }

              return failureCount < 2;
            },
          },

          mutations: {
            retry: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider
      client={queryClient}
    >
      <ThemeProvider><MobileGate><MobileRuntime/><AuthProvider>
        <NativeStart>{children}</NativeStart><DeviceNotifications/><NumberDialog/>
      </AuthProvider></MobileGate></ThemeProvider>
    </QueryClientProvider>
  );
}