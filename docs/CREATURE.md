# The creature (WP5a)

A deliberate chimera: **fly mushroom-body cognition in a worm-like body that we designed.** The
project started from the question of putting a connectome into a body. A fly brain in a fly body would
invite the claim "this is a fly", which we cannot support. Instead we use our own body, so that every
part we did not take from data is visibly ours. **Nothing about the body's shape or movement is claimed
to be biological.** Code: `src/neuralpet/body.py` (physics), `src/neuralpet/creature.py` (brain +
body + world + state). Tests: `tests/test_body.py`. Fixed rules: `docs/ADAPTERS.md` v8.

## Real data vs our design, part by part

| part | real data | our design |
|---|---|---|
| Body plan: 12 rigid segments (13 nodes), 1 body length (BL) long, head = node 0 | — | all of it; segment count configurable (`Body(n_seg=…)`) |
| Joints: torsional spring (K = 1) + damper (0.002) | — | all of it |
| Muscles: one dorsal/ventral torque pair per joint, torque = 0.4·(amp·sin φ_j + steer) | — | all of it |
| Medium: anisotropic viscous drag, normal / tangential = 10 (resistive-force theory, overdamped) | the physical principle (low-Reynolds undulatory locomotion) is textbook physics | the constants |
| Locomotor CPG: 11 coupled phase oscillators, one wave per body, head → tail | — | all of it (no connectome motor circuit is used) |
| Head sensors: two points 0.04 BL left/right of the head, 0.02 BL ahead | — | positions |
| Odour → glomeruli at each sensor | DoOR 2.0 receptor responses (Münch & Galizia 2016) mapped to glomeruli | Gaussian plumes (σ = 2 BL), mixing rule, noise, scaling (adapters v4, v8) |
| Brain: PN → KC → MBON | FlyWire v783 right mushroom body wiring (or hemibrain for checks) | binary kWTA KCs (10%), single global dopamine, plasticity rule (v1/v2) |
| Brain → body | — | steering = 0.35·tanh(25·valence·sensor contrast); state → CPG amplitude/frequency; innate avoidance reflex after a toxic hit |
| Internal state: energy, curiosity | — | all rules; reward dopamine = drive reduction after Keramati & Gutkin 2014 (a model, not data) |
| Metabolism: drain = baseline + effort·(mean squared muscle activation) | — | constants |
| Brain shape drawn in the head | FlyWire neuron positions and sampled synapse points (`data/mb/shapes.npz`) | scale and placement in the head (a display choice, labelled in the UI) |
| Body surface drawn as a tube | — | built every frame from the simulated centerline |
| Skin pattern | — | cosmetic readout of learned odour preferences and age, labelled cosmetic |

## Physics
- Overdamped: node velocity = force / drag, with drag split into the local body axis (c_t = 1) and the
  normal (c_n = 10). Forces come only from joint torques (as force couples on the two links of a joint)
  and soft walls. Links keep their length by symmetric projection after each step.
- Internal forces sum to zero and the projection keeps the centre of mass, so **with isotropic drag
  (c_n = c_t) the same wave gives exactly zero net travel** (`test_anisotropic_drag_gives_travel_isotropic_does_not`).
  With c_n = 10 it travels about 0.12 BL/s at 1 Hz, head first.
- Time step 2 ms, explicit Euler, Numba. Stable for 100 s with full drive and steering (link-length
  error < 5%, joint angles < 1 rad). The explicit joint damper is kept small because
  C_bend / (c_t·L²) must stay below ~1.
- Positive steer bends the body to the left and the path curves counter-clockwise (tested).
- Deterministic: physics has no random numbers; brain noise comes from seeded generators.
- Speed: ≥ 20× real time is required (tested); measured in `tests/test_body.py`.
- Body constants never change with age or play.

## What the brain does and does not do
- It never sets joint angles. The CPG makes the wave; the brain adds a steering bias and the state
  sets amplitude (0.6–1.0) and frequency (0.6–1.2 Hz): hungrier creatures undulate more and faster.
- No decoder is trained anywhere (cf. Brunton et al. 2026). Before any learning the valence readout is
  exactly zero for every odour (ratio readout), so a naive creature has no odour preference and only
  wanders; chemotaxis appears only after reward or punishment has changed KC→MBON weights.
