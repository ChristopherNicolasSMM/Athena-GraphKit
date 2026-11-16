"""API reutilizável do Athena GraphKit, sem dependência da CLI."""
from dataclasses import dataclass
from pathlib import Path
from core.leitor import ler_diagramas
from core.parser import interpretar
from core.renderizador import renderizar
from core.temas import carregar_tema

FORMATOS = ("svg", "png", "pdf")

@dataclass(frozen=True)
class ResultadoDiagrama:
    origem: str
    indice: int
    caminho: Path
    tema: str
    formato: str

class AthenaGraphKit:
    def __init__(self, tema="corporativo", formato="svg"):
        if formato not in FORMATOS:
            raise ValueError(f"Formato inválido: {formato}. Use {', '.join(FORMATOS)}")
        self.nome_tema = tema
        self.tema = carregar_tema(tema)
        self.formato = formato

    def gerar_texto(self, mermaid: str, destino: Path, origem="texto") -> ResultadoDiagrama:
        destino = Path(destino)
        if destino.suffix.lower() in (".svg", ".png", ".pdf"):
            if destino.suffix.lower() != f".{self.formato}":
                raise ValueError("Extensão do destino diferente do formato escolhido")
            destino = destino.with_suffix("")
        caminho = Path(renderizar(interpretar(mermaid), self.tema, destino, self.formato))
        return ResultadoDiagrama(origem, 1, caminho, self.nome_tema, self.formato)

    def gerar_arquivo(self, arquivo: Path, pasta_saida: Path) -> list[ResultadoDiagrama]:
        arquivo = Path(arquivo)
        pasta_saida = Path(pasta_saida)
        if arquivo.suffix.lower() not in (".md", ".mmd"):
            raise ValueError("Somente arquivos .md ou .mmd são aceitos")
        blocos = ler_diagramas(arquivo)
        resultados = []
        for indice, bloco in enumerate(blocos, 1):
            destino = pasta_saida / f"{arquivo.stem}_{indice:02d}"
            caminho = Path(renderizar(interpretar(bloco), self.tema, destino, self.formato))
            resultados.append(ResultadoDiagrama(str(arquivo), indice, caminho, self.nome_tema, self.formato))
        return resultados

    def gerar_pasta(self, pasta_entrada: Path, pasta_saida: Path) -> list[ResultadoDiagrama]:
        pasta_entrada = Path(pasta_entrada)
        if not pasta_entrada.is_dir():
            raise ValueError(f"Pasta não encontrada: {pasta_entrada}")
        resultados = []
        arquivos = sorted(p for p in pasta_entrada.rglob("*") if p.is_file() and p.suffix.lower() in (".md", ".mmd"))
        if not arquivos:
            raise ValueError("Nenhum arquivo .md ou .mmd encontrado")
        for arquivo in arquivos:
            # Reproduz subpastas para evitar colisões de nomes.
            relativa = arquivo.relative_to(pasta_entrada)
            resultados.extend(self.gerar_arquivo(arquivo, Path(pasta_saida) / relativa.parent))
        return resultados
