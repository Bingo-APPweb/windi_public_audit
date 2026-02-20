import Ajv from "ajv";
import addFormats from "ajv-formats";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const schemaPath = path.resolve(__dirname, "../../../windi-proof-spec/spec/proofset-schema.json");

const schema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const ajv = new Ajv();
addFormats(ajv);
const validate = ajv.compile(schema);

const HASH_PATTERN = /^sha256:[a-f0-9]{64}$/;

export function validateHashFormat(hash) {
  if (!HASH_PATTERN.test(hash)) {
    throw new Error("Invalid hash format: must be sha256:<64 hex chars>");
  }
}

export function validateProofSet(proofSet) {
  const valid = validate(proofSet);
  if (!valid) {
    throw new Error("Invalid ProofSet structure: " + JSON.stringify(validate.errors));
  }
}
