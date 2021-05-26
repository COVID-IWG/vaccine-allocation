#!/bin/bash 

tag=$(grep experiment_tag main.py | cut -d '"' -f2)
gcloud beta run 