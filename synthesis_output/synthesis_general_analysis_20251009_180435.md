# Multi-Model Synthesis Result

## Original Request
Write a Python function that calculates the factorial of a number

## Context Used
Minimal context available

## DeepSeek Analysis
Here's a comprehensive Python function to calculate the factorial of a number with multiple approaches and optimizations:

## Basic Recursive Implementation
```python
def factorial_recursive(n: int) -> int:
    """
    Calculate factorial using recursion.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n (n!)
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    # Input validation
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    # Base case
    if n == 0 or n == 1:
        return 1
    
    # Recursive case
    return n * factorial_recursive(n - 1)
```

## Optimized Iterative Implementation
```python
def factorial_iterative(n: int) -> int:
    """
    Calculate factorial using iteration (more memory efficient).
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n (n!)
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    # Input validation
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```

## Production-Ready Version with Caching
```python
from functools import lru_cache
import math

@lru_cache(maxsize=128)
def factorial_cached(n: int) -> int:
    """
    Calculate factorial with memoization for repeated calls.
    
    Args:
        n: Non-negative integer (0 <= n <= 170 for Python float precision)
        
    Returns:
        Factorial of n (n!)
        
    Raises:
        ValueError: If n is negative or too large
        TypeError: If n is not an integer
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n > 170:
        raise ValueError("Input too large - would cause overflow")
    
    # Use math.factorial for optimal performance
    return math.factorial(n)
```

## Complete Implementation with All Methods
```python
import math
from functools import lru_cache
from typing import Union

class FactorialCalculator:
    """
    A comprehensive factorial calculator with multiple implementations.
    """
    
    @staticmethod
    def recursive(n: int) -> int:
        """Recursive implementation (educational purpose)"""
        if not isinstance(n, int):
            raise TypeError("Input must be an integer")
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        return n * FactorialCalculator.recursive(n - 1)
    
    @staticmethod
    def iterative(n: int) -> int:
        """Iterative implementation (memory efficient)"""
        if not isinstance(n, int):
            raise TypeError("Input must be an integer")
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    @staticmethod
    @lru_cache(maxsize=128)
    def cached(n: int) -> int:
        """Cached implementation for repeated calls"""
        return FactorialCalculator.iterative(n)
    
    @staticmethod
    def builtin(n: int) -> int:
        """Using Python's built-in math.factorial (fastest)"""
        return math.factorial(n)

# Recommended usage for production:
def factorial(n: int, method: str = 'builtin') -> int:
    """
    Main factorial function with method selection.
    
    Args:
        n: Non-negative integer
        method: Implementation method ('recursive', 'iterative', 'cached', 'builtin')
        
    Returns:
        Factorial of n
    """
    calculator = FactorialCalculator()
    
    method_map = {
        'recursive': calculator.recursive,
        'iterative': calculator.iterative,
        'cached': calculator.cached,
        'builtin': calculator.builtin
    }
    
    if method not in method_map:
        raise ValueError(f"Method must be one of: {list(method_map.keys())}")
    
    return method_map[method](n)

# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_numbers = [0, 1, 5, 10]
    
    for num in test_numbers:
        result = factorial(num)
        print(f"{num}! = {result}")
    
    # Performance comparison
    import time
    
    n = 100
    methods = ['recursive', 'iterative', 'cached', 'builtin']
    
    for method in methods:
        start_time = time.time()
        result = factorial(n, method)
        end_time = time.time()
        print(f"{method}: {n}! = {result} (Time: {end_time - start_time:.6f}s)")
```

## Key Features:

1. **Input Validation**: Handles negative numbers and non-integer inputs
2. **Multiple Implementations**: 
   - Recursive (educational)
   - Iterative (memory efficient)
   - Cached (performance for repeated calls)
   - Built-in (fastest)
3. **Error Handling**: Clear error messages for invalid inputs
4. **Performance Optimized**: Uses Python's built-in `math.factorial` for production
5. **Type Hints**: Better code documentation and IDE support

## Performance Notes:
- **Built-in (`math.factorial`)**: Fastest, written in C
- **Iterative**: Good for learning, avoids recursion limits
- **Recursive**: Simple but limited by recursion depth (~1000 in Python)
- **Cached**: Best for repeated calculations of same values

For production use, I recommend the built-in `math.factorial` function as it's the most optimized implementation available in Python.

## Claude Synthesis
# Analysis of DeepSeek's Factorial Solution

## Verification

The solution is correct and comprehensive, providing multiple implementations of the factorial function:

1. **Recursive implementation**: Correctly handles base cases (0, 1) and recursively computes larger values
2. **Iterative implementation**: Properly accumulates the product from 2 to n
3. **Cached implementation**: Correctly applies memoization using `lru_cache`
4. **Built-in implementation**: Appropriately uses Python's optimized `math.factorial`

All implementations include proper input validation for negative numbers and non-integer inputs.

## Explanation

DeepSeek's solution goes beyond a basic factorial implementation by:

1. **Offering multiple approaches** - from educational (recursive) to production-ready (built-in)
2. **Implementing proper error handling** - type checking, range validation
3. **Optimizing performance** - using caching and the built-in function
4. **Providing a unified interface** - through the `factorial()` function with method selection
5. **Including documentation** - docstrings explaining parameters, returns, and exceptions

The `FactorialCalculator` class organizes the different implementations in a structured way, while the main `factorial()` function provides a clean API.

## Implementation Steps

For a simplified implementation based on DeepSeek's solution:

1. **Import necessary modules**:
   ```python
   import math
   from functools import lru_cache
   ```

2. **Create the basic factorial function**:
   ```python
   def factorial(n, method='builtin'):
       """
       Calculate the factorial of a non-negative integer.
       
       Args:
           n: Non-negative integer
           method: Implementation method ('recursive', 'iterative', 'cached', 'builtin')
           
       Returns:
           Factorial of n (n!)
       """
       # Input validation
       if not isinstance(n, int):
           raise TypeError("Input must be an integer")
       if n < 0:
           raise ValueError("Factorial is not defined for negative numbers")
           
       # Method selection
       if method == 'recursive':
           return _factorial_recursive(n)
       elif method == 'iterative':
           return _factorial_iterative(n)
       elif method == 'cached':
           return _factorial_cached(n)
       elif method == 'builtin':
           return math.factorial(n)
       else:
           raise ValueError(f"Method must be one of: ['recursive', 'iterative', 'cached', 'builtin']")
   ```

3. **Implement helper functions** for each method:
   ```python
   def _factorial_recursive(n):
       if n == 0 or n == 1:
           return 1
       return n * _factorial_recursive(n - 1)
       
   def _factorial_iterative(n):
       result = 1
       for i in range(2, n + 1):
           result *= i
       return result
       
   @lru_cache(maxsize=128)
   def _factorial_cached(n):
       return _factorial_iterative(n)
   ```

## Additional Considerations

While DeepSeek's solution is excellent, here are some additional considerations:

1. **Recursion depth limit**: The recursive implementation will fail for large values of n due to Python's recursion limit (~1000). The solution mentions this but could add a specific check:
   ```python
   import sys
   if n > sys.getrecursionlimit() - 50:  # Buffer for other calls
       raise RecursionError(f"n too large for recursive method (max ~{sys.getrecursionlimit()-50})")
   ```

2. **Numerical precision**: For very large n, even `math.factorial` will produce results that exceed Python's integer precision. The solution mentions a limit of 170, but this applies to floating-point representation. Python integers have arbitrary precision.

3. **Performance testing**: The included performance testing is good, but could be enhanced with:
   ```python
   def benchmark_factorial(n, iterations=100):
       """Benchmark different factorial implementations."""
       methods = ['recursive', 'iterative', 'cached', 'builtin']
       results = {}
       
       for method in methods:
           if method == 'recursive' and n > 900:
               print(f"Skipping recursive method for n={n} (recursion limit)")
               continue
               
           start = time.time()
           for _ in range(iterations):
               factorial(n, method=method)
           end = time.time()
           results[method] = (end - start) / iterations
       
       return results
   ```

4. **Memory usage**: For very large factorials, memory usage could be significant. Adding a warning:
   ```python
   if n > 100000:
       import warnings
       warnings.warn(f"Computing factorial of {n} may consume significant memory")
   ```

5. **Tail recursion optimization**: Python doesn't optimize tail recursion, but for educational purposes:
   ```python
   def _factorial_tail_recursive(n, acc=1):
       if n <= 1:
           return acc
       return _factorial_tail_recursive(n - 1, acc * n)
   ```

Overall, DeepSeek's solution is excellent, covering multiple implementations with proper error handling, documentation, and performance considerations.

## Synthesis Metadata
- DeepSeek Tokens: 1478
- DeepSeek Cost: $0.0004
- Claude Tokens: 3014
- Claude Cost: $0.0244
- Total Cost: $0.0248
