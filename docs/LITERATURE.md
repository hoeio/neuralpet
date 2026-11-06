# Literature (checked 2026-11-06)

Each entry was located online on 2026-11-06 (URL given). Statements are from the abstract/paper text,
not memory. Where only partly checked, it says so.

## Prior work named in CLAUDE.md

- **Minnick JR, Gonzalez-Ferrer J, Geng J, Eshraghian JK, Mostajo-Radji MA, Haussler D, Teodorescu M (2026).**
  "Sensorimotor behaviour from an untrained brain-and-nerve-cord connectome." arXiv:2610.33881.
  https://arxiv.org/abs/2610.33881 — ~172k-neuron spiking model in a body. Odour navigation: 95% of
  sources reached vs 18% for a degree- and sign-preserving rewired network. Learning arm:
  dopamine-gated KC→MBON depression flips approach to avoidance, odour-specific, but only after
  scaling down one synapse class (ALLN output, gain 0.15). Reports ~68% KCs active when read literally,
  median 6.8% in the scaled variant. **As far as we read (~100k of ~140k characters), the rewired
  control was used for navigation, not for learning.** The rest of the paper is not yet checked.
- **Brunton BW, Abe ETT, Hu LJ, Tuthill JC (2026).** "The digital sphinx: Can a worm brain control a
  fly body?" eLife Reviewed Preprint 111516, doi:10.7554/eLife.111516. A C. elegans connectome
  "drives" a MuJoCo fly body only through a 16-D encoder/decoder trained by deep RL; the walking is
  not evidence of anything about the connectome. → our rules 5 and 6.
- **Zheng Z, Li F, … Bock DD (2022).** "Structured sampling of olfactory input by the fly mushroom
  body." Curr Biol 32:3334–3349, doi:10.1016/j.cub.2022.06.031. FAFB PN→KC wiring is non-random:
  food-responsive PN types converge onto KCs above chance (αβ, α′β′). In their model, those inputs are
  discriminated better.
- **Li F, Lindsey JW, … Litwin-Kumar A, Rubin GM (2020).** "The connectome of the adult Drosophila
  mushroom body provides insights into function." eLife 9:e62576, doi:10.7554/eLife.62576. Hemibrain:
  the real KC representation has somewhat lower dimension than shuffled models ("modest" effect).
- **Eichler K, … Zlatic M, Cardona A (2017).** "The complete connectome of a learning and memory
  centre in an insect brain." Nature 548:175–182, doi:10.1038/nature23455. Larval MB. Citation only
  verified; its random-vs-structured analysis not read.
- **Keramati M, Gutkin B (2014).** "Homeostatic reinforcement learning for integrating reward
  collection and physiological stability." eLife 3:e04811, doi:10.7554/eLife.04811. Reward = reduction
  of drive (distance of internal state from setpoint). Used for the pet's internal state (step 3).

## Plasticity rule

- **Hige T, Aso Y, Modi MN, Rubin GM, Turner GC (2015).** "Heterosynaptic plasticity underlies
  aversive olfactory learning in Drosophila." Neuron 88:985–998, doi:10.1016/j.neuron.2015.11.003.
  Odour + DAN pairing → odour-specific LTD of KC→MBON synapses; needs KC activity before DA; no MBON
  spiking needed. **Our rule is this qualitative rule in a simple form: ΔW_im = −η·DA·KC_i·W_im.**
  (The equation is ours; the paper is experimental.)
- **Bennett JEM, Philippides A, Nowotny T (2021).** "Learning with reinforcement prediction errors in a
  model of the Drosophila mushroom body." Nat Commun 12:2569, doi:10.1038/s41467-021-22592-4.
  Model rule ΔW = η·k·(d± − d∓). Their KCs are hand-assigned, not connectome-wired.
- **Handler A, … Ruta V (2019).** Cell 178:60–75, doi:10.1016/j.cell.2019.05.040. DopR1 → depression
  (forward pairing), DopR2 → potentiation (backward). For a bidirectional rule later.
- Springer M, Nawrot MP (2021). eNeuro 8(3):ENEURO.0549-20.2021. Not read in depth.

## Sparsity, theory, data

- **Honegger KS, Campbell RAA, Turner GC (2011).** J Neurosci 31:11772–11785. "On average, an odor
  evokes responses in ∼5% of the KCs in an imaging plane."
- **Lin AC, Bygrave A, de Calignon A, Lee T, Miesenböck G (2014).** Nat Neurosci 17:559–568,
  doi:10.1038/nn.3660. APL feedback makes KC coding sparse; blocking APL → denser, more correlated codes
  and impaired discrimination of similar (not dissimilar) odours.
  - We use **10%** as the "sparse" setting (upper end of the commonly quoted 5–10%; no single primary
    source for 10% was found — Honegger reports ~5%).
- **Litwin-Kumar A, Harris KD, Axel R, Sompolinsky H, Abbott LF (2017).** "Optimal degrees of synaptic
  connectivity." Neuron 93:1153–1164. Random expansion with ~7 inputs/KC maximises dimension → a
  random control is a strong baseline, not a strawman.
- Dorkenwald S et al. (2024) Nature 634:124–138, doi:10.1038/s41586-024-07558-y.
  Schlegel P et al. (2024) Nature 634:139–152, doi:10.1038/s41586-024-07686-5.
  Zheng Z et al. (2018) Cell 174:730–743.e22, doi:10.1016/j.cell.2018.06.019.

## Odour data

- **Münch D, Galizia CG (2016).** "DoOR 2.0 - Comprehensive Mapping of Drosophila melanogaster
  Odorant Responses." Sci Rep 6:21841, doi:10.1038/srep21841 (verified via Crossref 2026-11-06).
  Data: github.com/ropensci/DoOR.data, CC BY-SA 4.0. Used in experiment 006.

## Recent related

- **Shiu PK et al. (2024).** Nature 634:210–219, doi:10.1038/s41586-024-07763-9. Whole-brain LIF model
  of feeding/grooming; no learning, no shuffled control.
- **MacKenzie AJ … Caron SJC (2025).** bioRxiv 10.1101/2025.10.29.684686 (v2 title "Biased projection
  neuron–Kenyon cell connectivity shapes odor representations and learning in the Drosophila mushroom
  body"). Some PN types connect to KCs up to ~15× more than others; in real flies, odours activating
  more KCs are learned better. Shuffles only as connectivity nulls; no model learning comparison.
- **Dhiman N (2026).** "Topological Sensitivity in Connectome-Constrained Neural Networks."
  arXiv:2604.04033. In flyvis, the apparent advantage of real topology vanishes with shared
  initialisation and a degree-preserving null. → we match initial weights (same weight multiset) and
  use a degree-preserving null.

## Done vs. open

Done: PN→KC wiring is statistically non-random (Zheng 2022, Li 2020, MacKenzie 2025); random expansion
is near-optimal in theory (Litwin-Kumar 2017); Minnick 2026 shows DA-gated KC→MBON learning in a
whole-CNS FlyWire model, the 68%-vs-sparse issue, and a rewired control for navigation.

Open (our experiment 001): does real MB wiring improve DA-gated learning — trials to learn, noise
robustness, odour interference — versus a degree-preserving shuffle and a matched random network, at
both literal and sparse KC coding? We found no paper doing exactly this. Expectation from theory
(Litwin-Kumar) and from Dhiman: **real may well not beat a good null on random odours.** Real wiring's
known bias is towards particular (food-related) glomeruli, so any advantage would most likely show for
odours that use those glomeruli. Random odours average that away. This is a key limitation of 001.
