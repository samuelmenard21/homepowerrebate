#!/bin/bash

# Consolidate all regional rebate CSVs into one master file
OUTPUT="all-rebates-consolidated.csv"

echo "🔄 Consolidating rebate data from all regions..."

# Add header from first file
head -1 bc-rebates.csv > $OUTPUT

# Append all data rows (skip headers)
for file in bc-rebates.csv on-rebates.csv ab-ns-rebates.csv ca-rebates.csv ny-rebates.csv ma-rebates.csv; do
  if [ -f "$file" ]; then
    echo "  Adding $(tail -1 $file | cut -d',' -f2): $(wc -l < $file | xargs) lines"
    tail -n +2 $file >> $OUTPUT
  fi
done

# Count total records
TOTAL=$(tail -n +2 $OUTPUT | wc -l)
echo ""
echo "✅ Consolidated: $TOTAL cities"
echo "📄 Output: $OUTPUT"
echo ""
echo "Next step: Load into D1"
echo "  wrangler d1 execute homepowerrebate-programs --remote --command \"$(cat $OUTPUT | head -c 100)...\""
