const mermaid = globalThis.mermaid;
import {parseFlow,flowCode,parseSequence,sequenceCode,parseC4,c4Code,parseER,erCode,parseClass,classCode,recoverLegacyFlow,validateBpmnModel,BPMN_COMPONENTS} from './model.js';
const $=id=>document.getElementById(id);
const state={project:null,active:null,tab:'visual',connect:false,source:null,selected:null,drag:null,dirty:false,saving:false,visualError:null,selectedNodes:new Set(),selectedEdge:null,undo:[],redo:[],baseline:null,restoring:false,zoom:1};
const themes={corporativo:{theme:'base',themeVariables:{primaryColor:'#e5f4fb',primaryTextColor:'#0b1f3a',primaryBorderColor:'#1769aa',lineColor:'#1769aa',secondaryColor:'#e1eff7',tertiaryColor:'#f6fbff',background:'#ffffff',fontFamily:'Segoe UI'}},sap_fiori:{theme:'base',themeVariables:{primaryColor:'#d8eaf6',primaryTextColor:'#0a3b61',primaryBorderColor:'#0a6ed1',lineColor:'#0a6ed1',secondaryColor:'#edf6fc',background:'#ffffff',fontFamily:'Arial'}},dark:{theme:'dark',themeVariables:{primaryColor:'#1b3653',primaryTextColor:'#f0f8ff',primaryBorderColor:'#40bce5',lineColor:'#64d2f5',secondaryColor:'#263e5c',background:'#0e1728',fontFamily:'Segoe UI'}}};
const samples={flowchart:'flowchart LR\n    A[Portal de Compras] --> B[API RAP]\n    B --> C[(SAP S/4HANA)]',sequence:'sequenceDiagram\n    autonumber\n    participant CLK as Processo de Compras\n    participant SAP as SAP RFC\n    CLK->>SAP: Consultar dados\n    SAP-->>CLK: Resultado',usecase:'flowchart LR\n    U([Usuário]) --> UC1([Consultar cotação])\n    U --> UC2([Criar pedido])\n    UC2 --> SAP[SAP S/4HANA]',er:'erDiagram\n    CUSTOMER ||--o{ ORDER : places\n    CUSTOMER {\n        int id PK\n        string name\n    }\n    ORDER {\n        int id PK\n        int customer_id FK\n    }',class:'classDiagram\n    class Pedido {\n        +String numero\n        +criar()\n    }\n    class Item {\n        +int quantidade\n    }\n    Pedido "1" *-- "many" Item : contém',bpmn:'flowchart LR\n    inicio((Início)) --> tarefa[Analisar solicitação]\n    tarefa --> gateway{Aprovado?}\n    gateway -->|Sim| fim((Fim))\n    gateway -->|Não| tarefa',c4:'C4Context\n    title Contexto da solução\n    Person(user, "Usuário", "Equipe de compras")\n    System(portal, "Portal de Compras", "Aplicação")\n    System_Ext(sap, "SAP S/4HANA", "ERP")\n    Rel(user, portal, "Utiliza")\n    Rel(portal, sap, "Integra")'};
const makeId=()=> 'd_'+Math.random().toString(36).slice(2,10);
function notice(msg,error=false){$('notice').textContent=msg;$('notice').style.color=error?'#ff9a9a':'#8ed5b1';}
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
function secureFetch(url, options={}) {
  if (!csrfToken || !options.method || ['GET','HEAD'].includes(options.method)) return fetch(url,options);
  const headers = new Headers(options.headers);
  headers.set('X-CSRF-Token', csrfToken);
  return fetch(url, {...options, headers});
}
async function api(url,options={}){const r=await secureFetch(url,options);if(!r.ok){let j=await r.json().catch(()=>({error:r.statusText}));throw Error(j.error||'Erro HTTP '+r.status);}return r.json();}
function current(){return state.project?.diagrams.find(d=>d.id===state.active)}
function snapshot(){
  if(!state.project)return null;
  const {_access,...content}=state.project;
  return JSON.stringify(content);
}
function resetHistory(){state.undo=[];state.redo=[];state.baseline=snapshot();updateHistoryButtons()}
function updateHistoryButtons(){if($('undo'))$('undo').disabled=!state.undo.length;if($('redo'))$('redo').disabled=!state.redo.length}
function mark(){if(!state.restoring&&state.project){const now=snapshot();if(state.baseline!==null&&now!==state.baseline){state.undo.push(state.baseline);if(state.undo.length>70)state.undo.shift();state.redo=[];state.baseline=now;updateHistoryButtons()}}state.dirty=true;notice('Alterações não salvas')}
function historyMove(back){const src=back?state.undo:state.redo,dst=back?state.redo:state.undo;if(!src.length)return;dst.push(snapshot());state.restoring=true;const selected=state.active;const access=state.project._access;state.project=JSON.parse(src.pop());if(access)state.project._access=access;state.baseline=snapshot();state.active=state.project.diagrams.some(d=>d.id===selected)?selected:state.project.diagrams[0]?.id;state.selectedNodes.clear();state.selectedEdge=null;$('projectTitle').value=state.project.title;$('theme').value=state.project.theme;$('markdown').value=state.project.markdown;switchDiagram(state.active);state.restoring=false;state.dirty=true;updateHistoryButtons();notice(back?'Desfeito':'Refeito')}

function htmlEscape(s){return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function downloadBlob(blob,name){const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}
async function loadProjects(selected){const r=await api('/api/projects');$('projects').replaceChildren();for(const p of r.projects){const o=new Option(p.title,p.id);$('projects').add(o)}if(selected&&r.projects.some(p=>p.id===selected))$('projects').value=selected;else if(r.projects.length)$('projects').value=r.projects[0].id;else{const p=await api('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...(csrfToken?{}:{id:'exemplo'}),title:'Arquitetura de Integração'})});return loadProjects(p.id)}await loadProject($('projects').value)}
async function loadProject(id){state.project=await api('/api/projects/'+id);const params=new URLSearchParams(location.search);const diagram=params.get('projeto')===id?params.get('diagrama'):null;state.active=state.project.diagrams.find(d=>d.id===diagram)?.id??state.project.diagrams[0]?.id??null;state.dirty=false;setProjectAccess(state.project._access);$('projectTitle').value=state.project.title;$('theme').value=state.project.theme;$('markdown').value=state.project.markdown;renderList();switchDiagram(state.active);resetHistory();notice('Projeto carregado')}
function setProjectAccess(access){
  const level=access?.level??3;
  for(const id of ['saveProject','toggleCanvasGrid','renameDiagram','deleteDiagram','addDiagram','newByType','connect','removeSelected','syncCode','repairCode','insertDiagramButton','insertHeading']){
    const control=$(id);
    if(control)control.disabled=level<2;
  }
  for(const id of ['code','markdown','projectTitle'])$(id).readOnly=level<2;
  const viewOnly=$('projectViewOnly');
  if(viewOnly)viewOnly.hidden=level>=2;
  $('saveProject').disabled=level<2||state.saving;
  $('deleteProject').disabled=level<3;
  const link=$('projectPermissions');
  if(link){link.hidden=level<3;link.href='/compartilhamento/'+state.project.id+'/permissoes'}
}
function refreshDiagramPicker(){const picker=$('insertDiagram');if(!picker||!state.project)return;const selected=picker.value;picker.replaceChildren();for(const d of state.project.diagrams)picker.add(new Option(d.title+' ('+d.kind+')',d.id));if([...picker.options].some(o=>o.value===selected))picker.value=selected}
function renderList(){refreshDiagramPicker();$('diagramList').replaceChildren();for(const d of state.project.diagrams){const b=document.createElement('button');b.className='diagram-item'+(d.id===state.active?' selected':'');b.innerHTML=`<span>${htmlEscape(d.title)}</span><small>${htmlEscape(d.kind)}</small>`;b.onclick=()=>switchDiagram(d.id);$('diagramList').append(b)}}
function switchDiagram(id){
  state.active=id;
  const url=new URL(location.href);
  url.searchParams.set('projeto',state.project.id);
  if(id)url.searchParams.set('diagrama',id);else url.searchParams.delete('diagrama');
  history.replaceState(null,'',url);
  updateCanvasGrid();state.source=null;state.selected=null;state.selectedNodes.clear();state.selectedEdge=null;const d=current();if(!d)return;$('diagramTitle').textContent=d.title;$('diagramKind').textContent=d.kind;$('diagramType').value=d.kind;$('code').value=d.code;renderList();drawNodes();if(state.tab==='preview')renderPreview();if(state.tab==='document')renderDocument()}
function switchTab(tab){state.tab=tab;document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('active',e.dataset.tab===tab));document.querySelectorAll('.tab-content').forEach(e=>e.classList.toggle('active',e.id===tab+'Tab'));if(tab==='preview')renderPreview();if(tab==='document')renderDocument();if(tab==='visual'){if(current()?.visualStale)importCode();else drawNodes()}}
function addNode(type,x,y){const d=current();if(!d)return;if(d.visualStale){notice('Importe o código para o visual antes de editar os nós',true);return}if(!['flowchart','usecase','bpmn','c4'].includes(d.kind)){notice('Use o editor de sequência para adicionar participantes e mensagens.',true);return}const id='N'+Math.random().toString(36).slice(2,7);d.nodes.push({id,label:type==='database'?'Banco de dados':type==='actor'?'Ator':type==='decision'?'Decisão':type==='external'?'Sistema externo':BPMN_COMPONENTS[type]||'Processo',type:d.kind==='c4'?({actor:'Person',database:'SystemDb',external:'System_Ext'}[type]||'System'):type,x:Math.max(10,x),y:Math.max(10,y)});syncGraph();drawNodes();mark()}
function flowDirection(d){return d.flowDirection||/^\s*(?:flowchart|graph)\s+(LR|RL|TB|TD|BT)\b/i.exec(d.code)?.[1].toUpperCase()||'LR'}
function syncGraph(){const d=current();if(!d)return;if(d.visualStale){notice('Importe o código para o visual antes de gerar Mermaid',true);return}
  if(['flowchart','usecase','bpmn'].includes(d.kind)){d.code=flowCode(d.nodes,d.edges,d.kind,flowDirection(d));if(d.kind==='bpmn'){const errors=validateBpmnModel(d.nodes,d.edges);if(errors.length)notice('Avisos BPMN: '+errors.join('; '),true)}}
  else if(d.kind==='c4')d.code=c4Code(d.nodes,d.edges,d.c4Title||d.title,d.c4Header||'C4Context');
  else if(d.kind==='sequence'&&d.sequence)d.code=sequenceCode(d.sequence);
  else if(d.kind==='er'&&d.structured)d.code=erCode(d.structured);
  else if(d.kind==='class'&&d.structured)d.code=classCode(d.structured);
  $('code').value=d.code;
}
function importCode(){const d=current();if(!d)return;try{
  if(['flowchart','usecase','bpmn'].includes(d.kind)){const parsed=parseFlow(d.code);const positions=new Map(d.nodes.map(n=>[n.id,n]));d.nodes=parsed.nodes.map(n=>({...n,x:positions.get(n.id)?.x??n.x,y:positions.get(n.id)?.y??n.y}));d.edges=parsed.edges;d.flowDirection=parsed.direction}
  else if(d.kind==='c4'){const parsed=parseC4(d.code);const positions=new Map(d.nodes.map(n=>[n.id,n]));d.nodes=parsed.nodes.map(n=>({...n,x:positions.get(n.id)?.x??n.x,y:positions.get(n.id)?.y??n.y}));d.edges=parsed.edges;d.c4Title=parsed.title;d.c4Header=parsed.header}
  else if(d.kind==='sequence')d.sequence=parseSequence(d.code);
  else if(d.kind==='er')d.structured=parseER(d.code);
  else if(d.kind==='class')d.structured=parseClass(d.code);
  else throw Error('Este tipo utiliza edição por código e prévia; não há importação visual ainda.');
  d.visualStale=false;state.visualError=null;drawNodes();notice('Código importado para o editor visual');return true;
}catch(e){state.visualError=e.message;notice('Importação visual: '+e.message,true);drawNodes();return false}}
function drawSequence(){const d=current();const host=$('sequenceEditor');host.replaceChildren();if(!d||d.kind!=='sequence')return;
  if(d.visualStale){host.textContent='Código alterado: clique em Importar código → Visual. O editor não sobrescreverá seu código.';return}if(!d.sequence){try{d.sequence=parseSequence(d.code)}catch(e){state.visualError=e.message;host.textContent='Este código contém sintaxe ainda não suportada no editor visual: '+e.message+' Edite na aba Código Mermaid.';return}}
  const model=d.sequence;
  const part=document.createElement('div');part.className='seq-participants';
  const h=document.createElement('strong');h.textContent='Participantes';part.append(h);
  model.participants.forEach((p,i)=>{const line=document.createElement('div');line.className='seq-row';const id=document.createElement('code');id.textContent=p.id;const label=document.createElement('input');label.value=p.label;label.setAttribute('aria-label','Nome do participante '+p.id);label.onchange=()=>{p.label=label.value;syncGraph();mark()};const remove=document.createElement('button');remove.textContent='×';remove.title='Remover participante';remove.onclick=()=>{if(model.steps.some(s=>s.from===p.id||s.to===p.id)){notice('Remova primeiro as mensagens deste participante',true);return}model.participants.splice(i,1);syncGraph();drawSequence();mark()};line.append(id,label,remove);part.append(line)});
  const addp=document.createElement('button');addp.textContent='+ Participante';addp.onclick=()=>{const id='P'+(model.participants.length+1);if(model.participants.some(p=>p.id===id)){notice('ID já utilizado',true);return}model.participants.push({id,label:'Participante '+id});syncGraph();drawSequence();mark()};part.append(addp);
  const numbering=document.createElement('label');const check=document.createElement('input');check.type='checkbox';check.checked=!!model.autonumber;check.onchange=()=>{model.autonumber=check.checked;syncGraph();mark()};numbering.append(check,' Numeração automática');part.append(numbering);host.append(part);
  const steps=document.createElement('div');steps.className='seq-steps';const heading=document.createElement('strong');heading.textContent='Etapas (ordem de execução)';steps.append(heading);
  model.steps.forEach((s,i)=>{const row=document.createElement('div');row.className='seq-row';row.draggable=true;row.ondragstart=e=>e.dataTransfer.setData('sequence-step',String(i));row.ondragover=e=>e.preventDefault();row.ondrop=e=>{e.preventDefault();const from=Number(e.dataTransfer.getData('sequence-step'));if(!Number.isInteger(from)||from<0||from>=model.steps.length||from===i)return;const [item]=model.steps.splice(from,1);model.steps.splice(i,0,item);syncGraph();drawSequence();mark()};const index=document.createElement('span');index.textContent=String(i+1);row.append(index);
    const sel=document.createElement('select');['message','block','else','end','note'].forEach(t=>sel.add(new Option(({message:'Mensagem',block:'Bloco',else:'Alternativa',end:'Fim',note:'Nota'})[t],t)));sel.value=s.type;sel.onchange=()=>{model.steps[i]=stepDefault(sel.value,model.participants);syncGraph();drawSequence();mark()};row.append(sel);
    const inp=(value,change,placeholder)=>{const input=document.createElement('input');input.value=value||'';input.placeholder=placeholder;input.onchange=()=>{change(input.value);syncGraph();mark()};row.append(input)};
    const choice=(values,value,change)=>{const el=document.createElement('select');for(const [id,label] of values)el.add(new Option(label,id));el.value=value;el.onchange=()=>{change(el.value);syncGraph();mark()};row.append(el)};
    const actors=model.participants.map(p=>[p.id,p.label]);
    if(s.type==='message'){choice(actors,s.from,v=>s.from=v);choice([['->>','Chamada'],['-->>','Retorno'],['->','Seta'],['-->','Tracejada']],s.arrow,v=>s.arrow=v);choice(actors,s.to,v=>s.to=v);inp(s.label,v=>s.label=v,'Descrição')}
    if(s.type==='block'){choice(['opt','loop','alt','par','critical','break','rect'].map(v=>[v,v]),s.keyword,v=>s.keyword=v);inp(s.label,v=>s.label=v,'Condição')}
    if(s.type==='else')inp(s.label,v=>s.label=v,'Condição alternativa');
    if(s.type==='note'){choice([['over','Sobre'],['left of','À esquerda'],['right of','À direita']],s.position,v=>s.position=v);choice(actors,s.from,v=>s.from=v);inp(s.label,v=>s.label=v,'Nota')}
    const up=document.createElement('button');up.textContent='↑';up.title='Subir';up.disabled=i===0;up.onclick=()=>{[model.steps[i-1],model.steps[i]]=[model.steps[i],model.steps[i-1]];syncGraph();drawSequence();mark()};
    const down=document.createElement('button');down.textContent='↓';down.title='Descer';down.disabled=i===model.steps.length-1;down.onclick=()=>{[model.steps[i+1],model.steps[i]]=[model.steps[i],model.steps[i+1]];syncGraph();drawSequence();mark()};
    const del=document.createElement('button');del.textContent='×';del.title='Excluir etapa';del.onclick=()=>{model.steps.splice(i,1);syncGraph();drawSequence();mark()};row.append(up,down,del);steps.append(row)});
  const add=document.createElement('div');add.className='seq-add';for(const [type,label] of [['message','+ Mensagem'],['block','+ Bloco opt/loop/alt'],['else','+ Else'],['end','+ End'],['note','+ Nota']]){const btn=document.createElement('button');btn.textContent=label;btn.onclick=()=>{if(!model.participants.length&&['message','note'].includes(type)){notice('Adicione um participante primeiro',true);return}model.steps.push(stepDefault(type,model.participants));syncGraph();drawSequence();mark()};add.append(btn)}steps.append(add);host.append(steps);
}
function stepDefault(type,participants){const p=participants[0]?.id||'A',q=participants[1]?.id||p;
  if(type==='message')return {type,from:p,to:q,arrow:'->>',label:'Nova mensagem'};
  if(type==='block')return {type,keyword:'opt',label:'Condição'};
  if(type==='else')return {type,label:'Alternativa'};
  if(type==='note')return {type,position:'over',from:p,to:'',label:'Nota'};
  return {type:'end'};
}
function drawStructured(){
 const d=current(),host=$('sequenceEditor');host.replaceChildren();
 if(!d.structured){try{d.structured=d.kind==='er'?parseER(d.code):parseClass(d.code)}catch(e){host.textContent='Importação não suportada: '+e.message;return}}
 const isER=d.kind==='er',model=d.structured,items=isER?model.entities:model.classes,links=isER?model.relations:model.relations;
 const make=(tag,text,parent)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;parent.append(e);return e};
 const field=(parent,value,change,placeholder='')=>{const i=make('input','',parent);i.value=value||'';i.placeholder=placeholder;i.onchange=()=>{change(i.value);syncGraph();mark()};return i};
 const left=make('div',undefined,host);left.className='seq-participants';make('strong',isER?'Entidades e atributos':'Classes e membros',left);
 items.forEach((item,index)=>{const card=make('div',undefined,left);card.className='structured-card';field(card,item.id,v=>{if(!/^[A-Za-z_]\w*$/.test(v)||items.some((x,j)=>j!==index&&x.id===v)){notice('Identificador inválido ou duplicado',true);return}const old=item.id;item.id=v;for(const r of links){if(r.from===old)r.from=v;if(r.to===old)r.to=v}},'Identificador');
 const area=make('textarea','',card);area.value=(isER?item.fields.map(f=>[f.type,f.name,f.key].filter(Boolean).join(' ')):item.members).join('\n');area.rows=4;area.title=isER?'Um atributo por linha: tipo nome PK/FK':'Um membro por linha: +String nome ou +metodo()';area.onchange=()=>{try{if(isER){const rows=area.value.split('\n').map(x=>x.trim()).filter(Boolean);item.fields=rows.map(row=>{const m=row.match(/^([\w\[\](),]+)\s+([A-Za-z_]\w*)(?:\s+(PK|FK|UK))?$/);if(!m)throw Error('Atributo inválido: '+row);return {type:m[1],name:m[2],key:m[3]||'',comment:''}})}else item.members=area.value.split('\n').map(x=>x.trim()).filter(Boolean);syncGraph();mark()}catch(e){notice(e.message,true)}};
 const del=make('button','Excluir',card);del.onclick=()=>{items.splice(index,1);for(let j=links.length-1;j>=0;j--)if(links[j].from===item.id||links[j].to===item.id)links.splice(j,1);syncGraph();drawStructured();mark()};});
 const add=make('button',isER?'+ Entidade':'+ Classe',left);add.onclick=()=>{let i=items.length+1,id;do{id=(isER?'ENTIDADE_':'Classe_')+i++}while(items.some(x=>x.id===id));items.push(isER?{id,fields:[]}:{id,members:[]});syncGraph();drawStructured();mark()};
 const right=make('div',undefined,host);right.className='seq-steps';make('strong',isER?'Relacionamentos e cardinalidade':'Relacionamentos UML',right);
 const options=isER?['||--o{','||--||','o|--o{','}o--o{','||..o{']:['--','-->','<--','<|--','*--','o--','..>'];
 links.forEach((r,index)=>{const row=make('div',undefined,right);row.className='seq-row';const select=(value,values,change)=>{const sel=make('select',undefined,row);for(const v of values)sel.add(new Option(v,v));sel.value=value;sel.onchange=()=>{change(sel.value);syncGraph();mark()};return sel};
 select(r.from,items.map(x=>x.id),v=>r.from=v);
 select(isER?r.left+r.line+r.right:r.arrow,options,v=>{if(isER){const m=v.match(/^(\|\||\|o|o\||o\{|\|\{|\}o|\}\{)(--|\.\.)(\|\||\|o|o\||o\{|\|\{|\}o|\}\{)$/);if(m){r.left=m[1];r.line=m[2];r.right=m[3]}}else r.arrow=v});
 select(r.to,items.map(x=>x.id),v=>r.to=v);field(row,r.label,v=>r.label=v,'Descrição');
 const del=make('button','×',row);del.onclick=()=>{links.splice(index,1);syncGraph();drawStructured();mark()}});
 const addRel=make('button','+ Relacionamento',right);addRel.onclick=()=>{if(items.length<2){notice('Crie pelo menos duas entidades/classes',true);return}links.push(isER?{from:items[0].id,to:items[1].id,left:'||',line:'--',right:'o{',label:'relaciona'}:{from:items[0].id,to:items[1].id,arrow:'-->',fromCard:'',toCard:'',label:'associa'});syncGraph();drawStructured();mark()};
}
function drawC4Level(){const d=current();if(d?.kind!=='c4')return;const bar=document.createElement('label');bar.className='c4-level';bar.textContent='Nível C4 ';const sel=document.createElement('select');for(const level of ['C4Context','C4Container','C4Component'])sel.add(new Option(level,level));sel.value=d.c4Header||'C4Context';sel.onchange=()=>{d.c4Header=sel.value;syncGraph();mark()};bar.append(sel);$('edgeInspector').prepend(bar)}
function drawNodes(){const d=current();$('nodeLayer').replaceChildren();$('connections').replaceChildren();$('edgeInspector').replaceChildren();if(!d)return;if(d.visualStale){$('visualNote').textContent='Código alterado: importe para o visual antes de editar.';return}const enabled=['flowchart','usecase','bpmn','c4'].includes(d.kind);$('sequenceEditor').hidden=!['sequence','er','class'].includes(d.kind);$('canvasWrap').parentElement.hidden=['sequence','er','class'].includes(d.kind);if(['er','class'].includes(d.kind)){drawStructured();return}if(d.kind==='sequence'){drawSequence();return}if(!enabled)return;drawC4Level();$('visualNote').textContent='Shift+clique: multisseleção · Arraste os nós selecionados · Delete: excluir · Ctrl+Z/Y: histórico';for(const n of d.nodes){const el=document.createElement('div');el.className='node '+(n.type||'process');el.textContent=n.label;el.style.left=n.x+'px';el.style.top=n.y+'px';el.dataset.id=n.id;
 el.onpointerdown=e=>{if(state.connect||(state.project._access?.level??3)<2)return;e.preventDefault();if(e.shiftKey){if(state.selectedNodes.has(n.id))state.selectedNodes.delete(n.id);else state.selectedNodes.add(n.id);state.selected=n.id;drawSelection();return}if(!state.selectedNodes.has(n.id)){state.selectedNodes=new Set([n.id]);state.selected=n.id}state.selectedEdge=null;state.drag={id:n.id,startX:e.clientX,startY:e.clientY,positions:new Map(d.nodes.filter(x=>state.selectedNodes.has(x.id)).map(x=>[x.id,{x:x.x,y:x.y}]))};el.setPointerCapture(e.pointerId);drawSelection()};
 el.onpointermove=e=>{if(!state.drag||state.drag.id!==n.id)return;const dx=(e.clientX-state.drag.startX)/state.zoom,dy=(e.clientY-state.drag.startY)/state.zoom;for(const node of d.nodes){const origin=state.drag.positions.get(node.id);if(origin){node.x=Math.max(0,Math.round((origin.x+dx)/10)*10);node.y=Math.max(0,Math.round((origin.y+dy)/10)*10);const dom=[...$('nodeLayer').children].find(c=>c.dataset.id===node.id);if(dom){dom.style.left=node.x+'px';dom.style.top=node.y+'px'}}}drawEdges()};
 el.onpointerup=el.onlostpointercapture=()=>{
   if(state.drag?.id!==n.id)return;
   state.drag=null;
   if(snapshot()!==state.baseline)mark();
 };
 el.onclick=e=>{if(state.connect){if(!state.source){state.source=n.id;notice('Selecione o nó de destino')}else if(state.source!==n.id){d.edges.push({from:state.source,to:n.id,label:'',direction:$('edgeDirection').value,kind:d.kind==='bpmn'?'sequenceFlow':'association'});state.source=null;state.connect=false;$('connect').classList.remove('active');syncGraph();drawEdges();drawEdgeInspector();mark()}}else if(!e.shiftKey&&!state.drag){state.selected=n.id;state.selectedNodes=new Set([n.id])}drawSelection()};
 el.ondblclick=()=>{const label=prompt('Nome do componente:',n.label);if(label!==null&&label.trim()){n.label=label.trim().slice(0,100);syncGraph();drawNodes();mark()}};$('nodeLayer').append(el)}drawSelection();drawEdges();drawEdgeInspector()}
function drawSelection(){document.querySelectorAll('.node').forEach(el=>{el.classList.toggle('selected',state.selectedNodes.has(el.dataset.id));el.classList.toggle('connect-source',el.dataset.id===state.source)})}
function drawEdgeInspector(){const d=current();const host=$('edgeInspector');host.replaceChildren();if(!d||!d.edges?.length)return;const title=document.createElement('span');title.textContent='Conexões: ';host.append(title);d.edges.forEach((edge,i)=>{const line=document.createElement('label');line.textContent=edge.from+' → '+edge.to+' ';line.classList.toggle('edge-active',state.selectedEdge===i);line.onclick=()=>{state.selectedEdge=i;state.selectedNodes.clear();drawSelection();drawEdges()};const direction=document.createElement('select');for(const [value,label] of [['forward','→'],['reverse','←'],['both','↔'],['none','—']])direction.add(new Option(label,value));direction.value=edge.direction||'forward';direction.title='Direção da conexão';direction.onchange=()=>{edge.direction=direction.value;syncGraph();drawEdges();mark()};const inp=document.createElement('input');inp.value=edge.label||'';inp.placeholder='Rótulo';inp.onchange=()=>{edge.label=inp.value;syncGraph();mark()};const del=document.createElement('button');del.textContent='×';del.title='Excluir conexão';del.onclick=()=>{d.edges.splice(i,1);syncGraph();drawNodes();mark()};if(d.kind==='bpmn'){const kind=document.createElement('select');for(const [v,t] of [['sequenceFlow','Sequência'],['messageFlow','Mensagem'],['association','Associação']])kind.add(new Option(t,v));kind.value=edge.kind||'sequenceFlow';kind.onchange=()=>{edge.kind=kind.value;syncGraph();drawEdges();mark()};line.append(kind)}line.append(direction,inp,del);host.append(line)})}
function nodeBounds(n){const el=[...$('nodeLayer').children].find(x=>x.dataset.id===n.id);return {x:n.x,y:n.y,w:el?.offsetWidth||150,h:el?.offsetHeight||60}}
function anchors(a,b){const A=nodeBounds(a),B=nodeBounds(b),acx=A.x+A.w/2,acy=A.y+A.h/2,bcx=B.x+B.w/2,bcy=B.y+B.h/2;const horizontal=Math.abs(bcx-acx)>=Math.abs(bcy-acy);if(horizontal){const right=bcx>=acx;return [[right?A.x+A.w:A.x,acy],[right?B.x:B.x+B.w,bcy],horizontal]}const down=bcy>=acy;return [[acx,down?A.y+A.h:A.y],[bcx,down?B.y:B.y+B.h],horizontal]}
function drawEdges(){const d=current();if(!d)return;const svg=$('connections');svg.replaceChildren();svg.setAttribute('viewBox','0 0 1800 1200');const ns='http://www.w3.org/2000/svg';const defs=document.createElementNS(ns,'defs');const marker=document.createElementNS(ns,'marker');for(const [k,v] of Object.entries({id:'arrow',viewBox:'0 0 10 10',refX:'9',refY:'5',markerWidth:'7',markerHeight:'7',orient:'auto-start-reverse'}))marker.setAttribute(k,v);const tri=document.createElementNS(ns,'path');tri.setAttribute('d','M 0 0 L 10 5 L 0 10 z');tri.setAttribute('fill','#54bfe8');marker.append(tri);defs.append(marker);svg.append(defs);svg.style.pointerEvents='auto';d.edges.forEach((e,i)=>{const a=d.nodes.find(n=>n.id===e.from),b=d.nodes.find(n=>n.id===e.to);if(!a||!b)return;const [p,q,h]=anchors(a,b);const path=document.createElementNS(ns,'path');const dx=q[0]-p[0],dy=q[1]-p[1];const bend=Math.max(36,Math.min(130,Math.hypot(dx,dy)*0.35));const route=h?`M${p[0]} ${p[1]} C${p[0]+Math.sign(dx||1)*bend} ${p[1]}, ${q[0]-Math.sign(dx||1)*bend} ${q[1]}, ${q[0]} ${q[1]}`:`M${p[0]} ${p[1]} C${p[0]} ${p[1]+Math.sign(dy||1)*bend}, ${q[0]} ${q[1]-Math.sign(dy||1)*bend}, ${q[0]} ${q[1]}`;path.setAttribute('d',route);path.setAttribute('fill','none');path.setAttribute('stroke',state.selectedEdge===i?'#ffd47e':'#54bfe8');path.setAttribute('stroke-width',state.selectedEdge===i?'4':'2.5');if(e.kind==='messageFlow')path.setAttribute('stroke-dasharray','6 5');if(e.kind==='association')path.setAttribute('stroke-dasharray','2 5');if((e.direction||'forward')==='forward'||e.direction==='both')path.setAttribute('marker-end','url(#arrow)');if(e.direction==='reverse'||e.direction==='both')path.setAttribute('marker-start','url(#arrow)');path.style.pointerEvents='stroke';path.style.cursor='pointer';path.onclick=()=>{state.selectedEdge=i;state.selectedNodes.clear();drawSelection();drawEdges();drawEdgeInspector()};svg.append(path)})}
$('sequenceEditor').ondragover=e=>e.preventDefault();$('sequenceEditor').ondrop=e=>{e.preventDefault();const type=e.dataTransfer.getData('component');const d=current();if(d?.kind!=='sequence'||!type)return;if(d.visualStale){notice('Importe o código antes de editar',true);return}if(!d.sequence){try{d.sequence=parseSequence(d.code)}catch(err){notice(err.message,true);return}}const id='P'+(d.sequence.participants.length+1);d.sequence.participants.push({id,label:type==='actor'?'Ator':type==='external'?'Sistema externo':'Participante'});syncGraph();drawSequence();mark()};
$('canvasWrap').ondragover=e=>e.preventDefault();$('canvasWrap').ondrop=e=>{e.preventDefault();const t=e.dataTransfer.getData('component');if(!t)return;const rect=$('nodeLayer').getBoundingClientRect();addNode(t,(e.clientX-rect.left)/state.zoom,(e.clientY-rect.top)/state.zoom)};document.querySelectorAll('[data-component]').forEach(el=>el.ondragstart=e=>e.dataTransfer.setData('component',el.dataset.component));
$('connect').onclick=()=>{state.connect=!state.connect;state.source=null;$('connect').classList.toggle('active',state.connect);notice(state.connect?'Clique no nó de origem e depois no destino':'Modo conectar desativado');drawSelection()};
$('removeSelected').onclick=()=>{const d=current();if(!d)return;if(state.selectedEdge!==null){d.edges.splice(state.selectedEdge,1);state.selectedEdge=null}else{if(!state.selectedNodes.size)return;d.nodes=d.nodes.filter(n=>!state.selectedNodes.has(n.id));d.edges=d.edges.filter(e=>!state.selectedNodes.has(e.from)&&!state.selectedNodes.has(e.to));state.selectedNodes.clear();state.selected=null;}syncGraph();drawNodes();mark()};
$('syncCode').onclick=async()=>{syncGraph();try{await mermaid.parse(current().code);notice('Mermaid validado e atualizado')}catch(e){notice('Mermaid inválido: '+e.message,true)}};
$('repairCode').onclick=async()=>{const d=current();if(!d)return;const repaired=recoverLegacyFlow(d.code);if(repaired!==d.code){try{await mermaid.parse(repaired);d.legacyBackup=d.code;d.code=repaired;d.visualStale=true;$('code').value=d.code;mark();notice('Código legado reparado; original em legacyBackup.');return}catch(e){/* Try reconstructing from the stored visual model. */}}
 if(!['flowchart','usecase','bpmn'].includes(d.kind)||!d.nodes?.length){notice('Não foi possível reparar automaticamente; código original preservado',true);return}
 const reconstructed=flowCode(d.nodes,d.edges||[],d.kind,flowDirection(d));try{await mermaid.parse(reconstructed)}catch(e){notice('Modelo visual salvo também está inválido: '+e.message,true);return}
 if(!confirm('Reconstruir o Mermaid usando os nós e conexões salvos? O código original será preservado em legacyBackup.'))return;
 d.legacyBackup=d.code;d.code=reconstructed;d.visualStale=false;$('code').value=d.code;drawNodes();mark();notice('Diagrama recuperado a partir do modelo visual; backup preservado.')};
$('importCode').onclick=importCode;$('code').oninput=()=>{const d=current();if(d){d.code=$('code').value;d.sequence=null;d.visualStale=true;state.visualError=null;mark()}};
function initMermaid(){mermaid.initialize({startOnLoad:false,securityLevel:'strict',htmlLabels:false,theme:themes[state.project.theme].theme,themeVariables:themes[state.project.theme].themeVariables,suppressErrorRendering:true})}
async function svgFor(d){initMermaid();await mermaid.parse(d.code); const id='athena'+Math.random().toString(36).slice(2);const {svg}=await mermaid.render(id,d.code);return svg}
async function renderPreview(){const d=current();if(!d)return;$('previewStatus').textContent='Renderizando...';try{$('preview').innerHTML=await svgFor(d);$('previewStatus').textContent='Prévia atualizada · '+d.kind}catch(e){$('preview').replaceChildren();$('previewStatus').textContent='Erro Mermaid: '+e.message;notice('Erro na sintaxe Mermaid',true)}}
// Convert Mermaid HTML labels (foreignObject) into native SVG text before rasterization.
// HTML foreignObject and externally referenced resources can taint browser canvases.
function portableSvg(source){
  // Use the browser's SVG-in-HTML parser, as the preview does. C4 can emit HTML entities.
  const doc=new DOMParser().parseFromString(source,'text/html');
  const root=doc.body.firstElementChild, ns='http://www.w3.org/2000/svg';
  if(root?.namespaceURI!==ns||root.localName!=='svg')throw Error('SVG inválido');
  for(const fo of [...root.querySelectorAll('foreignObject')]){
    const x=Number(fo.getAttribute('x')||0),y=Number(fo.getAttribute('y')||0);
    const w=Number(fo.getAttribute('width')||100),h=Number(fo.getAttribute('height')||30);
    for(const br of fo.querySelectorAll('br'))br.replaceWith(doc.createTextNode('\n'));
    const lines=(fo.textContent||'').trim().split(/\r?\n/).map(line=>line.replace(/\s+/g,' ').trim());
    const text=doc.createElementNS(ns,'text');text.setAttribute('x',String(x+w/2));
    text.setAttribute('y',String(y+h/2-(lines.length-1)*7));text.setAttribute('text-anchor','middle');
    text.setAttribute('dominant-baseline','middle');text.setAttribute('font-family','Arial, sans-serif');
    text.setAttribute('font-size','13');text.setAttribute('fill',state.project.theme==='dark'?'#f0f8ff':'#18334a');
    for(const [index,line] of lines.entries()){
      const span=doc.createElementNS(ns,'tspan');
      span.setAttribute('x',String(x+w/2));span.setAttribute('dy',index?'14':'0');
      span.textContent=line;text.append(span);
    }
    fo.replaceWith(text);
  }
  for(const el of [...root.querySelectorAll('image,use')]){
    const href=el.getAttribute('href')||el.getAttribute('xlink:href')||'';
    if(href && !href.startsWith('#') && !href.startsWith('data:'))el.remove();
  }
  for(const el of [...root.querySelectorAll('style')]){
    el.textContent=el.textContent.replace(/@import[^;]*;/g,'').replace(/url\((?!\s*['"]?\s*#)[^)]*\)/gi,'none');
  }
  return new XMLSerializer().serializeToString(root);
}
async function pngFor(d){const svg=portableSvg(await svgFor(d));const r=await secureFetch('/api/export/png',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({svg,theme:state.project.theme})});if(!r.ok){const j=await r.json().catch(()=>({error:'Falha no renderizador PNG'}));throw Error(j.error)}const blob=await r.blob();return await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob)})}
$('downloadSvg').onclick=async()=>{try{const svg=await svgFor(current());downloadBlob(new Blob([svg],{type:'image/svg+xml'}),current().id+'.svg')}catch(e){notice(e.message,true)}};
$('downloadPng').onclick=async()=>{try{const data=await pngFor(current());const r=await fetch(data);downloadBlob(await r.blob(),current().id+'.png')}catch(e){notice(e.message,true)}};
function simpleMd(md){return md.split('\n').map(line=>{if(/^### /.test(line))return '<h3>'+htmlEscape(line.slice(4))+'</h3>';if(/^## /.test(line))return '<h2>'+htmlEscape(line.slice(3))+'</h2>';if(/^# /.test(line))return '<h1>'+htmlEscape(line.slice(2))+'</h1>';if(!line.trim())return '<p></p>';return '<p>'+htmlEscape(line)+'</p>'}).join('')}
async function renderDocument(){let md=state.project.markdown;const re=/\{\{diagram:([a-zA-Z0-9_-]+)\}\}/g;const matches=[...md.matchAll(re)];for(const m of matches){const d=state.project.diagrams.find(x=>x.id===m[1]);if(!d){md=md.replace(m[0],'[Diagrama não encontrado: '+m[1]+']');continue}try{const img=await pngFor(d);md=md.replace(m[0],'@@IMG'+m[1]+'@@');state['img_'+m[1]]=img}catch(e){md=md.replace(m[0],'[Erro ao gerar '+m[1]+': '+e.message+']')}}let html=simpleMd(md);for(const m of matches){const data=state['img_'+m[1]];if(data)html=html.replaceAll('@@IMG'+m[1]+'@@',`<img alt="${htmlEscape(m[1])}" src="${data}">`)}$('docPreview').innerHTML=html;const problems=documentProblems();$('documentValidation').textContent=problems.missing.length?'Referências ausentes: '+problems.missing.join(', '):'Diagramas referenciados: '+problems.count}
function insertAtCursor(value){const box=$('markdown');const start=box.selectionStart,end=box.selectionEnd;box.setRangeText(value,start,end,'end');state.project.markdown=box.value;mark();box.focus();if(state.tab==='document')renderDocument()}
$('insertDiagramButton').onclick=()=>{const id=$('insertDiagram').value;if(id)insertAtCursor('\n\n{{diagram:'+id+'}}\n')};
$('insertHeading').onclick=()=>insertAtCursor('\n## Nova seção\n\nTexto da seção.\n');
function documentProblems(){const ids=new Set(state.project.diagrams.map(d=>d.id)),matches=[...state.project.markdown.matchAll(/\{\{diagram:([^}]+)\}\}/g)];const missing=[...new Set(matches.map(m=>m[1]).filter(id=>!ids.has(id)))];const unused=state.project.diagrams.filter(d=>!matches.some(m=>m[1]===d.id)).map(d=>d.title);return {missing,unused,count:matches.length}}
$('validateDocument').onclick=()=>{const r=documentProblems();$('documentValidation').textContent=r.missing.length?'Diagramas não encontrados: '+r.missing.join(', '):'Referências válidas: '+r.count+' · Diagramas não utilizados: '+r.unused.length;notice(r.missing.length?'Corrija as referências antes de exportar':'Documento validado',!!r.missing.length)};
$('exportMarkdown').onclick=()=>{const blob=new Blob([state.project.markdown],{type:'text/markdown;charset=utf-8'});downloadBlob(blob,state.project.id+'.md')};
$('markdown').oninput=()=>{state.project.markdown=$('markdown').value;mark()};
$('exportDocumentation').onclick=async()=>{try{notice('Gerando PNGs e pacote de documentação...');const problems=documentProblems();if(problems.missing.length)throw Error('Referências inválidas: '+problems.missing.join(', '));const images={};const used=new Set([...state.project.markdown.matchAll(/\{\{diagram:([^}]+)\}\}/g)].map(m=>m[1]));for(const d of state.project.diagrams.filter(d=>used.has(d.id)))images[d.id]=await pngFor(d);const r=await secureFetch('/api/export/documentation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:state.project,images})});if(!r.ok){const j=await r.json();throw Error(j.error)}downloadBlob(await r.blob(),'athena_documentacao.zip');notice('Pacote Markdown + imagens exportado')}catch(e){notice(e.message,true)}};
$('saveProject').onclick=async()=>{
  const project=state.project;
  if(!project||state.saving||(project._access?.level??3)<2)return;
  project.title=$('projectTitle').value.trim()||'Projeto';
  project.theme=$('theme').value;
  project.markdown=$('markdown').value;
  const savedContent=snapshot();
  const savedTitle=project.title;
  state.saving=true;
  setProjectAccess(project._access);
  try{
    const result=await api('/api/projects/'+project.id,{
      method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(project)
    });
    const option=[...$('projects').options].find(item=>item.value===project.id);
    if(option)option.textContent=savedTitle;
    if(state.project?.id!==project.id||state.project._access?.revision!==project._access?.revision)return;
    if(state.project._access)state.project._access.revision=result.revision;
    state.dirty=snapshot()!==savedContent;
    notice(state.dirty?'Ainda há alterações não salvas':'Projeto salvo');
  }catch(e){notice(e.message,true)}
  finally{
    state.saving=false;
    if(state.project)setProjectAccess(state.project._access);
  }
};
$('projects').onchange=async()=>{
  if(state.dirty&&!confirm('Descartar alterações não salvas?')){
    $('projects').value=state.project.id;
    return;
  }
  await loadProject($('projects').value);
};
window.addEventListener('beforeunload',event=>{
  if(!state.dirty&&!state.saving)return;
  event.preventDefault();
  event.returnValue=true;
});
$('newProject').onclick=async()=>{const title=prompt('Nome do novo projeto:','Novo projeto');if(!title)return;try{const p=await api('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title})});await loadProjects(p.id)}catch(e){notice(e.message,true)}};
$('deleteProject').onclick=async()=>{if(!confirm('Excluir este projeto permanentemente?'))return;try{await api('/api/projects/'+state.project.id,{method:'DELETE'});await loadProjects()}catch(e){notice(e.message,true)}};
$('theme').onchange=()=>{state.project.theme=$('theme').value;mark();if(state.tab==='preview')renderPreview()};$('projectTitle').oninput=mark;
$('renameDiagram').onclick=()=>{const d=current();if(!d)return;const name=prompt('Novo nome do diagrama:',d.title);if(!name?.trim())return;d.title=name.trim().slice(0,120);$('diagramTitle').textContent=d.title;renderList();mark()};
$('deleteDiagram').onclick=()=>{const d=current();if(!d||!confirm('Excluir diagrama '+d.title+'?'))return;state.project.diagrams=state.project.diagrams.filter(x=>x.id!==d.id);state.active=state.project.diagrams[0]?.id||null;renderList();switchDiagram(state.active);if(!state.active){$('nodeLayer').replaceChildren();$('code').value=''}mark();notice('Diagrama excluído. Remova também sua referência no Markdown.')};
$('addDiagram').onclick=()=>$('newDiagramDialog').showModal();$('newDiagramForm').onsubmit=e=>{if(e.submitter?.value!=='ok')return;const title=$('newDiagramTitle').value.trim()||'Diagrama';const kind=$('newDiagramKind').value;const id=makeId();const d={id,title,kind,code:samples[kind],nodes:[],edges:[]};if(kind==='sequence')d.sequence=parseSequence(d.code);if(kind==='er')d.structured=parseER(d.code);if(kind==='class')d.structured=parseClass(d.code);if(kind==='c4'){const m=parseC4(d.code);d.nodes=m.nodes;d.edges=m.edges;d.c4Title=m.title;d.c4Header=m.header}if(['flowchart','usecase','bpmn'].includes(kind)){const m=parseFlow(d.code);d.nodes=m.nodes;d.edges=m.edges}state.project.diagrams.push(d);state.project.markdown+='\n## '+title+'\n\n{{diagram:'+id+'}}\n';$('markdown').value=state.project.markdown;switchDiagram(id);mark()};
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>switchTab(t.dataset.tab));$('refreshPreview').onclick=()=>{switchTab('preview')};$('undo').onclick=()=>historyMove(true);$('redo').onclick=()=>historyMove(false);window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.target.closest('input,textarea,[contenteditable]')&&e.key.toLowerCase()==='z'){e.preventDefault();historyMove(e.shiftKey?false:true)}if((e.ctrlKey||e.metaKey)&&!e.target.closest('input,textarea,[contenteditable]')&&e.key.toLowerCase()==='y'){e.preventDefault();historyMove(false)}if(['Delete','Backspace'].includes(e.key)&&!e.target.closest('input,textarea,select,[contenteditable]')&&state.tab==='visual'&&(state.selectedNodes.size||state.selectedEdge!==null)){e.preventDefault();$('removeSelected').click()}if(e.key==='Escape'&&state.connect){state.connect=false;state.source=null;$('connect').classList.remove('active');drawSelection()}if(e.ctrlKey&&e.key.toLowerCase()==='s'){e.preventDefault();$('saveProject').click()}if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();switchTab('preview')}});
loadProjects(new URLSearchParams(location.search).get('projeto')).catch(e=>notice(e.message,true));

$('newByType').onclick=()=>{$('newDiagramKind').value=$('diagramType').value;$('newDiagramDialog').showModal()};

// v3.0: persistent interface settings and Markdown manual viewer.
const uiStrings={pt:{toggleCanvasGrid:'Grade',studioSharing:'Compartilhamento',projectPermissions:'Permissões',accountMenuLabel:'Minha conta',accountProfileLink:'Meu perfil',accountSharedLink:'Projetos compartilhados',accountLogout:'Encerrar sessão','newProject':'Novo projeto','deleteProject':'Excluir','saveProject':'Salvar projeto','exportDocumentation':'Exportar documentação','addDiagram':'Novo diagrama','newByType':'Criar deste tipo','renameDiagram':'Renomear diagrama','deleteDiagram':'Excluir diagrama','undo':'Desfazer','redo':'Refazer','connect':'Conectar','removeSelected':'Remover seleção','syncCode':'Gerar Mermaid','repairCode':'Reparar legado','importCode':'Importar código → Visual','refreshPreview':'Atualizar prévia','downloadSvg':'SVG','downloadPng':'PNG','openManuals':'Manuais','backupProjects':'Backup ZIP','downloadProject':'Exportar projeto','importProject':'Importar projeto'},en:{toggleCanvasGrid:'Grid',studioSharing:'Sharing',projectPermissions:'Permissions',accountMenuLabel:'My account',accountProfileLink:'My profile',accountSharedLink:'Shared projects',accountLogout:'Sign out','newProject':'New project','deleteProject':'Delete','saveProject':'Save project','exportDocumentation':'Export documentation','addDiagram':'New diagram','newByType':'Create this type','renameDiagram':'Rename diagram','deleteDiagram':'Delete diagram','undo':'Undo','redo':'Redo','connect':'Connect','removeSelected':'Remove selection','syncCode':'Generate Mermaid','repairCode':'Repair legacy','importCode':'Import code → Visual','refreshPreview':'Refresh preview','downloadSvg':'SVG','downloadPng':'PNG','openManuals':'Manuals','backupProjects':'Backup ZIP','downloadProject':'Export project','importProject':'Import project'}};
const uiLabels={pt:['Projeto','Nome','Tema','DIAGRAMAS','TIPO DO DIAGRAMA','BIBLIOTECA DE COMPONENTES','Construtor visual','Código Mermaid','Prévia','Documento Markdown'],en:['Project','Name','Theme','DIAGRAMS','DIAGRAM TYPE','COMPONENT LIBRARY','Visual builder','Mermaid code','Preview','Markdown document']};
// Extra static UI translations. Preserve the original text for reversible switching.
const extraUiEnglish={
  'Idioma':'Language','Interface':'Interface','Projeto':'Project','Nome':'Name','Tema':'Theme',
  'TIPO DO DIAGRAMA':'DIAGRAM TYPE','BIBLIOTECA DE COMPONENTES':'COMPONENT LIBRARY',
  'Atual':'Current','Flowchart':'Flowchart','Sequência':'Sequence','Casos de uso':'Use cases',
  'BPMN simplificado':'Simplified BPMN','DER / MER':'ER diagram','Classes UML':'UML classes',
  'Processo / Serviço':'Process / Service','Banco de dados':'Database','Sistema externo':'External system',
  'Decisão':'Decision','Ator / Participante':'Actor / Participant','Evento inicial':'Start event',
  'Evento final':'End event','Subprocesso':'Subprocess','Documento':'Document',
  'Evento intermediário':'Intermediate event','Tarefa humana':'User task','Tarefa serviço':'Service task',
  'Gateway exclusivo':'Exclusive gateway','Gateway paralelo':'Parallel gateway','Gateway inclusivo':'Inclusive gateway',
  'Pool / participante':'Pool / participant','Lane / área':'Lane / area','Gateway BPMN':'BPMN gateway',
  'Direção':'Direction','Origem → destino':'Source → target','Destino → origem':'Target → source',
  'Bidirecional ↔':'Bidirectional ↔','Sem seta —':'No arrow —','Atualizar prévia':'Refresh preview',
  'Baixar .md':'Download .md','Salvar projeto':'Save project','Novo diagrama':'New diagram',
  'TIPO DO DIAGRAMA':'DIAGRAM TYPE','Prévia':'Preview','Código Mermaid':'Mermaid code',
  'Construtor visual':'Visual builder','Documento Markdown':'Markdown document'
};
function applyStaticTranslations(lang){
  const targets=document.querySelectorAll('.sidebar,.panel-header,.tabs,.toolbar,header');
  for(const target of targets){
    const walker=document.createTreeWalker(target,NodeFilter.SHOW_TEXT);
    let node;
    while((node=walker.nextNode())){
      if(node.parentElement?.closest('textarea,script,style,option[data-dynamic]'))continue;
      if(node._athenaOriginal===undefined)node._athenaOriginal=node.textContent;
      const original=node._athenaOriginal;
      const trimmed=original.trim();
      if(!trimmed || !extraUiEnglish[trimmed])continue;
      node.textContent=original.replace(trimmed,lang==='en'?extraUiEnglish[trimmed]:trimmed);
    }
  }
}

function setUiLanguage(lang){lang=lang==='en'?'en':'pt';localStorage.setItem('athena.ui.lang',lang);if(csrfToken)document.cookie='athena_lang='+lang+'; Path=/; Max-Age=31536000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');document.documentElement.lang=lang==='en'?'en':'pt-BR';for(const [id,label] of Object.entries(uiStrings[lang])){const e=$(id);if(e){if(e.title)e.title=label;if(!['addDiagram','renameDiagram','deleteDiagram'].includes(id))e.textContent=label}}const labels=uiLabels[lang];document.querySelectorAll('.toolbar label').forEach((e,i)=>{if(i<3){const node=[...e.childNodes].find(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim());if(node)node.textContent=labels[i]+' '}});document.querySelectorAll('.section-title').forEach((e,i)=>{if(i>=3)return;const node=[...e.childNodes].find(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim());if(node)node.textContent=labels[i+3]+' '});document.querySelectorAll('.tab').forEach((e,i)=>e.textContent=labels[i+6]);applyStaticTranslations(lang);}
function setUiTheme(theme){theme=theme==='light'?'light':'dark';document.body.dataset.uiTheme=theme;localStorage.setItem('athena.ui.theme',theme)}
const accountLanguage=document.cookie.match(/(?:^|;\s*)athena_lang=(pt|en)(?:;|$)/)?.[1];
$('uiLanguage').value=(csrfToken&&accountLanguage)||localStorage.getItem('athena.ui.lang')||'pt';$('uiTheme').value=localStorage.getItem('athena.ui.theme')||'dark';setUiLanguage($('uiLanguage').value);setUiTheme($('uiTheme').value);
$('uiLanguage').addEventListener('change',e=>setUiLanguage(e.target.value));$('uiTheme').addEventListener('change',e=>setUiTheme(e.target.value));
$('openManuals').onclick=async()=>{
  const dialog=$('manualDialog'), host=$('manualList'), content=$('manualContent');
  try{
    const {manuals}=await api('/api/manuals');
    host.replaceChildren();
    content.replaceChildren();
    if(!dialog.open)dialog.showModal();
    let selected;
    for(const manual of manuals){
      const button=document.createElement('button');
      button.textContent=manual.title;
      button.onclick=async()=>{
        selected?.removeAttribute('aria-current');
        selected=button;
        button.setAttribute('aria-current','true');
        content.textContent='Carregando…';
        try{
          const doc=await api('/api/manuals/'+encodeURIComponent(manual.id));
          if(selected!==button || !button.isConnected)return;
          content.innerHTML=doc.html;
          content.scrollTop=0;
        }catch(e){
          if(selected===button && button.isConnected)content.textContent=e.message;
        }
      };
      host.append(button);
    }
    if(host.firstChild)host.firstChild.click();
    else content.textContent='Nenhum manual disponível.';
  }catch(e){notice(e.message,true)}
};
$('closeManuals').onclick=()=>$('manualDialog').close();

// Athena v4.0: portable project backup and import.
$('backupProjects').onclick=async()=>{try{const r=await fetch('/api/projects/backup/all');if(!r.ok)throw Error('Backup indisponível');downloadBlob(await r.blob(),'athena_projetos_backup.zip')}catch(e){notice(e.message,true)}};
$('downloadProject').onclick=async()=>{try{const r=await fetch('/api/projects/'+state.project.id+'/download');if(!r.ok)throw Error('Falha ao exportar');downloadBlob(await r.blob(),state.project.id+'.json')}catch(e){notice(e.message,true)}};
$('importProject').onclick=()=>$('projectImportFile').click();
$('projectImportFile').onchange=async()=>{const file=$('projectImportFile').files[0];if(!file)return;try{const obj=JSON.parse(await file.text());const r=await secureFetch('/api/projects/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});const data=await r.json();if(!r.ok)throw Error(data.error||'Importação inválida');await loadProjects(data.id);await loadProject(data.id);notice('Projeto importado')}catch(e){notice(e.message,true)}finally{$('projectImportFile').value=''}};


function updateCanvasGrid(){
  const enabled=current()?.showGrid!==false;
  $('canvasWrap').classList.toggle('grid-hidden',!enabled);
  $('toggleCanvasGrid').setAttribute('aria-pressed',String(enabled));
}
$('toggleCanvasGrid').onclick=()=>{
  const diagram=current();
  if(!diagram||(state.project._access?.level??3)<2)return;
  diagram.showGrid=diagram.showGrid===false;
  updateCanvasGrid();
  mark();
};

// Canvas zoom is independent from the browser zoom; browser Ctrl+/- remains available.
function setCanvasZoom(next){
 state.zoom=Math.max(0.4,Math.min(2,Math.round(next*10)/10));
 const stage=$('canvasStage');
 if(stage)stage.style.transform=`scale(${state.zoom})`;
 const indicator=$('canvasZoomValue');if(indicator)indicator.textContent=Math.round(state.zoom*100)+'%';
}
$('canvasZoomIn')?.addEventListener('click',()=>setCanvasZoom(state.zoom+0.1));
$('canvasZoomOut')?.addEventListener('click',()=>setCanvasZoom(state.zoom-0.1));
$('canvasZoomReset')?.addEventListener('click',()=>setCanvasZoom(1));
setCanvasZoom(1);

/* Athena brand lockup follows portal theme */
(function(){const logo=document.getElementById("brandLogo");if(!logo)return;const apply=()=>{const light=document.body.dataset.uiTheme==="light";logo.src="/static/branding/athena-logo-"+(light?"light":"dark")+".png"};apply();new MutationObserver(apply).observe(document.body,{attributes:true,attributeFilter:["data-ui-theme"]});})();

const accountMenu = document.querySelector('.account-menu');
if (accountMenu) {
  document.addEventListener('click', event => {
    if (accountMenu.open && !accountMenu.contains(event.target)) accountMenu.open = false;
  });
  accountMenu.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || !accountMenu.open) return;
    accountMenu.open = false;
    accountMenu.querySelector('summary').focus();
  });
}
