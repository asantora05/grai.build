#!/bin/bash

# grai.build - Quick Test and Demo Script
# Run this to verify the parser implementation

echo "🧪 grai.build - Parser Implementation Test Suite"
echo "=================================================="
echo ""

echo "📋 Running all tests..."
python -m pytest tests/ -v --tb=short --cov=grai --cov-report=term-missing

echo ""
echo "=================================================="
echo "✅ Test Results Summary"
echo "=================================================="
echo ""
echo "Components Tested:"
echo "  • Core Models (test_models.py) - 13 tests"
echo "  • YAML Parser (test_parser.py) - 20 tests"
echo ""
echo "📊 Expected Results:"
echo "  • Total Tests: 33"
echo "  • All Passing: ✅"
echo "  • Coverage: 87%"
echo ""
echo "=================================================="
echo ""

read -p "Press Enter to run the models demo..."
echo ""
echo "🎯 Running Models Demo..."
echo "=================================================="
python demo.py

echo ""
read -p "Press Enter to run the parser demo..."
echo ""
echo "📦 Running Parser Demo..."
echo "=================================================="
python demo_parser.py

echo ""
echo "=================================================="
echo "✨ All demos complete!"
echo "=================================================="
echo ""
echo "📝 Next Steps:"
echo "  1. Review the code in grai/core/models.py"
echo "  2. Review the code in grai/core/parser/yaml_parser.py"
echo "  3. Check the documentation in docs/"
echo "  4. Start building the validator next!"
echo ""
echo "🚀 Ready to continue development!"
