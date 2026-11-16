import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../portal/',import.meta.url);
test('UI exposes language and theme selectors',()=>{
 const html=readFileSync(new URL('templates/index.html',root),'utf8');
 assert.match(html,/id="uiLanguage"/);assert.match(html,/id="uiTheme"/);assert.match(html,/data-ui-theme="dark"/);
});
test('manual viewer and bilingual labels are present',()=>{
 const js=readFileSync(new URL('static/app.js',root),'utf8');
 assert.match(js,/uiStrings=\{pt:/);assert.match(js,/en:/);assert.match(js,/\/api\/manuals/);
});
