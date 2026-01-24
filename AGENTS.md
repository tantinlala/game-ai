# AI Agent Guidelines for Game-AI Development

This document provides guidance for AI coding agents working on the Game-AI codebase.

## Core Principles

### 1. Test-First Mentality
When modifying application code, **always update or add corresponding unit tests**.

**Why?** Tests serve as:
- Living documentation of expected behavior
- Regression prevention
- Contract verification for APIs
- Safety net for refactoring

### 2. Keep Tests Synchronized with Code

#### When Application Code Changes, Update Tests

**Always update tests when:**
- Changing function signatures or return types
- Modifying behavior or business logic
- Adding new features or functionality
- Fixing bugs (add test for the bug first)
- Refactoring internal implementations

**Example:**
```python
# ❌ Bad: Changed code without updating tests
# application code: changed return type from dict to bool
def save_session(name, data) -> bool:  # Was: -> dict
    return True

# test still expects old behavior
def test_save_session():
    result = save_session("test", {})
    assert result["success"] == True  # ❌ Will crash!

# ✅ Good: Updated test to match new behavior
def test_save_session():
    result = save_session("test", {})
    assert result == True  # ✅ Matches new return type
```

### 3. Add Tests to Existing Test Files

**Don't create new test files** unless you're testing a completely new module.

**Do:**
- Add new tests to `tests/test_<module_name>.py` for the module you're testing
- Group related tests together
- Follow existing naming conventions in the file

**Don't:**
- Create `test_new_feature.py` when `test_module.py` already exists
- Scatter related tests across multiple files
- Create one-off test files for specific bugs (add to appropriate existing file)

**Example:**
```python
# ✅ Good: Add to existing test_game_builder.py
def test_game_builder_handles_none_game_file():
    """Test that GameBuilder handles None game_file values."""
    ...

# ❌ Bad: Don't create test_none_handling.py
# when test_game_builder.py already exists
```

### 4. Test Edge Cases and Error Conditions

Always test:
- ✅ Happy path (expected behavior)
- ✅ Edge cases (None, empty strings, empty lists)
- ✅ Error conditions (invalid input, API failures)
- ✅ Boundary conditions (min/max values)

**Example:**
```python
def test_handles_none_value():
    """Test None doesn't crash."""
    result = process(None)
    assert result == default_value

def test_handles_empty_string():
    """Test empty string is handled."""
    result = process("")
    assert result == default_value

def test_handles_whitespace():
    """Test whitespace-only input."""
    result = process("   \n\t   ")
    assert result == default_value
```

### 5. Defensive Coding Practices

**Always handle None/null values:**
```python
# ❌ Bad: Assumes value is never None
length = len(response["game_file"])  # Crashes if None

# ✅ Good: Handle None explicitly
game_file = response.get("game_file") or ""
length = len(game_file)

# ✅ Also good: Check before using
if response.get("game_file"):
    length = len(response["game_file"])
```

**Use .get() with defaults for optional fields:**
```python
# ❌ Bad: KeyError if field missing
sources = response["sources"]

# ✅ Good: Default to empty list
sources = response.get("sources", [])
```

**Check before iterating:**
```python
# ❌ Bad: Crashes if None
for chunk in metadata.grounding_chunks:
    process(chunk)

# ✅ Good: Check first
if metadata.grounding_chunks:
    for chunk in metadata.grounding_chunks:
        process(chunk)

# ✅ Also good: Handle None explicitly
chunks = metadata.grounding_chunks
if chunks is not None:
    for chunk in chunks:
        process(chunk)
```

## Testing Standards

### Test Structure
```python
def test_function_name_scenario():
    """Brief description of what is being tested."""
    # Arrange: Set up test data and mocks
    mock_data = {...}
    
    # Act: Execute the code under test
    result = function_under_test(mock_data)
    
    # Assert: Verify expected behavior
    assert result == expected_value
```

### Test Naming Convention
- `test_<function_name>_<scenario>`
- Examples:
  - `test_save_session_with_valid_data`
  - `test_load_session_when_not_found`
  - `test_generate_response_handles_none_game_file`

### Coverage Goals
- All public functions should have tests
- All error paths should be tested
- Edge cases should be covered
- Bug fixes should include regression tests

## Common Pitfalls to Avoid

### 1. Assuming Values Are Never None
```python
# ❌ This will crash if game_file is None
print(f"Length: {len(response.get('game_file', ''))}")

# ✅ Handle None explicitly
game_file = response.get('game_file') or ''
print(f"Length: {len(game_file)}")
```

### 2. Not Testing After Changes
```python
# ❌ Changed code but didn't run tests
def save_session(name, data) -> bool:  # Changed from dict
    return True
# Commit without testing → breaks production

# ✅ Always run tests after changes
# $ pytest tests/
```

### 3. Inconsistent Return Types
```python
# ❌ Bad: Different return types based on success
def load_session(name):
    if exists(name):
        return {"data": ...}  # dict
    return None  # None

# ✅ Good: Consistent return type
def load_session(name):
    if exists(name):
        return {"success": True, "data": ...}
    return {"success": False, "error": "Not found"}
```

### 4. Not Using Type Hints
```python
# ❌ Unclear what types are expected
def process(data):
    return data.get("field")

# ✅ Clear types prevent errors
def process(data: dict) -> Optional[str]:
    return data.get("field")
```

## Workflow Checklist

When making changes:

- [ ] **Understand** the existing code and tests
- [ ] **Write** failing test(s) for new behavior (if TDD)
- [ ] **Implement** the code changes
- [ ] **Update** existing tests that are affected
- [ ] **Add** new tests for new functionality
- [ ] **Run** full test suite: `pytest tests/`
- [ ] **Verify** all tests pass
- [ ] **Check** code coverage for untested paths
- [ ] **Document** complex logic or non-obvious behavior
- [ ] **Commit** code and tests together

## Test Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_game_builder.py

# Run specific test
pytest tests/test_game_builder.py::test_function_name

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src

# Run tests that match pattern
pytest tests/ -k "handles_none"
```

## Key Takeaways

1. **Tests are code** - they need maintenance too
2. **Tests document behavior** - keep them in sync with implementation
3. **Test edge cases** - None, empty, invalid inputs matter
4. **Use existing test files** - don't create unnecessary new files
5. **Run tests before committing** - catch issues early
6. **Test the fix, not just happy path** - especially for bugs

## Resources

- Test files: `/tests/`
- Test coverage report: `pytest tests/ --cov=src --cov-report=html`
- Testing docs: `TESTING.md` (if exists)
- Bug tracking: `BUGS_FOUND_DURING_TESTING.md`
