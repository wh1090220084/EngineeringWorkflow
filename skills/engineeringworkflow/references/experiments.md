# Experiments and Reproducibility

Read this file for data processing, model changes, training, evaluation, inference, benchmarks, and experiment reports.

## Before Running

Identify the question, baseline or comparison, dataset and split, annotations/input format, model and weights, configuration, seed, environment, hardware, budget, expected artifacts, metric, and acceptance threshold. If a baseline is unavailable, state that the run is exploratory rather than blocking indefinitely.

## During and After Running

Record code version, command, configuration, data/split, weights, Python/framework/CUDA or equivalent environment, hardware, seed, key hyperparameters, metrics, output location, and material warnings or failures. Preserve old result comparability or explain why it changed.

Validate output shape, range, count, schema, and error handling before interpreting an aggregate metric. Do not treat a successful process exit as proof that a model result is correct.

## Exploration and Promotion

For a spike, use the Explore path and label the result exploratory. Before promoting it to a training, inference, or product change, move through Strict: write the plan, obtain required approval, define acceptance, and run the required reproducible validation.
