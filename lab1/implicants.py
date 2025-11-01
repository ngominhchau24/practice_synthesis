from __future__ import annotations
from typing import Dict, List, Set, Tuple

def combine_if_one_bit_diff(a: str, b: str) -> str | None:
    """
    Chỉ cho gộp nếu:
      - Tất cả các vị trí đều bằng nhau, TRỪ đúng 1 vị trí là 0/1 đối nghịch.
      - Ở các vị trí có '-', cả hai phải đều '-' (không cho case '-' vs '0/1').
    """
    diff = 0
    out = []
    for xa, xb in zip(a, b):
        if xa == xb:
            out.append(xa)  # có thể là '0'/'1' hoặc '-' giống nhau
        else:
            # nếu một bên là '-' còn bên kia là bit xác định -> KHÔNG gộp được
            if xa == '-' or xb == '-':
                return None
            # khác nhau 0 vs 1 -> tính 1 khác biệt
            diff += 1
            if diff > 1:
                return None
            out.append('-')
    # phải đúng 1 khác biệt
    if diff != 1:
        return None
    return ''.join(out)

def group_once(terms: List[str]) -> Tuple[List[str], List[str]]:
    used = set()
    new_terms_set: Set[str] = set()
    terms_sorted = sorted(terms, key=lambda s: s.count('1'))
    for i in range(len(terms_sorted)):
        for j in range(i + 1, len(terms_sorted)):
            c = combine_if_one_bit_diff(terms_sorted[i], terms_sorted[j])
            if c is not None:
                new_terms_set.add(c)
                used.add(terms_sorted[i])
                used.add(terms_sorted[j])
    leftovers = [t for t in terms_sorted if t not in used]
    new_terms = sorted(new_terms_set)
    return new_terms, leftovers

def implicant_covers_input(implicant: str, input_bits: str) -> bool:
    return all(ic == '-' or ic == xb for ic, xb in zip(implicant, input_bits))

def implicant_covers_implicant(a: str, b: str) -> bool:
    return all(xa == '-' or xa == xb for xa, xb in zip(a, b))

def derive_prime_implicants(minterms: List[str]) -> List[str]:
    current = sorted(set(minterms))
    prime_implicants: Set[str] = set()
    while True:
        new_terms, leftovers = group_once(current)
        prime_implicants.update(leftovers)
        if not new_terms:
            prime_implicants.update(current)
            break
        current = new_terms
    pis = sorted(prime_implicants)
    non_redundant: List[str] = []
    for i, pi in enumerate(pis):
        is_covered = any(i != j and implicant_covers_implicant(pj, pi) for j, pj in enumerate(pis))
        if not is_covered:
            non_redundant.append(pi)
    return sorted(set(non_redundant))

def build_onset_terms(inputs_bits: List[str], outputs_bits: List[str], out_index: int) -> List[str]:
    return [x for x, y in zip(inputs_bits, outputs_bits) if y[out_index] == '1']
