const crypto = require("crypto");

function sha256(buf) {
  return crypto.createHash("sha256").update(buf).digest();
}

function hex(buf) {
  return Buffer.isBuffer(buf) ? buf.toString("hex") : String(buf);
}

// RFC6962-style domain separation
function leafHash(leafPayloadCanonicalJson) {
  return sha256(Buffer.concat([Buffer.from([0x00]), Buffer.from(leafPayloadCanonicalJson, "utf8")]));
}

function nodeHash(left, right) {
  return sha256(Buffer.concat([Buffer.from([0x01]), left, right]));
}

module.exports = { sha256, hex, leafHash, nodeHash };
