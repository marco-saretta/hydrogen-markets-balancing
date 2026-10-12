import logging
from pathlib import Path
from types import SimpleNamespace

import gurobipy as gp
from omegaconf import DictConfig, OmegaConf

from .data_loader import load_data

log = logging.getLogger(__name__)


class Model:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.d = load_data(cfg)

        self.instantiate_model()
        self.add_variables()
        self.add_constraints()
        self.add_objective()
        self.save_results()
        self.optimize()

    def instantiate_model(self):
        self.m = gp.Model(self.cfg.model.name)
        for name, value in OmegaConf.to_container(self.cfg.solver.params).items():
            self.m.setParam(name, value)

    def add_variables(self):
        log.info("Adding variables")
        d = self.d
        n, t, i = len(d.nodes), d.timesteps, len(d.players)

        self.v = SimpleNamespace()  # Setup variables

        # Positions can be negative (buying), so lift Gurobi's default lb of 0
        free = -gp.GRB.INFINITY
        self.v.p_t = self.m.addMVar(
            shape=(t,), lb=d.p_t_lb, ub=d.p_t_ub, name="p_t"
        )  # total system position
        self.v.p_tn = self.m.addMVar(
            shape=(t, n), lb=d.p_tn_lb, ub=d.p_tn_ub, name="p_tn"
        )  # total node position
        self.v.p_tni = self.m.addMVar(
            shape=(t, n, i), lb=free, name="p_tni"
        )  # total node position per player

    def add_constraints(self):
        log.info("Adding constraints")
        self.m.addConstr(
            self.v.p_tn == self.v.p_tni.sum(axis=2), name="node_position"
        )  # nodes = sum over players
        self.m.addConstr(
            self.v.p_t == self.v.p_tn.sum(axis=1), name="system_position"
        )  # system = sum over nodes

    def add_objective(self):
        # Placeholder: no cost terms defined yet, so any feasible point is optimal
        self.m.setObjective(gp.LinExpr(), sense=gp.GRB.MINIMIZE)

    def optimize(self):
        self.m.optimize()

    def save_results(self):
        path = Path(self.cfg.paths.lp_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.m.write(str(path))
        log.info("Wrote %s", path)
