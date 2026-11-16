import assert from 'node:assert/strict';
import {parseC4,c4Code} from '../portal/static/model.js';
for(const kind of ['C4Context','C4Container','C4Component']){
 const code=`${kind}\n    title Arquitetura\n    Person(user, "Usuário", "Equipe")\n    Component(api, "API", "OData")\n    Rel(user, api, "Consome")`;
 const parsed=parseC4(code);assert.equal(parsed.header,kind);assert.equal(parsed.nodes.length,2);assert.equal(parsed.edges.length,1);
 const restored=c4Code(parsed.nodes,parsed.edges,parsed.title,parsed.header);assert.equal(parseC4(restored).header,kind);
}
console.log('C4 levels OK');
