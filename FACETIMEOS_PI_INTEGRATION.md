# FaceTimeOS Pi Integration Guide

## Overview

FaceTimeOS is designed to control a Mac via multiple input methods. For the Pi integration, we only need **one** of these methods: the `/pi_task` HTTP endpoint. The other methods (iMessage, FaceTime) are not needed.

## FaceTimeOS Architecture

### Original Design (3 Input Methods)

```
┌─────────────────────────────────────────────────────────────┐
│                    FaceTimeOS Backend (main.py)              │
│                    Port 8000                                 │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
         │                    │                    │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │         │         │         │         │         │
iMessage  FaceTime   Pi Task  (Frontend)  (Other)
Bridge     call.py   /pi_task    UI        Services
```

### 1. iMessage Trigger (NOT NEEDED for Pi)
- **File**: `FaceTimeOS/backend/imessage_bridge.py`
- **How it works**: 
  - Polls macOS Messages database (`~/Library/Messages/chat.db`)
  - Detects new incoming messages
  - Forwards to `main.py` → Agent-S
- **Trigger**: User sends iMessage to Mac
- **Use case**: Remote control via text messages
- **Status**: ❌ Not needed for Pi integration

### 2. FaceTime Trigger (NOT NEEDED for Pi)
- **File**: `FaceTimeOS/backend/call.py`
- **How it works**:
  - Captures audio from FaceTime call (via BlackHole virtual audio device)
  - Voice Activity Detection (VAD) detects speech
  - Streams audio chunks via WebSocket to `main.py`
  - `main.py` transcribes → Agent-S → TTS response → back to FaceTime
- **Trigger**: User calls Mac via FaceTime
- **Use case**: Voice control during FaceTime call
- **Status**: ❌ Not needed for Pi integration

### 3. Pi Task Endpoint (✅ THIS IS WHAT WE USE)
- **File**: `FaceTimeOS/backend/main.py` (lines 714-1000)
- **Endpoint**: `POST /pi_task`
- **How it works**:
  1. Pi agent sends HTTP POST with task description
  2. Backend forwards to Agent-S `/api/chat`
  3. Agent-S executes task on Mac
  4. Backend polls Agent-S for completion
  5. Returns result + optional screenshot to Pi
- **Trigger**: Pi agent decides task needs laptop (via intent classification)
- **Use case**: Pi voice assistant delegates GUI tasks to Mac
- **Status**: ✅ Already implemented and working!

## Current Pi Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Raspberry Pi Voice Assistant                   │
│              (main.py)                                      │
└─────────────────────────────────────────────────────────────┘
         │
         │ User speaks: "Open Safari"
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Audio Input → STT → Intent Classifier                      │
│  Intent: "laptop_action" (confidence: 0.8)                 │
└─────────────────────────────────────────────────────────────┘
         │
         │ Detected laptop_action
         ▼
┌─────────────────────────────────────────────────────────────┐
│  utils/laptop_client.py                                     │
│  send_laptop_task()                                         │
│  POST http://laptop:8000/pi_task                            │
└─────────────────────────────────────────────────────────────┘
         │
         │ HTTP POST
         ▼
┌─────────────────────────────────────────────────────────────┐
│  FaceTimeOS Backend (main.py)                               │
│  /pi_task endpoint                                          │
│  - Receives task                                            │
│  - Forwards to Agent-S                                      │
│  - Polls for completion                                     │
│  - Returns result                                           │
└─────────────────────────────────────────────────────────────┘
         │
         │ HTTP POST to Agent-S
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent-S (port 8001)                                        │
│  - Receives task                                            │
│  - Executes on Mac GUI                                      │
│  - Returns completion status                                │
└─────────────────────────────────────────────────────────────┘
         │
         │ Result
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Pi receives response                                       │
│  "Task completed: Open Safari"                            │
│  + Optional screenshot URL                                  │
└─────────────────────────────────────────────────────────────┘
```

## What Works vs What Doesn't

### ✅ What Works (Already Implemented)

1. **Pi → Backend Communication**
   - `utils/laptop_client.py` - HTTP client for `/pi_task`
   - Intent classification routes to laptop when needed
   - Error handling and timeouts

2. **Backend → Agent-S Communication**
   - `/pi_task` endpoint forwards to Agent-S
   - Polling mechanism for task completion
   - Screenshot capture and serving

3. **Task Execution**
   - Agent-S receives tasks and executes them
   - Simple tasks work (e.g., "Say hello")
   - Complex tasks work but may be slow (formatting retry issues)

### ❌ What Doesn't Work (But Not Needed)

1. **iMessage Bridge** - Not needed, Pi uses HTTP
2. **FaceTime/call.py** - Not needed, Pi uses voice locally
3. **Frontend UI** - Optional, for monitoring only

### ⚠️ Known Issues (Need Fixing)

1. **Agent-S Response Formatting**
   - Gemini generates wrong action format sometimes
   - Causes retries and delays (20-60s instead of 2-5s)
   - See `SYSTEM_FAILURE_ANALYSIS.md` for details

2. **Task Timeouts**
   - Some tasks get stuck in formatting retry loops
   - Backend correctly detects and logs stuck tasks

## Key Files for Pi Integration

### Pi Side (Raspberry Pi)
- `main.py` - Main voice assistant loop
- `utils/intent_classifier.py` - Decides when to use laptop
- `utils/laptop_client.py` - HTTP client for `/pi_task`
- `config.yaml` - Laptop backend configuration

### Laptop Side (Mac)
- `FaceTimeOS/backend/main.py` - `/pi_task` endpoint (lines 714-1000)
- `FaceTimeOS/Agent-S/` - GUI automation agent
- `FaceTimeOS/backend/imessage_bridge.py` - NOT NEEDED
- `FaceTimeOS/backend/call.py` - NOT NEEDED
- `FaceTimeOS/frontend/` - OPTIONAL (for monitoring)

## Configuration

### Pi Config (`config.yaml`)
```yaml
laptop:
  host: "localhost"       # Use "localhost" for Mac testing
  port: 8000              # FaceTimeOS backend port
  timeout_seconds: 60     # Client timeout
```

### Laptop Config (Environment Variables)
```bash
# FaceTimeOS/backend/.env or export
SERVER_HOST="0.0.0.0"
SERVER_PORT="8000"
AGENT_HOST="127.0.0.1"
AGENT_PORT="8001"
```

## How Intent Classification Works

The Pi agent uses keyword matching to decide when to delegate to the laptop:

```python
# utils/intent_classifier.py
LAPTOP_ACTION_KEYWORDS = [
    "open", "close", "launch", "start", "run",
    "safari", "browser", "chrome",
    "mail", "email", "send email",
    "click", "type", "screenshot",
    "laptop", "mac", "computer",
    # ... more keywords
]
```

**Example:**
- User: "Open Safari"
- Intent: `laptop_action` (confidence: 0.8)
- Action: Send to `/pi_task` endpoint
- Result: Agent-S opens Safari on Mac

## What Needs to Change?

### ✅ Nothing! The Architecture is Correct

The Pi integration is **already correctly implemented**. The only issues are:
1. Agent-S formatting errors (documented in `SYSTEM_FAILURE_ANALYSIS.md`)
2. Optional: Start frontend for monitoring

### Optional Improvements

1. **Better Intent Classification**
   - Could use LLM instead of keyword matching
   - More accurate detection of when laptop is needed

2. **Error Handling**
   - Better error messages when Agent-S fails
   - Retry logic for transient failures

3. **Monitoring**
   - Start frontend to monitor Agent-S activity
   - Better logging and status reporting

## Starting the System

### Minimal Setup (Pi Integration Only)

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

# Terminal 3: Pi Agent (on Pi or Mac for testing)
python3 main.py
```

### Full Setup (With Monitoring)

```bash
# Add Terminal 4: Frontend (optional)
cd FaceTimeOS/frontend
npm start
```

**Note**: You do NOT need:
- `imessage_bridge.py` - Only for iMessage triggers
- `call.py` - Only for FaceTime triggers

## Testing the Integration

### Test Pi → Backend Communication
```bash
python3 test_pi_laptop_bridge.py
```

### Test Intent Classification
```bash
python3 test_laptop_client_mac.py
```

### Test Agent-S Directly
```bash
python3 test_agent_s_capabilities.py
```

## Summary

**Key Insight**: FaceTimeOS is already set up correctly for Pi integration!

- ✅ `/pi_task` endpoint exists and works
- ✅ Pi agent correctly routes laptop tasks
- ✅ Backend correctly forwards to Agent-S
- ⚠️ Only issue: Agent-S formatting errors (non-blocking)

**What to ignore:**
- iMessage bridge (`imessage_bridge.py`) - Not needed
- FaceTime audio (`call.py`) - Not needed
- Frontend UI - Optional for monitoring

**What to use:**
- `/pi_task` endpoint - ✅ This is the bridge!
- Intent classification - ✅ Already working
- Laptop client - ✅ Already implemented

The system is working as designed. The only improvements needed are fixing Agent-S formatting issues (see `SYSTEM_FAILURE_ANALYSIS.md`).

