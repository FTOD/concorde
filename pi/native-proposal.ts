/** Capture proposals via the supported Pi event; neither submission nor capture is completion. */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { errorFeedback, executionError, failure } from "./execution-error.mjs";
import { errorDisplay } from "./error-display.mjs";

export function observeNativeProposal(
	pi: ExtensionAPI,
	submit: (value: Record<string, unknown>) => Promise<void>,
	invalidate: (reason: string) => Promise<void>,
	observeFailure?: (feedback: unknown) => Promise<void>,
): void {
	let observed = false;
	const recorded = new Set<string>();
	// Cache the settled notification, including refusal. Re-report a failed observation
	// without retrying persistence whose side effects may be unknown.
	const notifications = new Map<string, Promise<void>>();
	// SDK validation failures are immediate Agent-core results and bypass tool_result.
	// Its supported notification still arrives before native terminal publication.
	pi.on("tool_execution_end", async (event) => {
		if (event.toolName !== "structured_output" || !event.isError) return;
		const prior = notifications.get(event.toolCallId);
		if (prior) return prior;
		if (recorded.has(event.toolCallId)) return;
		const text =
			event.result.content
				?.filter((part: any) => part.type === "text")
				.map((part: any) => part.text)
				.join("\n") ?? "Lower-level tool error unavailable";
		const feedback = failure(
			"Native structured submission failed before capture",
			{
				layer: "structured-output",
				attempt: event.toolCallId,
				category: text.startsWith(
					'Validation failed for tool "structured_output":',
				)
					? "schema-rejection"
					: "unknown",
				diagnostics: text,
			},
		);
		const notification = (async () => {
			try {
				await observeFailure?.(feedback);
			} catch (error) {
				feedback.causes.push(
					errorFeedback(error, {
						layer: "proposal-observation",
						category: "observation",
						attempt: event.toolCallId,
					}),
				);
				feedback.diagnostics.complete = false;
				// SDK notification hooks cannot patch the tool result. Their supported
				// extension-error channel (also recorded by native child reporting)
				// receives the combined sanitized cause or its explicit retrieval ref.
				const reported = executionError(feedback, error);
				reported.message = errorDisplay(feedback);
				throw reported;
			}
		})();
		notifications.set(event.toolCallId, notification);
		return notification;
	});
	pi.on("tool_result", async (event) => {
		if (event.toolName !== "structured_output") return;
		const attempt = event.toolCallId;
		recorded.add(attempt);
		let feedback;
		if (event.isError) {
			// Native tool refusal is not necessarily a schema failure.
			const text = event.content
				.filter((part) => part.type === "text")
				.map((part: any) => part.text)
				.join("\n");
			feedback = failure(
				"Native structured submission was rejected before Host capture",
				{
					layer: "structured-output",
					category: text.startsWith(
						'Validation failed for tool "structured_output":',
					)
						? "schema-rejection"
						: "unknown",
					attempt,
					diagnostics: text,
				},
			);
			try {
				await observeFailure?.(feedback);
			} catch (error) {
				feedback.causes.push(
					errorFeedback(error, {
						layer: "proposal-observation",
						category: "observation",
						attempt,
					}),
				);
				feedback.diagnostics.complete = false;
			}
		} else {
			if (observed)
				feedback = failure(
					"Concorde rejects duplicate structured submissions",
					{
						code: "invalid_completion",
						layer: "proposal",
						category: "host-refusal",
						attempt,
					},
				);
			else {
				observed = true;
				const value = (event.input as Record<string, unknown>).value;
				if (!value || typeof value !== "object" || Array.isArray(value))
					feedback = failure("Concorde requires an object proposal", {
						code: "invalid_completion",
						layer: "proposal",
						category: "schema-rejection",
						attempt,
					});
				else
					try {
						await submit(value as Record<string, unknown>);
						return;
					} catch (error) {
						feedback = failure(
							"Concorde proposal submission failed; no business completion accepted",
							{
								layer: "proposal",
								category: "capture-failure",
								attempt,
								causes: [errorFeedback(error)],
							},
						);
					}
			}
			try {
				await invalidate(JSON.stringify(feedback));
			} catch (error) {
				feedback.causes.push(
					errorFeedback(error, { layer: "proposal-invalidation", attempt }),
				);
			}
		}
		return {
			isError: true,
			content: [{ type: "text" as const, text: errorDisplay(feedback) }],
			details: { concorde_failure: feedback },
		};
	});
}
