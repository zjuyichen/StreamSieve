# native/ — hot-path native kernels (planned)

Native extensions replacing the pure-Python reference for the production
performance path (M2/M3/M4):

- `phash_kernel/` (Rust + PyO3, or C++ + pybind11):
  - 1080p → 1/8 luma pyramid (SIMD downscale)
  - 64-bit pHash (32×32 DCT) and quadrant hashes
  - 128-bit batched Hamming distance (AVX2 / NEON popcount)
- Build artifacts are loaded dynamically via
  `streamsieve.modules.m2_features.accel`; when loading fails it falls back to the
  pure-Python reference (tests only, not a performance target).

Constraint: kernels must be stateless, I/O-free, and reentrant; no GPL
dependencies (stays Apache-2.0 compatible).
