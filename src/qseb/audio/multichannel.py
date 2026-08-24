"""Utilities for multichannel quantum audio benchmarks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MultichannelAudio:
    """Classical multichannel audio container.

    Shape:
        channels x samples
    """

    samples: list[list[int]]

    @property
    def channels(self):
        return len(self.samples)

    @property
    def samples_per_channel(self):
        if not self.samples:
            return 0
        return len(self.samples[0])


def create_stereo_example():
    """Create a small deterministic stereo example."""
    return MultichannelAudio(
        samples=[
            [1, 2, 3, 4],
            [5, 6, 7, 8],
        ]
    )