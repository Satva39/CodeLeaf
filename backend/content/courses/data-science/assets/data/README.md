# Synthetic teaching datasets

All CSVs in this folder are original synthetic examples created for this course. They are not customer records and should not be interpreted as real market evidence.

- `retail-sales.csv`: ten fictional transactions with quantity and unit prices in INR. Derived sales value is `quantity * unit_price_inr`.
- `monthly-demand.csv`: twelve fictional monthly demand observations; use as a tiny forecasting demonstration, not a reliable forecasting benchmark.
- `customer-churn-synthetic.csv`: twelve fictional rows for basic classification exercises; this is far too small for a credible predictive claim.
- `ab-test-summary.csv`: two fictional aggregate A/B groups; aggregate counts alone may be insufficient to audit randomization or user-level independence.

Check all schemas and caveats before use. Never replace these files with private or unlicensed data in a public repository.
