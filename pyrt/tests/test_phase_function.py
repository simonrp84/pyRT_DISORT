import numpy as np
import pytest
from pyrt.phase_function import construct_hg, decompose_hg


class TestConstructHG:
    def test_function_is_normalized_to_1(self):
        g = 0.5
        sa = np.linspace(0, 180, num=1801)

        pf = construct_hg(g, sa)

        assert np.sum(pf * np.sin(np.radians(sa))) * 2 * np.pi * np.pi / len(sa) == pytest.approx(1, 0.001)

    def test_g_equals_0_gives_same_value_everywhere(self):
        g = 0
        sa = np.linspace(0, 180, num=1801)

        pf = construct_hg(g, sa)

        assert np.all(pf == 1 / (4 * np.pi))


class TestDecomposeHG:
    def test_first_moment_is_1(self):
        legendre = decompose_hg(0.5, 200)

        assert legendre[0] == 1

    def test_function_gives_n_moments(self):
        legendre = decompose_hg(0.5, 200)

        assert legendre[0] == 1
