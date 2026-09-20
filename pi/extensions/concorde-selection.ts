/** Explicit per-launch provenance transport; never discovery or a fallback path. */
export function selectionPath(): string | undefined {
	const direct = process.env.CONCORDE_SESSION_SELECTION;
	const raw = process.env.PI_SUBAGENT_EXTENSION_BINDINGS;
	let bound: string | undefined;
	if (raw) {
		if (Buffer.byteLength(raw) > 16384)
			throw new Error("Invalid child extension bindings");
		const bindings = JSON.parse(raw);
		const value = bindings?.["concorde/1"];
		if (value !== undefined) {
			if (
				!value ||
				typeof value !== "object" ||
				Object.keys(value).join() !== "selection" ||
				typeof value.selection !== "string" ||
				!value.selection
			)
				throw new Error(
					"concorde/1 binding requires exactly one explicit selection path",
				);
			bound = value.selection;
		}
	}
	if (direct && bound && direct !== bound)
		throw new Error("Conflicting private selection transports");
	return bound ?? direct;
}
