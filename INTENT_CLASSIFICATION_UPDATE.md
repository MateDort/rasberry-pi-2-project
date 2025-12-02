# Intent Classification Update - LLM-Based System

## Summary

Replaced keyword-based intent classification with **LLM-based intelligent classification** using the local TinyLlama model. The system now uses the LLM to understand context and decide if a task requires GUI automation on the Mac or can be handled locally.

## Changes Made

### 1. Updated `utils/intent_classifier.py`

**Before**: Keyword matching with 4 intent types (laptop_action, weather, news, search, local_qa)

**After**: LLM-based classification with 2 intent types:
- `laptop_action` - Tasks requiring GUI automation on Mac
- `local_qa` - Questions that can be answered locally

**Key Features**:
- Uses local LLM (TinyLlama) to understand task context
- Handles complex multi-step tasks intelligently
- Fallback heuristics if LLM unavailable
- Clear system prompt explaining when to use each intent

### 2. Updated `main.py`

**Removed**:
- `_handle_weather()` - No longer needed
- `_handle_news()` - No longer needed  
- `_handle_search()` - No longer needed
- Serper client initialization

**Simplified**:
- `_process_question()` now only routes to:
  - `_handle_laptop_action()` - For GUI tasks
  - `_handle_local_qa()` - For local questions
- Passes `self.llm` to `classify_intent()` for intelligent classification

### 3. Updated `llm/llama_inference.py`

**Added**:
- `max_tokens` parameter to `generate()` method
- Allows overriding max tokens per call (useful for intent classification which only needs 1 word)

### 4. Updated Test Files

**Updated**:
- `test_laptop_client_mac.py` - Removed Serper tests, updated test cases
- `test_end_to_end.py` - Removed Serper tests, updated test cases

**Test Cases Now**:
- "go to blackboard life university and login" → `laptop_action`
- "text my girlfriend that song" → `laptop_action`
- "what is Python" → `local_qa`

## How It Works Now

### Intent Classification Flow

```
User: "go to blackboard life university and login"
    ↓
LLM receives system prompt + user text
    ↓
LLM analyzes: "This requires opening browser, navigating, typing"
    ↓
LLM responds: "laptop_action"
    ↓
Pi routes to _handle_laptop_action()
    ↓
Sends to Mac Agent-S for execution
```

### System Prompt

The LLM receives a clear prompt explaining:
- What `laptop_action` means (GUI tasks, opening apps, multi-step workflows)
- What `local_qa` means (simple questions, knowledge queries)
- Examples of each type
- Instruction to respond with only one word

### Fallback Behavior

If LLM is unavailable or fails:
- Uses simple heuristics (keyword matching)
- Common laptop indicators: "open", "go to", "login", "text", "message", etc.
- Defaults to `local_qa` if uncertain

## Benefits

1. **Handles Complex Tasks**: Understands multi-step workflows like "go to blackboard and login"
2. **Context-Aware**: Understands intent beyond keywords
3. **No Keyword Lists**: No need to maintain lists of keywords
4. **Uses Existing LLM**: Leverages the already-loaded TinyLlama model
5. **Simpler Architecture**: Only 2 intent types instead of 5

## Example Classifications

### Laptop Actions (GUI Tasks)
- ✅ "go to blackboard life university and login" → `laptop_action`
- ✅ "text my girlfriend that song I sent to my brother" → `laptop_action`
- ✅ "open Safari" → `laptop_action`
- ✅ "go to website X and do Y" → `laptop_action`
- ✅ "open Notes app and find my password" → `laptop_action`

### Local QA (Knowledge Questions)
- ✅ "what is Python" → `local_qa`
- ✅ "what time is it" → `local_qa`
- ✅ "what is the weather" → `local_qa` (can be answered with info)
- ✅ "explain how X works" → `local_qa`

## Testing

### Without LLM (Fallback)
```bash
python3 test_laptop_client_mac.py
# Uses heuristics - still works but less accurate
```

### With LLM (Production)
```bash
python3 main.py
# Uses LLM for intelligent classification
```

## Migration Notes

### Removed Features
- Weather API integration (Serper)
- News API integration (Serper)
- Search API integration (Serper)

**Note**: These can still be handled by the local LLM in `local_qa` mode if the user asks questions about weather/news/search topics.

### Configuration
No changes needed to `config.yaml` - the LLM configuration is already there and will be used automatically.

## Next Steps

1. **Test the new system**:
   ```bash
   python3 main.py
   # Try: "go to blackboard and login"
   # Try: "what is Python"
   ```

2. **Monitor LLM performance**:
   - Check if TinyLlama correctly classifies complex tasks
   - May need to adjust system prompt if classification is inaccurate
   - Consider using a larger model if TinyLlama struggles

3. **Fine-tune if needed**:
   - Adjust `INTENT_CLASSIFICATION_PROMPT` in `intent_classifier.py`
   - Add more examples to the prompt
   - Adjust temperature/max_tokens for classification calls

## Files Changed

1. ✅ `utils/intent_classifier.py` - Complete rewrite
2. ✅ `main.py` - Simplified routing, removed handlers
3. ✅ `llm/llama_inference.py` - Added max_tokens parameter
4. ✅ `test_laptop_client_mac.py` - Updated tests
5. ✅ `test_end_to_end.py` - Updated tests

## Backward Compatibility

- ✅ Old code that calls `classify_intent(text)` without LLM will use fallback heuristics
- ✅ Test files work without LLM (use fallback)
- ✅ Production code requires LLM for best results

The system is now ready to handle complex tasks intelligently!

