import type { ModelMessage } from "ai";
export type AISettings = {
  baseURL: string;
  model: string;
  effort: string;
  durationMs: number;
  gripperPowerMw: number;
  compactTokens?: number;
};
export const DEFAULT_AI: AISettings = {
  baseURL: "http://127.0.0.1:8317/v1",
  model: "gpt-6-astra",
  effort: "medium",
  durationMs: 2000,
  gripperPowerMw: 0,
  compactTokens: 262144,
};
export type Entry = {
  id: string;
  kind: "user" | "assistant" | "tool" | "status";
  text: string;
  at: number;
  detail?: string;
};
export type Session = {
  messages: ModelMessage[];
  entries: Entry[];
  active: boolean;
  pending: string[];
  cacheKey?: string;
  contextScope?: string;
  usage?: { inputTokens?: number; cachedTokens?: number; responseMs?: number };
};
export const emptySession = (): Session => ({
  messages: [], entries: [], active: false, pending: [],
});
