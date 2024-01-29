"""
# Created: 2023-12-26 12:41
# Copyright (C) 2023-now, RPL, KTH Royal Institute of Technology
# Author: Kin ZHANG  (https://kin-zhang.github.io/)
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Description: produce flow based on model predict and write into the dataset, 
#              then use tests/scene_flow.py flow_mode="flow_est" to visualize the flow.
"""

import torch
from torch.utils.data import DataLoader
import lightning.pytorch as pl
from lightning.pytorch.loggers import WandbLogger
from omegaconf import DictConfig, OmegaConf
import hydra, wandb, os, sys
from hydra.core.hydra_config import HydraConfig
from scripts.network.dataloader import HDF5Dataset
from scripts.pl_model import ModelWrapper

@hydra.main(version_base=None, config_path="conf", config_name="eval")
def main(cfg):
    pl.seed_everything(cfg.seed, workers=True)
    output_dir = HydraConfig.get().runtime.output_dir

    if not os.path.exists(cfg.checkpoint):
        print(f"Checkpoint {cfg.checkpoint} does not exist. Need checkpoints for evaluation.")
        sys.exit(1)
    
    checkpoint_params = DictConfig(torch.load(cfg.checkpoint)["hyper_parameters"])
    cfg.output = checkpoint_params.cfg.output + f"-{cfg.av2_mode}"
    cfg.model.update(checkpoint_params.cfg.model)
    mymodel = ModelWrapper.load_from_checkpoint(cfg.checkpoint, cfg=cfg, eval=True)

    wandb_logger = WandbLogger(save_dir=output_dir,
                               entity="hdmaptest",
                               project=f"sceneflow-eval", 
                               name=f"{cfg.output}",
                               offline=(cfg.wandb_mode == "offline"))
    
    trainer = pl.Trainer(logger=wandb_logger, devices=1)
    # NOTE(Qingwen): search & check in pl_model.py : def test_step(self, batch, res_dict)
    trainer.test(model = mymodel, \
                 dataloaders = DataLoader(HDF5Dataset(cfg.dataset_path), batch_size=1, shuffle=False))
    wandb.finish()

if __name__ == "__main__":
    main()