#!/bin/zsh
# Wait for Kenya CHIRPS, then run the full pipeline (obs + real MME + hybrid) for Kenya.
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate accord-chc
cd /Users/emmettculhane/Desktop/ACCORD/analyses/AGU-autoscience
export AREA=kenya

echo "[driver] waiting for data/kenya_chirps_monthly.nc ..."
until [ -f data/kenya_chirps_monthly.nc ]; do sleep 20; done
echo "[driver] CHIRPS present."
for s in seasons teleconnections feature_discovery composites synthesize_recipes mme_search hybrid_forecast; do
  echo "[driver] running $s.py (kenya)"
  python src/$s.py > outputs/ken_$s.out 2>&1
  echo "[driver] $s exit=$?"
done
echo "[driver] KENYA PIPELINE DONE"
