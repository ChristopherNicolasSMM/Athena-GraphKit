import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=readFileSync(new URL('../portal/static/model.js',import.meta.url),'utf8');
const mod=await import('data:text/javascript;base64,'+Buffer.from(src).toString('base64'));
const flow='flowchart LR\n    A[Portal Comlink] --> B[API RAP]\n    B --> C[(SAP S/4HANA)]';
const f=mod.parseFlow(flow);assert.equal(f.nodes.length,3);assert.equal(f.edges.length,2);assert.equal(mod.parseFlow(mod.flowCode(f.nodes,f.edges)).edges.length,2);
const uc='flowchart LR\n    U([Usuário]) --> UC1([Consultar cotação])\n    U --> UC2([Criar pedido])';assert.equal(mod.parseFlow(uc).edges.length,2);
const seq=`sequenceDiagram
 autonumber
 participant CLK as Processo Comlink
 participant SAP as SAP RFC
 participant API as Endpoints Comlink
 opt !retornoCDC
 CLK->>SAP: Consultas
 SAP-->>CLK: Dados
 CLK->>API: POST retorno
 end
 Note over CLK,SAP: Conexão principal
 loop MSP_MOVCRF: por fornecedor
 CLK->>SAP: Validações
 end
 alt Tipo de pedido
 CLK->>SAP: Criar pedido
 else Tipo de contrato
 CLK->>SAP: Criar contrato
 end`;
const s=mod.parseSequence(seq);assert.equal(s.participants.length,3);assert.equal(s.autonumber,true);assert.deepEqual(mod.parseSequence(mod.sequenceCode(s)),s);
const c4=`C4Context
 title Contexto da solução
 Person(user, "Usuário", "Equipe de compras")
 System(portal, "Portal Comlink", "Aplicação")
 System_Ext(sap, "SAP S/4HANA", "ERP")
 Rel(user, portal, "Utiliza")
 Rel(portal, sap, "Integra")`;
const c=mod.parseC4(c4);assert.equal(c.nodes.length,3);assert.equal(c.edges.length,2);assert.equal(mod.parseC4(mod.c4Code(c.nodes,c.edges,c.title)).edges.length,2);
assert.throws(()=>mod.parseSequence('sequenceDiagram\n activate A'),/não suportada/);
assert.throws(()=>mod.parseFlow('flowchart LR\n subgraph cluster'),/fora do subconjunto/);
console.log('Athena visual adapters: 7 checks OK');

// Regression: reverse arrows must not produce the invalid <-- Mermaid token.
const reverse=mod.flowCode([{id:'A',label:'A',type:'process'},{id:'B',label:'B',type:'decision'}],[{from:'A',to:'B',direction:'reverse',label:'volta'}]);
assert.match(reverse,/B -->\|volta\| A/);
assert.doesNotMatch(reverse, /\s<--\s/);
assert.equal(mod.parseFlow(reverse).edges.length,1);
const bi=mod.flowCode([{id:'A',label:'A',type:'database'},{id:'B',label:'B',type:'external'}],[{from:'A',to:'B',direction:'both'}]);
assert.equal(mod.parseFlow(bi).edges[0].direction,'both');

const portableFlow = mod.parseFlow('flowchart TB\n  A("Tarefa") <--> D[/"Documento"/]\n  D -->|A #124; B| C[("Dados")]');
assert.equal(portableFlow.direction, 'TB');
assert.deepEqual(portableFlow.nodes.map(({type})=>type), ['task','document','database']);
assert.deepEqual(
  mod.parseFlow(mod.flowCode(portableFlow.nodes, portableFlow.edges, 'flowchart', portableFlow.direction)),
  portableFlow
);
