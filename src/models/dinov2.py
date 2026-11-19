"""DINOv2 feature extraction utilities."""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

import timm


class DINOv2Extractor(nn.Module):
    """Thin wrapper around timm's DINOv2 ViT-S/14 backbone."""

    def __init__(
        self,
        model_name: str,
        image_size: int = 224,
        pretrained: bool = True,
        l2_normalize: bool = True,
        feature_mode: str = 'cls',
    ) -> None:
        super().__init__()
        if feature_mode not in ('cls', 'cls_patch_mean', 'cls4_patch_mean'):
            raise ValueError(f'Unknown feature mode: {feature_mode}')
        self.feature_mode = feature_mode
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            img_size=image_size,
        )
        self.backbone.eval()
        self.embed_dim = int(getattr(self.backbone, "embed_dim")) * {'cls': 1, 'cls_patch_mean': 2, 'cls4_patch_mean': 5}[feature_mode]
        self.l2_normalize = l2_normalize

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """Extract the configured frozen token representation."""
        if self.feature_mode == 'cls4_patch_mean':
            result = self.backbone.forward_intermediates(
                images, indices=4, return_prefix_tokens=True, norm=True,
                output_fmt='NLC', output_dict=True)
            prefixes = result.get('image_intermediates_prefix', [])
            patches = result.get('image_intermediates', [])
            if len(prefixes) != 4 or len(patches) != 4:
                raise ValueError('Four-CLS feature mode requires exactly four intermediate layers.')
            width = int(self.backbone.embed_dim)
            for prefix, patch in zip(prefixes, patches):
                if (prefix.ndim != 3 or patch.ndim != 3 or prefix.shape[1] < 1
                        or patch.shape[1] < 1 or prefix.shape[0] != len(images)
                        or patch.shape[0] != len(images) or prefix.shape[2] != width
                        or patch.shape[2] != width):
                    raise ValueError('Invalid intermediate CLS/patch token shape.')
            blocks = [prefixes[-1][:, 0].float(), patches[-1].float().mean(dim=1)]
            blocks.extend(prefix[:, 0].float() for prefix in prefixes[:-1])
            features = torch.cat(blocks, dim=-1)
            return F.normalize(features, p=2, dim=-1) if self.l2_normalize else features
        features = self.backbone.forward_features(images)
        cls_token = _extract_cls_token(features)
        cls_token = cls_token.float()
        if self.feature_mode == 'cls_patch_mean':
            if isinstance(features, dict) and 'x_norm_clstoken' in features and 'x_norm_patchtokens' in features:
                patch_tokens = features['x_norm_patchtokens']
            elif isinstance(features, torch.Tensor) and features.ndim == 3:
                prefix = int(getattr(self.backbone, 'num_prefix_tokens', 1))
                if prefix < 1:
                    raise ValueError('CLS plus patch features require a CLS prefix token.')
                patch_tokens = features[:, prefix:]
            else:
                raise ValueError('Patch feature mode requires explicit normalized patch tokens or a token tensor.')
            if patch_tokens.ndim != 3 or patch_tokens.shape[1] == 0:
                raise ValueError('Patch feature mode requires at least one patch token.')
            patch_mean = patch_tokens.float().mean(dim=1)
            cls_token = torch.cat((cls_token, patch_mean), dim=-1)
        if self.l2_normalize:
            cls_token = F.normalize(cls_token, p=2, dim=-1)
        return cls_token


def create_dinov2_extractor(
    config: dict,
    pretrained: bool = True,
) -> DINOv2Extractor:
    """Create the configured DINOv2 extractor."""
    model_cfg = config["model"]
    return DINOv2Extractor(
        model_name=model_cfg["name"],
        image_size=int(model_cfg["image_size"]),
        pretrained=pretrained,
        l2_normalize=bool(model_cfg.get("l2_normalize", True)),
        feature_mode=model_cfg.get('feature_mode', 'cls'),
    )


def _extract_cls_token(features) -> torch.Tensor:
    if isinstance(features, dict):
        if "x_norm_clstoken" in features:
            return features["x_norm_clstoken"]
        if "x_prenorm" in features and isinstance(features["x_prenorm"], torch.Tensor):
            return features["x_prenorm"][:, 0]
        if "x" in features and isinstance(features["x"], torch.Tensor):
            return features["x"][:, 0]
        raise TypeError("Unsupported DINOv2 feature dictionary structure.")

    if isinstance(features, torch.Tensor):
        if features.ndim == 3:
            return features[:, 0]
        if features.ndim == 2:
            return features

    raise TypeError(f"Unsupported DINOv2 feature output type: {type(features)!r}")
