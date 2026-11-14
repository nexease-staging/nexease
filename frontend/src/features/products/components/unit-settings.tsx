"use client";
import {useState} from "react";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";

export default function UnitSettings({canCreate}: {canCreate: boolean}) {
  const [name, setName] = useState("");
  const client = useQueryClient();
  const units = useQuery({
    queryKey: ["product-units"],
    queryFn: async () => (await apiRequest<{units: string[]}>("/units/")).data.units,
  });
  const save = useMutation({
    mutationFn: () => apiRequest("/units/", {method: "POST", body: {name: name.trim()}}),
    onSuccess: async () => {
      setName("");
      await client.invalidateQueries({queryKey: ["product-units"]});
    },
  });
  return <details className="nx-card p-4"><summary>Product units</summary>
    <p>{units.isLoading ? "Loading units…" : units.isError ? "Could not load units." : units.data?.join(", ") || "No units yet."}</p>
    {canCreate && <form onSubmit={e => {e.preventDefault(); if (name.trim() && !save.isPending) save.mutate();}}>
      <label>New unit<input className="nx-input" value={name} maxLength={30} required
        placeholder="e.g. Carton" onChange={e => setName(e.target.value)} /></label>
      <button className="nx-button" disabled={save.isPending || !name.trim()}>Add unit</button>
      {save.isError && <p role="alert">{save.error.message}</p>}
    </form>}
  </details>;
}
