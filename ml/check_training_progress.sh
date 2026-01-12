#!/bin/bash
# Quick script to check training progress

echo "=== Training Progress ==="
echo "Models completed: $(ls -d ml/models_all_categories_improved/*/ 2>/dev/null | wc -l | tr -d ' ') / 500"
echo ""
echo "Recent progress:"
tail -20 ml/training_log_all_categories.txt 2>/dev/null | grep -E "(Dataset:|Normalized MAE)" | tail -10
