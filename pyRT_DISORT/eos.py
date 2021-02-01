"""eos.py contains data structures to hold euqation of state variables used
throughout the model.
"""

import numpy as np
from scipy.constants import Boltzmann
from pyRT_DISORT.utilities.array_checks import ArrayChecker


class ModelEquationOfState:
    """ModelEquationOfState computes EoS variables on a model grid.

    ModelEquationOfState accepts altitudes [km], pressures [Pa],
    temperatures [K], and number densities [particles / m**3], along with the
    altitudes where the model will be defined. It interpolates each of the EoS
    variables onto this grid and computes the column density within each layer.
    For this computation, quantities are assumed to be in SI units.

    """
    def __init__(self, altitude_grid: np.ndarray, pressure_grid: np.ndarray,
                 temperature_grid: np.ndarray, number_density_grid: np.ndarray,
                 altitude_model: np.ndarray) -> None:
        """
        Parameters
        ----------
        altitude_grid: np.ndarray
            The altitudes [km] at which the EoS variables are defined.
        pressure_grid: np.ndarray
            The pressures [Pa] at the corresponding altitudes.
        temperature_grid: np.ndarray
            The temperatures [K] at the corresponding altitudes.
        number_density_grid: np.ndarray
            The number densities [particles / m**3] at the corresponding
            altitudes.
        altitude_model: np.ndarray
            The desired altitudes [km] of the model boundaries.

        Raises
        ------
        IndexError
            Raised if the input grids do not have the same shape.
        TypeError
            Raised if any of the inputs are not np.ndarrays.
        ValueError
            Raised if any of the inputs have unphysical values.

        """
        self.__altitude_grid = altitude_grid
        self.__pressure_grid = pressure_grid
        self.__temperature_grid = temperature_grid
        self.__number_density_grid = number_density_grid
        self.__altitude_model = altitude_model

        self.__raise_error_if_input_variables_are_bad()
        self.__flip_grids_if_altitudes_are_mono_decreasing()

        self.__pressure_model = self.__make_pressure_model()
        self.__temperature_model = self.__make_temperature_model()
        self.__number_density_model = self.__make_number_density_model()

    def __raise_error_if_input_variables_are_bad(self) -> None:
        self.__raise_error_if_altitude_grid_is_bad()
        self.__raise_error_if_pressure_grid_is_bad()
        self.__raise_error_if_temperature_grid_is_bad()
        self.__raise_error_if_number_density_grid_is_bad()
        self.__raise_error_if_altitude_model_is_bad()
        self.__raise_index_error_if_grids_are_not_same_shape()

    def __raise_error_if_altitude_grid_is_bad(self) -> None:
        self.__raise_error_if_grid_is_bad(self.__altitude_grid, 'altitude_grid')

    def __raise_error_if_pressure_grid_is_bad(self) -> None:
        self.__raise_error_if_grid_is_bad(self.__pressure_grid, 'pressure_grid')

    def __raise_error_if_temperature_grid_is_bad(self) -> None:
        self.__raise_error_if_grid_is_bad(
            self.__temperature_grid, 'temperature_grid')

    def __raise_error_if_number_density_grid_is_bad(self) -> None:
        self.__raise_error_if_grid_is_bad(
            self.__number_density_grid, 'number_density_grid')

    def __raise_index_error_if_grids_are_not_same_shape(self) -> None:
        if not self.__altitude_grid.shape == self.__temperature_grid.shape == \
               self.__pressure_grid.shape == self.__number_density_grid.shape:
            raise IndexError('All input grids must have the same shape.')

    def __raise_error_if_altitude_model_is_bad(self) -> None:
        self.__raise_error_if_grid_is_bad(
            self.__altitude_model, 'altitude_model')
        self.__raise_value_error_if_model_altitudes_are_not_mono_decreasing()
        self.__raise_value_error_if_too_few_layers_are_included()

    def __raise_error_if_grid_is_bad(self, array: np.ndarray, name: str) \
            -> None:
        try:
            checks = self.__make_grid_checks(array)
        except TypeError:
            raise TypeError(f'{name} is not a np.ndarray.') from None
        if not all(checks):
            raise ValueError(
                f'{name} must be a 1D array containing positive, finite '
                f'values.')

    @staticmethod
    def __make_grid_checks(grid: np.ndarray) -> list[bool]:
        grid_checker = ArrayChecker(grid)
        checks = [grid_checker.determine_if_array_is_1d(),
                  grid_checker.determine_if_array_is_positive_finite()]
        return checks

    def __raise_value_error_if_model_altitudes_are_not_mono_decreasing(self) \
            -> None:
        model_checker = ArrayChecker(self.__altitude_model)
        if not model_checker.determine_if_array_is_monotonically_decreasing():
            raise ValueError('altitude_model must be monotonically decreasing.')

    def __raise_value_error_if_too_few_layers_are_included(self) -> None:
        if len(self.__altitude_model) < 2:
            raise ValueError('The model must contain at least 2 boundaries '
                             '(i.e. one layer).')

    def __flip_grids_if_altitudes_are_mono_decreasing(self) -> None:
        altitude_checker = ArrayChecker(self.__altitude_grid)
        if altitude_checker.determine_if_array_is_monotonically_decreasing():
            self.__altitude_grid = np.flip(self.__altitude_grid)
            self.__pressure_grid = np.flip(self.__pressure_grid)
            self.__temperature_grid = np.flip(self.__temperature_grid)
            self.__number_density_grid = np.flip(self.__number_density_grid)

    def __make_pressure_model(self):
        return self.__interpolate_variable_to_model_altitudes(
            self.__pressure_grid)

    def __make_temperature_model(self):
        return self.__interpolate_variable_to_model_altitudes(
            self.__temperature_grid)

    def __make_number_density_model(self):
        return self.__interpolate_variable_to_model_altitudes(
            self.__number_density_grid)

    def __interpolate_variable_to_model_altitudes(self, grid):
        return np.interp(self.__altitude_model, self.__altitude_grid, grid)
