"""Standalone CBAM (Convolutional Block Attention Module) for YOLO YAML.

This module is designed to be monkey-patched into ultralytics.nn.tasks so that
model YAML files can reference it by name (CBAM) without modifying the
ultralytics source package.

The lazy-initialisation pattern (submodules created on first forward) allows
the ``else`` branch of ultralytics parse_model to handle CBAM correctly without
any source modification — CBAM's YAML args are just [kernel_size], and c1
(input channels) is auto-detected from the input tensor shape.
"""

import torch
import torch.nn as nn


class ChannelAttention(nn.Module):
    """Channel-attention: squeeze-excite style."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Conv2d(channels, channels, 1, 1, 0, bias=True)
        self.act = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.act(self.fc(self.pool(x)))


class SpatialAttention(nn.Module):
    """Spatial-attention: channel-pool + conv."""

    def __init__(self, kernel_size=7):
        super().__init__()
        assert kernel_size in {3, 7}, "kernel size must be 3 or 7"
        padding = 3 if kernel_size == 7 else 1
        self.cv1 = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.act = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        return x * self.act(self.cv1(torch.cat([avg_out, max_out], dim=1)))


class CBAM(nn.Module):
    """Convolutional Block Attention Module.

    YAML usage (monkey-patched into ultralytics.nn.tasks)::

        [-1, 1, CBAM, [3]]   # kernel_size=3

    The parse_model default (``else``) branch calls ``CBAM(kernel_size)``.
    Submodules are lazily created on the first forward pass so that the
    correct input channel count (c1) is inferred from the input tensor.
    """

    def __init__(self, kernel_size=3):
        super().__init__()
        self.kernel_size = kernel_size
        self.ca = None  # ChannelAttention — lazy
        self.sa = None  # SpatialAttention — lazy

    def forward(self, x):
        if self.ca is None:
            c = x.shape[1]
            self.ca = ChannelAttention(c)
            self.sa = SpatialAttention(self.kernel_size)
            # Match parent device / training mode
            self.ca.to(device=x.device, dtype=x.dtype)
            self.sa.to(device=x.device, dtype=x.dtype)
            if not self.training:
                self.ca.eval()
                self.sa.eval()
        return self.sa(self.ca(x))
