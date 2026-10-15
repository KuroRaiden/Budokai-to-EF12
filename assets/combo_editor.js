// Combo draft lives in the same recipe as single-move replacements.
let comboActive='',comboCounter=0;
const comboId=()=> 'c'+Date.now().toString(36)+'_'+(++comboCounter);
const activeCombo=()=>combos.find(c=>c.id===comboActive);
function comboPath(c,n){const path=[];while(n){path.unshift(n);n=c.nodes.find(x=>x.id===n.parent)}return path;}
function drawCombos(){
 if(!data)return;
 const selected=comboActive,c=activeCombo();
 $('combo-select').innerHTML='<option value="">New string…</option>'+combos.map(c=>`<option value="${esc(c.id)}">${esc(c.name)} · ${c.nodes.length} moves</option>`).join('');$('combo-select').value=selected;
 const entry=c?.entry||$('combo-entry').value;
 $('combo-entry').innerHTML=data.actions.filter(a=>a.combo_entry).map(a=>`<option value="${a.id}">${esc(actionName(a))} · ${esc(a.entry_input||a.input)}</option>`).join('');
 if(entry)$('combo-entry').value=entry;$('combo-entry').disabled=!!c;
 $('combo-name').value=c?.name||$('combo-name').value||'My Shin string';$('combo-create').disabled=!!c;$('combo-add').disabled=!c||!chosen||c.nodes.length>=24;$('combo-delete').disabled=!c;
 $('combo-selected').textContent='Library selection: '+moveName(chosen);
 $('combo-nodes').innerHTML=c?c.nodes.map((n,i)=>{
  const m=data.moves.find(x=>x.id===n.clip),parent=c.nodes.find(x=>x.id===n.parent),limit=parent?data.moves.find(x=>x.id===parent.clip).frames-1:0;
  const route=comboPath(c,n).map((x,j)=>j===0?'Entry':(x.direction==='5'?'':x.direction+' + ')+x.button).join(' → ');
  return `<div class="assignment" data-node="${esc(n.id)}"><div class="top"><strong>${i+1}. ${esc(m?.label||'Missing animation')}</strong><button data-combo-preview="${esc(n.id)}" class="small">Preview move ${i+1}</button></div><div class="small muted">${esc(m?.character||'')} · ${m?.frames||0} frames · ${esc(route)}</div><button class="small full" data-combo-use="${esc(n.id)}">Use selected library animation here</button>${i?`<label>Follow after<select data-field="parent" aria-label="Move ${i+1} follows">${c.nodes.slice(0,i).map((p,j)=>`<option value="${esc(p.id)}" ${p.id===n.parent?'selected':''}>${j+1}. ${esc(data.moves.find(x=>x.id===p.clip)?.label||'Move')}</option>`).join('')}</select></label><div class="split"><label>Input<select data-field="button" aria-label="Move ${i+1} input">${['L','H','E'].map(v=>`<option ${v===n.button?'selected':''}>${v}</option>`).join('')}</select></label><label>Direction<select data-field="direction" aria-label="Move ${i+1} direction">${[['5','Any'],['6','→ Forward'],['4','← Back'],['2','↓ Down'],['8','↑ Up'],['1','↙ Down-back'],['3','↘ Down-forward'],['7','↖ Up-back'],['9','↗ Up-forward']].map(([v,t])=>`<option value="${v}" ${v===n.direction?'selected':''}>${t}</option>`).join('')}</select></label></div><div class="split"><label>Transition frame<input type="number" min="1" max="${limit}" data-field="start" value="${n.start}" aria-label="Move ${i+1} transition frame"></label><label>Accept until frame<input type="number" min="${n.start}" max="${limit}" data-field="end" value="${n.end}" aria-label="Move ${i+1} input deadline"></label></div><div class="small muted">Timing uses the parent move’s frames (1–${limit}).</div>`:'<p class="small muted">First move uses the entry action’s existing VF command.</p>'}<div class="split"><label>Damage<input type="number" min="0" max="999" data-field="damage" value="${n.damage}" aria-label="Move ${i+1} damage"></label><label>Hit frame (−1 auto)<input type="number" min="-1" max="${(m?.frames||1)-1}" data-field="hit" value="${n.hit}" aria-label="Move ${i+1} hit frame"></label></div>${i?`<button class="small full" data-combo-remove="${esc(n.id)}">Remove move ${i+1} and its follow-ups</button>`:''}</div>`;
 }).join(''):'<p class="small muted">Choose a library animation, select an entry move, then start your string.</p>';
 const count=combos.reduce((n,c)=>n+c.nodes.length,0);$('combo-summary').textContent=combos.length?`${combos.length} strings · ${count} moves. `+(c?.nodes.length===1?'Add at least one follow-up before saving or exporting.':'Branches need different inputs from the same parent.'):'';
 if(c){const leaves=c.nodes.filter(n=>!c.nodes.some(x=>x.parent===n.id));$('combo-routes').innerHTML=leaves.map(n=>`<div class="notice">${comboPath(c,n).map((x,i)=>`<b>${esc(i===0?'Entry ('+(data.actions.find(a=>a.id===c.entry)?.entry_input||'VF command')+')':(x.direction==='5'?'':x.direction+' + ')+x.button)}</b>`).join(' → ')}</div>`).join('');}else $('combo-routes').innerHTML='';
 updateReplacement();
 if(combos.length)$('build').textContent=`Export · ${combos.length} strings + ${Object.keys(assignments).length} replacements`;
}
function fitComboTiming(c){for(const n of c.nodes){if(n.parent){const p=c.nodes.find(x=>x.id===n.parent),max=data.moves.find(x=>x.id===p.clip).frames-1;n.start=Math.max(1,Math.min(max,n.start));n.end=Math.max(n.start,Math.min(max,n.end));}}}
$('combo-select').onchange=()=>{comboActive=$('combo-select').value;drawCombos();};
$('combo-name').oninput=()=>{const c=activeCombo();if(c)c.name=$('combo-name').value;};
$('combo-create').onclick=()=>{
 if(!chosen)return toast('Select the first animation in the move library.');
 const entry=$('combo-entry').value;if(combos.some(c=>c.entry===entry))return toast('This entry already has a string. Select it above and add a branch.');
 if(assignments[entry])return toast('Restore the single-move replacement for this entry before making its string.');
 const a=data.actions.find(a=>a.id===entry),button=a.motion==='M_LHK'?'H':'L';
 const c={id:comboId(),name:$('combo-name').value||'My Shin string',entry,nodes:[{id:comboId(),parent:null,clip:chosen.id,button,direction:'5',damage:12,hit:-1,start:0,end:0}]};
 combos.push(c);comboActive=c.id;drawAssignments();drawCombos();toast('First move added. Pick another animation and add a follow-up.');};
$('combo-add').onclick=()=>{const c=activeCombo();if(!c||!chosen)return;const p=c.nodes.at(-1),frames=data.moves.find(m=>m.id===p.clip).frames;
 const siblings=c.nodes.filter(n=>n.parent===p.id&&n.direction==='5');const button=['L','H','E'].find(b=>!siblings.some(n=>n.button===b))||'L';
 c.nodes.push({id:comboId(),parent:p.id,clip:chosen.id,button,direction:'5',damage:12,hit:-1,start:Math.max(1,Math.min(frames-1,Math.round(frames*.55))),end:frames-1});drawCombos();};
$('combo-delete').onclick=()=>{combos=combos.filter(c=>c.id!==comboActive);comboActive='';drawAssignments();drawCombos();toast('String removed from recipe. Original template route will be used.');};
$('combo-nodes').onchange=e=>{const field=e.target.dataset.field;if(!field)return;const c=activeCombo(),n=c?.nodes.find(n=>n.id===e.target.closest('[data-node]')?.dataset.node);if(!n)return;const old=n[field];n[field]=['start','end','hit','damage'].includes(field)?Number(e.target.value):e.target.value;
 if(c.nodes.some(x=>x.id!==n.id&&x.parent===n.parent&&x.button===n.button&&x.direction===n.direction)){n[field]=old;toast('A branch from this parent already uses that input. Choose a different input or direction.');}
 fitComboTiming(c);drawCombos();};
$('combo-nodes').onclick=e=>{const c=activeCombo();if(!c)return;const preview=e.target.closest('[data-combo-preview]'),use=e.target.closest('[data-combo-use]'),remove=e.target.closest('[data-combo-remove]');
 if(preview)selectMove(c.nodes.find(n=>n.id===preview.dataset.comboPreview).clip);
 if(use&&chosen){const n=c.nodes.find(n=>n.id===use.dataset.comboUse);n.clip=chosen.id;n.hit=-1;fitComboTiming(c);drawCombos();}
 if(remove){const ids=new Set([remove.dataset.comboRemove]);let size;do{size=ids.size;for(const n of c.nodes)if(ids.has(n.parent))ids.add(n.id);}while(ids.size!==size);c.nodes=c.nodes.filter(n=>!ids.has(n.id));drawCombos();}};
if(data)drawCombos();

$('combo-save').onclick=()=>$('save').click();
$('combo-export').onclick=()=>$('build').click();
