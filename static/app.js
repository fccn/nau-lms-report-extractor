const form = document.getElementById('report-form');
const submitBtn = document.getElementById('submit-btn');
const resultsEl = document.getElementById('results');
const summaryEl = document.getElementById('summary');
const detailsEl = document.getElementById('details');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';
  resultsEl.classList.add('hidden');
  detailsEl.innerHTML = '';
  summaryEl.textContent = '';

  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const lms_url = document.getElementById('lms_url').value.trim();
  const report = document.getElementById('report').value;
  const courses_input = document.getElementById('courses').value;
  const courses_file = document.getElementById('courses_file').files[0];

  try {
    let res;
    if (courses_file) {
      const fd = new FormData();
      fd.append('email', email);
      fd.append('password', password);
      fd.append('lms_url', lms_url);
      fd.append('report', report);
      fd.append('courses_input', courses_input);
      fd.append('courses_file', courses_file);
      res = await fetch('/api/generate-multipart', { method: 'POST', body: fd });
    } else {
      const payload = { email, password, lms_url, report, courses_input };
      res = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.detail || 'Request failed');
    }

    summaryEl.textContent = `Total: ${data.total} | Success: ${data.success} | Failed: ${data.failed}`;
    data.results.forEach(r => {
      const li = document.createElement('li');
      li.textContent = r.message;
      li.style.borderColor = r.success ? '#2b8a3e' : '#b02a37';
      detailsEl.appendChild(li);
    });
    resultsEl.classList.remove('hidden');
  } catch (err) {
    summaryEl.textContent = String(err.message || err);
    resultsEl.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Reports';
  }
});


