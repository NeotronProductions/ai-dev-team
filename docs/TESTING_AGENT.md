# Testing Agent Integration

## Overview

A **QA Tester agent** has been added to the CrewAI crew that automatically executes tests after code patches are applied. This agent can run automated tests, create test data, and verify functionality including performance and accessibility testing.

## What Was Added

### 1. **Tester Agent**
- **Role**: QA Tester
- **Capabilities**:
  - Executes automated tests (unit, integration, performance)
  - Creates test data (e.g., 100+ sessions for performance testing)
  - Verifies accessibility (screen reader compatibility)
  - Reports detailed test results

### 2. **ExecuteCommandTool**
- Custom tool that allows the tester agent to run shell commands
- Executes commands in the project working directory
- Supports test frameworks: npm, pytest, jest, vitest, go test, etc.
- Includes timeout protection (5 minutes)

### 3. **Automatic Test Execution**
- Tests run automatically after a patch is successfully applied
- Test results are saved to the implementation plan
- Test framework is auto-detected from project files

## How It Works

1. **Code Generation**: The crew generates code (Product Manager → Architect → Developer → Reviewer)
2. **Patch Application**: The patch is applied to the repository
3. **Test Execution**: If patch is applied successfully, the Tester agent runs:
   - Detects test framework (npm, pytest, etc.)
   - Executes appropriate test commands
   - Creates test scenarios for specific requirements (e.g., "100+ sessions", "scroll performance")
   - Verifies accessibility features (screen reader testing)
   - Generates a detailed test report

## Test Scenarios Supported

The tester agent can handle:

- **Performance Testing**: Creates test data (e.g., 100+ sessions) and verifies scroll performance
- **Accessibility Testing**: Verifies screen reader compatibility
- **Automated Tests**: Runs unit tests, integration tests
- **Manual Test Scenarios**: Executes test scenarios mentioned in the issue or implementation plan

## Example Test Execution

When the tester agent runs, it will:

1. Detect the test framework:
   ```bash
   # For npm/JavaScript projects
   npm test
   
   # For Python projects
   pytest
   
   # For Go projects
   go test ./...
   ```

2. Execute specific test scenarios:
   - If issue mentions "100+ sessions": Creates test data and verifies performance
   - If issue mentions "screen reader": Tests accessibility features
   - Runs any custom test scenarios from the implementation plan

3. Report results:
   - Test pass/fail status
   - Any issues or failures
   - Recommendations for fixes

## Test Results

Test results are automatically:
- Printed to console during execution
- Saved to the implementation plan file (`implementations/issue_<N>_plan.md`)
- Included in the "Test Results" section

## Configuration

The testing agent uses the same LLM configuration as other agents:
- Defaults to Ollama (qwen2.5-coder:3b) if available
- Falls back to OpenAI (gpt-4o-mini) if Ollama is not available
- Can be forced to use OpenAI with `FORCE_OPENAI=true`

## Disabling Testing

If you want to skip test execution, you can modify `run_tests_after_patch()` in `automated_crew.py` to return early, or comment out the test execution call in `apply_implementation()`.

## Manual Testing

The tester agent can also help with manual testing scenarios. For example:

- **100+ Sessions Test**: The agent can create a script to generate 100+ test sessions and verify scroll performance
- **Screen Reader Test**: The agent can check for accessibility attributes and verify screen reader compatibility

## Troubleshooting

### Tests Not Running
- Check that the patch was successfully applied (`has_changes()` returns True)
- Verify the test framework is detected correctly
- Check console output for error messages

### Test Timeout
- Commands have a 5-minute timeout
- For longer tests, you may need to modify the timeout in `ExecuteCommandTool`

### Tool Not Available
- Ensure `crewai_tools` is installed: `pip install crewai-tools`
- Check that `BaseTool` can be imported from `crewai_tools`

## Future Enhancements

Potential improvements:
- Support for CI/CD integration
- Test coverage reporting
- Parallel test execution
- Custom test script generation
- Integration with test result visualization tools
