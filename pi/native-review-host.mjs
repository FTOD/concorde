/** The review workflow's Host steps (bind, finalize); provider logic only. */
import { runHostStep } from "./native-host-step.mjs";

const { value } = await runHostStep({ timeout: 1800000 });
console.log(JSON.stringify(value));
