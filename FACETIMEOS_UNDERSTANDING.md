# Understanding FaceTimeOS for Pi Integration

## TL;DR

**The Pi integration is already correctly implemented!** FaceTimeOS has a `/pi_task` endpoint that works perfectly for the Pi use case. You don't need iMessage or FaceTime features.

## Original FaceTimeOS Design

FaceTimeOS was designed to control a Mac via **three different input methods**:

### 1. iMessage (Text Messages)
```
User sends iMessage → imessage_bridge.py polls database → main.py → Agent-S
```
- **Trigger**: User texts Mac
- **Use case**: Remote control via text
- **Status**: ❌ Not needed for Pi

### 2. FaceTime (Voice Calls)
```
User calls Mac → call.py captures audio → VAD → main.py → Agent-S → TTS → FaceTime
```
- **Trigger**: User calls Mac via FaceTime
- **Use case**: Voice control during call
- **Status**: ❌ Not needed for Pi

### 3. Pi Task (HTTP API) ✅
```
Pi agent → HTTP POST /pi_task → main.py → Agent-S → Response
```
- **Trigger**: Pi agent decides task needs laptop
- **Use case**: Pi voice assistant delegates GUI tasks
- **Status**: ✅ Already implemented!

## How Pi Integration Works

### Decision Flow

```
User speaks to Pi
    ↓
STT transcribes
    ↓
Intent Classifier analyzes
    ↓
Is it a laptop_action?
    ├─ NO → Handle locally (weather, news, search, QA)
    └─ YES → Send to /pi_task endpoint
                ↓
            Agent-S executes on Mac
                ↓
            Response back to Pi
```

### Intent Classification

The Pi agent uses **keyword matching** to decide when to use the laptop:

```python
# Keywords that trigger laptop_action:
"open", "close", "launch", "safari", "browser", 
"mail", "email", "click", "type", "laptop", "mac"
```

**Example:**
- "Open Safari" → `laptop_action` → Send to `/pi_task`
- "What's the weather?" → `weather` → Handle locally
- "Search for Python" → `search` → Handle locally

### The Bridge: `/pi_task` Endpoint

This is the **only** FaceTimeOS component you need:

**Location**: `FaceTimeOS/backend/main.py` (lines 714-1000)

**What it does:**
1. Receives HTTP POST from Pi with task description
2. Forwards to Agent-S `/api/chat`
3. Polls Agent-S for completion (every 2 seconds)
4. Captures screenshot if requested
5. Returns result to Pi

**Request Format:**
```json
{
  "task_id": "unique-id",
  "user_text": "Open Safari",
  "mode": "gui_task",
  "options": {"send_screenshot": true}
}
```

**Response Format:**
```json
{
  "task_id": "unique-id",
  "status": "done",
  "message": "Task completed: Open Safari",
  "screenshot_url": "http://laptop:8000/screenshots/xyz.png"
}
```

## What You DON'T Need

### ❌ imessage_bridge.py
- **Purpose**: Polls iMessage database for incoming messages
- **Why not needed**: Pi uses HTTP, not iMessage
- **Action**: Ignore this file

### ❌ call.py
- **Purpose**: Captures FaceTime audio, VAD, streams to main.py
- **Why not needed**: Pi handles voice locally, doesn't need FaceTime
- **Action**: Ignore this file

### ⚠️ Frontend (Optional)
- **Purpose**: Electron UI to monitor Agent-S activity
- **Why optional**: Nice to have for debugging, but not required
- **Action**: Can start with `npm start` if you want monitoring

## What You DO Need

### ✅ main.py (Backend)
- **Purpose**: HTTP server with `/pi_task` endpoint
- **Status**: Already working!
- **Action**: Just start it: `uv run python main.py`

### ✅ Agent-S
- **Purpose**: GUI automation agent that executes tasks
- **Status**: Working (but has formatting issues)
- **Action**: Start with `./run_gemini.sh` or `./run_claude_sonnet_4_5.sh`

### ✅ Pi Agent Code
- **Files**: `main.py`, `utils/intent_classifier.py`, `utils/laptop_client.py`
- **Status**: Already implemented!
- **Action**: Just run `python3 main.py`

## Current Status

### ✅ Working Components

1. **Pi → Backend Communication**
   - HTTP POST to `/pi_task` works
   - Error handling and timeouts work
   - Screenshot download works

2. **Backend → Agent-S Communication**
   - Task forwarding works
   - Polling mechanism works
   - Status detection works

3. **Task Execution**
   - Simple tasks complete successfully
   - Complex tasks work but may be slow

### ⚠️ Known Issues

1. **Agent-S Formatting Errors**
   - Sometimes generates wrong action format
   - Causes 3 retry attempts (20-60s delay)
   - See `SYSTEM_FAILURE_ANALYSIS.md` for details

2. **Task Timeouts**
   - Some tasks get stuck in retry loops
   - Backend correctly detects and logs this

## Key Insight

**The architecture is already correct!** 

FaceTimeOS was designed with multiple input methods in mind. The `/pi_task` endpoint was specifically added for this use case. You don't need to modify anything - just:

1. Start Agent-S
2. Start backend (`main.py`)
3. Run Pi agent
4. It works!

The only "issue" is Agent-S formatting errors, which are a known problem with Gemini and don't affect the architecture.

## Comparison: Original vs Pi Integration

### Original FaceTimeOS Flow
```
User → iMessage/FaceTime → Bridge → main.py → Agent-S
```

### Pi Integration Flow
```
User → Pi Voice → Intent Classifier → /pi_task → main.py → Agent-S
```

**Key Difference**: 
- Original: External trigger (iMessage/FaceTime)
- Pi: Internal trigger (Pi agent decides)

**Same Backend**: Both use `main.py` and Agent-S

## Files to Understand

### Must Read
1. `FACETIMEOS_PI_INTEGRATION.md` - This document
2. `FaceTimeOS/backend/main.py` (lines 714-1000) - `/pi_task` endpoint
3. `utils/laptop_client.py` - Pi HTTP client
4. `utils/intent_classifier.py` - Decision logic

### Optional
5. `FaceTimeOS/README.md` - Original FaceTimeOS docs
6. `SYSTEM_FAILURE_ANALYSIS.md` - Known issues
7. `QUICK_FIX_GUIDE.md` - Troubleshooting

### Ignore (Not Needed)
- `FaceTimeOS/backend/imessage_bridge.py`
- `FaceTimeOS/backend/call.py`
- `FaceTimeOS/backend/AUDIO_STREAMING_ARCHITECTURE.md`
- `FaceTimeOS/backend/VAD_ARCHITECTURE.md`

## Summary

**Question**: How does FaceTimeOS work and what needs to change for Pi?

**Answer**: 
- FaceTimeOS has 3 input methods (iMessage, FaceTime, Pi Task)
- Pi integration uses the **Pi Task** method (HTTP `/pi_task` endpoint)
- **Nothing needs to change** - it's already implemented!
- The trigger is the Pi agent's intent classifier (not "call me")
- When Pi detects `laptop_action` intent, it sends to `/pi_task`
- Backend forwards to Agent-S, which executes on Mac
- Result comes back to Pi

**The system is working as designed.** The only issues are Agent-S formatting errors, which are documented and don't affect the architecture.

