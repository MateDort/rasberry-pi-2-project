#!/usr/bin/env bash
# Run all component tests in sequence

echo "🧪 Running All Component Tests"
echo "================================"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo ""

# Check if Agent-S is running
echo "   Checking Agent-S (port 8001)..."
if curl -s http://127.0.0.1:8001/api/state > /dev/null 2>&1; then
    echo "   ✅ Agent-S is running"
else
    echo "   ⚠️  Agent-S is NOT running"
    echo "   → Start it with: cd FaceTimeOS/Agent-S && ./run_claude_sonnet_4_5.sh"
    echo "   → Or use Gemini: cd FaceTimeOS/Agent-S && ./run_gemini.sh"
    echo ""
    read -p "   Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Exiting..."
        exit 1
    fi
fi

# Check if backend is running
echo "   Checking Backend (port 8000)..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend is running"
else
    echo "   ⚠️  Backend is NOT running"
    echo "   → Start it with: cd FaceTimeOS/backend && uv run python main.py"
    echo ""
    read -p "   Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Exiting..."
        exit 1
    fi
fi

echo ""
echo "================================"
echo ""

echo "1️⃣  Testing GUI Automation (Mouse, Keyboard, Screen)..."
echo "   This will test if your Mac can be controlled programmatically"
python3 test_gui_automation.py

echo ""
echo "2️⃣  Testing Agent-S Capabilities (Vision, Task Understanding)..."
echo "   This will test if Agent-S can see and understand tasks"
python3 test_agent_s_capabilities.py

echo ""
echo "3️⃣  Testing Pi ↔ Laptop Bridge (Communication)..."
echo "   This will test if the Pi can communicate with the laptop backend"
python3 test_pi_laptop_bridge.py

echo ""
echo "✅ All tests completed!"
echo ""
echo "📋 Summary:"
echo "   - GUI Automation: Tests basic Mac control capabilities"
echo "   - Agent-S: Tests AI agent vision and task understanding"
echo "   - Bridge: Tests communication between Pi and laptop"

