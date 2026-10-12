import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xarray as xr
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelData:
    """Labelled arrays that feed the model variables, with dims time, node, player."""

    time: pd.Index
    nodes: pd.Index
    players: pd.Index

    # Bounds on the system position p_t, dims (time,)
    p_t_lb: xr.DataArray
    p_t_ub: xr.DataArray

    # Bounds on the node position p_tn, dims (time, node)
    p_tn_lb: xr.DataArray
    p_tn_ub: xr.DataArray

    # Nominated position of each player at each node, dims (node, player)
    nominations: xr.DataArray


def load_data(cfg: DictConfig) -> ModelData:
    """Build the bound arrays and nomination matrix from cfg.model."""
    m = cfg.model
    time = pd.RangeIndex(m.timesteps, name="time")
    nodes = pd.Index(list(m.nodes), name="node")
    players = pd.Index(list(m.players), name="player")

    node_lb = xr.DataArray(np.array([m.nodes[n].cap.lower for n in nodes], dtype=float), coords=[nodes])
    node_ub = xr.DataArray(np.array([m.nodes[n].cap.upper for n in nodes], dtype=float), coords=[nodes])
    if (node_lb > node_ub).any():
        raise ValueError("Node cap lower bound exceeds upper bound")
    if m.linepack.lower > m.linepack.upper:
        raise ValueError("Linepack lower bound exceeds upper bound")

    nominations = xr.DataArray(np.zeros((len(nodes), len(players))), coords=[nodes, players])
    for player in players:
        unknown = set(m.players[player]) - set(nodes)
        if unknown:
            raise ValueError(f"{player} refers to unknown nodes: {sorted(unknown)}")
        for node in nodes:
            nominations.loc[node, player] = m.players[player].get(node, 0)

    on_time = xr.DataArray(np.ones(len(time)), coords=[time])  # broadcasts bounds over time
    data = ModelData(
        time=time,
        nodes=nodes,
        players=players,
        p_t_lb=on_time * float(m.linepack.lower),
        p_t_ub=on_time * float(m.linepack.upper),
        p_tn_lb=on_time * node_lb,
        p_tn_ub=on_time * node_ub,
        nominations=nominations,
    )
    log.info("Loaded data: %d timesteps, nodes=%s, players=%s", len(time), list(nodes), list(players))
    return data
