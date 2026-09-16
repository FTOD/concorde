/** Bounded offline contract schema vocabulary. No remote/schema-driven file loading or code generation. */
import { requireThat } from "./reading-format";

const vocabulary = new Set([
  "$schema",
  "$id",
  "$defs",
  "$ref",
  "title",
  "description",
  "examples",
  "default",
  "type",
  "properties",
  "required",
  "additionalProperties",
  "items",
  "minItems",
  "maxItems",
  "uniqueItems",
  "minLength",
  "maxLength",
  "pattern",
  "minimum",
  "maximum",
  "enum",
  "const",
  "anyOf",
  "oneOf",
  "allOf",
  "format",
]);
const kinds = new Set([
  "object",
  "array",
  "string",
  "integer",
  "number",
  "boolean",
  "null",
]);
const object = (v: unknown): v is Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v);
function canonical(value: any): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (object(value))
    return `{${Object.keys(value)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`)
      .join(",")}}`;
  return JSON.stringify(value);
}
function target(ref: unknown, root: any, subject: string): any {
  requireThat(
    typeof ref === "string" && /^#\/\$defs\/[^/]+$/.test(ref),
    `Only direct offline $defs references are supported: ${subject}`,
  );
  const name = ref.slice(8).replace(/~1/g, "/").replace(/~0/g, "~");
  requireThat(
    object(root.$defs) && Object.hasOwn(root.$defs, name),
    `Unknown schema reference: ${subject}`,
  );
  return root.$defs[name];
}
function admit(schema: any, root: any, subject: string, depth = 0): void {
  requireThat(depth <= 100, `Schema nesting limit exceeded: ${subject}`);
  if (typeof schema === "boolean") return;
  requireThat(
    object(schema),
    `Schema must be an object or boolean: ${subject}`,
  );
  requireThat(
    Object.keys(schema).every((k) => vocabulary.has(k)),
    `Unsupported offline schema keyword: ${subject}`,
  );
  if (schema.$ref !== undefined) target(schema.$ref, root, subject);
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    requireThat(
      types.length &&
        new Set(types).size === types.length &&
        types.every((t) => kinds.has(t)),
      `Invalid schema type: ${subject}`,
    );
  }
  for (const key of ["properties", "$defs"])
    if (schema[key] !== undefined) {
      requireThat(object(schema[key]), `Invalid schema ${key}: ${subject}`);
      for (const child of Object.values(schema[key]))
        admit(child, root, subject, depth + 1);
    }
  for (const key of ["items", "additionalProperties"])
    if (schema[key] !== undefined) admit(schema[key], root, subject, depth + 1);
  if (schema.required !== undefined)
    requireThat(
      Array.isArray(schema.required) &&
        schema.required.every((k: any) => typeof k === "string") &&
        new Set(schema.required).size === schema.required.length,
      `Invalid required keys: ${subject}`,
    );
  for (const key of ["anyOf", "oneOf", "allOf"])
    if (schema[key] !== undefined) {
      requireThat(
        Array.isArray(schema[key]) && schema[key].length,
        `Invalid ${key}: ${subject}`,
      );
      for (const child of schema[key]) admit(child, root, subject, depth + 1);
    }
  for (const key of ["minItems", "maxItems", "minLength", "maxLength"])
    if (schema[key] !== undefined)
      requireThat(
        typeof schema[key] === "number" &&
          Number.isInteger(schema[key]) &&
          schema[key] >= 0,
        `Invalid schema bound: ${subject}`,
      );
  for (const key of ["minimum", "maximum"])
    if (schema[key] !== undefined)
      requireThat(
        typeof schema[key] === "number" && Number.isFinite(schema[key]),
        `Invalid numeric bound: ${subject}`,
      );
  for (const [min, max] of [
    ["minItems", "maxItems"],
    ["minLength", "maxLength"],
    ["minimum", "maximum"],
  ]) {
    const lower = schema[min],
      upper = schema[max];
    requireThat(
      lower === undefined ||
        upper === undefined ||
        (typeof lower === "number" &&
          typeof upper === "number" &&
          lower <= upper),
      `Inverted bounds: ${subject}`,
    );
  }
  if (schema.uniqueItems !== undefined)
    requireThat(
      typeof schema.uniqueItems === "boolean",
      `Invalid uniqueItems: ${subject}`,
    );
  if (schema.enum !== undefined)
    requireThat(
      Array.isArray(schema.enum) && schema.enum.length,
      `Invalid enum: ${subject}`,
    );
  if (schema.format !== undefined)
    requireThat(
      schema.format === "project-path",
      `Unsupported schema format: ${subject}`,
    );
  if (schema.pattern !== undefined) {
    requireThat(
      typeof schema.pattern === "string",
      `Invalid pattern: ${subject}`,
    );
    new RegExp(schema.pattern);
  }
}
function matches(value: any, type: string): boolean {
  return type === "null"
    ? value === null
    : type === "array"
      ? Array.isArray(value)
      : type === "object"
        ? object(value)
        : type === "integer"
          ? typeof value === "number" && Number.isInteger(value)
          : type === "number"
            ? typeof value === "number" && Number.isFinite(value)
            : typeof value === type;
}
function check(
  value: any,
  schema: any,
  root: any,
  subject: string,
  depth = 0,
): void {
  requireThat(depth <= 100, `Schema validation depth exceeded: ${subject}`);
  if (schema === true) return;
  requireThat(schema !== false, `Example rejected by schema: ${subject}`);
  if (schema.$ref !== undefined)
    check(value, target(schema.$ref, root, subject), root, subject, depth + 1);
  if (schema.type !== undefined)
    requireThat(
      (Array.isArray(schema.type) ? schema.type : [schema.type]).some(
        (t: string) => matches(value, t),
      ),
      `Example type differs from schema: ${subject}`,
    );
  if (schema.enum !== undefined)
    requireThat(
      schema.enum.some((item: any) => canonical(item) === canonical(value)),
      `Example not in enum: ${subject}`,
    );
  if (Object.hasOwn(schema, "const"))
    requireThat(
      canonical(schema.const) === canonical(value),
      `Example differs from const: ${subject}`,
    );
  for (const key of ["anyOf", "oneOf", "allOf"])
    if (schema[key] !== undefined) {
      const results = schema[key].map((child: any) => {
        try {
          check(value, child, root, subject, depth + 1);
          return true;
        } catch {
          return false;
        }
      });
      requireThat(
        key === "anyOf"
          ? results.some(Boolean)
          : key === "allOf"
            ? results.every(Boolean)
            : results.filter(Boolean).length === 1,
        `Example fails ${key}: ${subject}`,
      );
    }
  if (object(value)) {
    for (const key of schema.required ?? [])
      requireThat(
        Object.hasOwn(value, key),
        `Missing required example property: ${subject}`,
      );
    for (const [key, item] of Object.entries(value)) {
      if (Object.hasOwn(schema.properties ?? {}, key))
        check(item, schema.properties[key], root, subject, depth + 1);
      else if (schema.additionalProperties !== undefined)
        check(item, schema.additionalProperties, root, subject, depth + 1);
    }
  }
  if (Array.isArray(value)) {
    requireThat(
      schema.minItems === undefined || value.length >= schema.minItems,
      `Example array too short: ${subject}`,
    );
    requireThat(
      schema.maxItems === undefined || value.length <= schema.maxItems,
      `Example array too long: ${subject}`,
    );
    if (schema.uniqueItems)
      requireThat(
        new Set(value.map(canonical)).size === value.length,
        `Example array is not unique: ${subject}`,
      );
    if (schema.items !== undefined)
      for (const item of value)
        check(item, schema.items, root, subject, depth + 1);
  }
  if (typeof value === "string") {
    const length = [...value].length;
    requireThat(
      schema.minLength === undefined || length >= schema.minLength,
      `Example string too short: ${subject}`,
    );
    requireThat(
      schema.maxLength === undefined || length <= schema.maxLength,
      `Example string too long: ${subject}`,
    );
    if (schema.pattern !== undefined)
      requireThat(
        new RegExp(schema.pattern).test(value),
        `Example pattern mismatch: ${subject}`,
      );
    if (schema.format === "project-path")
      requireThat(
        value &&
          !/[\\:\x00-\x1f\x7f]/.test(value) &&
          !value.startsWith("/") &&
          value.split("/").every((p) => p && p !== "." && p !== ".."),
        `Unsafe example path: ${subject}`,
      );
  }
  if (typeof value === "number") {
    requireThat(
      Number.isFinite(value),
      `Non-finite example number: ${subject}`,
    );
    requireThat(
      schema.minimum === undefined || value >= schema.minimum,
      `Example below minimum: ${subject}`,
    );
    requireThat(
      schema.maximum === undefined || value <= schema.maximum,
      `Example above maximum: ${subject}`,
    );
  }
}
export function validateContractExample(
  schema: any,
  example: any,
  subject: string,
): void {
  admit(schema, schema, subject);
  check(example, schema, schema, subject);
}
