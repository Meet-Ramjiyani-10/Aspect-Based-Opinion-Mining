'use strict';
const $ = s => document.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = ['positive', 'negative', 'mixed', 'neutral'];
const colors = {positive:'#38a994',negative:'#df827d',mixed:'#dfb360',neutral:'#b7c3c9'};
let corpus = {reviews:[],insights:{total:0,sentiments:{},languages:{},aspects:[],topics:[],keywords:[]}};
let rawReviews = [], evaluation = null, activeAnnotation = null;
let datasetPage = 1;
const pageSize = 25;
const pill = s => `<span class="pill ${labels.includes(s) ? s : 'neutral'}">${esc(s)}</span>`;
const empty = text => `<div class="message">${esc(text)}</div>`;

async function api(path, body) {
  const response = await fetch('/api/' + path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function toast(message) {
  $('#toast').textContent = message; $('#toast').style.display = 'block';
  clearTimeout(toast.timer); toast.timer = setTimeout(() => $('#toast').style.display = 'none', 6000);
}
async function busy(button, work) {
  const old = button.textContent; button.disabled = true; button.textContent = 'Working…';
  try { await work(); } catch (e) { toast(e.message); }
  finally { button.disabled = false; button.textContent = old; }
}
function view(name) {
  if (!$('#view-' + name)) return;
  document.querySelectorAll('.view').forEach(el => el.classList.toggle('active',el.id === 'view-' + name));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active',el.dataset.view === name));
  $('#breadcrumb').textContent = ({overview:'Overview',analyze:'Review analyzer',dataset:'Dataset & labels',pipeline:'NLP pipeline',evaluation:'Model evaluation'})[name];
  history.replaceState(null,'','#' + name);
  window.scrollTo({top:0,behavior:'instant'});
}
document.addEventListener('click', event => {
  const link = event.target.closest('[data-view]'); if (link) view(link.dataset.view);
  const example = event.target.closest('[data-example]'); if (example) $('#review-input').value = example.dataset.example;
  const annotate = event.target.closest('[data-annotate]'); if (annotate) openAnnotation(annotate.dataset.annotate);
  const page = event.target.closest('[data-page]'); if(page){datasetPage=Number(page.dataset.page);renderDataset();$('#search').scrollIntoView({block:'start'});}
});

function download(filename, data, type='application/json') {
  const url = URL.createObjectURL(new Blob([data],{type})); const link = document.createElement('a');
  link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
}
function csvValue(value) {
  let s = typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
  // Prevent formula execution when exported text is opened in a spreadsheet.
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
  return '"' + s.replaceAll('"','""') + '"';
}
function exportCSV(filename, rows) {
  if (!rows.length) return toast('There are no reviews to export yet.');
  const keys = Object.keys(rows[0]);
  download(filename, '\ufeff' + [keys.join(','),...rows.map(r => keys.map(k => csvValue(r[k])).join(','))].join('\r\n'), 'text/csv;charset=utf-8');
}

async function refresh() {
  const [data, raw] = await Promise.all([api('corpus',{}), api('reviews')]);
  corpus = data; rawReviews = raw.reviews; renderOverview(); renderDataset(); renderReadiness();
}
function renderOverview() {
  const {insights:s, reviews} = corpus;
  const positive = s.sentiments.positive || 0, aspects = s.aspects.reduce((n,a) => n + a.total,0);
  const annotated = rawReviews.filter(r => r.annotation.sentiment && !r.is_demo).length;
  const metrics = [
    ['Reviews in corpus',s.total,'▤',`${reviews.filter(r => r.metadata.is_demo).length} synthetic · ${reviews.filter(r => !r.metadata.is_demo).length} imported`],
    ['Positive reviews',s.total ? Math.round(positive / s.total * 100) + '<small>%</small>' : '—','↗',`${positive} reviews with exclusively positive cues`],
    ['Aspect mentions',aspects,'◎',`${s.aspects.length} categories with explicit mentions`],
    ['Human-annotated',annotated,'◈','Non-demo labels available for evaluation']
  ];
  $('#metrics').innerHTML = metrics.map(([name,value,icon,note]) => `<article class="metric-card"><div class="metric-title">${name}<span>${icon}</span></div><div class="metric-value">${value}</div><div class="metric-note">${note}</div></article>`).join('');
  $('#aspect-chart').innerHTML = s.aspects.length ? s.aspects.map(a => `<div class="bar-row"><span>${esc(a.aspect)}</span><div class="bar-track" aria-label="${esc(a.aspect)}: ${a.positive} positive, ${a.negative} negative, ${a.mixed} mixed, ${a.neutral} neutral">${labels.map(label => `<span class="${label}" data-share="${a[label] / a.total * 100}" title="${label}: ${a[label]}"></span>`).join('')}</div><span>${a.total}</span></div>`).join('') : empty('Load the demo corpus or import reviews to discover aspect insights.');
  document.querySelectorAll('[data-share]').forEach(el => el.style.width = el.dataset.share + '%');
  let offset = 0; const circumference = 2 * Math.PI * 70;
  const circles = labels.map(label => { const length = s.total ? (s.sentiments[label] || 0) / s.total * circumference : 0; const circle = `<circle cx="90" cy="90" r="70" stroke="${colors[label]}" stroke-dasharray="${length} ${circumference-length}" stroke-dashoffset="${-offset}"/>`; offset += length; return circle; }).join('');
  $('#sentiment-chart').innerHTML = `<div class="donut-wrap"><svg class="donut" viewBox="0 0 180 180" role="img" aria-label="Overall sentiment distribution"><circle cx="90" cy="90" r="70" stroke="#f0f4f2"/>${circles}</svg><div class="donut-label"><strong>${s.total}</strong><small>total reviews</small></div></div>`;
  $('#sentiment-legend').innerHTML = labels.map(l => `<div class="sentiment-item"><i class="${l}"></i>${l[0].toUpperCase()+l.slice(1)}<strong>${s.sentiments[l] || 0}</strong><small>${s.total ? Math.round((s.sentiments[l] || 0) / s.total * 100) : 0}%</small></div>`).join('');
  $('#topics').innerHTML = s.topics.length ? s.topics.map(t => `<div class="topic-row"><span class="topic-number">0${t.topic}</span><div><strong>Topic ${t.topic}</strong><div class="topic-terms">${t.terms.map(esc).join(' · ')}</div></div></div>`).join('') : empty('Topics appear after at least three usable reviews are analyzed.');
  $('#keywords').innerHTML = s.keywords.length ? s.keywords.map(k => `<span class="keyword" title="TF-IDF weight: ${k.weight}">${esc(k.term)}</span>`).join('') : empty('Your corpus vocabulary will appear here.');
  $('#recent-reviews').innerHTML = reviews.length ? reviews.slice(-5).reverse().map(r => `<div class="review-row"><div class="review-avatar">${r.language.label.startsWith('Marathi') ? 'म' : r.language.label.startsWith('Hindi') ? 'ह' : '↳'}</div><div class="review-copy"><p>${esc(r.text)}</p><small>${r.metadata.is_demo ? 'SYNTHETIC DEMO' : esc(r.metadata.source)}</small><div class="aspect-tags">${r.aspects.map(a => `<span class="tag">${esc(a.aspect)}</span>`).join('')}</div></div><div class="language-label">${esc(r.language.label)}</div>${pill(r.sentiment)}</div>`).join('') : empty('Your first review is the beginning of the story.');
}
function renderDataset() {
  const q = $('#search').value.toLocaleLowerCase(), sentiment = $('#sentiment-filter').value, language = $('#language-filter').value;
  const filtered = corpus.reviews.filter(r => r.text.toLocaleLowerCase().includes(q) && (!sentiment || r.sentiment === sentiment) && (!language || r.language.label === language));
  const pages = Math.max(1,Math.ceil(filtered.length/pageSize));
  datasetPage = Math.min(Math.max(1,datasetPage),pages);
  const pageRows = filtered.slice((datasetPage-1)*pageSize,datasetPage*pageSize);
  $('#row-count').textContent = filtered.length + ' reviews';
  $('#dataset-table').innerHTML = filtered.length ? `<table><thead><tr><th>REVIEW & SOURCE</th><th>LANGUAGE ESTIMATE</th><th>PREDICTION</th><th>HUMAN LABEL</th><th></th></tr></thead><tbody>${pageRows.map(r => `<tr><td>${esc(r.text)}<small>${r.metadata.is_demo ? 'SYNTHETIC DEMO · EXCLUDED FROM EVALUATION' : esc(r.metadata.source)}</small></td><td>${esc(r.language.label)}<small>Lexicon heuristic</small></td><td>${pill(r.sentiment)}<div class="aspect-tags">${r.aspects.map(a => `<span class="tag">${esc(a.aspect)} · ${esc(a.sentiment)}</span>`).join('')}</div></td><td>${r.metadata.annotation.sentiment ? pill(r.metadata.annotation.sentiment) : '<small>Unlabelled</small>'}</td><td><button data-annotate="${esc(r.id)}">Annotate ↗</button></td></tr>`).join('')}</tbody></table>` : empty('No reviews match. Import a CSV or load demo reviews from Overview.');
  if(filtered.length) $('#dataset-table').insertAdjacentHTML('beforeend',`<div class="pager"><span>Page ${datasetPage} of ${pages} | ${filtered.length} matching reviews</span><div class="pager-actions"><button class="button secondary" data-page="${datasetPage-1}" ${datasetPage===1?'disabled':''}>Previous</button><button class="button secondary" data-page="${datasetPage+1}" ${datasetPage===pages?'disabled':''}>Next</button></div></div>`);
}
['search','sentiment-filter','language-filter'].forEach(id => $('#'+id).addEventListener(id === 'search' ? 'input':'change',()=>{datasetPage=1;renderDataset();}));

$('#demo-button').onclick = event => busy(event.currentTarget, async () => {const r = await api('demo',{}); await refresh(); toast(`${r.added} synthetic reviews loaded; ${r.skipped} duplicates skipped.`);});
$('#csv-file').onchange = async event => {const file = event.target.files[0]; if (!file) return; try {if(file.size > 6_000_000) throw new Error('CSV must be smaller than 6 MB.'); const result = await api('import',{csv:await file.text()}); await refresh(); toast(`${result.added} imported · ${result.skipped} blank/duplicate rows skipped.`);} catch(e){toast(e.message);} finally {event.target.value='';}};
$('#export-overview').onclick = () => {if(!corpus.reviews.length)return toast('Load or import reviews first.');download('bhashalens-analysis.json',JSON.stringify({exported_at:new Date().toISOString(),...corpus},null,2));};
$('#export-labels').onclick = () => exportCSV('bhashalens-annotations.csv',rawReviews.map(r => ({id:r.id,text:r.text,source:r.source,source_url:r.source_url,language:r.language,collected_at:r.collected_at,is_demo:r.is_demo,gold_sentiment:r.annotation.sentiment || '',gold_aspects:r.annotation.aspects || {}})));
$('#download-template').onclick = () => download('review-template.csv','text,source,source_url,language,collected_at\r\n','text/csv');
$('#analyze-button').onclick = event => busy(event.currentTarget, async () => {
  const r = await api('analyze',{text:$('#review-input').value});
  $('#analysis-result').innerHTML = `<article class="panel"><div class="result-top"><h2>Opinion snapshot</h2>${pill(r.sentiment)}</div><div class="analysis-summary"><span>${esc(r.language.label)}</span><span>${r.word_count} tokens</span><span>${r.sentence_count} sentences</span></div><p class="micro-note">${esc(r.language.method)}</p></article><article class="panel"><div class="panel-heading"><div><h2>${r.aspects.length} aspects in focus</h2><p>Sentiment assigned to the nearest explicit aspect in each clause.</p></div></div>${r.aspects.length ? r.aspects.map(a => `<div class="aspect-result"><div class="aspect-result-header"><strong>${esc(a.aspect)}</strong>${pill(a.sentiment)}</div>${a.evidence.map(e => `<div class="evidence">“${esc(e.clause)}”<br>${e.cues.map(c => `<span class="cue ${c.score < 0 ? 'negative':''}">${esc(c.word)}${c.negated ? ' · negated':''} · ${c.score > 0 ? '+':''}${c.score}</span>`).join('') || '<span class="micro-note">Mention detected; no explicit opinion cue assigned.</span>'}</div>`).join('')}</div>`).join('') : empty('No supported explicit aspect found. Try mentioning food, delivery, service, price, quality, app, battery, or camera.')}<p class="micro-note">${r.limitations.map(esc).join(' ')}</p></article>`;
});

function openAnnotation(id) {
  activeAnnotation = rawReviews.find(r => r.id === id); if (!activeAnnotation) return;
  $('#annotation-text').textContent = activeAnnotation.text;
  $('#gold-sentiment').value = activeAnnotation.annotation.sentiment || '';
  $('#aspect-labels').innerHTML = ['Food','Delivery','Service','Price','Quality','App','Battery','Camera'].map(a => `<div><label for="label-${a}">${a}</label><select id="label-${a}" data-aspect="${a}"><option value="">Absent</option>${labels.map(l => `<option${activeAnnotation.annotation.aspects?.[a] === l ? ' selected':''}>${l}</option>`).join('')}</select></div>`).join('');
  $('#annotation-dialog').showModal();
}
$('#close-dialog').onclick = () => $('#annotation-dialog').close();
$('#annotation-form').onsubmit = async event => {
  event.preventDefault(); const button = event.submitter;
  await busy(button, async () => {const aspects = {}; document.querySelectorAll('[data-aspect]').forEach(el => {if(el.value)aspects[el.dataset.aspect]=el.value;}); await api('annotate',{id:activeAnnotation.id,annotation:{sentiment:$('#gold-sentiment').value,aspects}}); $('#annotation-dialog').close(); await refresh(); toast('Independent annotation saved.');});
};

$('#pipeline-button').onclick = event => busy(event.currentTarget,async () => {
  const p = await api('pipeline',{text:$('#pipeline-input').value});
  const card = (title,subtitle,content) => `<article class="panel"><div class="panel-heading"><div><h2>${title}</h2><p>${esc(subtitle)}</p></div></div>${content}</article>`;
  $('#pipeline-result').innerHTML = card('Normalized text','Unicode NFC · URL removal · contraction and elongation handling',`<div class="code">${esc(p.normalized)}</div>`) + card('Token-level language estimates',p.language.method,`<div class="token-list">${p.language.tokens.map(t => `<span class="token-chip">${esc(t.token)}<small>${esc(t.language)}</small></span>`).join('')}</div>`) + card('Stemming & lemmatization',p.lemma_method,`<div class="code">${p.stems.map(s => `${esc(s.token)} → ${esc(s.stem)}`).join('\n')}</div><p class="micro-note">Lemmas: ${p.lemmas.map(l => `${esc(l.token)} → ${esc(l.lemma)}`).join(' · ') || 'WordNet corpus not installed.'}</p>`) + card('Part-of-speech tags',p.pos_method,`<div class="token-list">${p.pos.map(t => `<span class="token-chip">${esc(t.token)}<small>${esc(t.tag)}</small></span>`).join('') || empty('Run the NLTK setup command in the README to enable POS tagging.')}</div>`) + card('Bigram language model',p.ngram_note,`<div class="code">${p.bigrams.slice(0,25).map(b => `${esc(b.bigram)}   P = ${b.probability.toFixed(4)}`).join('\n')}</div><p class="micro-note">Log probability: ${p.log_probability.toFixed(4)} · Demonstration perplexity: ${p.perplexity.toFixed(3)}</p>`) + card('Pattern entities',p.entity_method,`<div class="token-list">${p.entities.map(e => `<span class="token-chip">${esc(e.text)}<small>${esc(e.type)}</small></span>`).join('') || empty('No URLs or currency amounts found.')}</div>`) + card('LSA semantic neighbors','TF-IDF → truncated SVD → cosine similarity; current corpus only',`<div class="code">${(corpus.insights.semantic_neighbors || []).map(n => `${esc(n.review.slice(0,8))} ↔ ${esc(n.neighbor.slice(0,8))} · cosine ${n.cosine}`).join('\n') || 'Import at least three reviews to compute corpus embeddings.'}</div>`);
});
function renderReadiness() {
  const real = rawReviews.filter(r=>!r.is_demo);
  const annotated = real.filter(r=>r.annotation.sentiment);
  const counts = Object.fromEntries(labels.map(l=>[l,annotated.filter(r=>r.annotation.sentiment===l).length]));
  const represented = Object.values(counts).filter(n=>n>0);
  const ready = annotated.length>=20 && represented.length>=2 && represented.every(n=>n>=4);
  let panel = $('#evaluation-readiness');
  if(!panel){panel=document.createElement('article');panel.id='evaluation-readiness';panel.className='panel readiness';$('#evaluation-result').before(panel);}
  panel.innerHTML=`<h2>${ready?'Ready to evaluate your annotations':'Prepare your evaluation dataset'}</h2><p>Analysis predictions are available now. Accuracy and F1 need independent human labels to compare against.</p><div class="readiness-grid"><div class="readiness-stat"><strong>${real.length}</strong><span>Imported non-demo reviews</span></div><div class="readiness-stat"><strong>${annotated.length} / 20</strong><span>Minimum labelled reviews</span></div><div class="readiness-stat"><strong>${represented.filter(n=>n>=4).length} / 2</strong><span>Minimum classes with 4+ labels</span></div></div><div class="class-support">${labels.map(l=>`<span class="tag">${l}: ${counts[l]}</span>`).join('')}</div><p>${ready?'The server will also check normalized duplicates and conflicting labels before splitting.':'Open Dataset & labels, choose Annotate, and assign your own overall sentiment and explicit aspect labels. Demo rows do not count. Use at least two classes, with four or more labels in every represented class.'}</p><div class="actions"><button class="button primary" data-view="dataset">Go to Dataset & labels</button><button class="button secondary" data-view="analyze">Try live analysis</button></div><p class="micro-note">A 20-review minimum enables a small experiment. It does not establish reliable real-world accuracy.</p>`;
  $('#evaluate-button').disabled=!ready;
  $('#evaluate-button').title=ready?'Evaluate on a shared held-out split':'Add independent labels using Dataset & labels first';
  $('#export-evaluation').disabled=!evaluation;
}
$('#evaluate-button').onclick = event => busy(event.currentTarget,async () => {
  try {
    const report = await api('evaluate',{}); evaluation = report; renderReadiness();
    const matrix = (name,m) => `<article class="panel"><h2>${esc(name)}</h2><p class="micro-note">Rows = gold · columns = prediction</p><div class="table-scroll"><table><thead><tr><th></th>${report.labels.map(l=>`<th>${l}</th>`).join('')}</tr></thead><tbody>${m.confusion_matrix.map((row,i)=>`<tr><th>${report.labels[i]}</th>${row.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div></article>`;
    $('#evaluation-result').innerHTML = `<div class="evaluation-cards">${Object.entries(report.models).map(([name,m])=>`<article class="panel eval-card"><h2>${esc(name)}</h2><div class="eval-score">${(m.macro_f1*100).toFixed(1)}<small>%</small></div><p>Macro-F1 · all 4 labels</p><p>Accuracy ${(m.accuracy*100).toFixed(1)}%</p></article>`).join('')}</div><article class="panel"><h2>Experiment manifest</h2><p class="micro-note">${report.train_count} training · ${report.test_count} held-out · seed ${report.seed}<br>Dataset SHA-256: ${esc(report.dataset_hash)}<br>${report.notes.map(esc).join('<br>')}</p><h2>Aspect baseline on held-out annotations</h2><p class="micro-note">${report.aspect_evaluation.gold_aspect_support} gold aspect labels · Extraction F1 ${(report.aspect_evaluation.extraction_f1*100).toFixed(1)}% · End-to-end aspect sentiment ${report.aspect_evaluation.end_to_end_sentiment_accuracy === null ? 'unavailable; annotate aspects' : (report.aspect_evaluation.end_to_end_sentiment_accuracy*100).toFixed(1)+'%'}</p></article><div class="dashboard-grid">${Object.entries(report.models).map(([n,m])=>matrix(n,m)).join('')}</div><article class="panel"><h2>Error analysis · character TF-IDF classifier</h2>${report.models['Character TF-IDF + Logistic Regression'].errors.map(e=>`<div class="aspect-result"><p>${esc(e.text)}</p><p class="micro-note">Gold ${pill(e.gold)} · Prediction ${pill(e.predicted)}</p></div>`).join('') || empty('No errors on this split. Review test size and class support before drawing conclusions.')}</article>`;
  } catch(e) {$('#evaluation-result').innerHTML = `<div class="error-message">${esc(e.message)}</div>`;throw e;}
});
$('#export-evaluation').onclick = () => {if(!evaluation)return toast('Run an experiment first.');download('bhashalens-evaluation.json',JSON.stringify(evaluation,null,2));};
$('#export-evaluation').disabled=true;
$('#evaluate-button').disabled=true;
view(location.hash.slice(1) || 'overview');
refresh().catch(e => toast('Could not load corpus: '+e.message));
