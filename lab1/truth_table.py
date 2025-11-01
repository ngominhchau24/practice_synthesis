from __future__ import annotations
import itertools
import random
from typing import Dict, List, Optional, Set, Tuple

def gen_all_input_combinations(n_inputs: int) -> List[str]:
    if n_inputs < 1:
        raise ValueError("n_inputs must be >= 1")
    return [''.join(bits) for bits in itertools.product('01', repeat=n_inputs)]

def build_outputs_from_minterm_indices(
    n_inputs: int,
    outputs_spec: Dict[str, Tuple[Set[int], Set[int]]],  # name -> (on_set, dc_set)
) -> Tuple[List[str], List[str], List[str]]:
    """
    Returns:
      - inputs_bits: 2^N strings of N bits
      - outputs_trits: 2^N strings of M chars where each char in {'0','1','-'}
      - output_names: ordered list of output function names
    '-' denotes don't care (used like 1 during grouping only).
    """
    inputs_bits = gen_all_input_combinations(n_inputs)
    max_index = (1 << n_inputs) - 1
    out_names = sorted(outputs_spec.keys())

    # validate indices and overlap
    for name, (on_set, dc_set) in outputs_spec.items():
        bad_on = [i for i in on_set if i < 0 or i > max_index]
        bad_dc = [i for i in dc_set if i < 0 or i > max_index]
        if bad_on:
            raise ValueError(f"Output '{name}' has invalid ON indices: {bad_on} (N={n_inputs})")
        if bad_dc:
            raise ValueError(f"Output '{name}' has invalid DC indices: {bad_dc} (N={n_inputs})")
        if (on_set & dc_set):
            raise ValueError(f"Output '{name}' has overlap between ON and DC: {sorted(on_set & dc_set)}")

    M = len(out_names)
    rows: List[str] = []
    for i in range(1 << n_inputs):
        chars = []
        for name in out_names:
            on_set, dc_set = outputs_spec[name]
            if i in on_set:
                chars.append('1')
            elif i in dc_set:
                chars.append('-')
            else:
                chars.append('0')
        rows.append(''.join(chars))
    return inputs_bits, rows, out_names

def parse_sum_of_minterms_file(path: str) -> Dict[str, Tuple[Set[int], Set[int]]]:
    """
    Parse extended syntax with don't cares:
        f = sum{0,2,3,4} d{5,7}
        g = sum{1,6} + d{0,3}
        h = sum{} d{}
    Returns: dict name -> (on_set, dc_set)
    """
    import re
    spec: Dict[str, Tuple[Set[int], Set[int]]] = {}
    pat = re.compile(
        r"""^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*sum\s*\{\s*([0-9,\s]*)\s*\}\s*(?:\+?\s*d\s*\{\s*([0-9,\s]*)\s*\}\s*)?$"""
    )
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = pat.match(line)
            if not m:
                raise ValueError(f"Line {lineno}: invalid format -> {raw.strip()}")
            name, on_body, dc_body = m.group(1), m.group(2), m.group(3)

            def parse_list(body: Optional[str]) -> Set[int]:
                if body is None or body.strip() == "":
                    return set()
                xs = []
                for tok in body.split(','):
                    tok = tok.strip()
                    if tok == "":
                        continue
                    xs.append(int(tok))
                return set(xs)

            on_set = parse_list(on_body)
            dc_set = parse_list(dc_body)
            spec[name] = (on_set, dc_set)
    if not spec:
        raise ValueError("No outputs found in the file.")
    return spec

def gen_random_outputs(
    n_rows: int,
    n_outputs: int,
    densities: Optional[List[float]] = None,
    force_at_least_one_1: bool = True,
    rng: Optional[random.Random] = None,
    max_one_ratio: float = 0.5,
) -> List[str]:
    """
    Legacy helper: generates only '0'/'1' columns (no '-').
    Kept for completeness, not used by the new CLI.
    """
    if n_outputs < 1 or n_rows < 1:
        raise ValueError("n_outputs and n_rows must be >= 1")
    if densities is None:
        densities = [0.5] * n_outputs
    if len(densities) != n_outputs:
        raise ValueError("densities length must equal n_outputs")

    R = rng or random.Random()
    cols = [[] for _ in range(n_outputs)]
    cap = max(0, int(max_one_ratio * n_rows))

    for j in range(n_outputs):
        p = max(0.0, min(1.0, float(densities[j])))
        want_ones = sum(1 for _ in range(n_rows) if R.random() < p)
        want_ones = min(want_ones, cap)
        if force_at_least_one_1 and want_ones == 0 and cap > 0:
            want_ones = 1
        ones_idx = set(R.sample(range(n_rows), want_ones)) if want_ones > 0 else set()
        for i in range(n_rows):
            cols[j].append('1' if i in ones_idx else '0')

    return [''.join(cols[j][i] for j in range(n_outputs)) for i in range(n_rows)]

def step1_build_truth_table(
    use_default: bool,
    n_inputs: int,
    n_outputs: int,
    *,
    default_seed: int = 42,
    random_seed: Optional[int] = None,
    densities: Optional[List[float]] = None,
    force_at_least_one_1: bool = True,
) -> Tuple[List[str], List[str]]:
    inputs_bits = gen_all_input_combinations(n_inputs)
    n_rows = len(inputs_bits)
    rng = random.Random(default_seed) if use_default else (random.Random(random_seed) if random_seed is not None else random.Random())
    outputs_bits = gen_random_outputs(
        n_rows,
        n_outputs,
        densities=densities if densities is not None else [0.5] * n_outputs,
        force_at_least_one_1=force_at_least_one_1,
        rng=rng,
    )
    return inputs_bits, outputs_bits

def print_truth_table(
    inputs_bits: List[str],
    outputs_trits: List[str],
    input_names: Optional[List[str]] = None,
    output_names: Optional[List[str]] = None,
) -> None:
    if not inputs_bits or not outputs_trits:
        print("(empty truth table)")
        return
    N = len(inputs_bits[0])
    M = len(outputs_trits[0])
    if input_names is None:
        input_names = [f"x{i+1}" for i in range(N)]
    if output_names is None:
        output_names = [f"f{i+1}" for i in range(M)]

    header = " ".join(input_names + output_names)
    print(header)
    for xb, yb in zip(inputs_bits, outputs_trits):
        row_in = " ".join(list(xb))
        row_out = " ".join(list(yb))
        print(f"{row_in} {row_out}")

def print_truth_table_markdown(
    inputs_bits: List[str],
    outputs_trits: List[str],
    input_names: Optional[List[str]] = None,
    output_names: Optional[List[str]] = None,
) -> None:
    if not inputs_bits or not outputs_trits:
        print("_(empty truth table)_")
        return
    N = len(inputs_bits[0])
    M = len(outputs_trits[0])
    if input_names is None:
        input_names = [f"x{i+1}" for i in range(N)]
    if output_names is None:
        output_names = [f"f{i+1}" for i in range(M)]

    headers = input_names + output_names
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for xb, yb in zip(inputs_bits, outputs_trits):
        row = list(xb) + list(yb)
        print("| " + " | ".join(row) + " |")

# ---- Random spec generation (new) ----

from typing import Tuple

def _random_on_dc_indices(
    n_inputs: int,
    n_outputs: int,
    *,
    on_ratio: float = 0.35,     # <= 0.5
    dc_ratio: float = 0.15,
    ensure_on: bool = True,
    seed: Optional[int] = None,
) -> Dict[str, Tuple[Set[int], Set[int]]]:
    import random as _r
    R = _r.Random(seed)
    n_rows = 1 << n_inputs
    max_on = max(0, int(0.5 * n_rows))
    want_on = min(int(on_ratio * n_rows), max_on)
    want_dc = max(0, int(dc_ratio * n_rows))

    spec: Dict[str, Tuple[Set[int], Set[int]]] = {}
    all_indices = list(range(n_rows))
    for j in range(1, n_outputs + 1):
        name = f"f{j}"
        on_k = want_on
        if ensure_on and on_k == 0 and max_on > 0:
            on_k = 1
        on_set = set(R.sample(all_indices, on_k)) if on_k > 0 else set()
        remaining = [i for i in all_indices if i not in on_set]
        dc_k = min(want_dc, len(remaining))
        dc_set = set(R.sample(remaining, dc_k)) if dc_k > 0 else set()
        spec[name] = (on_set, dc_set)
    return spec

def write_sum_of_minterms_file(
    path: str,
    spec: Dict[str, Tuple[Set[int], Set[int]]]
) -> None:
    lines = []
    for name in sorted(spec.keys()):
        on_set, dc_set = spec[name]
        on_part = ",".join(str(i) for i in sorted(on_set))
        dc_part = ",".join(str(i) for i in sorted(dc_set))
        if dc_set:
            lines.append(f"{name} = sum{{{on_part}}} d{{{dc_part}}}")
        else:
            lines.append(f"{name} = sum{{{on_part}}}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def generate_random_spec_file(
    path: str,
    n_inputs: int,
    n_outputs: int,
    *,
    on_ratio: float = 0.35,
    dc_ratio: float = 0.15,
    ensure_on: bool = True,
    seed: Optional[int] = None,
) -> None:
    spec = _random_on_dc_indices(
        n_inputs=n_inputs,
        n_outputs=n_outputs,
        on_ratio=on_ratio,
        dc_ratio=dc_ratio,
        ensure_on=ensure_on,
        seed=seed,
    )
    write_sum_of_minterms_file(path, spec)
