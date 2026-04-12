# training

Fine-tuning pipeline for Gemma 3n. Produces the model checkpoint deployed in `jobflow-llm`.

## Run
```bash
uv sync
uv run python scripts/generate_data.py   # synthetic training data generation
uv run python scripts/train.py           # fine-tune with Unsloth + TRL
uv run python scripts/eval.py            # evaluate on held-out set
uv run python scripts/export.py          # export to LiteRT (quantized)
```

## Structure
```
scripts/
  generate_data.py   Synthetic pair generation (job + resume → tailored resume, cover letter)
  train.py           Unsloth/TRL SFT fine-tuning loop
  eval.py            ROUGE + BERTScore evaluation
  export.py          HuggingFace → LiteRT quantized export
data/
  raw/               Source job/resume samples (not committed — see .gitignore)
  synthetic/         Generated training pairs (not committed)
  eval/              Held-out evaluation set (committed, small)
configs/
  training_config.yaml   Model, LoRA, hyperparameter settings
  lora_config.yaml       LoRA rank/alpha/target modules
```

## Pipeline
```
generate_data.py
  → GPT-4o generates (job, resume) → (tailored_resume, cover_letter, qa_answers) pairs
  → Saved as JSONL in data/synthetic/

train.py
  → Loads Gemma 3n base from HuggingFace Hub
  → Applies LoRA via Unsloth (4-bit quantization during training)
  → SFT with TRL on synthetic pairs
  → Checkpoints to runs/{timestamp}/

eval.py
  → ROUGE-L on cover letters
  → BERTScore on tailored resumes
  → Logs to W&B

export.py
  → Merges LoRA weights into base
  → Exports to LiteRT int8 format
  → Pushes to HuggingFace Hub (private repo)
  → Updates JOBFLOW_MODEL_VERSION in infra/helm/jobflow-llm/values.yaml
```

## Key rules
- Training runs on GPU — not part of the Kubernetes cluster (run locally or on Colab)
- `JOBFLOW_MODEL_VERSION` in Helm values must match the exported checkpoint tag
- Raw data (`data/raw/`, `data/synthetic/`) is gitignored — do not commit training data
- Evaluation set (`data/eval/`) is committed — small, anonymized samples only
- HuggingFace token required: `HF_TOKEN` env var
