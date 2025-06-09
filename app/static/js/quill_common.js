window.QUILL_OPTIONS = {
  theme: 'snow',
  modules: {
    toolbar: [
      [{ font: [] }, { size: [] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ color: [] }, { background: [] }],
      [{ script: 'sub' }, { script: 'super' }],
      [{ header: 1 }, { header: 2 }, { header: 3 }, { header: 4 }, { header: 5 }, { header: 6 }, 'blockquote', 'code-block'],
      [{ list: 'ordered' }, { list: 'bullet' }, { indent: '-1' }, { indent: '+1' }],
      [{ direction: 'rtl' }, { align: [] }],
      ['link', 'image', 'video', 'formula'],
      ['clean']
    ]
  }
};

window.initQuill = function(selector, hidden, options = {}) {
  const el = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (!el) {
    console.error('initQuill: element not found for', selector);
    return null;
  }
  const opts = Object.assign({}, window.QUILL_OPTIONS, options);
  const q = new Quill(el, opts);
  if (hidden) {
    const input = typeof hidden === 'string' ? document.querySelector(hidden) : hidden;
    if (input) {
      if (input.value) q.root.innerHTML = input.value;
      q.on('text-change', () => {
        input.value = q.root.innerHTML;
      });
    }
  }
  return q;
};
