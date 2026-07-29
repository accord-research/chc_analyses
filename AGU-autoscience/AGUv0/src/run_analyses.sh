#!/bin/zsh
# Wait for the CHIRPS cache, then run the two observation-only analyses end to end.
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate accord-chc
cd /Users/emmettculhane/Desktop/ACCORD/analyses/AGU-autoscience

echo "[driver] waiting for data/nigeria_chirps_monthly.nc ..."
until [ -f data/nigeria_chirps_monthly.nc ]; do sleep 20; done
echo "[driver] CHIRPS present. running seasons.py"
python src/seasons.py > outputs/seasons.out 2>&1
echo "[driver] seasons.py exit=$?"
echo "[driver] running teleconnections.py"
python src/teleconnections.py > outputs/teleconn.out 2>&1
echo "[driver] teleconnections.py exit=$?"
echo "[driver] DONE"
