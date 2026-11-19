"""Label mapping utilities for VecToMorph."""

from __future__ import annotations

from typing import Optional


COARSE_LABELS = [
    "neutrophils",
    "eosinophils",
    "basophils",
    "lymphocytes",
    "monocytes",
    "immature_granulocytes",
    "erythroblasts",
]
COARSE_TO_ID = {label: index for index, label in enumerate(COARSE_LABELS)}


MLL23_FINE_TO_COARSE = {
    "neutrophil_band": "neutrophils",
    "neutrophil_segmented": "neutrophils",
    "eosinophil": "eosinophils",
    "basophil": "basophils",
    "lymphocyte": "lymphocytes",
    "monocyte": "monocytes",
    "promyelocyte": "immature_granulocytes",
    "myelocyte": "immature_granulocytes",
    "metamyelocyte": "immature_granulocytes",
    "normoblast": "erythroblasts",
    "myeloblast": None,
    "promyelocyte_atypical": None,
    "plasma_cell": None,
    "hairy_cell": None,
    "smudge_cell": None,
    "lymphocyte_reactive": None,
    "lymphocyte_neoplastic": None,
    "lymphocyte_large_granular": None,
}

ACEVEDO_FINE_TO_COARSE = {
    "neutrophil": "neutrophils",
    "eosinophil": "eosinophils",
    "basophil": "basophils",
    "lymphocyte": "lymphocytes",
    "monocyte": "monocytes",
    "ig": "immature_granulocytes",
    "erythroblast": "erythroblasts",
    "platelet": None,
}

MLL23_REQUIRED_LABELS = {
    label for label, coarse in MLL23_FINE_TO_COARSE.items() if coarse is not None
}
ACEVEDO_REQUIRED_LABELS = {
    label for label, coarse in ACEVEDO_FINE_TO_COARSE.items() if coarse is not None
}


def map_mll23_label(fine_label: str) -> Optional[str]:
    """Map an MLL23 fine-grained label to a 7-way coarse label."""
    return MLL23_FINE_TO_COARSE.get(fine_label)


def map_acevedo_label(fine_label: str) -> Optional[str]:
    """Map an Acevedo fine-grained label to a 7-way coarse label."""
    return ACEVEDO_FINE_TO_COARSE.get(fine_label)


def coarse_label_to_id(coarse_label: str) -> int:
    """Convert a coarse label string to a stable class index."""
    return COARSE_TO_ID[coarse_label]
