#!/bin/zsh
# Patient retry for the two IRI-dependent analyses (lead-time, downscaling frontier).
# The IRI OPeNDAP server is intermittently/fully down for NMME precip; this keeps retrying
# with backoff until BOTH produce non-empty output, then rebuilds+executes the notebook.
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate accord-chc
cd /Users/emmettculhane/Desktop/ACCORD/analyses/AGU-autoscience

FIG=outputs/figures
MAXATT=24            # ~ up to 6h at 15min spacing
att=0
while (( att < MAXATT )); do
  att=$((att+1))
  echo "=== attempt $att / $MAXATT ==="
  # probe: does one CCSR (IRI-free) fetch succeed now? geoss2s lives on forecast.ccsr.columbia.edu
  if python -c "
import rosetta,warnings,sys; warnings.filterwarnings('ignore')
try:
    rosetta.fetch(product='nmme/geoss2s',variable='precip',init='2016-07',target='OND',
      region=[-5,5,34,42],hindcast=(1993,2016),year_index=True,verbose=False,progress=False,max_retries=2)
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
    echo "IRI reachable — running analyses"
    [[ -f $FIG/lead_skill_kenya.png ]] || python src/lead_skill.py > outputs/lead.log 2>&1
    [[ -f $FIG/downscale_frontier_kenya.png ]] || python src/downscale_frontier.py > outputs/frontier.log 2>&1
    if [[ -f $FIG/lead_skill_kenya.png && -f $FIG/downscale_frontier_kenya.png ]]; then
      echo "BOTH DONE — rebuilding notebook"
      python src/build_report.py
      jupyter nbconvert --to notebook --execute --inplace AUTOSCIENCE_REPORT.ipynb > /dev/null 2>&1
      jupyter nbconvert --to html AUTOSCIENCE_REPORT.ipynb > /dev/null 2>&1
      echo "PATIENT_GCM_COMPLETE"
      exit 0
    fi
    echo "partial: lead=$([[ -f $FIG/lead_skill_kenya.png ]] && echo y || echo n) frontier=$([[ -f $FIG/downscale_frontier_kenya.png ]] && echo y || echo n)"
  else
    echo "IRI still down — sleeping 15m"
  fi
  sleep 900
done
echo "PATIENT_GCM_GAVEUP after $MAXATT attempts"
