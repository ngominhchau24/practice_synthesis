from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
from implicants import derive_prime_implicants, implicant_covers_input
from implicants import build_onset_terms

def build_minterm_to_pis(inputs_bits, onset_minterms, pis) -> Dict[int, Set[str]]:
    idx_by_bits = {bits: idx for idx, bits in enumerate(inputs_bits)}
    on_indices: Set[int] = set(idx_by_bits[b] for b in onset_minterms)
    table: Dict[int, Set[str]] = {i: set() for i in on_indices}
    for pi in pis:
        for bits, idx in idx_by_bits.items():
            if bits in onset_minterms and implicant_covers_input(pi, bits):
                table[idx].add(pi)
    return table

def pick_epis(minterm_to_pis: Dict[int, Set[str]]) -> Tuple[Set[str], Set[int]]:
    epis: Set[str] = set()
    covered: Set[int] = set()
    for m, cand in minterm_to_pis.items():
        if len(cand) == 1:
            epis.add(next(iter(cand)))
    if epis:
        for m, cand in minterm_to_pis.items():
            if any(pi in cand for pi in epis):
                covered.add(m)
    return epis, covered

def score_pi_for_greedy(pi: str, uncovered: Set[int], covers: Dict[str, Set[int]]) -> Tuple[int, int, int]:
    cover_gain = len(covers.get(pi, set()) & uncovered)
    dash_count = pi.count('-')
    literal_count = len(pi) - dash_count
    return (cover_gain, dash_count, -literal_count)

def greedy_complete_cover(pis, covers, already_selected, all_on_indices) -> Tuple[Set[str], Set[int]]:
    selected = set(already_selected)
    uncovered = set(all_on_indices)
    for pi in selected:
        uncovered -= covers.get(pi, set())
    remaining = [pi for pi in pis if pi not in selected]
    while uncovered:
        best_pi, best_score = None, (0, 0, 0)
        for pi in remaining:
            sc = score_pi_for_greedy(pi, uncovered, covers)
            if sc > best_score:
                best_score, best_pi = sc, pi
        if best_pi is None or best_score[0] == 0:
            break
        selected.add(best_pi)
        uncovered -= covers.get(best_pi, set())
        remaining = [pi for pi in remaining if pi != best_pi]
    return selected, uncovered

def implicant_to_product_term(implicant: str, var_names: Optional[List[str]] = None) -> str:
    N = len(implicant)
    if var_names is None:
        var_names = [f"x{i+1}" for i in range(N)]
    terms = []
    for b, name in zip(implicant, var_names):
        if b == '1':
            terms.append(name)
        elif b == '0':
            terms.append(name + "'")
    return ''.join(terms) if terms else "1"

def build_sum_of_products(selected_pis: List[str], var_names: Optional[List[str]] = None) -> str:
    return ' + '.join(implicant_to_product_term(pi, var_names) for pi in selected_pis) if selected_pis else "0"

def cubes_for_espresso(selected_pis: List[str], n_outputs: int, which_output: int) -> List[str]:
    out = []
    for pi in selected_pis:
        y = ['0'] * n_outputs
        y[which_output] = '1'
        out.append(f"{pi} {''.join(y)}")
    return out

def select_cover_for_one_output(
    inputs_bits: List[str],
    outputs_trits: List[str],
    which_output: int,
    input_var_names: Optional[List[str]] = None,
) -> Tuple[List[str], Set[int], str, List[str]]:
    onset_bits  = [x for x, y in zip(inputs_bits, outputs_trits) if y[which_output] == '1']
    dcare_bits  = [x for x, y in zip(inputs_bits, outputs_trits) if y[which_output] == '-']
    union_bits  = sorted(set(onset_bits) | set(dcare_bits))

    pis = derive_prime_implicants(union_bits)
    # Xác định tập OFF = toàn bộ - (ON ∪ DC)
    off_bits = set(inputs_bits) - set(union_bits)

    # Giữ lại chỉ những PI không che bất kỳ OFF nào
    from implicants import implicant_covers_input
    pis = [
        pi for pi in pis
        if not any(implicant_covers_input(pi, xoff) for xoff in off_bits)
    ]


    idx_by_bits = {bits: idx for idx, bits in enumerate(inputs_bits)}
    on_indices: Set[int] = set(idx_by_bits[b] for b in onset_bits)

    covers: Dict[str, Set[int]] = {}
    for pi in pis:
        indices = set()
        for bits, idx in idx_by_bits.items():
            if bits in onset_bits and implicant_covers_input(pi, bits):
                indices.add(idx)
        covers[pi] = indices

    minterm_to_pis: Dict[int, Set[str]] = {i: set() for i in on_indices}
    for pi, covered_set in covers.items():
        for i in covered_set:
            if i in minterm_to_pis:
                minterm_to_pis[i].add(pi)

    epis, _ = pick_epis(minterm_to_pis)
    selected_all, uncovered = greedy_complete_cover(
        pis=pis, covers=covers, already_selected=epis, all_on_indices=on_indices
    )

    selected_pis = sorted(selected_all)
    sop = build_sum_of_products(selected_pis, var_names=input_var_names)
    cubes = cubes_for_espresso(selected_pis, n_outputs=len(outputs_trits[0]), which_output=which_output)
    return selected_pis, uncovered, sop, cubes
