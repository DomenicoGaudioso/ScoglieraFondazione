from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_src():
    spec = importlib.util.spec_from_file_location("scogliera_fondazione_src", ROOT / "src.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_close(name: str, actual: float, expected: float, tol: float) -> None:
    if math.isnan(actual) or abs(actual - expected) > tol:
        raise AssertionError(f"{name}: actual={actual!r}, expected={expected!r}, tol={tol}")


def main() -> None:
    src = load_src()
    bench = json.loads((ROOT / "test" / "benchmark" / "base.json").read_text(encoding="utf-8"))
    data = bench["input"]
    design = src.progetto_fondazione(
        data["D50"], data["ys_atteso"], data["fattore_spessore"], data["fattore_larghezza"]
    )
    vol = src.stima_volume_apron(
        data["D50"], data["ys_atteso"], data["larghezza_pila"], data["lunghezza_pila"],
        data["fattore_spessore"], data["fattore_larghezza"]
    )
    filtro = src.spessore_filtro_fondazione(data["D50"])
    mc = src.massa_e_costo_apron(
        vol, data["S_s"], data["rho"], data["porosita"], data["costo_eur_m3"],
        filtro, data["costo_filtro_eur_m3"]
    )
    actual = {
        "spessore": design.spessore,
        "larghezza": design.larghezza,
        "sottofondo": design.sottofondo,
        "volume": vol["Volume_apron [m3]"],
        "massa_t": mc["Massa_totale_roccia [t]"],
        "costo_totale": mc["Costo_totale [EUR]"],
        "filtro": filtro,
    }
    tol = float(bench["abs_tolerance"])
    for key, expected in bench["expected"].items():
        assert_close(key, float(actual[key]), float(expected), tol)
    print("OK ScoglieraFondazione benchmark: base")


if __name__ == "__main__":
    main()
