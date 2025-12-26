#!/bin/bash

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
# Path to your Blender executable
BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"

# Path to your Python script
SCRIPT_PATH="ShapeNet_batch.py"

# List of rotation angles to process sequentially
ANGLES=(15 30)

# -----------------------------------------------------------------------------
# EXECUTION LOOP
# -----------------------------------------------------------------------------

echo "🚀 Starting Sequential Batch Processing..."
echo "=========================================="

for angle in "${ANGLES[@]}"; do
    echo ""
    echo "------------------------------------------"
    echo "▶️  Processing Angle: $angle°"
    echo "------------------------------------------"
    
    # Execute Blender in background mode (-b) with the python script (-P)
    "$BLENDER_PATH" -b -P "$SCRIPT_PATH" -- "$angle"
    
    # Check if the previous command was successful
    if [ $? -eq 0 ]; then
        echo "✅ Angle $angle° completed successfully."
    else
        echo "❌ Angle $angle° failed."
        # Optional: exit 1 # Uncomment if you want the whole script to stop on error
    fi
    
    echo "------------------------------------------"
done

echo ""
echo "🎉 All batches finished."
