# Testing Agent Parameter Control

## Overview

A parameter has been added to control whether the testing agent runs when executing a single issue. This allows you to skip testing for faster iterations or when tests aren't needed.

## Configuration

### Environment Variable

Set the `ENABLE_TESTING` environment variable:

```bash
# Enable testing (default)
export ENABLE_TESTING=true

# Disable testing
export ENABLE_TESTING=false
```

### Default Behavior

- **Default**: `true` (testing enabled)
- If not set, testing will run by default
- Valid values: `true`, `1`, `yes` (case-insensitive) = enabled
- Any other value = disabled

## Usage

### Via Environment Variable

```bash
# Run with testing enabled (default)
python automated_crew.py --issue 123

# Run with testing disabled
ENABLE_TESTING=false python automated_crew.py --issue 123
```

### In .env File

Add to your `.env` file:

```env
# Enable testing
ENABLE_TESTING=true

# Or disable testing
ENABLE_TESTING=false
```

## Function Parameters

The parameter is also available as a function parameter:

```python
# Enable testing
apply_implementation(result, issue_number, work_dir, enable_testing=True)

# Disable testing
apply_implementation(result, issue_number, work_dir, enable_testing=False)

# Use environment variable (default)
apply_implementation(result, issue_number, work_dir)  # Uses ENABLE_TESTING env var
```

## Behavior

### When Testing is Enabled (`ENABLE_TESTING=true`)

1. After code changes are applied
2. Testing phase starts
3. Tester agent executes tests
4. Test results saved to implementation plan
5. Test status displayed in console

**Console output:**
```
======================================================================
🧪 TESTING PHASE
======================================================================
🚀 Starting test execution...
...
✅ Tests PASSED - Code changes verified successfully
```

### When Testing is Disabled (`ENABLE_TESTING=false`)

1. After code changes are applied
2. Testing phase is skipped
3. Message displayed: "Testing skipped"

**Console output:**
```
ℹ️  Testing skipped (ENABLE_TESTING=false or enable_testing=False)
```

## Examples

### Example 1: Quick Iteration (No Testing)

```bash
# Fast iteration without running tests
ENABLE_TESTING=false python automated_crew.py --issue 456
```

### Example 2: Full Pipeline (With Testing)

```bash
# Complete pipeline with testing
ENABLE_TESTING=true python automated_crew.py --issue 789
# or just (default)
python automated_crew.py --issue 789
```

### Example 3: Batch Processing

```bash
# Process multiple issues without testing
export ENABLE_TESTING=false
python automated_crew.py --max-issues 5
```

## Implementation Details

### Functions Modified

1. **`apply_implementation()`**
   - Added `enable_testing: bool = None` parameter
   - Checks environment variable if parameter is None
   - Skips testing phase if disabled

2. **`process_issue()`**
   - Added `enable_testing: bool = None` parameter
   - Passes parameter to `apply_implementation()`

### Code Flow

```
process_issue()
  └─> apply_implementation()
       └─> Check enable_testing parameter
            ├─> If True: Run tests
            └─> If False: Skip tests
```

## Use Cases

### When to Disable Testing

- **Fast prototyping**: Quick iterations without waiting for tests
- **Code review**: When you want to review code before testing
- **Debugging**: When tests are failing and you want to focus on code
- **Performance**: When test execution is slow and not needed

### When to Enable Testing

- **Production changes**: Always test before committing
- **CI/CD pipeline**: Automated testing in workflows
- **Quality assurance**: Ensure code works correctly
- **Regression prevention**: Catch issues early

## Notes

- Testing parameter applies to both main issues and sub-issues
- If testing is disabled, no test results are saved to the implementation plan
- The testing agent is still created, but not executed when disabled
- This only affects the testing phase, not code generation or patch application
