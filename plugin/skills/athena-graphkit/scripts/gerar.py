#!/usr/bin/env python3
import argparse
from pathlib import Path
from athena import AthenaGraphKit

def main():
    parser=argparse.ArgumentParser(description="Athena GraphKit - gerador de flowcharts")
    parser.add_argument('arquivo',type=Path)
    parser.add_argument('--tema',choices=['dark','corporativo','sap_fiori'],default='dark')
    parser.add_argument('--formato',choices=['svg','png','pdf'],default='png')
    parser.add_argument('--saida',type=Path,default=Path('saidas'))
    args=parser.parse_args()
    args.saida.mkdir(parents=True,exist_ok=True)
    engine=AthenaGraphKit(tema=args.tema,formato=args.formato)
    for result in engine.gerar_arquivo(args.arquivo,args.saida): print(result.caminho)

if __name__=='__main__': main()
