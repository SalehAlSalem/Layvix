# Tools — Offline Training Utilities

This directory contains scripts used to train and retrain the Layvix AI model offline.
These scripts are NOT part of the application runtime and are NOT imported by main.py.

## Files

- `train_ai.py` — Initial model training from word lists in `data/`
- `retrain_ai.py` — Incremental retraining on new data
- `mapper.py` — Character mapping utilities used by the training scripts

## Usage

Run these scripts from the `tools/` directory:
```powershell
cd tools
python train_ai.py
```
