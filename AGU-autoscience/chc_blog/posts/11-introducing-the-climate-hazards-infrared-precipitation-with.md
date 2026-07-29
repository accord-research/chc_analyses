---
id: 1510
title: "Introducing the Climate Hazards Infrared Precipitation with Stations data (CHIRPS v3.0)"
date: "February 12, 2025"
iso_date: 2025-02-12
author: "Daniella Alaso"
categories: [Forecasting]
url: https://blog.chc.ucsb.edu/?p=1510
---
# Introducing the Climate Hazards Infrared Precipitation with Stations data (CHIRPS v3.0)

![](https://blog.chc.ucsb.edu/wp-content/uploads/2025/02/CHIRPS-3-monthly.png)

*Map of CHIRPS version 3.0 final, which shows total precipitation (mm) received globally during December 2024.*

The Climate Hazards Center (CHC) is dedicated to advancing the field of climate science by providing accurate, open-source, and high-resolution data products. Representing a significant improvement from the previous dataset (Climate Hazards Infrared Precipitation with Stations version 2.0 –[CHIRPS v2.0](https://www.nature.com/articles/sdata201566)), CHC has released a new precipitation dataset – CHIRPS v3.0. CHIRPS3 builds on the strong foundation of CHIRPS2 while also incorporating three major improvements:

1. A major improvement in the satellite-only precipitation algorithm, increasing the precipitation variability in CHIRP3 versus CHIRP2.
2. An extension from 50°S-50°N to 60°S-60°N.
3. The inclusion of thousands of additional rain gauge observations.
4. A switch to “gauge-undercatch corrected” precipitation estimates.

*“Version 2.0 of CHIRPS has been a success. Over the years, many peer-reviewed studies have shown that the dataset performs well,”*says Pete Peterson, Lead Programmer and CHIRPS Curator at the Climate Hazards Center.

*“Just in the third quarter of 2024 (Fig. 1), there were almost 6,000 unique IP addresses visiting the CHIRPS v2.0 web page, coming from 128 different countries all over the world. Several million files were downloaded in a quarter – amounting to about 40 terabytes of data. This is remarkable and underscores the global utility of this product.”*

*Figure 1. CHIRPS v2.0 download metrics for the 3rd quarter of 2024. 5,839 unique IP addresses accessed the data, 3.2M files were downloaded (approximately 40.8 terabytes of data).*

![](https://blog.chc.ucsb.edu/wp-content/uploads/2025/02/download-metrics.png)

The downloaded precipitation data goes on to be used in various applications, such as drought monitoring and prediction. *“Better data means more accurate information to make predictions with,”*says Chris Funk, Research Director at CHC*. “Our extensive work on CHIRPS v3.0 ensures that we are up-to-date with new technologies, and we are providing users with more accurate datasets that better represent the state of the climate.”*

CHIRPS v3.0 provides significant updates that increase the accuracy of precipitation estimates, and enhance the general representation of the climate system. In this version, all three major components of CHIRPS – the climatology (CHPclim), satellite-derived precipitation estimates (CHIRP), and station observations – have been updated.

**Improvements in the Climate Hazards Climatology (CHPclim2)**

The accurate representation of mean climate conditions at a given location is important for monitoring and prediction. Many applications, such as crop and hydrology models, can be sensitive to the absolute amount of rainfall. In data-scarce regions with shorter, often unreliable, in situ observation records, satellite-based precipitation estimates provide a unique resource for producing climatologies.

Compared to CHIRPS v2.0, CHIRPS v3.0 utilizes an updated climatology – Climate Hazards Precipitation Climatology version 2.0 (CHPclim2). *“In our latest climatology , we leverage excellent mean fields from the NASA IMERG precipitation dataset. We combine these data with available in situ observations and important physiographic indicators e.g. elevation, and we get a good estimate of the mean climate for a region,”* says Peterson.

Another strength of CHPclim2 is the utility of more station data. Through a partnership with the Global Precipitation Climatology Centre ([GPCC](https://www.dwd.de/EN/ourservices/gpcc/gpcc.html)), CHC received about 80,000 new gauge-undercatch corrected precipitation normals, and these were incorporated into the climatology for higher accuracy.

A [gauge-undercatch correction](https://www.sciencedirect.com/science/article/pii/S0022169422004590#b0200) attempts to account for systematic bias in gauge precipitation measurements wherein the gauge measures less precipitation than what actually fell, due to the influence of winds, especially in mountainous areas. In situ data in CHPclim2 and CHIRPS v3.0 are adjusted using a monthly correction factor from [Legates and Willmott (1990)](https://rmets.onlinelibrary.wiley.com/doi/abs/10.1002/joc.3370100202).

By factoring in this undercatch correction, CHPclim2 is overall wetter when compared to CHPclim1. For comparisons of CHIRPS v3.0 data to station observations, Funk recommends that researchers apply the same Legates adjustment to the gauges. *“Since CHIRPS3 is gauge-undercatch corrected, it should be compared to gauge-undercatch corrected stations,”* says Funk. To support the comparison, CHC offers these monthly scaling grids available for download [here](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/diagnostics/legates-willmott_corrections/).

**Improvements in CHIRP**

CHIRP is the satellite component of CHIRPS. The CHIRP approach uses locally calibrated satellite-derived precipitation estimates based on thermal infrared cold cloud duration (CCD) observations. The regression formula used in CHIRP version 2.0 provides reasonable estimates and represents mean rainfall very well. However, CHIRP2 has a tendency to underestimate temporal precipitation variance. This means that CHIRP2 may underestimate the magnitude of rainfall deficits and the magnitude of extreme precipitation events.

The new CHIRP v3.0 algorithm also estimates precipitation from geostationary satellite thermal infrared measurements of CCD, but version 3.0 performs better when it comes to estimating a wider range of precipitation values. The reason for this improvement is a reduction of the intercept term in the v3.0 formulation. While not always exactly zero, this term is greatly reduced in the new algorithm, while the slope term is increased in magnitude. This relatively simple change increases the variance of the b1*CCD (where b is the beta coefficient) variations in CHIRP v3.0. This increase in the variance provides improved performance, while also producing a new CHIRP v3.0 product that is well correlated with the old CHIRP v2.0 dataset.

An example of this is the November 2023 Greater Horn of Africa flooding and Southern Africa drying (Fig. 2). CHIRP3 anomalies show more rainfall over the Horn of Africa and more intense drying over Southern Africa.

*Figure 2. A comparison between CHIRP v2.0 (left) and CHIRP v3.0 (right) for November 2023 precipitation anomalies. Shadings of blue indicate positive anomalies (above-average rainfall) while shadings of red indicate negative anomalies (below-average rainfall).*

![](https://blog.chc.ucsb.edu/wp-content/uploads/2025/02/CHIRP2-and-CHIRP3-comparison.png)

*“CHIRP v3.0 is capturing a similar rainfall pattern as v2.0, but one that is more intense,”*says Laura Harrison, Monitoring and Forecasting Lead at the UCSB Climate Hazards Center. *“A change to the algorithm opened up the dynamic range of estimates. This feature is especially useful for capturing spatial and temporal patterns of large, impactful, or out of season storms. CHIRP v2.0 spatially tracked climatology well, but the downside was it estimated low values in out of the ordinary situations. In v3.0, CHIRP is doing a better job at capturing observed high values.”*

**The best and most labor-intensive part of CHIRPS – Station Data**

The final component of CHIRPS is station data, which is gathered from private archives and public data streams, including national meteorological centers. Each month, thousands of station observations are blended with CHPclim2 and CHIRP v3.0 to make CHIRPS v3.0. While there are many sources of satellite-based precipitation estimates, CHIRPS products stand out because they rapidly and routinely incorporate thousands of quality-controlled station observations. The density of station coverage varies across regions, and CHIRPS tends to perform better in those areas with more extensive station networks.

One troubling trend is that in recent years there has been a substantial decline in station observations globally. In the early 1980s, about 32,000 station observations went into CHIRPS v2.0 (Fig. 3), with this number steadily declining to about 15,000 by 2024. The decline in CHIRPS v2.0 station input directly reflects a broader reduction in weather stations globally over the last decades – with particularly concerning declines in Africa, South America, and West Asia.

*Figure 3. Monthly station counts for CHIRPS v2.0, CHIRPS v3.0, and GPCC v2022 in thousands.*

![](https://blog.chc.ucsb.edu/wp-content/uploads/2025/02/station-counts.png)

To address this challenge, CHC has expanded its data sources through partnerships with various agencies and the use of affordable 3D-printed automatic weather stations (3D-PAWS). As a result, CHIRPS v3.0 benefits from over 90 sources of station data, nearly four times the 24 sources originally used in CHIRPS v2.0.

Station data received from these sources are processed and archived in the CHC database. Currently, CHC maintains a gigantic precipitation database in the world. This database has more unique recent observations than any other global archive. *“The CHC has been working closely with national meteorology agencies and other agencies and we are excited about this progress,”* says Funk.

Overall, CHIRPS v3.0 integrates many more station observations than CHIRPS v2.0. These changes mean that CHIRPS3 is able to capture local precipitation characteristics better. In early 2025, the number of unique monthly observations in v3.0 is almost twice the number of observations in v2.0 (Fig. 3).

**Future Work**

CHIRPS v3.0 comes at a critical time of increasing climatic variability and climate extremes, when governments and humanitarian agencies are working to improve climate forecasts and strengthen early warning systems. This gridded dataset is the result of decades of research and continuous improvements.

CHIRPS v3.0 can be downloaded [here](https://www.chc.ucsb.edu/data) and is also accessible via an online interactive tool – the [Early Warning Explorer](https://ewx3.chc.ucsb.edu/ewx/index.html), that enables users to manipulate and visualize data in ways that suit their needs.

*“Our ambition is to continue to support data users efficiently. We’d like to see the new version of CHIRPS incorporated into the products and analysis tools that have already benefited from the good performance of CHIRPS v2.0, and into new applications too.”* says Harrison.

With the support of our partners – [NOAA](https://www.noaa.gov/), [NASA](https://www.nasa.gov/), and [USGS](https://www.usgs.gov/) – CHC continues to be at the forefront of environmental decision-making, providing routinely updated, long-term climate data.

The CHC has also developed [tools](https://www.chc.ucsb.edu/tools) that are used to monitor agro-climatic conditions and help warn of famine well in advance.

**To download CHIRPS v3.0 and access other data products, visit** [https://www.chc.ucsb.edu/data](https://www.chc.ucsb.edu/data)

**Key References**

Ehsani, M. R., & Behrangi, A. (2022). A comparison of correction factors for the systematic gauge-measurement errors to improve the global land precipitation estimate. Journal of Hydrology, 610, 127884.

Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., … & Michaelsen, J. (2015). The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes. Scientific data, 2(1), 1-21.

Legates, D. R., & Willmott, C. J. (1990). Mean seasonal and spatial variability in gauge‐corrected, global precipitation. International Journal of Climatology, 10(2), 111-127.
