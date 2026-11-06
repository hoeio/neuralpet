# Mushroom-body sub-circuit extraction (2026-11-06)

Script: `scripts/extract_mb.py` → `data/mb/mb.npz`, `data/mb/counts.json` (gitignored).
Inputs: FlyWire v783 `proofread_connections_783.feather` (16,847,997 rows: pre, post, neuropil,
syn_count, NT averages) + Schlegel et al. 2024 annotations (`cell_class`, `cell_type`, `side`).

## Selection rules
- **Right hemisphere** only (soma `side == right`), so it is one MB.
- KC = `cell_class == Kenyon_Cell`; MBON = `MBON`; DAN = `DAN`; APL = `cell_type == APL` (its
  `cell_class` is `MBIN`, together with DPM).
- PN = `cell_class == ALPN` (either side) with ≥1 kept connection onto a selected KC.
- Connections summed over neuropils per (pre, post) pair; kept if **≥ 5 synapses** (FlyWire
  convention; chosen before looking at counts).
- Glomerulus per PN: uniglomerular PNs from the `cell_type` prefix (e.g. `DA1_lPN` → `DA1`); each
  multiglomerular PN is its own input unit.

## Counts (from counts.json)

| item | count |
|---|---|
| KCs (right) | 2,597 (γm 1,120, αβ 799, α′β′m 174, α′β′ap2 160, γd 148, α′β′ap1 132, αβp 61, other 3) |
| MBONs | 48 |
| DANs | 165 |
| APL | 1 |
| ALPNs onto these KCs | 149 (120 uniglomerular in 55 glomeruli, 29 multiglomerular) → 84 input units |
| PN→KC | 10,505 edges, 143,275 synapses; mean 4.05 PNs per KC (quartiles 3/4/5, max 9) |
| KC→MBON | 7,485 edges, 55,237 synapses; KC out-degree quartiles 1/2/4, max 9 |
| DAN→KC | 72 edges, 402 synapses (not used) |
| KC→APL / APL→KC | 2,596 / 2,586 edges (not used: APL modelled as kWTA) |
| KC→KC | 942 edges (not used) |

## Things to know
- At ≥5 synapses, ALPNs supply **68.3%** of KC input synapses. The rest is from other cells
  (e.g. visual and thermo/hygro PNs). Those inputs are not modelled.
- **233 KCs have no ALPN input** at ≥5 synapses, mostly γd (136) and αβp (49), the KC types known to
  get non-olfactory input. They can never fire in `real` or `shuffle` (degree preserved). In `random`
  they can.
- **201 KCs have no KC→MBON edge** at ≥5 synapses. KC→MBON contacts are small per pair, so the
  threshold removes many weak contacts. (Fixed beforehand; a ≥1 variant would be a new experiment.)
- **Literal KC fraction**: with v1 odours (20% of glomeruli active), the fraction of KCs with any
  positive drive on the real wiring is **0.552**. Minnick et al. 2026 report ~68% in their spiking
  model; these are different models and odour sets, so the numbers are not expected to match.
- Speed: one experiment-001 run (1 seed × 1 condition, ~1,100 KC-code evaluations) takes 0.4–0.5 s on
  one M4 Pro core; the curveball shuffle is most of it. Brian2/Numba are not needed at this size.
