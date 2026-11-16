mermaid.initialize({startOnLoad: false, securityLevel: 'strict', htmlLabels: false, suppressErrorRendering: true});
const preview = document.querySelector('#diagramPreview');
async function renderSharedDiagram() {
  try {
    const code = document.querySelector('#diagramCode').value;
    const result = await mermaid.render('shared' + Math.random().toString(36).slice(2), code);
    preview.innerHTML = result.svg;
  } catch {
    preview.textContent = 'Revise a sintaxe Mermaid para exibir a prévia.';
  }
}
document.querySelector('#previewButton').onclick = renderSharedDiagram;
renderSharedDiagram();
