# 3rd-party imports
import numpy as np

# Local imports
from preprocessing.model.aerosol_column import Column


class EmpiricalPhaseFunction:
    def __init__(self, phase_function_file, particle_sizes_file, wavelengths_file):
        self.phase_function_file = phase_function_file
        self.particle_sizes_file = particle_sizes_file
        self.wavelengths_file = wavelengths_file

        self.phase_functions = np.load(self.phase_function_file)
        self.particle_sizes = np.load(self.particle_sizes_file)
        self.wavelengths = np.load(self.wavelengths_file)

        assert len(self.particle_sizes) == self.phase_functions.shape[1], \
            'The shape of radii doesn\'t match the phase function dimension.'
        assert len(self.wavelengths) == self.phase_functions.shape[2], \
            'The shape of wavelengths doesn\'t match the phase function dimension.'


class NearestNeighborPhaseFunction:
    def __init__(self, aerosol_phase_function, column, n_moments):
        self.aerosol_phase_function = aerosol_phase_function
        self.column = column
        self.n_moments = n_moments

        assert isinstance(self.aerosol_phase_function, EmpiricalPhaseFunction)
        assert isinstance(self.column, Column), 'column must be a Column.'
        assert isinstance(self.n_moments, int), 'n_moments but be an int.'

        self.nearest_neighbor_phase_functions = self.get_nearest_neighbor_phase_functions()
        self.make_nearest_neighbor_phase_functions_match_n_moments()
        self.normalize_nearest_neighbor_phase_functions()
        self.layered_nearest_neighbor_phase_functions = self.expand_nearest_neighbor_phase_function_layers()
        self.layered_hyperspectral_nearest_neighbor_phase_functions = self.make_phase_function_without_size()

    def get_nearest_neighbor_phase_functions(self):
        radius_indices = self.get_nearest_indices(self.column.particle_sizes,
                                                  self.aerosol_phase_function.particle_sizes)
        wavelength_indices = self.get_nearest_indices(self.column.aerosol.wavelengths,
                                                      self.aerosol_phase_function.wavelengths)
        all_phase_functions = self.aerosol_phase_function.phase_functions

        # I'm not sure why I cannot do this on one line...
        nearest_neighbor_phase_functions = all_phase_functions[:, radius_indices, :]
        nearest_neighbor_phase_functions = nearest_neighbor_phase_functions[:, :, wavelength_indices]
        return nearest_neighbor_phase_functions

    @staticmethod
    def get_nearest_indices(values, array):
        diff = (values.reshape(1, -1) - array.reshape(-1, 1))
        indices = np.abs(diff).argmin(axis=0)
        return indices

    def make_nearest_neighbor_phase_functions_match_n_moments(self):
        if self.nearest_neighbor_phase_functions.shape[0] < self.n_moments:
            self.add_moments()
        else:
            self.trim_moments()

    def add_moments(self):
        nnpf_shapes = self.nearest_neighbor_phase_functions.shape
        moments = np.zeros((self.n_moments, nnpf_shapes[1], nnpf_shapes[2]))
        moments[:nnpf_shapes[0], :, :] = self.nearest_neighbor_phase_functions
        self.nearest_neighbor_phase_functions = moments

    def trim_moments(self):
        self.nearest_neighbor_phase_functions = self.nearest_neighbor_phase_functions[:self.n_moments, :, :]

    def normalize_nearest_neighbor_phase_functions(self):
        # Divide the k-th moment by 2k+1
        normalization = np.linspace(0, self.n_moments-1, num=self.n_moments)*2 + 1
        self.nearest_neighbor_phase_functions = (self.nearest_neighbor_phase_functions.T / normalization).T

    def expand_nearest_neighbor_phase_function_layers(self):
        nnpf = self.nearest_neighbor_phase_functions
        expanded_phase_function = np.broadcast_to(nnpf[:, None, :, :], (self.n_moments, self.column.layers.n_layers,
                                                                        nnpf.shape[1], nnpf.shape[2]))
        return expanded_phase_function

    def make_phase_function_without_size(self):
        # Calculate C_sca / C_ext * tau_aerosol * PMOM_aerosol and weight its sum over size
        aerosol_polynomial_moments = self.layered_nearest_neighbor_phase_functions * \
                                     self.column.multisize_hyperspectral_scattering_optical_depths
        return np.average(aerosol_polynomial_moments, axis=2, weights=self.column.column_integrated_optical_depths)