/** Capture a native structured_output proposal through Pi's supported tool event.
 * This does not mark execution or business work complete and does not schedule work.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export function observeNativeProposal(
	pi: ExtensionAPI,
	submit: (value: Record<string, unknown>) => Promise<void>,
	invalidate: (reason: string) => Promise<void>,
): void {
	let observed = false;
	pi.on("tool_result", async (event) => {
		if (event.toolName !== "structured_output" || event.isError) return;
		if (observed) {
			await invalidate("multiple native structured submissions");
			return {
				isError: true,
				content: [
					{
						type: "text",
						text: "Concorde rejects duplicate structured submissions.",
					},
				],
			};
		}
		observed = true;
		const input = event.input as Record<string, unknown>;
		const value = input.value;
		if (!value || typeof value !== "object" || Array.isArray(value)) {
			await invalidate("native proposal is not an object");
			return {
				isError: true,
				content: [
					{ type: "text", text: "Concorde requires an object proposal." },
				],
			};
		}
		try {
			await submit(value as Record<string, unknown>);
		} catch {
			await invalidate("native proposal capture failed");
			return {
				isError: true,
				content: [
					{
						type: "text",
						text: "Concorde rejected this proposal; no business completion was accepted.",
					},
				],
			};
		}
	});
}
