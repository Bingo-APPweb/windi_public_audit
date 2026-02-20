/**
 * WINDI D1 — Document Sidebar
 * Document list, create new, load existing
 */
import React, { useEffect, useState } from 'react';
import useDocStore from '../stores/docStore';

export default function DocSidebar({ onClose }) {
  const { docId, createDoc, loadDoc, deleteDoc, listDocs } = useDocStore();
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    const list = await listDocs();
    setDocs(list);
    setLoading(false);
  };

  useEffect(() => { refresh(); }, [docId]);

  const handleCreate = async () => {
    await createDoc();
    await refresh();
    if (onClose) onClose();
  };

  const handleLoad = async (id) => {
    await loadDoc(id);
    if (onClose) onClose();
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this document? This cannot be undone.')) return;
    await deleteDoc(id);
    await refresh();
  };

  return (
    <div className="d1-sidebar">
      <div className="sidebar-header">
        <h2>Documents</h2>
        <button className="btn-create" onClick={handleCreate} title="New Document">
          + New
        </button>
      </div>

      {loading ? (
        <div className="sidebar-loading">Loading...</div>
      ) : docs.length === 0 ? (
        <div className="sidebar-empty">
          <p>No documents yet.</p>
          <p>Click <strong>+ New</strong> to start.</p>
        </div>
      ) : (
        <ul className="doc-list">
          {docs.map(doc => (
            <li
              key={doc.docId}
              className={`doc-item ${doc.docId === docId ? 'active' : ''}`}
              onClick={() => handleLoad(doc.docId)}
            >
              <span className="doc-title">{doc.title || 'Untitled'}</span>
              <span className="doc-date">
                {new Date(doc.updatedAt).toLocaleDateString('de-DE', {
                  day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
                })}
              </span>
              <button
                className="btn-delete"
                onClick={(e) => handleDelete(doc.docId, e)}
                title="Delete"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="sidebar-footer">
        <span className="windi-mark">WINDI Desktop • DOC</span>
      </div>
    </div>
  );
}
