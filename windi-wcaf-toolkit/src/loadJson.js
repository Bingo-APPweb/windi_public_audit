// src/loadJson.js
const fs = require("fs");
const path = require("path");

function loadJson(filePath) {
  const resolved = path.resolve(filePath);

  if (!fs.existsSync(resolved)) {
    throw new Error(`File not found: ${resolved}`);
  }

  const content = fs.readFileSync(resolved, "utf8");

  try {
    return JSON.parse(content);
  } catch (err) {
    throw new Error(`Invalid JSON in ${filePath}: ${err.message}`);
  }
}

module.exports = { loadJson };
