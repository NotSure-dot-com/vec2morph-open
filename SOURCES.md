# Training and evaluation sources

The following licenses were checked against the original dataset metadata on 18 November 2026. These entries identify the image sources and their supplied labels. Model weights and the source images are distinct artifacts.

| Use | Source | Recorded license | Original record |
|---|---|---|---|
| Training | MLL23, Shetab Boushehri et al. | CC BY 4.0 | [Zenodo 14277609](https://zenodo.org/records/14277609) |
| Training | Acevedo et al., microscopic peripheral blood cell images | CC BY 4.0 | [Mendeley Data v1](https://data.mendeley.com/datasets/snkd93bnjr/1) |
| Training | KU-Optofil PBC, Yarıkan et al. | CC BY 4.0 | [Zenodo 17333317](https://zenodo.org/records/17333317) |
| Training | UNIVALI Leukocyte Dataset, Kasprowicz et al. | CC BY 4.0 | [Zenodo 17743609](https://zenodo.org/records/17743609) |
| External evaluation | Multi-focus WBC, Park et al. | See original dataset record | [Data descriptor](https://doi.org/10.1038/s41597-024-03938-1) |

The three Zenodo training records identify their license as `cc-by-4.0` in `GET https://zenodo.org/api/records/<id>`. Acevedo's Mendeley record states CC BY 4.0. Their license text is available at [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

DINOv2 base weights are `timm/vit_small_patch14_dinov2.lvd142m`, revision `4610ca143709d58a633b6397a74412c2c3842454`, SHA-256 `04d27f3400d059fc0cfd7d17dd1909a75bf3ea8fb3eeb48b97cb99e57ee20081`. The [upstream model card](https://huggingface.co/timm/vit_small_patch14_dinov2.lvd142m) specifies Apache 2.0. Cite Oquab et al., DINOv2, [arXiv 2304.07193](https://arxiv.org/abs/2304.07193), and Ross Wightman's [timm implementation](https://github.com/huggingface/pytorch-image-models).

Image processing in VecToMorph uses the source-specific crops described in the model card. Training employs right-angle rotations and reflections. Dataset names and references preserve attribution to the original image authors. The release downloads contain model weights, source and evaluation records.
