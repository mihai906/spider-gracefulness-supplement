#!/usr/bin/env python3
"""Check the computer-assisted part of the proof. Python standard library only.

  python3 verify.py --finite        rebuild the finite tables and compare them
                                    with the tables printed in the supplement
  python3 verify.py --arithmetic    bind and check all 130 CPC refutations
  python3 verify.py --arithmetic --family seven|eight-odd|eight-even-min
"""
from pathlib import Path
import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
PRINTED = HERE.parent / "supplement_source" / "supplement"
CHECKER = HERE / "checker" / "logos"


def cases():
    for proof in sorted((HERE / "seven" / "proofs").glob("*.cpc")):
        yield "seven", HERE / "seven" / "inputs" / (proof.stem + ".smt2"), proof
    yield "eight-odd", HERE / "eight_odd" / "input.smt2", HERE / "eight_odd" / "proof.cpc"
    yield "eight-even-min", HERE / "eight_even_min" / "input.smt2", HERE / "eight_even_min" / "proof.cpc"


def tables(text):
    return [re.sub(r"\s+", "", body) for body in
            re.findall(r"\\begin\{longtable\}(.*?)\\end\{longtable\}", text, re.S)]


def check_finite():
    with tempfile.TemporaryDirectory() as out:
        for builder in ("build_finite_tables.py", "build_auxiliary_tables.py"):
            subprocess.run([sys.executable, str(HERE / "finite" / builder), out],
                           check=True, stdout=subprocess.DEVNULL)
        for name in ("finite_tables.tex", "auxiliary_finite.tex"):
            built = tables((Path(out) / name).read_text())
            printed = tables((PRINTED / name).read_text())
            assert built and built == printed, ("tables differ from the supplement", name)
    print("finite: all printed bases, inventories and the 311 decompositions verified; "
          "tables identical to the supplement", flush=True)


def load_binder():
    spec = importlib.util.spec_from_file_location("binder", HERE / "binder.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_normalization(binder):
    """The even-minimum input is the conjunction of fourteen original assertions."""
    with (HERE / "eight_even_min" / "input_fourteen_assertions.smt2").open() as f:
        old = list(binder.commands(f))
    with (HERE / "eight_even_min" / "input.smt2").open() as f:
        new = list(binder.commands(f))
    assertions = [c[1] for c in old if c[0] == "assert"]
    assert len(assertions) == 14
    assert [c[1] for c in new if c[0] == "assert"] == [["and"] + assertions]
    assert [c for c in old if c[0] != "assert"] == [c for c in new if c[0] != "assert"]
    print("eight-even-min: input is exactly the conjunction of the fourteen assertions", flush=True)


def check_arithmetic(family):
    binder = load_binder()
    if family in ("all", "eight-even-min"):
        check_normalization(binder)
    CHECKER.chmod(CHECKER.stat().st_mode | 0o100)
    count = 0
    for fam, source, proof in cases():
        if family != "all" and fam != family:
            continue
        start = time.monotonic()
        assert binder.bind(source, proof)["status"] == "identical", ("premise differs", proof)
        result = subprocess.run([str(CHECKER), str(proof)], cwd=HERE, capture_output=True,
                                text=True, timeout=1800)
        assert result.returncode == 0 and result.stdout.strip() == "correct", \
            (proof, result.stdout, result.stderr)
        count += 1
        print(json.dumps({"family": fam, "proof": str(proof.relative_to(HERE)),
                          "premise": "identical", "checker": "correct",
                          "seconds": round(time.monotonic() - start, 1)}), flush=True)
    print(f"arithmetic: {count} refutations checked", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--finite", action="store_true")
    parser.add_argument("--arithmetic", action="store_true")
    parser.add_argument("--family", default="all",
                        choices=["all", "seven", "eight-odd", "eight-even-min"])
    args = parser.parse_args()
    if sys.flags.optimize:
        raise SystemExit("Run without -O; the checks use assertions.")
    if not (args.finite or args.arithmetic):
        parser.print_help()
        return
    if args.finite:
        check_finite()
    if args.arithmetic:
        check_arithmetic(args.family)


if __name__ == "__main__":
    main()
