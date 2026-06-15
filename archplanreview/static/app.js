const uploadForm = document.querySelector('#upload-form');
const searchForm = document.querySelector('#search-form');
const statusEl = document.querySelector('#upload-status');
const docsEl = document.querySelector('#documents');
const resultsEl = document.querySelector('#results');
const pageTextEl = document.querySelector('#page-text');

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadDocuments() {
  const payload = await api('/api/documents');
  docsEl.innerHTML = payload.documents.length ? '' : '<li>No plans indexed yet.</li>';
  for (const doc of payload.documents) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${escapeHtml(doc.filename)}</strong><br><small>${doc.page_count} page(s) • ${doc.created_at}</small>`;
    docsEl.appendChild(li);
  }
}

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  statusEl.textContent = 'Uploading and extracting sheet text...';
  try {
    const payload = await api('/api/documents', { method: 'POST', body: data });
    statusEl.textContent = `Indexed ${payload.filename} (${payload.page_count} page(s)).`;
    form.reset();
    await loadDocuments();
  } catch (err) {
    statusEl.textContent = err.message;
  }
});

searchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const q = document.querySelector('#query').value.trim();
  if (!q) return;
  resultsEl.classList.remove('empty');
  resultsEl.textContent = 'Searching...';
  try {
    const payload = await api(`/api/search?q=${encodeURIComponent(q)}`);
    renderResults(payload.results);
  } catch (err) {
    resultsEl.textContent = err.message;
  }
});

function renderResults(results) {
  if (!results.length) {
    resultsEl.classList.add('empty');
    resultsEl.textContent = 'No matches found.';
    return;
  }
  resultsEl.innerHTML = '';
  for (const hit of results) {
    const div = document.createElement('div');
    div.className = 'hit';
    div.innerHTML = `<strong>${escapeHtml(hit.filename)}</strong> — page ${hit.page_number}<p>${hit.snippet.replaceAll('[', '<span class="hl">').replaceAll(']', '</span>')}</p>`;
    const button = document.createElement('button');
    button.textContent = 'View extracted page text';
    button.addEventListener('click', () => loadPage(hit.document_id, hit.page_number));
    div.appendChild(button);
    resultsEl.appendChild(div);
  }
}

async function loadPage(documentId, pageNumber) {
  const payload = await api(`/api/documents/${documentId}/pages/${pageNumber}`);
  pageTextEl.textContent = payload.text || '[No text extracted for this page]';
}

function escapeHtml(text) {
  return String(text).replace(/[&<>'"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}

loadDocuments().catch(err => { docsEl.innerHTML = `<li>${escapeHtml(err.message)}</li>`; });
