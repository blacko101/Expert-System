(function(){
  const form = document.getElementById('diagForm');
  const resultsWrap = document.getElementById('results');
  const resultsCard = document.getElementById('resultsCard');
  const runBtn = document.getElementById('runBtn');
  const runSpin = document.getElementById('runSpin');
  const exampleBtn = document.getElementById('exampleBtn');

  // --- FIXED LOAD EXAMPLE BUTTON ---
  exampleBtn.addEventListener('click', ()=>{
    const example = {
      ping_latency: 34,
      speed_mbps: 72.5,
      wifi_connected: true,
      packet_loss: 0,
      rssi: -55,
      cpu_temp: 58,
      ram_usage: 42
    };

    const textarea = document.getElementById('id_structured');  // FIXED ID
    textarea.value = JSON.stringify(example, null, 2);

    textarea.animate(
      [{ background:'#fff6d9' }, { background:'#F5F3ED' }],
      { duration:700 }
    );
  });


  // Escape HTML
  function escapeHtml(s){
    if(!s) return '';
    return String(s).replace(/[&<>\"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    })[c]);
  }

  // Render diagnosis cards
  function renderDiagnoses(diags){
    const seen = new Set();
    const unique = diags.filter(d => {
      if(!d || !d.name) return false;
      if(seen.has(d.name)) return false;
      seen.add(d.name);
      return true;
    });

    resultsWrap.innerHTML = '';

    if(unique.length === 0){
      const el = document.createElement('div');
      el.className='result-card';
      el.innerHTML = `
        <h3 class="result-title">Insufficient Data to Diagnose</h3>
        <p class="muted"><strong>Confidence:</strong> 20%</p>
        <p class="muted"><strong>Evidence:</strong> Not enough facts supplied</p>
        <p class="muted"><strong>Remedy:</strong> Provide more diagnostics.</p>
      `;
      resultsWrap.appendChild(el);
      return;
    }

    unique.forEach(d => {
      const el = document.createElement('div');
      el.className='result-card';
      el.innerHTML = `
        <h3 class="result-title">${escapeHtml(d.name)}</h3>
        <p class="muted"><strong>Confidence:</strong> ${Math.round((d.confidence||0)*100)}%</p>
        <p class="muted"><strong>Evidence:</strong> ${escapeHtml(d.evidence||'—')}</p>
        <p class="muted"><strong>Remedy:</strong> ${escapeHtml(d.remedy||'—')}</p>
      `;
      resultsWrap.appendChild(el);
    });
  }


  // --- FORM SUBMIT HANDLER (POST to backend) ---
  form.addEventListener('submit', async (ev)=>{
    ev.preventDefault();

    runSpin.style.display='inline-block';
    runBtn.disabled=true;

    resultsCard.style.display='block';
    resultsWrap.innerHTML='';

    // Build FormData (includes csrfmiddlewaretoken rendered by Django)
    const formData = new FormData(form);

    // If user pasted JSON into structured, leave it in the textarea (server expects string)
    try{
      const structured = document.getElementById('id_structured').value.trim();
      if(structured){
        // ensure textarea value is set in the FormData
        formData.set('structured', structured);
      }
    }catch(e){
      // ignore
    }

    // POST to server endpoint (form.action)
    try{
      const resp = await fetch(form.action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      runSpin.style.display='none';
      runBtn.disabled=false;

      if(!resp.ok){
        const txt = await resp.text();
        console.error('Server error', resp.status, txt);
        resultsWrap.innerHTML = `<div class="result-card"><p class="muted">Server error: ${resp.status}</p></div>`;
        return;
      }

      const data = await resp.json();
      const diags = data && data.diagnoses ? data.diagnoses : [];
      renderDiagnoses(diags);

      // Smooth scroll to results
      window.scrollTo({
        top: resultsCard.getBoundingClientRect().top + window.scrollY - 20,
        behavior:'smooth'
      });

    }catch(err){
      console.error('Fetch error', err);
      runSpin.style.display='none';
      runBtn.disabled=false;
      resultsWrap.innerHTML = `<div class="result-card"><p class="muted">Network error contacting server.</p></div>`;
    }
  });

})();
