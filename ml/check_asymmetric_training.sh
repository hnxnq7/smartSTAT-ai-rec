#!/bin/bash
# Quick script to check asymmetric training progress

echo "=== Asymmetric Training Progress ==="
echo "Models completed: $(ls -d ml/models_asymmetric_all/*/ 2>/dev/null | wc -l | tr -d ' ') / 500"
echo ""
echo "Recent progress:"
tail -20 ml/training_log_asymmetric.txt 2>/dev/null | grep -E "(Dataset:|Normalized MAE|Error)" | tail -10
