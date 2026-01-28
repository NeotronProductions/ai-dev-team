# OpenAI Token Limit Error Fix

## Error Explanation

**Error Code 429 - Rate Limit Exceeded (Tokens Per Minute)**

The error means:
- **Limit**: 200,000 tokens per minute for `gpt-4o-mini`
- **Requested**: 466,675 tokens (2.3x over the limit!)
- **Problem**: Your request is too large

## Why This Happens

The script loads a lot of context:
1. **PROJECT_CONTEXT.md** - No size limit (could be huge!)
2. **README.md** - First 2000 chars
3. **Code examples** - Up to 5 files, 1500 chars each
4. **Agent backstories** - Multiple long descriptions
5. **Task descriptions** - Full issue content + context
6. **All combined** = Over 466k tokens!

## Solutions Applied

### ✅ Fix 1: Limited PROJECT_CONTEXT.md Size
- **Before**: No limit (could be 100k+ characters)
- **After**: Limited to 10,000 characters (~2,500 tokens)
- **Location**: `get_project_context()` function

### ✅ Fix 2: Reduced Code Examples
- **Before**: 5 files × 1,500 chars = 7,500 chars
- **After**: 3 files × 1,000 chars = 3,000 chars
- **Savings**: ~4,500 characters (~1,125 tokens)

### 📝 Additional Recommendations

#### Option 1: Use a Model with Higher Limits
Switch to `gpt-4o` which has 2,000,000 TPM limit:

```python
llm_model = LLM(model="gpt-4o", temperature=0.7)
```

#### Option 2: Reduce Agent Backstory Length
Shorten the backstories in `create_implementation_crew()`:

```python
# Instead of long backstories, use concise ones:
backstory="Expert QA engineer. Runs tests and reports results."
```

#### Option 3: Split Large Tasks
Break large issues into smaller sub-tasks that can be processed separately.

#### Option 4: Use Token Limit Utilities
Use the `token_limit_fix.py` module to automatically truncate context:

```python
from token_limit_fix import reduce_context_size, get_safe_context_size

# Get safe context size for your model
max_tokens = get_safe_context_size("gpt-4o-mini")  # Returns ~100k tokens

# Reduce context if needed
context = reduce_context_size(context, max_tokens=max_tokens)
```

#### Option 5: Wait and Retry
If you hit the limit, wait 1 minute and retry. The limit resets every minute.

## Quick Fix Commands

### Check Current Token Usage
```python
# Estimate tokens in your context
from token_limit_fix import estimate_tokens
context = get_project_context(work_dir)
tokens = estimate_tokens(context)
print(f"Context tokens: {tokens:,}")
```

### Manually Limit PROJECT_CONTEXT.md
If your `PROJECT_CONTEXT.md` is very large, consider:
1. Split it into multiple smaller files
2. Keep only the most essential information
3. Move detailed docs to a separate location

## Verification

After applying fixes, you should see:
- ✅ No more 429 errors
- ✅ Requests complete successfully
- ✅ Context size under 150k tokens (safe for gpt-4o-mini)

## Model Token Limits Reference

| Model | Tokens Per Minute (TPM) |
|-------|------------------------|
| gpt-4o-mini | 200,000 |
| gpt-4o | 2,000,000 |
| gpt-4-turbo | 2,000,000 |
| gpt-3.5-turbo | 2,000,000 |

## Notes

- **1 token ≈ 4 characters** (rough estimate)
- The limit is **per minute**, not per request
- If you make multiple requests quickly, they all count toward the same minute
- Consider adding delays between requests if processing multiple issues
