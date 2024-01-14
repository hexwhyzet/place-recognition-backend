import coremltools as ct
import numpy as np
import torch

from ml_models.mixvpr.interface import get_loaded_model

shape = (1, 3, 320, 320)
example_input = torch.rand(*shape)

model = get_loaded_model('cpu')

resnet = model.backbone
traced_resnet = torch.jit.trace(resnet, example_input)

resnet_model = ct.convert(
    traced_resnet,
    convert_to="mlprogram",
    inputs=[ct.ImageType(shape=shape)],
    # compute_units=ct.ComputeUnit.CPU_AND_NE,
)

resnet_model.save("resnet.mlpackage")

medium_shape = (1, 1024, 20, 20)
example_medium_input = torch.rand(*medium_shape)

mixvpr = model.aggregator
traced_mixvpr = torch.jit.trace(mixvpr, example_medium_input)

mixvpr_model = ct.convert(
    traced_mixvpr,
    convert_to="mlprogram",
    inputs=[ct.TensorType(shape=medium_shape, dtype=np.float32)],
    # compute_units=ct.ComputeUnit.CPU_AND_NE,
)

mixvpr_model.save("mixvpr.mlpackage")
