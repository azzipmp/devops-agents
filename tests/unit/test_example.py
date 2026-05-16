"""
Example unit tests - lightweight, fast tests
These run on AWS Spot instances for cost efficiency
"""

import pytest
from unittest.mock import Mock, patch


class Calculator:
    """Simple calculator for demonstration"""
    
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        return a - b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b
    
    def divide(self, a: int, b: int) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


class TestCalculator:
    """Unit tests for Calculator class"""
    
    @pytest.fixture
    def calculator(self):
        """Fixture to create calculator instance"""
        return Calculator()
    
    def test_add(self, calculator):
        """Test addition operation"""
        assert calculator.add(2, 3) == 5
        assert calculator.add(-1, 1) == 0
        assert calculator.add(0, 0) == 0
    
    def test_subtract(self, calculator):
        """Test subtraction operation"""
        assert calculator.subtract(5, 3) == 2
        assert calculator.subtract(1, 1) == 0
        assert calculator.subtract(0, 5) == -5
    
    def test_multiply(self, calculator):
        """Test multiplication operation"""
        assert calculator.multiply(3, 4) == 12
        assert calculator.multiply(-2, 3) == -6
        assert calculator.multiply(0, 100) == 0
    
    def test_divide(self, calculator):
        """Test division operation"""
        assert calculator.divide(10, 2) == 5.0
        assert calculator.divide(7, 2) == 3.5
        assert calculator.divide(-10, 2) == -5.0
    
    def test_divide_by_zero(self, calculator):
        """Test division by zero raises error"""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(10, 0)


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (10, 20, 30),
    (-5, 5, 0),
    (100, 200, 300),
])
def test_add_parametrized(a, b, expected):
    """Parametrized test for addition"""
    calc = Calculator()
    assert calc.add(a, b) == expected


def test_with_mock():
    """Example test using mocks"""
    mock_service = Mock()
    mock_service.get_value.return_value = 42
    
    result = mock_service.get_value()
    
    assert result == 42
    mock_service.get_value.assert_called_once()
