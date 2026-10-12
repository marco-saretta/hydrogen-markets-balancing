import logging

import hydra
from omegaconf import DictConfig, OmegaConf

from hydrogen_markets_balancing import Model

log = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    log.info("Config:\n%s", OmegaConf.to_yaml(cfg))
    Model(cfg)


if __name__ == "__main__":
    main()
