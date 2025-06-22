"""Complex Python sample for testing."""

import asyncio
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Person:
    """Person data class."""
    name: str
    age: int
    email: Optional[str] = None
    
    def __post_init__(self):
        if self.age < 0:
            raise ValueError("Age must be non-negative")


class AsyncTaskManager:
    """Manages async tasks with proper error handling."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.tasks: List[asyncio.Task] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def add_task(self, coro):
        """Add a coroutine to be executed."""
        async with self._semaphore:
            task = asyncio.create_task(coro)
            self.tasks.append(task)
            return await task
    
    async def wait_all(self) -> List[Union[Exception, any]]:
        """Wait for all tasks to complete."""
        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        return results


def fibonacci(n: int) -> int:
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


async def fetch_data(url: str, retry_count: int = 3) -> dict:
    """Fetch data with retry logic."""
    for attempt in range(retry_count):
        try:
            # Simulated async operation
            await asyncio.sleep(0.1)
            return {"url": url, "data": "sample"}
        except Exception as e:
            if attempt == retry_count - 1:
                raise
            await asyncio.sleep(2 ** attempt)


# List comprehension and generator examples
squares = [x**2 for x in range(10) if x % 2 == 0]
generator = (x for x in range(100) if x % 3 == 0)

# Dictionary comprehension
word_lengths = {word: len(word) for word in ["hello", "world", "python"]}

# Complex lambda
process = lambda x: x**2 if x > 0 else -x**2

# Decorator
def timing_decorator(func):
    """Decorator to time function execution."""
    async def wrapper(*args, **kwargs):
        start = asyncio.get_event_loop().time()
        result = await func(*args, **kwargs)
        end = asyncio.get_event_loop().time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper


@timing_decorator
async def main():
    """Main async function."""
    manager = AsyncTaskManager(max_concurrent=5)
    
    # Create some tasks
    urls = [f"https://api.example.com/data/{i}" for i in range(10)]
    
    tasks = []
    for url in urls:
        task = manager.add_task(fetch_data(url))
        tasks.append(task)
    
    results = await manager.wait_all()
    
    # Error handling
    try:
        person = Person("John", 30, "john@example.com")
        print(f"Created person: {person}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Pattern matching (Python 3.10+)
    match person.age:
        case age if age < 18:
            status = "minor"
        case age if age < 65:
            status = "adult"
        case _:
            status = "senior"
    
    return results


if __name__ == "__main__":
    asyncio.run(main())