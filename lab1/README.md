# K‑map / Quine–McCluskey Minimizer (with Don't Care)

Small modular project to read boolean functions in **sum-of-minterms** format (with optional **don't care** indices), derive **prime implicants**, pick a cover (EPI + greedy), and emit **Espresso .pla** cubes. Also prints the truth table as **Markdown**.

## Input format

Each output on its own line:
```
F = sum{0,2,3,4} d{5,7}
G = sum{1,6} + d{0,3}
```
Notes:
- `sum{…}` is required; `d{…}` is optional (you can also write `sum{…} + d{…}`).
- Indices are decimal minterm numbers (0..2^N-1). `d{…}` are don't-cares and are used as `1` during grouping only.

## CLI

```
python3 main.py random [N] [M] [on_ratio] [dc_ratio]
# Generate random_spec.txt (with d{…}) then run it
# Defaults: N=4, M=2, on_ratio=0.35, dc_ratio=0.15 (on_ratio is clamped to ≤ 0.5)

python3 main.py spec.txt [N]
# Run with a provided spec file; default N=3
```

## Output
- Prints **Markdown** truth table.
- Prints `.pla` content in a code block.

## Files
- `main.py` – CLI + orchestration
- `truth_table.py` – parsing, table building, random spec generation, pretty printers
- `implicants.py` – implicant generation
- `cover.py` – EPI + greedy cover, SOP & cube generation
- `pla.py` – builds a full Espresso `.pla` text
- `examples/spec.txt` – small example

## Example

```
python3 main.py random 3 2 0.4 0.2
```

This creates `random_spec.txt`, prints the truth table in Markdown, and then prints the corresponding `.pla`.
