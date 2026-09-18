import { useState } from "react";

import { PageHeader } from "../components/shared/page-header";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useDiscovery } from "../hooks/use-discovery";
import { DashboardLayout } from "../layouts/dashboard-layout";
import type { DiscoveryFormat } from "../services/api/discovery";

const formats = ["OpenAPI JSON", "OpenAPI YAML", "Swagger", "GraphQL SDL", "GraphQL Introspection"];

export function NewScanPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceUrl, setSourceUrl] = useState("");
  const [rawSpecification, setRawSpecification] = useState("");
  const [formatHint, setFormatHint] = useState<DiscoveryFormat>("openapi_json");
  const [source, setSource] = useState<"file" | "url" | "text">("file");
  const [inputError, setInputError] = useState<string | null>(null);
  const { discover, endpoints, stage, error } = useDiscovery();

  const runDiscovery = async () => {
    setInputError(null);
    if (source === "file") {
      if (!selectedFile) return setInputError("Choose an API specification file to continue.");
      await discover({ content: await selectedFile.text(), filename: selectedFile.name, format_hint: formatHint });
      return;
    }
    if (source === "url") {
      if (!sourceUrl.trim()) return setInputError("Enter an API specification URL to continue.");
      await discover({ source_url: sourceUrl.trim(), format_hint: formatHint });
      return;
    }
    if (!rawSpecification.trim()) return setInputError("Paste an API specification to continue.");
    const extension = formatHint === "openapi_yaml" ? "yaml" : formatHint === "graphql_sdl" ? "graphql" : "json";
    await discover({ content: rawSpecification, filename: `specification.${extension}`, format_hint: formatHint });
  };

  const displayError = inputError ?? error;
  return (
    <DashboardLayout>
      <PageHeader title="Create a new scan" description="Discover API endpoints from a specification or URL." action={<Button onClick={runDiscovery} disabled={Boolean(stage)}>{stage ?? "Discover Endpoints"}</Button>} />
      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <div className="space-y-4">
          <Card className="p-5 sm:p-6"><p className="font-semibold">Upload API Specification</p><p className="mt-1 text-sm text-muted">Supported: {formats.join(" · ")}</p><label className="mt-5 flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-emerald-400/40 bg-emerald-400/[0.03] p-6 text-center transition-colors hover:bg-emerald-400/[0.08]"><span className="text-sm font-medium text-accent">{selectedFile?.name ?? "Drop a specification file here"}</span><span className="mt-2 text-xs text-muted">or click to browse from your device</span><input className="sr-only" type="file" accept=".json,.yaml,.yml,.graphql,.gql" onChange={event => { setSelectedFile(event.target.files?.[0] ?? null); setSource("file"); }} /></label></Card>
          <Card className="p-5 sm:p-6"><p className="font-semibold">Paste API URL</p><Input value={sourceUrl} onFocus={() => setSource("url")} onChange={event => { setSourceUrl(event.target.value); setSource("url"); }} className="mt-4" placeholder="https://api.example.com/openapi.json" /></Card>
          <Card className="p-5 sm:p-6"><p className="font-semibold">Paste API specification text</p><textarea value={rawSpecification} onFocus={() => setSource("text")} onChange={event => { setRawSpecification(event.target.value); setSource("text"); }} className="mt-4 min-h-40 w-full rounded-xl border border-line bg-slate-900/70 p-3 text-sm outline-none placeholder:text-slate-500 focus:border-emerald-400/60" placeholder="Paste OpenAPI, Swagger, or GraphQL schema text..." /></Card>
        </div>
        <Card className="h-fit p-5 sm:p-6"><p className="font-semibold">Discovery Configuration</p><p className="mt-1 text-sm text-muted">Only endpoint discovery runs in this milestone.</p><div className="mt-5 space-y-5"><label className="block text-sm text-slate-300">Specification format<select value={formatHint} onChange={event => setFormatHint(event.target.value as DiscoveryFormat)} className="mt-2 h-10 w-full rounded-lg border border-line bg-slate-900 px-3 text-sm"><option value="openapi_json">OpenAPI / Swagger JSON</option><option value="openapi_yaml">OpenAPI / Swagger YAML</option><option value="graphql_sdl">GraphQL SDL</option><option value="graphql_introspection">GraphQL Introspection</option></select></label><div><p className="text-sm text-slate-300">Authentication options</p><div className="mt-2 rounded-xl border border-line bg-slate-900/50 p-3 text-sm text-muted">Not included in endpoint discovery</div></div><Button onClick={runDiscovery} disabled={Boolean(stage)} className="w-full">{stage ?? "Discover Endpoints"}</Button></div></Card>
      </div>
      {stage && <p className="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-accent">{stage}</p>}
      {displayError && <p role="alert" className="mt-4 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{displayError}</p>}
      {endpoints.length > 0 && <Card className="mt-4 overflow-hidden"><div className="border-b border-line p-5 sm:p-6"><p className="font-semibold">Discovered Endpoints</p><p className="mt-1 text-sm text-muted">{endpoints.length} endpoints parsed and enriched by the Discovery Service.</p></div><div className="overflow-x-auto"><table className="min-w-[900px] w-full text-left text-sm"><thead className="bg-slate-950/25 text-xs uppercase tracking-wide text-muted"><tr>{["Endpoint", "Method", "Authentication Required", "Sensitivity", "Resource Group", "Parameters"].map(label => <th key={label} className="px-5 py-3 font-medium">{label}</th>)}</tr></thead><tbody>{endpoints.map(endpoint => <tr key={endpoint.id} className="border-b border-line/80 last:border-0"><td className="px-5 py-4 font-mono text-xs text-slate-200">{endpoint.path ?? endpoint.name ?? endpoint.id}</td><td className="px-5 py-4"><span className="rounded bg-slate-800 px-2 py-1 text-xs font-medium">{endpoint.method ?? endpoint.operation_type ?? "QUERY"}</span></td><td className="px-5 py-4 text-slate-300">{endpoint.enrichment.auth_required ? "Yes" : "No"}</td><td className="px-5 py-4 capitalize text-slate-300">{endpoint.enrichment.sensitivity}</td><td className="px-5 py-4 text-slate-300">{endpoint.enrichment.resource_group ?? "—"}</td><td className="px-5 py-4 text-xs text-muted">{[...endpoint.parameters.map(parameter => `${parameter.location}: ${parameter.name}`), ...endpoint.arguments.map(argument => argument.name)].join(", ") || "None"}</td></tr>)}</tbody></table></div></Card>}
    </DashboardLayout>
  );
}
