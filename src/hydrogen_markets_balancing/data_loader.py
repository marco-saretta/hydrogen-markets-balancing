import logging
from dataclasses import dataclass

import numpy as np
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelData:
    """Arrays that feed the model variables. Axis order is always (t, n, i)."""

    nodes: list[str]
    players: list[str]
    timesteps: int

    # Bounds on the system position p_t, shape (t,)
    p_t_lb: np.ndarray
    p_t_ub: np.ndarray

    # Bounds on the node position p_tn, shape (t, n)
    p_tn_lb: np.ndarray
    p_tn_ub: np.ndarray

    # Nominated position of each player at each node, shape (n, i)
    nominations: np.ndarray


def load_data(cfg: DictConfig) -> ModelData:
    """Build the bound matrices and nomination tensor from cfg.model."""
    m = cfg.model
    t = m.timesteps
    nodes = list(m.nodes)
    players = list(m.players)

    node_lb = np.array([m.nodes[n].cap.lower for n in nodes], dtype=float)
    node_ub = np.array([m.nodes[n].cap.upper for n in nodes], dtype=float)
    if (node_lb > node_ub).any():
        raise ValueError("Node cap lower bound exceeds upper bound")
    if m.linepack.lower > m.linepack.upper:
        raise ValueError("Linepack lower bound exceeds upper bound")

    nominations = np.zeros((len(nodes), len(players)))
    for j, player in enumerate(players):
        unknown = set(m.players[player]) - set(nodes)
        if unknown:
            raise ValueError(f"{player} refers to unknown nodes: {sorted(unknown)}")
        for k, node in enumerate(nodes):
            nominations[k, j] = m.players[player].get(node, 0)

    data = ModelData(
        nodes=nodes,
        players=players,
        timesteps=t,
        p_t_lb=np.full(t, float(m.linepack.lower)),
        p_t_ub=np.full(t, float(m.linepack.upper)),
        p_tn_lb=np.tile(node_lb, (t, 1)),
        p_tn_ub=np.tile(node_ub, (t, 1)),
        nominations=nominations,
    )
    log.info("Loaded data: %d timesteps, nodes=%s, players=%s", t, nodes, players)
    return data
