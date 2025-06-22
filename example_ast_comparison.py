#!/usr/bin/env python3
"""Compare raw tree-sitter output vs mcp-code-parser filtered output."""

import asyncio

# Example Python code to parse
sample_code = """
def calculate_fibonacci(n):
    '''Calculate nth Fibonacci number'''
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""

print("=== SAMPLE CODE ===")
print(sample_code)
print("\n=== RAW TREE-SITTER OUTPUT (ALL NODES) ===")

# Simulate what raw tree-sitter would show
raw_output = """module
  function_definition
    def
    identifier: calculate_fibonacci
    parameters
      (
      identifier: n
      )
    :
    block
      expression_statement
        string: '''Calculate nth Fibonacci number'''
      if_statement
        if
        comparison_operator
          identifier: n
          <=
          integer: 1
        :
        block
          return_statement
            return
            identifier: n
      return_statement
        return
        binary_operator
          call
            identifier: calculate_fibonacci
            argument_list
              (
              binary_operator
                identifier: n
                -
                integer: 1
              )
          +
          call
            identifier: calculate_fibonacci
            argument_list
              (
              binary_operator
                identifier: n
                -
                integer: 2
              )
  expression_statement
    assignment
      identifier: result
      =
      call
        identifier: calculate_fibonacci
        argument_list
          (
          integer: 10
          )
  expression_statement
    call
      identifier: print
      argument_list
        (
        string
          f"
          interpolation
            {
            identifier: result
            }
          "
        )
"""

print(raw_output)

print("\n=== AGENT-TOOLS FILTERED OUTPUT (RELEVANT NODES ONLY) ===")

# What mcp-code-parser would show with configured filters
filtered_output = """module
  function_definition
    block
      if_statement
        comparison_operator: 'n <= 1'
      return_statement
        binary_operator: 'calculate_fibonacci(n-1) + ca...'
          call: 'calculate_fibonacci(n-1)'
          call: 'calculate_fibonacci(n-2)'
  assignment: 'result = calculate_fibonacci(10)'
    call: 'calculate_fibonacci(10)'
  call: 'print(f"Fibonacci(10) = {result}")'
"""

print(filtered_output)

print("\n=== KEY DIFFERENCES ===")
print("""
1. NOISE REDUCTION:
   - Raw: Shows every token (def, :, (, ), etc.)
   - Filtered: Shows only semantically important nodes

2. READABILITY:
   - Raw: 40+ nodes for simple function
   - Filtered: ~10 nodes focusing on structure

3. LEAF NODE VALUES:
   - Raw: Just shows node types
   - Filtered: Includes actual code snippets for context

4. USE CASE OPTIMIZATION:
   - Raw: Good for syntax highlighting, refactoring tools
   - Filtered: Better for AI agents understanding code structure

This filtering is particularly valuable for AI agents that need to:
- Understand code structure without syntax noise
- Focus on logic flow rather than punctuation
- Get a high-level view of what the code does
""")

# Now show actual mcp-code-parser usage
print("\n=== ACTUAL AGENT-TOOLS USAGE ===")

async def demo():
    from mcp_code_parser import parse_code
    
    result = await parse_code(sample_code, "python")
    
    print(f"Success: {result.success}")
    print(f"Language: {result.language}")
    print(f"Node count: {result.metadata.get('node_count', 'N/A')}")
    print(f"\nFiltered AST (first 20 lines):")
    lines = result.ast_text.split('\n')[:20]
    for line in lines:
        print(line)
    if len(result.ast_text.split('\n')) > 20:
        print("... (truncated)")

# Only run if mcp_code_parser is available
try:
    asyncio.run(demo())
except ImportError:
    print("\n(mcp_code_parser not available in environment - showing simulated output)")
    print("Success: True")
    print("Language: python")
    print("Node count: 28")
    print("\nFiltered AST (simulated):")
    print(filtered_output)