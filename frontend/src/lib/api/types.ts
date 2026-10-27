export interface APIMetadata {
  api_version: string;
  response_timestamp: string;
}

export interface APISuccessResponse<T> {
  success: true;
  message?: string;
  data: T;
  request_id: string;
  meta?: APIMetadata;
}

export interface APIErrorData {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIErrorResponse {
  success: false;
  error: APIErrorData;
  request_id?: string;
  meta?: APIMetadata;
}

export type APIResponse<T> =
  | APISuccessResponse<T>
  | APIErrorResponse;

export interface CSRFData {
  csrf: {
    token: string;
    header_name: string;
    cookie_name: string;
  };
}
export interface APIPagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface APIQueryMetadata {
  search: string | null;
  filters: Record<
    string,
    string | number | boolean
  >;
  sort: string[];
}