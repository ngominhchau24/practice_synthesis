from __future__ import annotations
from typing import List, Optional

def build_full_pla(
    inputs_bits: List[str],
    outputs_trits: List[str],
    all_cubes: List[str],
    input_names: Optional[List[str]] = None,
    output_names: Optional[List[str]] = None,
) -> str:
    if not inputs_bits or not outputs_trits:
        raise ValueError("inputs_bits/outputs are empty.")
    N = len(inputs_bits[0])
    M = len(outputs_trits[0])
    if input_names is None:
        input_names  = [f"x{i+1}" for i in range(N)]
    if output_names is None:
        output_names = [f"f{i+1}" for i in range(M)]
    lines = []
    lines.append(f".i {N}")
    lines.append(f".o {M}")
    lines.append(".ilb " + " ".join(input_names))
    lines.append(".ob " + " ".join(output_names))
    lines.extend(all_cubes)
    lines.append(".e")
    return "\n".join(lines)
