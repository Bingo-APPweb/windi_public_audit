// src/engine/timeline.js
async function getTimeline({ store, document_id }) {
  const events = await store.getByDocumentId(document_id);
  // já está em ordem de append; se futuramente vier de DB, ordenar por ts + inserção
  return events;
}

module.exports = { getTimeline };
