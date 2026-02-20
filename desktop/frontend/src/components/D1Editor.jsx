/**
 * WINDI D1 — Tiptap Editor Core
 * Governance-aware document editor with integrity tracking
 */
import React, { useEffect, useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Placeholder from '@tiptap/extension-placeholder';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import useDocStore from '../stores/docStore';
import EditorToolbar from './EditorToolbar';

export default function D1Editor() {
  const { docId, content, saveStatus, integrityStatus, updateContent, createDoc, loadDoc } = useDocStore();

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        history: { depth: 100 },
      }),
      Underline,
      Link.configure({ openOnClick: false, HTMLAttributes: { rel: 'noopener noreferrer' } }),
      Image.configure({ inline: false, allowBase64: true }),
      Placeholder.configure({ placeholder: 'Begin typing your document...' }),
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
    ],
    content: content || { type: 'doc', content: [{ type: 'paragraph' }] },
    onUpdate: ({ editor }) => {
      const json = editor.getJSON();
      updateContent(json);
    },
    editorProps: {
      attributes: {
        class: 'windi-d1-editor-content',
        spellcheck: 'true',
      },
    },
  });

  // Sync store content → editor when loading a doc
  useEffect(() => {
    if (editor && content && !editor.isDestroyed) {
      const currentJson = JSON.stringify(editor.getJSON());
      const storeJson = JSON.stringify(content);
      if (currentJson !== storeJson) {
        editor.commands.setContent(content, false);
      }
    }
  }, [docId]); // only on doc change, not every content update

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeydown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        useDocStore.getState().saveDoc();
      }
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  if (!editor) return null;

  return (
    <div className="d1-editor-wrapper">
      <EditorToolbar editor={editor} />
      <div className="d1-editor-body">
        <EditorContent editor={editor} />
      </div>
      <StatusBar saveStatus={saveStatus} integrityStatus={integrityStatus} />
    </div>
  );
}

function StatusBar({ saveStatus, integrityStatus }) {
  const statusIcons = {
    idle: '—',
    saving: '⟳ Saving...',
    saved: '✓ Saved',
    error: '✗ Error',
  };

  const integrityIcons = {
    unknown: '◌',
    ok: '🟢 Integrity OK',
    mismatch: '🔴 MISMATCH',
    checking: '⟳ Checking...',
  };

  return (
    <div className="d1-status-bar">
      <span className={`save-status save-${saveStatus}`}>
        {statusIcons[saveStatus] || '—'}
      </span>
      <span className={`integrity-status integrity-${integrityStatus}`}>
        {integrityIcons[integrityStatus] || '◌'}
      </span>
      <span className="d1-branding">WINDI D1 • Foundation v1.0</span>
    </div>
  );
}
