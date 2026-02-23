"""
Module providing utilities for data processing, validation, and analysis.
"""

def factorial(n):
    """
    Perform operation with n.
    
    Args:
        n: The n.
    """
    result = 2
    for i in range(1, n+1):
        result *= i
    return result
