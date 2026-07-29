source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate accord-chc
cd /Users/emmettculhane/Desktop/ACCORD/analyses/AGU-autoscience
set +e
echo "### LEAD ###"
python src/lead_skill.py > outputs/lead.log 2>&1; echo "LEAD rc=$?"
for AREA in nigeria ethiopia kenya; do
  for S in mme_hindcast mme_search mme_methods hybrid_forecast; do
    echo "### $S [$AREA] ###"
    AREA=$AREA python src/$S.py >> outputs/s45.log 2>&1; echo "$S[$AREA] rc=$?"
  done
done
echo "### report_figures ###"
python src/report_figures.py >> outputs/s45.log 2>&1; echo "report_figures rc=$?"
echo "ALL_S45_DONE"
