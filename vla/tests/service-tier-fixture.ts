// Responses protocol fixture for SDK and page tests; sends no network requests.
import { DEFAULT_AI } from "../src/lib/types";

export function streamResponse(index: number, tier: string, callName?: string) {
  const call = callName && {
    type: "function_call",
    id: `fc-${index}`,
    call_id: `call-${index}`,
    name: callName,
    arguments:
      callName === "describe_input" ? '{"description":"Text only"}' : "{}",
    status: "completed",
  };
  const text = {
    type: "message",
    id: `msg-${index}`,
    role: "assistant",
    status: "completed",
    content: [{ type: "output_text", text: "Done", annotations: [] }],
  };
  const events = [
    {
      type: "response.created",
      response: {
        id: `resp-${index}`,
        created_at: index,
        model: DEFAULT_AI.model,
      },
    },
    ...(call
      ? [
          {
            type: "response.output_item.added",
            output_index: 0,
            item: { ...call, arguments: "" },
          },
          {
            type: "response.function_call_arguments.delta",
            item_id: call.id,
            output_index: 0,
            delta: call.arguments,
          },
          { type: "response.output_item.done", output_index: 0, item: call },
        ]
      : [
          {
            type: "response.output_item.added",
            output_index: 0,
            item: { ...text, content: [] },
          },
          {
            type: "response.output_text.delta",
            item_id: text.id,
            output_index: 0,
            content_index: 0,
            delta: "Done",
          },
          { type: "response.output_item.done", output_index: 0, item: text },
        ]),
    {
      type: "response.completed",
      response: {
        id: `resp-${index}`,
        status: "completed",
        service_tier: tier,
        output: [call || text],
        usage: { input_tokens: 100, output_tokens: 10, total_tokens: 110 },
      },
    },
  ];
  return new Response(
    events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""),
    { headers: { "content-type": "text/event-stream" } },
  );
}
