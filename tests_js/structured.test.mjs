import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=readFileSync(new URL('../portal/static/model.js',import.meta.url),'utf8');
const m=await import('data:text/javascript;base64,'+Buffer.from(src).toString('base64'));
const er=`erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        int id PK
        string name
    }
    ORDER {
        int id PK
        int customer_id FK
    }`;
const e=m.parseER(er);assert.equal(e.entities.length,2);assert.equal(e.relations.length,1);assert.equal(m.parseER(m.erCode(e)).relations.length,1);
const cls=`classDiagram
    class Pedido {
        +String numero
        +criar()
    }
    class Item {
        +int quantidade
    }
    Pedido "1" *-- "many" Item : contém`;
const c=m.parseClass(cls);assert.equal(c.classes.length,2);assert.equal(c.relations.length,1);assert.equal(m.parseClass(m.classCode(c)).relations.length,1);
assert.throws(()=>m.parseER('erDiagram\n direction LR'),/não suportada/);
assert.throws(()=>m.parseClass('classDiagram\n note for A "hello"'),/não suportada/);
console.log('ER and Class adapters: 6 checks OK');
