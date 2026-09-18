export type DiscoveryFormat = "openapi_json" | "openapi_yaml" | "graphql_sdl" | "graphql_introspection";

export interface DiscoveryRequest {
  content?: string;
  source_url?: string;
  filename?: string;
  format_hint?: DiscoveryFormat;
}

export interface DiscoveredEndpoint {
  id: string;
  endpoint_type: string;
  path: string | null;
  method: string | null;
  operation_type: string | null;
  name: string | null;
  parameters: Array<{ name: string; location: string; required: boolean }>;
  arguments: Array<{ name: string; type_name: string | null; required: boolean }>;
  enrichment: {
    auth_required: boolean;
    sensitivity: "low" | "medium" | "high";
    resource_group: string | null;
  };
}

interface DiscoveryResponse { items: DiscoveredEndpoint[]; }

export class DiscoveryApiError extends Error {
  constructor(message: string, readonly code: "INVALID_SPECIFICATION" | "SERVER_UNAVAILABLE") {
    super(message);
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function discoverApi(request: DiscoveryRequest): Promise<DiscoveredEndpoint[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/discovery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof payload.detail === "string" ? payload.detail : "The specification could not be parsed.";
      throw new DiscoveryApiError(
        response.status >= 500 ? "The discovery server is unavailable. Please try again." : detail,
        response.status >= 500 ? "SERVER_UNAVAILABLE" : "INVALID_SPECIFICATION"
      );
    }
    return (payload as DiscoveryResponse).items;
  } catch (error) {
    if (error instanceof DiscoveryApiError) throw error;
    throw new DiscoveryApiError("The discovery server is unavailable. Please try again.", "SERVER_UNAVAILABLE");
  }
}
