import { messages } from "./messages";

export type Locale = "en" | "zh";
export const LOCALE_KEY = "vla-language";
let locale: Locale = "en";
const listeners = new Set<() => void>();
const reverse = new Map(Object.entries(messages).map(([zh, en]) => [en, zh]));
const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// Translate saved application statuses too; user and assistant prose stays intact.
const patterns = Object.entries(messages).flatMap(([zh, en]) => {
  if (!/\{\d+\}/.test(zh)) return [];
  return [zh, en].map((source) => {
    const indices = [...source.matchAll(/\{(\d+)\}/g)].map((m) => +m[1]);
    const parts = source.split(/\{\d+\}/).map(escape);
    return {
      pattern: new RegExp(`^${parts.join("([\\s\\S]*?)")}$`),
      indices,
      zh,
      en,
    };
  });
});

export function translate(
  text: string,
  language: Locale,
  ...values: unknown[]
): string {
  const key = Object.hasOwn(messages, text) ? text : reverse.get(text);
  const result = key ? (language === "zh" ? key : messages[key]) : text;
  if (!key && !values.length) {
    for (const { pattern, indices, zh } of patterns) {
      const match = pattern.exec(text);
      if (!match) continue;
      const captured: string[] = [];
      indices.forEach((index, i) => {
        captured[index] = match[i + 1];
      });
      return translate(zh, language, ...captured);
    }
  }
  return result.replace(/\{(\d+)\}/g, (token, index) => {
    if (Number(index) >= values.length) return token;
    const value = String(values[index]);
    const valueKey = Object.hasOwn(messages, value)
      ? value
      : reverse.get(value);
    return valueKey
      ? language === "zh"
        ? valueKey
        : messages[valueKey]
      : value;
  });
}
export const t = (text: string, ...values: unknown[]) =>
  translate(text, locale, ...values);
export const getLocale = () => locale;
export const subscribeLocale = (listener: () => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};
export function setLocale(next: Locale) {
  locale = next;
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(LOCALE_KEY, next);
    } catch {
      /* Language still works without storage. */
    }
  }
  listeners.forEach((listener) => listener());
}
export function restoreLocale() {
  let saved: string | null = null;
  try {
    saved = localStorage.getItem(LOCALE_KEY);
  } catch {
    /* Default to English. */
  }
  setLocale(saved === "zh" ? "zh" : "en");
}
