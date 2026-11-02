import {notify} from "@/components/nex-feedback";
import { apiFetch } from "./transport";
import { Capacitor } from "@capacitor/core";
import { savedServer } from "@/lib/mobile-config";
import {askNumber,numberKind} from "./number-choice";
import type {
  APIErrorResponse,
  APIResponse,
  APISuccessResponse,
  CSRFData,
} from "@/lib/api/types";

const configuredBaseURL = process.env.NEXT_PUBLIC_API_BASE_URL || '';
export const API_BASE_URL = (savedServer() || configuredBaseURL).replace(/\/+$/, '');
function mobileHeaders(): Record<string, string> {
  return Capacitor.isNativePlatform() ? { Origin: 'https://localhost' } : {};
}

const UNSAFE_METHODS = new Set([
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
]);

let cachedCSRFToken: string | null = null;

export class APIRequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;
  readonly requestId?: string;

  constructor({
    status,
    code,
    message,
    details,
    requestId,
  }: {
    status: number;
    code: string;
    message: string;
    details?: Record<string, unknown>;
    requestId?: string;
  }) {
    super(message);

    this.name = "APIRequestError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

function buildURL(path: string): string {
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${savedServer() || API_BASE_URL}${normalizedPath}`;
}

function isUnsafeMethod(method: string): boolean {
  return UNSAFE_METHODS.has(
    method.toUpperCase(),
  );
}

async function parseAPIResponse<T>(
  response: Response,
): Promise<APIResponse<T>> {
  const contentType =
    response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    throw new APIRequestError({
      status: response.status,
      code: "INVALID_API_RESPONSE",
      message:
        "The server returned an invalid response.",
    });
  }

  return (await response.json()) as APIResponse<T>;
}

export function clearCSRFToken(): void {
  cachedCSRFToken = null;
}

export async function getCSRFToken(
  forceRefresh = false,
): Promise<string> {
  if (cachedCSRFToken && !forceRefresh) {
    return cachedCSRFToken;
  }

  const response = await apiFetch(
    buildURL("/auth/csrf/"),
    {
      method: "GET",
      credentials: "include",
      cache: "no-store",
      headers: {
        Accept: "application/json", ...mobileHeaders(),
      },
    },
  );

  const body =
    await parseAPIResponse<CSRFData>(response);

  if (!response.ok || !body.success) {
    const errorBody = body as APIErrorResponse;

    throw new APIRequestError({
      status: response.status,
      code:
        errorBody.error?.code ??
        "CSRF_BOOTSTRAP_FAILED",
      message:
        errorBody.error?.message ??
        "Unable to initialize CSRF protection.",
      details: errorBody.error?.details,
      requestId: errorBody.request_id,
    });
  }

  const token = body.data.csrf.token;

  if (!token) {
    throw new APIRequestError({
      status: response.status,
      code: "CSRF_TOKEN_MISSING",
      message:
        "The server did not return a CSRF token.",
      requestId: body.request_id,
    });
  }

  cachedCSRFToken = token;

  return token;
}

export interface APIRequestOptions
  extends Omit<RequestInit, "body"> {
  body?: unknown;
}

export interface APIBinaryResponse {
  blob: Blob;
  filename: string | null;
  contentType: string;
}

export async function apiRequest<T>(
  path: string,
  options: APIRequestOptions = {},
  retryCSRF = true,
): Promise<APISuccessResponse<T>> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  const headers = new Headers(
    options.headers,
  );

  const kind=method==='POST'?numberKind(path,options.body):undefined;
  if(kind && typeof window!=='undefined' && document.documentElement.dataset.numberDialog==='ready' && !headers.has('X-NexEase-Numbering')){
    headers.set('X-NexEase-Numbering',JSON.stringify(await askNumber(kind,options.body)));
    options={...options,headers};
  }
  if (Capacitor.isNativePlatform()) headers.set("Origin", "https://localhost");
  headers.set(
    "Accept",
    "application/json",
  );

  let requestBody: BodyInit | undefined;

  if (options.body !== undefined) {
    if (
      options.body
      instanceof FormData
    ) {
      requestBody =
        options.body;
    } else {
      headers.set(
        "Content-Type",
        "application/json",
      );

      requestBody = JSON.stringify(
        options.body,
      );
    }
  }

  if (isUnsafeMethod(method)) {
    const csrfToken =
      await getCSRFToken();

    headers.set(
      "X-CSRFToken",
      csrfToken,
    );
  }

  const response = await apiFetch(
    buildURL(path),
    {
      ...options,
      method,
      headers,
      body: requestBody,
      credentials: "include",
      cache: options.cache ?? "no-store",
    },
  );

  const body =
    await parseAPIResponse<T>(response);

  if (!response.ok || !body.success) {
    const errorBody = body as APIErrorResponse;

    if (
      response.status === 403 &&
      errorBody.error?.code === "CSRF_FAILED" &&
      isUnsafeMethod(method) &&
      retryCSRF
    ) {
      clearCSRFToken();

      await getCSRFToken(true);

      return apiRequest<T>(
        path,
        options,
        false,
      );
    }

    if(isUnsafeMethod(method) && !path.startsWith("/auth/")) notify(errorBody.error?.message ?? "Could not save. Please try again.", response.status===403?"warning":"error");
    throw new APIRequestError({
      status: response.status,
      code:
        errorBody.error?.code ??
        "API_REQUEST_FAILED",
      message:
        errorBody.error?.message ??
        "The API request failed.",
      details: errorBody.error?.details,
      requestId: errorBody.request_id,
    });
  }

  if(isUnsafeMethod(method) && !/\/(auth|ai|ocr|lookup|preview|validate|subscription|owner|notifications)\//.test(path)) notify(body.message || "Your changes were saved successfully.");
  return body;
}

function getResponseFilename(
  response: Response,
): string | null {
  const disposition =
    response.headers.get(
      "content-disposition",
    );

  if (!disposition) {
    return null;
  }

  const utf8Match =
    disposition.match(
      /filename\*=UTF-8''([^;]+)/i,
    );

  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(
        utf8Match[1],
      );
    } catch {
      return utf8Match[1];
    }
  }

  const quotedMatch =
    disposition.match(
      /filename="([^"]+)"/i,
    );

  if (quotedMatch?.[1]) {
    return quotedMatch[1];
  }

  const plainMatch =
    disposition.match(
      /filename=([^;]+)/i,
    );

  return plainMatch?.[1]?.trim() ?? null;
}

async function throwBinaryAPIError(
  response: Response,
): Promise<never> {
  const contentType =
    response.headers.get(
      "content-type",
    ) ?? "";

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    const body =
      (await response.json()) as APIErrorResponse;

    throw new APIRequestError({
      status: response.status,

      code:
        body.error?.code ??
        "API_REQUEST_FAILED",

      message:
        body.error?.message ??
        "The API request failed.",

      details:
        body.error?.details,

      requestId:
        body.request_id,
    });
  }

  throw new APIRequestError({
    status: response.status,
    code: "API_REQUEST_FAILED",
    message: "The API request failed.",
  });
}

export async function apiBinaryRequest(
  path: string,
  options: APIRequestOptions = {},
  retryCSRF = true,
): Promise<APIBinaryResponse> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  const headers =
    new Headers(
      options.headers,
    );
  if (Capacitor.isNativePlatform()) headers.set("Origin", "https://localhost");
  headers.set(
    "Accept",
    "*/*",
  );

  let requestBody:
    BodyInit | undefined;

  if (options.body !== undefined) {
    if (
      options.body
      instanceof FormData
    ) {
      requestBody =
        options.body;
    } else {
      headers.set(
        "Content-Type",
        "application/json",
      );

      requestBody =
        JSON.stringify(
          options.body,
        );
    }
  }

  if (isUnsafeMethod(method)) {
    const csrfToken =
      await getCSRFToken();

    headers.set(
      "X-CSRFToken",
      csrfToken,
    );
  }

  const response =
    await apiFetch(
      buildURL(path),
      {
        ...options,
        method,
        headers,
        body: requestBody,
        credentials: "include",
        cache:
          options.cache ??
          "no-store",
      },
      true,
    );

  if (!response.ok) {
    if (
      response.status === 403
      &&
      isUnsafeMethod(method)
      &&
      retryCSRF
    ) {
      const contentType =
        response.headers.get(
          "content-type",
        ) ?? "";

      if (
        contentType.includes(
          "application/json",
        )
      ) {
        const body =
          (await response.clone().json()) as APIErrorResponse;

        if (
          body.error?.code
          === "CSRF_FAILED"
        ) {
          clearCSRFToken();

          await getCSRFToken(
            true,
          );

          return apiBinaryRequest(
            path,
            options,
            false,
          );
        }
      }
    }

    return throwBinaryAPIError(
      response,
    );
  }

  const blob =
    await response.blob();

  return {
    blob,

    filename:
      getResponseFilename(
        response,
      ),

    contentType:
      response.headers.get(
        "content-type",
      )
      ??
      blob.type
      ??
      "application/octet-stream",
  };
}