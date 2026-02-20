// src/store/store.js
class Store {
  async append(_event) { throw new Error("Not implemented"); }
  async getByDocumentId(_documentId) { throw new Error("Not implemented"); }
  async getLastHash(_documentId) { throw new Error("Not implemented"); }
}

module.exports = { Store };
