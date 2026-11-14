import type { AssistantContent, ModelMessage } from "ai";

type AssistantPart = Exclude<AssistantContent, string>[number];
function isCompaction(part: AssistantPart) {
  return part.type === "custom" && part.kind === "openai.compaction" &&
    typeof part.providerOptions?.openai?.itemId === "string" &&
    part.providerOptions.openai.itemId.length > 0 &&
    typeof part.providerOptions.openai.encryptedContent === "string" &&
    part.providerOptions.openai.encryptedContent.length > 0;
}
export function hasCompaction(messages: ModelMessage[]) {
  return messages.some((m) => m.role === "assistant" && Array.isArray(m.content) && m.content.some(isCompaction));
}

// OpenAI's stateless native compaction protocol: retain the opaque checkpoint
// and everything after it. Stored history stays complete; nothing is summarized
// or removed from the active window between native checkpoints.
export function activeContext(messages: ModelMessage[]): ModelMessage[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    if (message.role !== "assistant" || typeof message.content === "string") continue;
    const index = message.content.findLastIndex(isCompaction);
    if (index >= 0)
      return [{ ...message, content: message.content.slice(index) }, ...messages.slice(i + 1)];
  }
  return messages;
}

// Opaque checkpoints belong to the provider/model that produced them. The full
// original transcript remains available when the user changes that configuration.
export function withoutCompactions(messages: ModelMessage[]): ModelMessage[] {
  return messages.flatMap((message) => {
    if (message.role !== "assistant" || typeof message.content === "string") return [message];
    const content = message.content.filter((p) => p.type !== "custom" || p.kind !== "openai.compaction");
    return content.length ? [{ ...message, content }] : [];
  });
}
