// src/store/memoryStore.js
const { Store } = require("./store");

class MemoryStore extends Store {
  constructor() {
    super();
    this.eventsByDoc = new Map(); // document_id -> [events]
  }

  async append(event) {
    const docId = event.document_id;
    const arr = this.eventsByDoc.get(docId) || [];
    arr.push(event);
    this.eventsByDoc.set(docId, arr);
    return event;
  }

  async getByDocumentId(documentId) {
    return (this.eventsByDoc.get(documentId) || []).slice();
  }

  async getLastHash(documentId) {
    const arr = this.eventsByDoc.get(documentId) || [];
    if (!arr.length) return null;
    return arr[arr.length - 1].event_hash || null;
  }
}

module.exports = { MemoryStore };
