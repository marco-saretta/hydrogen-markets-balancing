# hydrogen-markets-balancing

Optimisation models for comparing hydrogen network balancing regimes, and what they mean for an electrolyser.

This is the quantitative follow-up to the survey paper *Towards European Hydrogen Market Design: Perspectives from Transmission System Operators* ([arXiv:2603.26451](https://arxiv.org/abs/2603.26451)). The guiding question: what does it mean for an electrolyser to participate in the German, Danish and Dutch hydrogen markets, given their different balancing rules?

## Balancing regimes

Each regime is defined by how the system linepack flexibility (SLF) is shared between network users.

| Regime | Example | Individual allowance | Consequence depends on system state | Helper reward |
| --- | --- | --- | --- | --- |
| Full DLF | NL (Hynetwork) | yes | no | no |
| Hybrid | DK (Energinet) | yes | yes | no |
| Non-DLF | DE (WasABi) | no | yes | yes |

DLF is designated linepack flexibility, an allowance reserved for an individual user. Under full DLF a user is penalised whenever it leaves its band. Under the hybrid it is penalised only if it is also a causer while the system balance is outside the SLF. Under non-DLF there is no individual band: causers pay on their whole position and helpers are paid.

## Status

Early stage. The current model is a skeleton: it builds player, node and system positions over time, bounds node positions by capacity and the system position by linepack, and solves with a placeholder objective. Settlement rules and the electrolyser decision problem are not implemented yet.

## Setup

Requires Python 3.13 (Hydra 1.3 does not run on 3.14) and [uv](https://docs.astral.sh/uv/). Models are written in [linopy](https://linopy.readthedocs.io/) and solved with the open-source [HiGHS](https://highs.dev/) solver, which `uv sync` installs; no licence is needed.

```bash
uv sync                      # creates .venv and installs the package in editable mode
uv run python main.py        # builds and solves the model, writes the LP file
```

Each run writes its resolved config, log and `model.lp` to `outputs/<date>/<time>/`.

## Configuration

Settings are managed with [Hydra](https://hydra.cc/) under `config/`:

- `model/default.yaml`: time steps, nodes with capacity bounds, linepack bounds, and players with their nominated position at each node
- `solver/highs.yaml`: the default solver and its options, passed directly to HiGHS
- `solver/gurobi.yaml`: optional alternative; needs `uv add gurobipy` and a Gurobi licence, then select it with `solver=gurobi`
- `paths/default.yaml`: output locations

Any value can be overridden on the command line:

```bash
uv run python main.py model.timesteps=168 solver.options.time_limit=60
```

## Layout

```text
main.py                              entry point
config/                              Hydra configuration
src/hydrogen_markets_balancing/
  data_loader.py                     turns the config into labelled bound arrays (time, node, player)
  model.py                           linopy model
```
