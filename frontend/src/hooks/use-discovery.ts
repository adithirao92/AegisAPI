import { useState } from "react";

import { discoverApi, type DiscoveredEndpoint, type DiscoveryRequest } from "../services/api/discovery";

const pause = (milliseconds: number) => new Promise(resolve => window.setTimeout(resolve, milliseconds));

export function useDiscovery() {
  const [endpoints, setEndpoints] = useState<DiscoveredEndpoint[]>([]);
  const [stage, setStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function discover(request: DiscoveryRequest) {
    setError(null);
    setEndpoints([]);
    setStage("Uploading...");
    await pause(180);
    setStage("Parsing API...");
    await pause(180);
    setStage("Discovering endpoints...");
    try {
      setEndpoints(await discoverApi(request));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Discovery failed. Please try again.");
    } finally {
      setStage(null);
    }
  }

  return { discover, endpoints, stage, error };
}
