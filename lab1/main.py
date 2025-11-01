from __future__ import annotations
import sys
import os
from io import StringIO
from contextlib import redirect_stdout
from typing import List, Optional
from truth_table import (
    parse_sum_of_minterms_file,
    build_outputs_from_minterm_indices,
    print_truth_table,              # plain-text printer to console
    print_truth_table_markdown,     # used only to SAVE a .md table
    generate_random_spec_file,
)
from cover import select_cover_for_one_output
from pla import build_full_pla


def _safe_stem(path: str) -> str:
    base = os.path.basename(path)
    if "." in base:
        return ".".join(base.split(".")[:-1]) or base
    return base or "run"


def _save_truth_table_markdown(
    inputs_bits: List[str],
    outputs_trits: List[str],
    input_names: List[str],
    output_names: List[str],
    out_path: str,
) -> None:
    """Capture the markdown table and write it to `out_path`."""
    buf = StringIO()
    with redirect_stdout(buf):
        print_truth_table_markdown(inputs_bits, outputs_trits, input_names, output_names)
    md = buf.getvalue()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)


def run_from_sum_file(
    path: str,
    n_inputs: int,
    input_names: Optional[List[str]] = None,
    use_markdown: bool = False,  # if True -> save ONLY the truth table in Markdown
) -> str:
    # Parse spec and build truth table
    spec = parse_sum_of_minterms_file(path)  # name -> (on_set, dc_set)
    inputs_bits, outputs_trits, out_names = build_outputs_from_minterm_indices(n_inputs, spec)

    if input_names is None:
        input_names = [f"x{i+1}" for i in range(n_inputs)]
    output_names = out_names

    # Console: always plain text truth table
    print("Truth table (plain):")
    print_truth_table(inputs_bits, outputs_trits, input_names, output_names)

    # Optionally save ONLY the truth table as Markdown
    if use_markdown:
        stem = _safe_stem(path)
        md_path = f"{stem}_truth_table.md"
        _save_truth_table_markdown(inputs_bits, outputs_trits, input_names, output_names, md_path)
        print(f"[i] Markdown truth table saved to: {md_path}")

    # Cover each output (console plain text)
    all_cubes: List[str] = []
    for k, out_name in enumerate(output_names):
        selected_pis, uncovered, sop, cubes = select_cover_for_one_output(
            inputs_bits=inputs_bits,
            outputs_trits=outputs_trits,
            which_output=k,
            input_var_names=input_names,
        )
        print(f"\n=== {out_name} ===")
        print("PIs:", selected_pis)
        if uncovered:
            print("Warning: uncovered ON minterms (indices):", sorted(uncovered))
        print("SOP:", sop)
        all_cubes.extend(cubes)

    # Build and print PLA (plain text)
    pla_text = build_full_pla(inputs_bits, outputs_trits, all_cubes, input_names, output_names)
    print("\nPLA:")
    print(pla_text)

    return pla_text


def print_usage():
    print(
        "Usage:\n"
        "  python3 main.py random [N] [M] [on_ratio] [dc_ratio]\n"
        "      -> Generate random_spec.txt then run it.\n"
        "         Defaults: N=4, M=2, on_ratio=0.35 (clamped ≤0.5), dc_ratio=0.15\n"
        "         Set use_markdown=True in code to also save the truth table as Markdown.\n"
        "\n"
        "  python3 main.py spec.txt [N]\n"
        "      -> Run with provided spec file (supports d{...}); default N=3.\n"
    )


def main():
    args = sys.argv[1:]
    if not args:
        print_usage()
        return

    mode = args[0].strip()
    use_markdown = True   # << toggle here: True saves ONLY the truth table .md file

    if mode.lower() == "random":
        try:
            N  = int(args[1]) if len(args) >= 2 else 4
            M  = int(args[2]) if len(args) >= 3 else 2
            on = float(args[3]) if len(args) >= 4 else 0.35
            dc = float(args[4]) if len(args) >= 5 else 0.15
        except ValueError:
            print("Error: parameters must be numeric (N,M ints; on_ratio, dc_ratio floats).")
            return

        if on > 0.5:
            print("Warning: on_ratio > 0.5 is clamped to 0.5.")
            on = 0.5

        out_path = "random_spec.txt"
        generate_random_spec_file(
            out_path, n_inputs=N, n_outputs=M,
            on_ratio=on, dc_ratio=dc, ensure_on=True, seed=None
        )
        print(f"[i] Generated random spec -> {out_path}")
        run_from_sum_file(path=out_path, n_inputs=N, use_markdown=use_markdown)
        return

    # spec file: python3 main.py spec.txt [N]
    path = mode
    try:
        N = int(args[1]) if len(args) >= 2 else 3
    except ValueError:
        print("Error: N must be an integer.")
        return

    run_from_sum_file(path=path, n_inputs=N, use_markdown=use_markdown)


if __name__ == "__main__":
    main()
