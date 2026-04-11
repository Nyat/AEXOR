/**
 * AEXOR_HUB // NEURAL_FETCH_API
 * A high-performance, resilient fetch wrapper for professional image and media operations.
 * Standardized for Aexor Hub to ensure maximum security and zero-dependency compliance.
 */

type RequestConfig = {
  baseUrl?: string;
  headers?: Record<string, string>;
  timeout?: number;
};

type FetchOptions = RequestInit & {
  params?: Record<string, string | number | boolean>;
  timeout?: number;
};

class APIError extends Error {
  status: number;
  statusText: string;
  data: any;

  constructor(status: number, statusText: string, data: any) {
    super(`API_EXCEPTION: ${status} ${statusText}`);
    this.name = 'APIError';
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export class FetchAPI {
  private config: RequestConfig;

  constructor(config: RequestConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || '',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      timeout: config.timeout || 30000,
    };
  }

  private async request<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { params, timeout, ...init } = options;
    
    // Construct URL with params
    const url = new URL(endpoint, this.config.baseUrl || window.location.origin);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }

    // Prepare headers
    const headers = { ...this.config.headers, ...init.headers };

    // Handle abort/timeout
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout || this.config.timeout);

    try {
      const response = await fetch(url.toString(), {
        ...init,
        headers,
        signal: controller.signal,
      });

      clearTimeout(id);

      let data: any;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        throw new APIError(response.status, response.statusText, data);
      }

      return data as T;
    } catch (error: any) {
      clearTimeout(id);
      if (error.name === 'AbortError') {
        throw new Error('NETWORK_TIMEOUT: Request uplink failed to stabilize within the allotted window.');
      }
      throw error;
    }
  }

  public get<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  public post<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public put<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public delete<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Singleton instances for common endpoints
export const api = new FetchAPI();
