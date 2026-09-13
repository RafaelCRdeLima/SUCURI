"""python -m sucuri.interface [--porta N] [--host H] [--sem-navegador]"""

import argparse

from .servidor import servir


def main():
    p = argparse.ArgumentParser(prog="sucuri", description="Sucuri — interface local")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=8765)
    p.add_argument("--sem-navegador", action="store_true",
                   help="não abrir o navegador automaticamente")
    a = p.parse_args()
    servir(a.host, a.porta, abrir=not a.sem_navegador)


if __name__ == "__main__":
    main()
