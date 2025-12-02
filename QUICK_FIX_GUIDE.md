# Quick Fix Guide for FaceTimeOS Issues

## Current Status Summary

### ✅ What's Working
- Backend server (port 8000) ✅
- Agent-S server (port 8001) ✅  
- Basic task routing ✅
- Simple tasks like "Say hello" complete ✅

### ❌ What's Failing
1. **Agent-S Response Formatting** - Gemini generates wrong action format
2. **Gemini API Timeouts** - Notification summaries timing out
3. **Tasks Getting Stuck** - Complex tasks hang for 30-60+ seconds
4. **Frontend Not Running** - UI not started

## Immediate Actions

### 1. Start the Frontend (5 minutes)

```bash
cd FaceTimeOS/frontend
npm install  # If not already done
npm start
```

This will:
- Start Vite dev server on port 5180
- Launch Electron app
- Provide UI to monitor Agent-S activity

**Note:** The frontend connects to backend on `http://localhost:8000` by default.

### 2. Check Agent-S Logs for Formatting Errors

Watch for these patterns in Agent-S logs:
```
Response formatting error on attempt X for gemini-2.5-pro
Incorrect code: The agent action must be a valid function
```

**What to look for:**
- Tasks that should use `agent.done()` but generate `agent.call_code_agent()`
- Tasks retrying 3 times before succeeding/failing

### 3. Monitor Backend for Stuck Tasks

Backend will log:
```
⚠️ Agent-S appears stuck (no state change for 30s)
```

**Action:** If you see this, check Agent-S terminal for formatting errors.

## Understanding the Errors

### Error: "Incorrect code: The agent action must be a valid function"

**What it means:**
- Agent-S (Gemini) generated code like `agent.call_code_agent("Say hello")`
- But for simple tasks, it should use `agent.done()` or `agent.open("Safari")`

**Why it happens:**
- Gemini doesn't understand when to use which action
- The prompt may not be clear enough
- `call_code_agent` is for code/data tasks, not GUI tasks

**Available Actions:**
- `agent.open("AppName")` - Open applications
- `agent.type(text="...")` - Type text
- `agent.scroll(...)` - Scroll elements
- `agent.done()` - Complete task
- `agent.fail()` - Fail task
- `agent.call_code_agent()` - For code/data tasks only

### Error: "Gemini API Read timed out"

**What it means:**
- Gemini API took longer than 4 seconds to respond
- This is for notification summaries (non-critical)

**Impact:**
- Log spam
- Missing notification summaries
- Does NOT block core functionality

**Fix:**
- Can be ignored (non-critical)
- Or increase timeout in Agent-S config

## Test Results Interpretation

### ✅ Passing Tests
- Backend Connection
- Agent-S Connection  
- /pi_task Endpoint
- Response Format
- Error Handling

### ⏱️ Timing Out Tests
- Vision Capability - Task stuck in formatting retry
- Task with Screenshot - "Open Safari" task stuck

**What to do:**
- Check Agent-S logs for formatting errors
- Wait longer (tasks may complete after 30-60s)
- Or interrupt and check what Agent-S is doing

## Recommended Next Steps

### Priority 1: Immediate
1. ✅ Start frontend to monitor system
2. ✅ Review SYSTEM_FAILURE_ANALYSIS.md for full details
3. ⚠️ Monitor Agent-S logs during next test run

### Priority 2: Short-term
4. Consider switching to Claude Sonnet 4.5 (better formatting)
   ```bash
   cd FaceTimeOS/Agent-S
   ./run_claude_sonnet_4_5.sh
   ```
5. Add better error messages when formatting fails
6. Increase Gemini timeout for notifications

### Priority 3: Long-term
7. Improve Agent-S prompts for action selection
8. Add health check endpoints
9. Implement task queue management

## Quick Commands Reference

### Start All Services
```bash
# Terminal 1: Agent-S
cd FaceTimeOS/Agent-S
./run_gemini.sh  # or ./run_claude_sonnet_4_5.sh

# Terminal 2: Backend
cd FaceTimeOS/backend
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8000"
export AGENT_HOST="127.0.0.1"
export AGENT_PORT="8001"
uv run python main.py

# Terminal 3: Frontend (optional)
cd FaceTimeOS/frontend
npm start
```

### Run Tests
```bash
# Test Pi-Laptop bridge
python3 test_pi_laptop_bridge.py

# Test Agent-S capabilities
python3 test_agent_s_capabilities.py

# Test Mac client
python3 test_laptop_client_mac.py
```

## Troubleshooting

### Agent-S Not Responding
1. Check if Agent-S is running: `curl http://127.0.0.1:8001/api/state`
2. Check Agent-S logs for errors
3. Restart Agent-S

### Backend Can't Connect to Agent-S
1. Verify Agent-S is on port 8001
2. Check `AGENT_HOST` and `AGENT_PORT` env vars
3. Check firewall/network settings

### Tasks Always Timeout
1. Check Agent-S logs for formatting errors
2. Try simpler tasks first ("Say hello")
3. Consider switching to Claude model
4. Check Gemini API key/quota

### Frontend Won't Start
1. Check if port 5180 is in use: `lsof -i :5180`
2. Kill existing process if needed
3. Try `npm install` again
4. Check Node.js version (need LTS)

## Key Files to Monitor

- `FaceTimeOS/Agent-S/logs/` - Agent-S activity logs
- `FaceTimeOS/backend/main.py` - Backend logs (stdout)
- `SYSTEM_FAILURE_ANALYSIS.md` - Full analysis
- `test_pi_laptop_bridge.py` - Test script logs

## Success Indicators

✅ **System is healthy when:**
- Backend responds to `/pi_task` in < 5 seconds for simple tasks
- Agent-S completes "Say hello" in 2-5 seconds
- No formatting errors in Agent-S logs
- Frontend shows Agent-S status as "Idle" or "Running" (not stuck)

❌ **System needs attention when:**
- Tasks take > 30 seconds
- Formatting errors appear in logs
- Backend reports "Agent-S appears stuck"
- Tests timeout consistently

