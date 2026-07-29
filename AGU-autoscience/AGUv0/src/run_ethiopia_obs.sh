#!/bin/zsh
# Wait for the Ethiopia CHIRPS cache, then run the observation-only pipeline for Ethiopia.
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate accord-chc
cd /Users/emmettculhane/Desktop/ACCORD/analyses/AGU-autoscience
export AREA=ethiopia

echo "[driver] waiting for data/ethiopia_chirps_monthly.nc ..."
until [ -f data/ethiopia_chirps_monthly.nc ]; do sleep 20; done
echo "[driver] CHIRPS present."
for s in seasons teleconnections feature_discovery composites synthesize_recipes; do
  echo "[driver] running $s.py (ethiopia)"
  python src/$s.py > outputs/eth_$s.out 2>&1
  echo "[driver] $s exit=$?"
done
echo "[driver] ETHIOPIA OBS PIPELINE DONE"
