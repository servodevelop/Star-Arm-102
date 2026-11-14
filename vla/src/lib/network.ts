// Adapted from robot-arm frontend AI network recovery (5412efe).
import { wrapLanguageModel } from "ai";

export const networkRetries = 15;
export const networkRetryDelayMs = 10_000;
export type NetworkRetry = { attempt: number; nextAt: number; error: string };

export function networkErrorMessage(error: unknown): string {
  if (error && typeof error === "object") {
    const value = error as { message?: unknown; cause?: unknown; value?: { response?: { error?: unknown } } };
    if (typeof value.message === "string") return value.message;
    const nested = value.value?.response?.error ?? value.cause;
    if (nested) return networkErrorMessage(nested);
  }
  return String(error);
}

export function transientNetworkError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const value = error as {
    name?: string;
    message?: string;
    code?: string;
    statusCode?: number;
    cause?: unknown;
    value?: { response?: { error?: unknown } };
  };
  if (value.name === "AbortError") return false;
  if (value.statusCode != null && value.statusCode >= 400)
    return [408, 500, 502, 503, 504].includes(value.statusCode);
  return (
    value.name === "TimeoutError" ||
    /ECONNRESET|ECONNREFUSED|EHOSTUNREACH|ENETUNREACH|ETIMEDOUT|EAI_AGAIN|UND_ERR_(SOCKET|CONNECT_TIMEOUT|HEADERS_TIMEOUT|BODY_TIMEOUT)/.test(
      value.code ?? "",
    ) ||
    /fetch failed|failed to fetch|network error|network request failed|socket|TLS handshake.*EOF|stream (disconnected|closed)|stream ended without a terminal response event|connection (reset|closed)|Cannot connect to API/i.test(
      value.message ?? "",
    ) ||
    transientNetworkError(value.cause) ||
    transientNetworkError(value.value?.response?.error)
  );
}

export function networkRecovery(
  signal?: AbortSignal,
  onRetry?: (status: NetworkRetry) => Promise<void>,
) {
  let attempts = 0;
  async function retry(error: unknown) {
    signal?.throwIfAborted();
    if (!transientNetworkError(error) || attempts >= networkRetries)
      throw error;
    attempts++;
    await onRetry?.({
      attempt: attempts,
      nextAt: Date.now() + networkRetryDelayMs,
      error: networkErrorMessage(error),
    });
    await new Promise<void>((resolve, reject) => {
      const abort = () => {
        clearTimeout(timer);
        reject(signal!.reason);
      };
      const timer = setTimeout(() => {
        signal?.removeEventListener("abort", abort);
        resolve();
      }, networkRetryDelayMs);
      if (signal?.aborted) abort();
      else signal?.addEventListener("abort", abort, { once: true });
    });
  }
  return {
    retry,
    async run<T>(operation: () => PromiseLike<T>): Promise<T> {
      for (;;) {
        signal?.throwIfAborted();
        try {
          return await operation();
        } catch (error) {
          await retry(error);
        }
      }
    },
  };
}

/** One retry budget per model step, including connection and stream failures.
 * SDK streamRetries owns buffering/discarding incomplete tool calls. This
 * middleware only classifies failures and supplies the requested fixed delay.
 */
export function resilientModel(
  model: Parameters<typeof wrapLanguageModel>[0]["model"],
  signal: AbortSignal,
  onRetry?: (status: NetworkRetry) => Promise<void>,
) {
  const recovery = networkRecovery(signal, onRetry);
  return wrapLanguageModel({
    model,
    middleware: {
      specificationVersion: "v4",
      wrapStream: async ({ doStream }) => {
        const result = await recovery.run(doStream);
        const reader = result.stream.getReader();
        let finished = false;
        return {
          ...result,
          stream: new ReadableStream({
            async pull(controller) {
              try {
                let part;
                try {
                  part = await reader.read();
                } catch (error) {
                  part = {
                    done: false,
                    value: { type: "error" as const, error },
                  };
                }
                if (part.done) {
                  if (finished) {
                    controller.close();
                    return;
                  }
                  part = {
                    done: false,
                    value: {
                      type: "error" as const,
                      error: Error(
                        "stream ended without a terminal response event",
                      ),
                    },
                  };
                }
                if (part.value.type === "finish") finished = true;
                if (part.value.type === "error") {
                  await recovery.retry(part.value.error);
                  controller.enqueue(part.value);
                  controller.close();
                  await reader.cancel().catch(() => {});
                  return;
                }
                controller.enqueue(part.value);
              } catch (error) {
                // Fatal/exhausted errors must not flush an incomplete tool call.
                controller.error(error);
                await reader.cancel(error).catch(() => {});
              }
            },
            cancel: (reason) => reader.cancel(reason),
          }),
        };
      },
    },
  });
}
