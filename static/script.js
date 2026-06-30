document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('prepForm');
  const spinner = document.getElementById('spinner');
  const resultDiv = document.getElementById('result');
  const downloadBtn = document.getElementById('downloadBtn');

  const formatTitle = (key) => {
    const titles = {
      snapshot: "Candidate Snapshot",
      company_intel: "Company Intel",
      questions: "Top Behavioral Questions",
      answers: "Tailored STAR Answers",
      smart_questions: "Smart Questions to Ask",
      talking_points: "Key Talking Points"
    };
    return titles[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const renderContent = (key, value) => {
    if (!value) return '';
    let html = `<div class="section-block"><h2>${formatTitle(key)}</h2>`;
    
    if (key === 'answers' && Array.isArray(value)) {
      html += '<div class="answers-grid">';
      value.forEach((ans, idx) => {
        html += `<div class="answer-card">
                  <span class="answer-badge">Answer ${idx + 1}</span>`;
        if (typeof ans === 'object') {
          for (const [k, v] of Object.entries(ans)) {
            html += `<strong>${k.toUpperCase()}:</strong> <p>${v}</p>`;
          }
        } else {
          html += `<p>${ans}</p>`;
        }
        html += `</div>`;
      });
      html += '</div>';
    } 
    else if (Array.isArray(value)) {
      html += `<ul class="styled-list">`;
      value.forEach(item => {
        if (typeof item === 'object') {
          html += `<li>${JSON.stringify(item)}</li>`;
        } else {
          html += `<li>${item}</li>`;
        }
      });
      html += `</ul>`;
    } 
    else if (typeof value === 'object') {
      html += `<pre>${JSON.stringify(value, null, 2)}</pre>`;
    } 
    else {
      html += `<p class="text-content">${value}</p>`;
    }
    
    html += `</div>`;
    return html;
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    resultDiv.style.opacity = '0';
    setTimeout(() => {
      resultDiv.style.display = 'none';
      downloadBtn.style.display = 'none';
      spinner.style.display = 'flex';
    }, 300);

    const formData = new FormData();
    formData.append('resume', document.getElementById('resume').files[0]);
    formData.append('job_url', document.getElementById('jobUrl').value);

    try {
      const response = await fetch('/generate', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`Server responded ${response.status}`);
      const data = await response.json();
      
      spinner.style.display = 'none';
      
      let html = '<div class="result-header"><h2>Your Interview Brief</h2></div>';
      // Render in specific order if available
      const order = ['snapshot', 'company_intel', 'questions', 'answers', 'smart_questions', 'talking_points'];
      
      order.forEach(k => {
        if (data[k]) {
          html += renderContent(k, data[k]);
          delete data[k];
        }
      });
      
      // Render any remaining keys
      for (const [key, value] of Object.entries(data)) {
        html += renderContent(key, value);
      }

      resultDiv.innerHTML = html;
      resultDiv.style.display = 'block';
      // Trigger reflow for fade-in
      void resultDiv.offsetWidth;
      resultDiv.style.opacity = '1';
      
      downloadBtn.style.display = 'inline-flex';
    } catch (err) {
      spinner.style.display = 'none';
      resultDiv.innerHTML = `<div class="error-msg">⚠️ Error: ${err.message}</div>`;
      resultDiv.style.display = 'block';
      resultDiv.style.opacity = '1';
    }
  });

  downloadBtn.addEventListener('click', () => {
    const printContent = resultDiv.innerHTML;
    const win = window.open('', '', 'height=800,width=800');
    win.document.write(`
      <html>
        <head>
          <title>Interview Brief</title>
          <style>
            body { font-family: 'Inter', sans-serif; padding: 2rem; color: #222; }
            h2 { color: #1a237e; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; margin-top: 2rem; }
            .result-header h2 { font-size: 2rem; text-align: center; border: none; }
            p, li { line-height: 1.6; }
            .styled-list { margin-left: 1.5rem; }
            .styled-list li { margin-bottom: 0.8rem; }
            .answer-card { margin-bottom: 1.5rem; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
            .answer-badge { font-weight: bold; color: #3949ab; display: block; margin-bottom: 0.5rem; }
            strong { color: #333; }
          </style>
        </head>
        <body>
          ${printContent}
        </body>
      </html>
    `);
    win.document.close();
    win.focus();
    setTimeout(() => {
      win.print();
      win.close();
    }, 250);
  });
});
