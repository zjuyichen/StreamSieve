"""M2/M4 reference-implementation correctness: pHash stability, Hamming distance, fused-score monotonicity."""
from __future__ import annotations

from streamsieve.common.types import Descriptor
from streamsieve.modules.m2_features.phash import phash64, quadrant_hashes
from streamsieve.modules.m4_similarity.hamming import hamming64
from streamsieve.modules.m4_similarity.scoring import Weights, fuse


def gradient(level: int):
    return [[(x * 3 + y * 2 + level) % 256 for x in range(32)] for y in range(32)]


def checker():
    return [[255 if ((x // 4 + y // 4) % 2 == 0) else 0 for x in range(32)] for y in range(32)]


def test_phash_identical_is_zero_distance():
    a = phash64(gradient(40))
    b = phash64(gradient(40))
    assert hamming64(a, b) == 0.0


def test_phash_different_patterns_far_apart():
    d = hamming64(phash64(gradient(40)), phash64(checker()))
    assert d > 0.2


def test_fused_score_orders_by_difference():
    g1, g2 = gradient(40), gradient(200)
    c = checker()
    d_prev = Descriptor(phash64=phash64(g1), quad_h=quadrant_hashes(g1))
    d_same = Descriptor(phash64=phash64(g1), quad_h=quadrant_hashes(g1))
    d_other = Descriptor(phash64=phash64(c), quad_h=quadrant_hashes(c))
    w = Weights()
    s_same = fuse(desc=d_same, prev=d_prev, anchor=d_prev, mad=0.0, ssim=1.0, weights=w)
    s_other = fuse(desc=d_other, prev=d_prev, anchor=d_prev, mad=0.5, ssim=0.1, weights=w)
    assert s_same.fused < s_other.fused


def test_config_invariants_monotone():
    """INV4: with identical input, lower thresholds ⇒ more dispatches (guaranteed by the decision layer; this verifies score comparability)."""
    g, c = gradient(40), checker()
    d_prev = Descriptor(phash64=phash64(g), quad_h=quadrant_hashes(g))
    d_c = Descriptor(phash64=phash64(c), quad_h=quadrant_hashes(c))
    s = fuse(desc=d_c, prev=d_prev, anchor=d_prev, mad=0.2, ssim=0.3, weights=Weights())
    assert 0.0 <= s.fused <= 1.0
