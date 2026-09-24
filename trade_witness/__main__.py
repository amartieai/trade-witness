"""Daemon entry point: `python3 -m trade_witness` runs the witness in the
background. The installer wires this into login auto-start."""
from .config import Config
from .daemon import Daemon


def main():
    cfg = Config.load()
    Daemon(cfg).run()


if __name__ == "__main__":
    main()