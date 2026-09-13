#!/usr/bin/env python3
"""Stage 1: drop rows with missing values. (Naive on purpose.)"""
import sys, pandas as pd
df = pd.read_csv(sys.argv[1])
df = df.dropna()
df.to_csv(sys.argv[2], index=False)
