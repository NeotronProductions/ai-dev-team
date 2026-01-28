# CrewAI Tracing Guide

Should you enable tracing? Here's what you need to know.

## What is Tracing?

CrewAI tracing provides detailed monitoring and debugging information about:
- **Agent activities** - What each agent is doing
- **Task execution** - Step-by-step task progress
- **LLM calls** - API requests and responses
- **Performance metrics** - Timing and resource usage
- **Decision paths** - How agents make decisions

## Pros and Cons

### ✅ Benefits

1. **Better Debugging**
   - See exactly what each agent is doing
   - Identify where issues occur
   - Understand agent decision-making

2. **Performance Insights**
   - See which tasks take longest
   - Identify bottlenecks
   - Optimize agent workflows

3. **Transparency**
   - Full visibility into AI operations
   - Track all LLM interactions
   - Audit trail for compliance

4. **Troubleshooting**
   - Easier to diagnose failures
   - See intermediate results
   - Understand why agents made specific choices

### ⚠️ Drawbacks

1. **Performance Overhead**
   - May slow down execution slightly
   - Additional logging/processing
   - More data to store

2. **Verbose Output**
   - More console output
   - Can be overwhelming
   - Harder to see important messages

3. **Storage**
   - Traces need to be stored
   - Can accumulate over time
   - May require cleanup

## When to Use Tracing

### ✅ Enable Tracing When:

- **Debugging issues** - Something isn't working as expected
- **First-time setup** - Understanding how the crew works
- **Optimizing performance** - Finding slow operations
- **Development/Testing** - Iterating on crew configuration
- **Complex issues** - Large user stories with many sub-tasks

### ❌ Skip Tracing When:

- **Production runs** - Regular automated processing
- **Simple tasks** - Straightforward issues
- **Performance critical** - Need maximum speed
- **Batch processing** - Processing many issues

## How to Enable Tracing

### Option 1: Environment Variable (Recommended)

Add to `~/ai-dev-team/.env`:
```env
CREWAI_TRACING_ENABLED=true
```

### Option 2: Command Line

```bash
export CREWAI_TRACING_ENABLED=true
python3 scripts/automated_crew.py owner/repo 1 550
```

### Option 3: In Code

Modify `automated_crew.py`:
```python
crew = Crew(
    agents=[product, architect, developer, reviewer],
    tasks=[product_task, architect_task, developer_task, review_task],
    verbose=True,
    tracing=True  # Add this
)
```

### Option 4: CrewAI CLI

```bash
crewai traces enable
```

## Recommended Approach

### For US-001 (Complex User Story)

**Enable tracing** to see how it handles all sub-tasks:

```bash
export CREWAI_TRACING_ENABLED=true
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550 --openai
```

This will help you:
- See how agents coordinate
- Understand the implementation approach
- Debug any issues with sub-task handling

### For Regular Processing

**Disable tracing** for faster execution:

```bash
# Don't set CREWAI_TRACING_ENABLED
python3 scripts/automated_crew.py owner/repo 5
```

### For Troubleshooting

**Enable tracing** when debugging:

```bash
export CREWAI_TRACING_ENABLED=true
python3 scripts/automated_crew.py owner/repo 1 550
```

## What You'll See

With tracing enabled, you'll see:

1. **Agent Activity Logs**
   ```
   [Product Manager] Starting task...
   [Product Manager] Analyzing issue...
   [Product Manager] Generating user story...
   ```

2. **Task Progress**
   ```
   Task 1/4: Product Manager - In Progress
   Task 2/4: Architect - Waiting
   ```

3. **LLM Interactions**
   ```
   LLM Call: OpenAI API
   Request: [prompt details]
   Response: [response details]
   ```

4. **Performance Metrics**
   ```
   Task completed in 45.2s
   Total execution time: 180.5s
   ```

## Viewing Traces

Traces are typically stored and can be viewed via:

1. **CrewAI Dashboard** (if available)
2. **Trace files** in the project directory
3. **Console output** (verbose mode)

## Best Practice Recommendation

### For Your Use Case

**Enable tracing for:**
- ✅ First run of US-001 (to understand the process)
- ✅ When debugging timeout issues
- ✅ When troubleshooting incomplete outputs
- ✅ When optimizing crew configuration

**Disable tracing for:**
- ❌ Regular batch processing
- ❌ Simple, straightforward issues
- ❌ Production automation

### Suggested Workflow

1. **First time processing US-001:**
   ```bash
   export CREWAI_TRACING_ENABLED=true
   python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550 --openai
   ```

2. **Review the traces** to understand the process

3. **Disable tracing** for subsequent runs:
   ```bash
   unset CREWAI_TRACING_ENABLED
   python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 551
   ```

## Performance Impact

Tracing typically adds:
- **5-10% overhead** in execution time
- **Minimal** impact on API costs
- **Moderate** increase in console output

For complex tasks like US-001, the insights are usually worth the small overhead.

## Summary

**Should you enable tracing?**

- **Yes, for US-001** - Complex task, first time, worth understanding
- **Yes, for debugging** - When things go wrong
- **No, for regular runs** - Keep it simple and fast

**Quick enable for next run:**
```bash
export CREWAI_TRACING_ENABLED=true
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550 --openai
```

---

**Related Documentation:**
- [TERMINAL_COMMANDS.md](TERMINAL_COMMANDS.md) - How to run the crew
- [TIMEOUT_TROUBLESHOOTING.md](TIMEOUT_TROUBLESHOOTING.md) - Debugging timeouts
- [OUTPUT_TROUBLESHOOTING.md](OUTPUT_TROUBLESHOOTING.md) - Debugging outputs

---

**Last Updated:** January 2025
