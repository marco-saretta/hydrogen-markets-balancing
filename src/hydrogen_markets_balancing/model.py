import logging
from pathlib import Path
from types import SimpleNamespace

import linopy
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
        log.info("Building model %s", self.cfg.model.name)
        self.m = linopy.Model()

    def add_variables(self):
        log.info("Adding variables")
        d = self.d

        self.v = SimpleNamespace()  # Setup variables

        # linopy variables are free unless bounded, so p_tni can go negative (buying)
        self.v.p_t = self.m.add_variables(
            lower=d.p_t_lb, upper=d.p_t_ub, name="p_t"
        )  # total system position
        self.v.p_tn = self.m.add_variables(
            lower=d.p_tn_lb, upper=d.p_tn_ub, name="p_tn"
        )  # total node position
        self.v.p_tni = self.m.add_variables(
            coords=[d.time, d.nodes, d.players], name="p_tni"
        )  # total node position per player

    def add_constraints(self):
        log.info("Adding constraints")
        self.m.add_constraints(
            self.v.p_tn == self.v.p_tni.sum("player"), name="node_position"
        )  # nodes = sum over players
        self.m.add_constraints(
            self.v.p_t == self.v.p_tn.sum("node"), name="system_position"
        )  # system = sum over nodes

    def add_objective(self):
        # Placeholder: no cost terms defined yet, so any feasible point is optimal
        self.m.add_objective(0 * self.v.p_t.sum(), sense="min")

    def optimize(self):
        options = OmegaConf.to_container(self.cfg.solver.options)
        status, condition = self.m.solve(solver_name=self.cfg.solver.name, **options)
        log.info("Solver status %s, termination condition %s", status, condition)
        # HiGHS reports status "ok" with condition "unknown" on problems it cannot solve (e.g. MIQP)
        if condition != "optimal":
            raise RuntimeError(f"Solver did not reach optimality: status {status}, condition {condition}")

    def save_results(self):
        path = Path(self.cfg.paths.lp_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.m.to_file(path, explicit_coordinate_names=True)
        log.info("Wrote %s", path)
