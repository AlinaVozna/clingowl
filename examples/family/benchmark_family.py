from __future__ import annotations

import statistics
import time
from pathlib import Path
import clingo
from clingo.ast import parse_string

BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = BASE_DIR / "clingowl_family.py"

def load_components():
    """Load Context and MyTranslator from clingowl_family.py without running the script body."""
    source = SOURCE_FILE.read_text(encoding="utf-8")
    marker = 'with open(ASP_FILE, "r") as f:'
    if marker not in source:
        raise RuntimeError("Could not find benchmark split marker in clingowl_family.py")

    prefix = source.split(marker, 1)[0]
    namespace = {"__file__": str(SOURCE_FILE), "__name__": "benchmark_components"}
    exec(prefix, namespace)
    return namespace["Context"], namespace["MyTranslator"]

QUERY_TEMPLATES = [
    "q{0}(X) :- &owlquery{{ adult & (father | mother) }} = X.",
    "q{0}(X) :- &owlquery{{ adult & mother }} = X.",
    "q{0}(X) :- &owlquery{{ ~female }} = X.",
    "q{0}(X) :- &owlquery{{ hasChild ! male }} = X.",
    "q{0}(X) :- &owlquery{{ hasChild ? ~nothing }} = X.",
]

BOOL_TEMPLATES = [
    "b{0} :- &owl{{ father <: person }}.",
    "b{0} :- &owl{{ mother <: person }}.",
    "b{0} :- &owl{{ parent = (person & (hasChild ! person)) }}.",
    "b{0} :- &owl{{ (peter) :: father }}.",
    "b{0} :- &owl{{ (susan, peter) :: hasChild }}.",
]

def generate_program(num_atoms: int) -> str:
    lines = []
    counter = 1
    templates = QUERY_TEMPLATES + BOOL_TEMPLATES

    while len(lines) < num_atoms:
        for template in templates:
            if len(lines) >= num_atoms:
                break
            lines.append(template.format(counter))
            counter += 1

    return "\n".join(lines) + "\n"

def run_once(program_text: str, translator_cls, context_cls):
    start_total = time.perf_counter()

    asts = []
    start_parse = time.perf_counter()
    parse_string(program_text, lambda ast: asts.append(ast))
    end_parse = time.perf_counter()

    translator = translator_cls()
    start_translate = time.perf_counter()
    for ast in asts:
        translator.translate_rule(ast)
    translated_program = translator.get_translation()
    end_translate = time.perf_counter()

    ctl = clingo.Control()
    ctl.add("base", [], translated_program)

    start_reasoning = time.perf_counter()
    ctl.ground([("base", [])], context=context_cls())
    with ctl.solve(yield_=True) as handle:
        for _model in handle:
            pass
    end_reasoning = time.perf_counter()

    end_total = time.perf_counter()

    return {
        "parsing": end_parse - start_parse,
        "translation": end_translate - start_translate,
        "reasoning": end_reasoning - start_reasoning,
        "total": end_total - start_total,
    }

def summarize(samples: list[dict[str, float]]):
    keys = ["parsing", "translation", "reasoning", "total"]
    return {
        key: {
            "mean_ms": statistics.mean(sample[key] for sample in samples) * 1000,
            "stdev_ms": (statistics.stdev(sample[key] for sample in samples) * 1000) if len(samples) > 1 else 0.0,
        }
        for key in keys
    }

def print_results(results_by_size):
    print("theory_atoms,parsing_mean_ms,parsing_stdev_ms,translation_mean_ms,translation_stdev_ms,reasoning_mean_ms,reasoning_stdev_ms,total_mean_ms,total_stdev_ms")
    for size, metrics in results_by_size.items():
        print(
            f"{size},"
            f"{metrics['parsing']['mean_ms']:.3f},{metrics['parsing']['stdev_ms']:.3f},"
            f"{metrics['translation']['mean_ms']:.3f},{metrics['translation']['stdev_ms']:.3f},"
            f"{metrics['reasoning']['mean_ms']:.3f},{metrics['reasoning']['stdev_ms']:.3f},"
            f"{metrics['total']['mean_ms']:.3f},{metrics['total']['stdev_ms']:.3f}"
        )

def main():
    context_cls, translator_cls = load_components()
    sizes = [10, 50, 100, 500]
    repeats = 10

    print(f"Running translation overhead benchmark with repeats={repeats}")
    results_by_size = {}

    for size in sizes:
        print(f"Benchmarking {size} theory atoms...")
        program_text = generate_program(size)
        samples = [run_once(program_text, translator_cls, context_cls) for _ in range(repeats)]
        results_by_size[size] = summarize(samples)

    print()
    print_results(results_by_size)

if __name__ == "__main__":
    main()