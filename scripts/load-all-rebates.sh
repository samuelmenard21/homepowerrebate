#!/bin/bash

# Create D1 database if it doesn't exist
echo "🗄️  Creating D1 database: homepowerrebate-programs..."
wrangler d1 create homepowerrebate-programs --yes 2>/dev/null || echo "Database may already exist"

# Apply schema
echo "📋 Applying schema..."
wrangler d1 execute homepowerrebate-programs --remote --file scripts/schema.sql

# Load all regional CSVs (each CSV needs transformation to match schema)
echo "📤 Loading rebate data..."

# For now, list what needs to be loaded
echo ""
echo "✅ Ready to load CSVs:"
echo "  - ca-rebates.csv (25 CA cities)"
echo "  - ny-rebates.csv (6 NY cities)"
echo "  - ma-rebates.csv (13 MA cities)"
echo "  - bc-rebates.csv (18 BC cities)"
echo "  - on-rebates.csv (20 ON cities)"
echo "  - ab-ns-rebates.csv (7 AB/NS cities)"
echo ""
echo "Total: 89 cities across 7 regions"
echo ""
echo "Next: Transform CSVs to schema format and bulk-insert"
