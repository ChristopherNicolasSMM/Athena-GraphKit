/* Athena Studio: conservative Mermaid <-> visual model adapters.
   Never silently rewrite syntax outside the supported subset. */
export const cleanLabel = s => String(s ?? '').replace(/[\r\n\[\]{}<>|"`]/g,' ').trim().slice(0,120);
const flowShapes = [
  ['start', '((', '))'], ['database', '[(', ')]'], ['subprocess', '[[', ']]'],
  ['external', '{{', '}}'], ['actor', '([', '])'], ['document', '[/', '/]'],
  ['decision', '{', '}'], ['task', '(', ')'], ['process', '[', ']'],
];
const shapeAliases = {
  end: 'start', 'event-intermediate': 'start', gateway: 'decision',
  exclusiveGateway: 'decision', parallelGateway: 'decision', inclusiveGateway: 'decision',
  pool: 'subprocess', lane: 'subprocess', input: 'document', output: 'document',
};
const flowLabel = value => String(value).replace(/<br\s*\/?>|[#"<>&|`]/gi, char => char.length > 1 ? '<br/>' : '#'+char.codePointAt(0)+';');
const readFlowLabel = value => value.replace(/#(35|34|60|62|38|124|96);/g, (_, code) => String.fromCodePoint(Number(code)));
const flowShape = node => {
  const type = shapeAliases[node.type] || node.type;
  const [, open, close] = flowShapes.find(shape => shape[0] === type) || flowShapes.at(-1);
  return node.id+open+'"'+flowLabel(node.label ?? node.id)+'"'+close;
};
function readFlowNode(raw) {
  const match = /^([A-Za-z][\w]*)(.*)$/.exec(raw.trim());
  if (!match) return null;
  const [, id, suffix] = match;
  if (!suffix) return {id, label:id, type:'process'};
  for (const [type, open, close] of flowShapes) {
    if (!suffix.startsWith(open) || !suffix.endsWith(close)) continue;
    const body = suffix.slice(open.length, -close.length);
    const quoted = /^"([^"]*)"$/.exec(body);
    if (!quoted && /[()[\]{}"]/.test(body)) continue;
    return {id, label:readFlowLabel(quoted ? quoted[1] : body), type};
  }
  return null;
}
export function parseFlow(code){
 code=recoverLegacyFlow(code);const lines=code.split(/\r?\n/),head=(lines.shift()||'').trim();
 if(!/^(flowchart|graph)\s+(LR|RL|TB|TD|BT)$/i.test(head))throw Error('Cabeçalho de flowchart não suportado');
 const nodes=[],edges=[],seen=new Map();
 const add=(raw)=>{const n=readFlowNode(raw);if(!n)throw Error('Linha fora do subconjunto visual: '+raw);if(!seen.has(n.id)){n.x=45+(nodes.length%4)*215;n.y=80+Math.floor(nodes.length/4)*145;seen.set(n.id,n);nodes.push(n)}else if(raw.trim()!==n.id){Object.assign(seen.get(n.id),{label:n.label,type:n.type})}return n.id};
 for(const raw of lines){const line=raw.trim().replace(/;$/,'');if(!line||line.startsWith('%%'))continue;
  const edge=line.match(/^(.+?)\s+(<-->|-->|<--|---)(?:\|([^|]*)\|)?\s+(.+)$/);
  if(edge){const from=add(edge[1]),to=add(edge[4]);edges.push({from,to,direction:({'-->':'forward','<--':'reverse','<-->':'both','---':'none'})[edge[2]],label:readFlowLabel(edge[3]||'')});continue}
  add(line);
 }
 return {nodes,edges,direction:head.split(/\s+/)[1].toUpperCase()};
}
export function flowCode(nodes,edges,kind='flowchart',direction='LR'){
 const lines=['flowchart '+direction,...nodes.map(n=>'    '+flowShape(n))];
 for(const e of edges){const dir=e.direction||'forward',label=flowLabel(e.label||'');let from=e.from,to=e.to;
  // Reversed arrows are serialized by swapping endpoints, avoiding the Mermaid lexical error with <--.
  if(dir==='reverse'){[from,to]=[to,from]}
  const arrow=dir==='both'?'<-->':dir==='none'?'---':'-->';
  lines.push(`    ${from} ${arrow}${label?'|'+label+'|':''} ${to}`);
 }
 return lines.join('\n');
}
export function parseSequence(code){
  const lines=code.split(/\r?\n/);if(lines.shift()?.trim()!=='sequenceDiagram')throw Error('Cabeçalho sequenceDiagram obrigatório');
  const participants=[],steps=[];let autonumber=false;
  for(const raw of lines){const line=raw.trim();if(!line||line.startsWith('%%'))continue;
    if(line==='autonumber'){autonumber=true;continue}
    let m=line.match(/^participant\s+([A-Za-z]\w*)(?:\s+as\s+(.+))?$/);
    if(m){participants.push({id:m[1],label:m[2]||m[1]});continue}
    m=line.match(/^([A-Za-z]\w*)\s*(->>|-->>|->|-->)\s*([A-Za-z]\w*)\s*:\s*(.*)$/);
    if(m){steps.push({type:'message',from:m[1],to:m[3],arrow:m[2],label:m[4]});continue}
    m=line.match(/^(opt|loop|alt|par|critical|break|rect)\s+(.+)$/);
    if(m){steps.push({type:'block',keyword:m[1],label:m[2]});continue}
    m=line.match(/^else(?:\s+(.*))?$/);if(m){steps.push({type:'else',label:m[1]||''});continue}
    if(line==='end'){steps.push({type:'end'});continue}
    m=line.match(/^Note\s+(over|left of|right of)\s+([A-Za-z]\w*)(?:\s*,\s*([A-Za-z]\w*))?\s*:\s*(.*)$/i);
    if(m){steps.push({type:'note',position:m[1],from:m[2],to:m[3]||'',label:m[4]});continue}
    throw Error('Linha de sequência não suportada no editor visual: '+line.slice(0,100));
  }
  return {participants,steps,autonumber};
}
export function sequenceCode(model){
  const lines=['sequenceDiagram'];if(model.autonumber)lines.push('    autonumber');
  for(const p of model.participants)lines.push(`    participant ${p.id} as ${cleanLabel(p.label)}`);
  for(const s of model.steps){
    if(s.type==='message')lines.push(`    ${s.from}${s.arrow||'->>'}${s.to}: ${cleanLabel(s.label)}`);
    if(s.type==='block')lines.push(`    ${s.keyword||'opt'} ${cleanLabel(s.label)}`);
    if(s.type==='else')lines.push(`    else${s.label?' '+cleanLabel(s.label):''}`);
    if(s.type==='end')lines.push('    end');
    if(s.type==='note')lines.push(`    Note ${s.position||'over'} ${s.from}${s.to?','+s.to:''}: ${cleanLabel(s.label)}`);
  }
  return lines.join('\n');
}
export function parseC4(code){
  const lines=code.split(/\r?\n/);const header=lines.shift()?.trim();if(!['C4Context','C4Container','C4Component'].includes(header))throw Error('Tipo C4 não suportado no visual');
  const nodes=[],edges=[];let title='';
  for(const raw of lines){const line=raw.trim();if(!line||line.startsWith('%%'))continue;
    if(line.startsWith('title ')){title=line.slice(6);continue}
    let m=line.match(/^(Person|Person_Ext|System|System_Ext|SystemDb|Container|ContainerDb|Container_Ext|Component|ComponentDb|Component_Ext)\(\s*([A-Za-z]\w*)\s*,\s*"([^"]*)"(?:\s*,\s*"([^"]*)")?\s*\)$/);
    if(m){nodes.push({id:m[2],label:m[3],description:m[4]||'',type:m[1],x:45+(nodes.length%4)*215,y:80+Math.floor(nodes.length/4)*145});continue}
    m=line.match(/^Rel\(\s*([A-Za-z]\w*)\s*,\s*([A-Za-z]\w*)\s*,\s*"([^"]*)"\s*\)$/);
    if(m){edges.push({from:m[1],to:m[2],label:m[3]});continue}
    throw Error('Linha C4 não suportada no editor visual: '+line.slice(0,100));
  }
  return {nodes,edges,title,header};
}
export function c4Code(nodes,edges,title='Contexto da solução',header='C4Context'){
  const q=s=>'"'+cleanLabel(s).replace(/"/g,'')+'"';
  const lines=[['C4Context','C4Container','C4Component'].includes(header)?header:'C4Context','    title '+cleanLabel(title)];
  for(const n of nodes)lines.push(`    ${n.type||'System'}(${n.id}, ${q(n.label)}, ${q(n.description||'')})`);
  for(const e of edges)lines.push(`    Rel(${e.from}, ${e.to}, ${q(e.label||'Utiliza')})`);
  return lines.join('\n');
}


// Conservative ER/class adapters: reject unsupported syntax instead of losing it.
const identifier = /^[A-Za-z_][A-Za-z0-9_]*$/;
export function parseER(code){
 const lines=code.split(/\r?\n/);if(lines.shift()?.trim()!=='erDiagram')throw Error('Cabeçalho erDiagram obrigatório');
 const entities=[],relations=[];let current=null;
 for(const raw of lines){const s=raw.trim();if(!s||s.startsWith('%%'))continue;
  if(current){if(s==='}'){current=null;continue}const m=s.match(/^([A-Za-z][\w\[\](),]*)\s+([A-Za-z_]\w*)(?:\s+(PK|FK|UK)(?:,\s*(PK|FK|UK))?)?(?:\s+"([^"]*)")?$/);if(!m)throw Error('Atributo ER não suportado: '+s);current.fields.push({type:m[1],name:m[2],key:[m[3],m[4]].filter(Boolean).join(','),comment:m[5]||''});continue}
  let m=s.match(/^([A-Za-z_]\w*)\s*\{$/);if(m){current=entities.find(e=>e.id===m[1]);if(!current){current={id:m[1],fields:[]};entities.push(current)}continue}
  m=s.match(/^([A-Za-z_]\w*)\s+(\|\||\|o|o\||o\{|\|\{|\}\||\}o|\}\{|--|\|\||o\{|\|\{)(--|\.\.)(\|\||\|o|o\||o\{|\|\{|\}\||\}o|\}\{)\s+([A-Za-z_]\w*)\s*:\s*(.*)$/);
  if(m){for(const id of [m[1],m[5]])if(!entities.some(e=>e.id===id))entities.push({id,fields:[]});relations.push({from:m[1],left:m[2],line:m[3],right:m[4],to:m[5],label:m[6]});continue}
  if(identifier.test(s)){if(!entities.some(e=>e.id===s))entities.push({id:s,fields:[]});continue}
  throw Error('Linha ER não suportada: '+s)
 }
 if(current)throw Error('Bloco de entidade ER não fechado');return {entities,relations};
}
export function erCode(model){const lines=['erDiagram'];for(const e of model.entities){if(!identifier.test(e.id))throw Error('Identificador ER inválido');lines.push('    '+e.id+' {');for(const f of e.fields){lines.push(`        ${f.type} ${f.name}${f.key?' '+f.key:''}${f.comment?' "'+f.comment.replaceAll('"','')+'"':''}`)}lines.push('    }')}for(const r of model.relations)lines.push(`    ${r.from} ${r.left}${r.line}${r.right} ${r.to} : ${r.label||'relaciona'}`);return lines.join('\n')}
export function parseClass(code){
 const lines=code.split(/\r?\n/);if(lines.shift()?.trim()!=='classDiagram')throw Error('Cabeçalho classDiagram obrigatório');
 const classes=[],relations=[];let current=null;
 for(const raw of lines){const s=raw.trim();if(!s||s.startsWith('%%'))continue;
  if(current){if(s==='}'){current=null;continue}if(/[{}]/.test(s))throw Error('Membro de classe não suportado: '+s);current.members.push(s);continue}
  let m=s.match(/^class\s+([A-Za-z_]\w*)\s*\{$/);if(m){current=classes.find(c=>c.id===m[1]);if(!current){current={id:m[1],members:[]};classes.push(current)}continue}
  m=s.match(/^class\s+([A-Za-z_]\w*)$/);if(m){if(!classes.some(c=>c.id===m[1]))classes.push({id:m[1],members:[]});continue}
  m=s.match(/^([A-Za-z_]\w*)\s+(?:"([^"]*)"\s+)?(<\|--|--\|>|\*--|--\*|o--|--o|<--|-->|--|\.\.|<\.\.|\.\.>)(?:\s+"([^"]*)")?\s+([A-Za-z_]\w*)(?:\s*:\s*(.*))?$/);
  if(m){for(const id of [m[1],m[5]])if(!classes.some(c=>c.id===id))classes.push({id,members:[]});relations.push({from:m[1],fromCard:m[2]||'',arrow:m[3],toCard:m[4]||'',to:m[5],label:m[6]||''});continue}
  throw Error('Linha de classe não suportada: '+s)
 }
 if(current)throw Error('Bloco de classe não fechado');return {classes,relations};
}
export function classCode(model){const lines=['classDiagram'];for(const c of model.classes){if(!identifier.test(c.id))throw Error('Identificador de classe inválido');lines.push('    class '+c.id+' {');for(const m of c.members)lines.push('        '+m);lines.push('    }')}for(const r of model.relations)lines.push(`    ${r.from}${r.fromCard?' "'+r.fromCard+'"':''} ${r.arrow} ${r.toCard?'"'+r.toCard+'" ':''}${r.to}${r.label?' : '+r.label:''}`);return lines.join('\n')}

// Conservative legacy repair: fixes only known v2.6 invalid edge forms.
export function recoverLegacyFlow(code){
 return code.split(/\r?\n/).map(line=>{
  const m=line.match(/^(\s*)([A-Za-z]\w*)\s+<--\s+([A-Za-z]\w*)(?:\s+\3)+\s*$/);
  if(m)return `${m[1]}${m[3]} --> ${m[2]}`;
  const reverse=line.match(/^(\s*)([A-Za-z]\w*)\s+<--\s+([A-Za-z]\w*)\s*$/);
  return reverse?`${reverse[1]}${reverse[3]} --> ${reverse[2]}`:line;
 }).join('\n');
}
export const BPMN_COMPONENTS=Object.freeze({
 start:'Evento inicial',end:'Evento final','event-intermediate':'Evento intermediário',userTask:'Tarefa humana',serviceTask:'Tarefa de serviço',subprocess:'Subprocesso',exclusiveGateway:'Gateway exclusivo',parallelGateway:'Gateway paralelo',inclusiveGateway:'Gateway inclusivo',pool:'Pool',lane:'Lane',document:'Objeto de dados'
});
export function validateBpmnModel(nodes,edges){
 const errors=[];const byId=new Map(nodes.map(n=>[n.id,n]));
 for(const e of edges){const a=byId.get(e.from),b=byId.get(e.to);if(!a||!b){errors.push('Conexão com componente inexistente');continue}
  if(a.type==='end'&&e.kind!=='association')errors.push('Evento final não pode iniciar fluxo: '+a.id);
  if(b.type==='start'&&e.kind!=='association')errors.push('Evento inicial não pode receber fluxo: '+b.id);
  if(e.kind==='messageFlow'&&e.from===e.to)errors.push('Fluxo de mensagem não pode ser reflexivo');
  if(e.kind==='sequenceFlow'&&(a.type==='pool'||b.type==='pool'))errors.push('Fluxo de sequência não deve ligar diretamente pools');
 }
 return errors;
}
