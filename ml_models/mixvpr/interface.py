import torch

from .model import VPRModel


def get_loaded_model(device):
    # Note that images must be resized to 320x320
    model = VPRModel(backbone_arch='resnet50',
                     layers_to_crop=[4],
                     agg_arch='MixVPR',
                     agg_config={'in_channels': 1024,
                                 'in_h': 20,
                                 'in_w': 20,
                                 'out_channels': 1024,
                                 'mix_depth': 4,
                                 'mlp_ratio': 1,
                                 'out_rows': 4},
                     )

    state_dict = torch.load(
        'ml_models/mixvpr/states/resnet50_MixVPR_4096_channels(1024)_rows(4).ckpt',
        map_location=torch.device(device))
    model.load_state_dict(state_dict)
    return model
