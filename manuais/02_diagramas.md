# Diagramas e Mermaid

## Tipos

- Flowchart: fluxos de processos e decisões.
- SequenceDiagram: participantes e mensagens ao longo do tempo.
- DER/MER: entidades e relacionamentos.
- ClassDiagram: classes, métodos e herança.
- C4Context: arquitetura de sistemas (Mermaid experimental).
- BPMN simplificado: símbolos e fluxos visuais, não exportação BPMN XML.

## Organizar o diagrama

1. Abra a aba **Construtor visual** e arraste os elementos para as posições desejadas.
2. Use **Grade**, ao lado dos controles de zoom, para mostrar ou ocultar os pontos do fundo.
3. Clique em **Salvar projeto**. As posições e a preferência de grade ficam armazenadas por diagrama.
4. Ao recarregar a página, o Studio reabre o projeto e o diagrama selecionados, se ainda estiverem disponíveis.

## Exemplo de fluxo

```mermaid
flowchart LR
  A[Portal] --> B{Validar}
  B -->|OK| C[(SAP)]
```

## Exemplo de sequência

```mermaid
sequenceDiagram
  participant A as Portal
  participant B as SAP
  A->>B: Consultar
  B-->>A: Resultado
```

## Referências

- [Mermaid](https://mermaid.js.org/intro/)
- [Flowchart](https://mermaid.js.org/syntax/flowchart.html)
- [Sequence](https://mermaid.js.org/syntax/sequenceDiagram.html)
- [ER](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)
- [Class](https://mermaid.js.org/syntax/classDiagram.html)
- [C4](https://mermaid.js.org/syntax/c4.html)
