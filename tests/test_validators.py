"""
Tests para las funciones de validación
"""

import pytest
from src.utils.validators import (
    validate_positive_number,
    validate_percentage,
    validate_investment_financing_balance
)


class TestValidatePositiveNumber:
    """Tests para validate_positive_number"""

    def test_valid_positive_number(self):
        is_valid, error = validate_positive_number(100)
        assert is_valid is True
        assert error is None

    def test_zero_is_valid(self):
        is_valid, error = validate_positive_number(0)
        assert is_valid is True
        assert error is None

    def test_negative_number(self):
        is_valid, error = validate_positive_number(-10)
        assert is_valid is False
        assert "positivo" in error.lower()

    def test_invalid_string(self):
        is_valid, error = validate_positive_number("abc")
        assert is_valid is False
        assert "válido" in error.lower()


class TestValidatePercentage:
    """Tests para validate_percentage"""

    def test_valid_percentage(self):
        is_valid, error = validate_percentage(50)
        assert is_valid is True
        assert error is None

    def test_percentage_over_100(self):
        is_valid, error = validate_percentage(150)
        assert is_valid is False
        assert "100" in error


class TestValidateInvestmentFinancing:
    """Tests para validate_investment_financing_balance"""

    def test_sufficient_financing(self):
        is_valid, warning = validate_investment_financing_balance(10000, 10000)
        assert is_valid is True

    def test_insufficient_financing(self):
        is_valid, warning = validate_investment_financing_balance(10000, 8000)
        assert is_valid is False
        assert "insuficiente" in warning.lower()

    def test_excess_financing_warning(self):
        is_valid, warning = validate_investment_financing_balance(10000, 20000)
        assert is_valid is True
        assert warning is not None


# TODO: Añadir más tests según se implementen más validaciones
