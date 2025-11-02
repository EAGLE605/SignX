# Task Report — demo-materials-1
            Timestamp: 2025-11-01T01:20:16.735705Z

            ## materials
- confidence: **0.88**
- assumptions: []

```json
{
  "caveats": [
    "Using synthesized material dataset; results illustrative."
  ],
  "confidence": 0.88,
  "contributions": [
    {
      "contribution": 50.0,
      "normalized_value": 100.0,
      "property": "strength",
      "weight": 0.5
    },
    {
      "contribution": 0.0,
      "normalized_value": 0.0,
      "property": "cost",
      "weight": 0.3
    },
    {
      "contribution": 13.333,
      "normalized_value": 66.667,
      "property": "corrosion",
      "weight": 0.2
    }
  ],
  "provenance": [
    "synth"
  ],
  "task_id": "demo-materials-1",
  "top_recommendations": [
    {
      "constraints_satisfied": [
        "min_yield_mpa",
        "corrosion_considered"
      ],
      "material": "Ti-6Al-4V",
      "reason": "weighted sum of normalized properties",
      "score": 63.333
    },
    {
      "constraints_satisfied": [
        "min_yield_mpa",
        "corrosion_considered"
      ],
      "material": "7075-T6 Al",
      "reason": "weighted sum of normalized properties",
      "score": 51.629
    },
    {
      "constraints_satisfied": [
        "min_yield_mpa",
        "corrosion_considered"
      ],
      "material": "6061-T6 Al",
      "reason": "weighted sum of normalized properties",
      "score": 44.621
    },
    {
      "constraints_satisfied": [
        "corrosion_considered"
      ],
      "material": "316L SS",
      "reason": "weighted sum of normalized properties",
      "score": 42.5
    },
    {
      "constraints_satisfied": [
        "corrosion_considered"
      ],
      "material": "304 SS",
      "reason": "weighted sum of normalized properties",
      "score": 40.742
    }
  ]
}
```