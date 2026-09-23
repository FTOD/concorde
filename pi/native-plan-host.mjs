/** The plan workflow's Host steps (bind, advance, finalize); provider logic only. */
import { runHostStep } from "./native-host-step.mjs";

const { value } = await runHostStep({ timeout: 60000 });
console.log(JSON.stringify(value));
