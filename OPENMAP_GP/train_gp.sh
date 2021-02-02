#!/bin/bash

. ~/venv/gaussian_process/bin/activate
python train_gp.py "$@"
