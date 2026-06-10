const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const previewImg = document.getElementById('preview-img');
const btnAnalyze = document.getElementById('btn-analyze');
const formContainer = document.getElementById('form-container');
const uploadZone = document.getElementById('upload-zone');
const confirmationContainer = document.getElementById('confirmation-container');

let currentFile = null;

function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) return;
  currentFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    previewImg.src = e.target.result;
    previewContainer.style.display = 'block';
    btnAnalyze.disabled = false;
  };
  reader.readAsDataURL(file);
  formContainer.innerHTML = '';
  confirmationContainer.innerHTML = '';
}

fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  handleFile(e.dataTransfer.files[0]);
});

btnAnalyze.addEventListener('click', () => {
  if (!currentFile) return;
  const formData = new FormData();
  formData.append('file', currentFile);
  btnAnalyze.disabled = true;
  btnAnalyze.textContent = 'Analyse en cours…';

  fetch('/api/analyze', { method: 'POST', body: formData })
    .then(r => r.text())
    .then(html => {
      formContainer.innerHTML = html;
      htmx.process(formContainer);
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = 'Analyser la note de frais';
    })
    .catch(() => {
      formContainer.innerHTML = '<p class="result-error">Erreur lors de l\'analyse. Veuillez réessayer.</p>';
      btnAnalyze.disabled = false;
      btnAnalyze.textContent = 'Analyser la note de frais';
    });
});

document.body.addEventListener('htmx:responseError', e => {
  confirmationContainer.innerHTML = `<p class="result-error">${e.detail.xhr.responseText}</p>`;
});