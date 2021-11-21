#!/bin/bash

# activate virtualenv 
source /Users/honzapulpan/Projects/.venvs/jupyter/bin/activate

cd /Users/honzapulpan/Projects/covid
jupyter nbconvert --execute --to notebook covid19_stats_api3.ipynb --output covid19_stats_api3.ipynb
/Users/honzapulpan/Projects/covid/cmt.sh


