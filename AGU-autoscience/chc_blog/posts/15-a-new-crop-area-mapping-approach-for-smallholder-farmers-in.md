---
id: 1829
title: "A New Crop Area Mapping Approach for Smallholder Farmers in Africa Using High Resolution Satellite Data and Cloud Computing"
date: "May 21, 2025"
iso_date: 2025-05-21
author: "Daniella Alaso"
categories: [Forecasting]
url: https://blog.chc.ucsb.edu/?p=1829
---
# A New Crop Area Mapping Approach for Smallholder Farmers in Africa Using High Resolution Satellite Data and Cloud Computing

**Seth Peterson, Greg Husak, and Daniella Alaso**

Crop area maps are essential tools to help estimate crop acreage and provide a way to highlight key locations of other critical variables used as inputs to yield estimates. Given the considerable logistical challenges of responding to production shortfalls, early and accurate estimates of crop areas are crucial inputs for ensuring food security for vulnerable populations.

To support food security early warning, the Climate Hazards Center has developed a crop area mapping approach using remote sensing Sentinel-2 data and Google Earth Engine that works well in sub-Saharan Africa. The approach uses green vegetation, non-photosynthetic vegetation, soil, and shade endmember fractions (Figure 1) from Spectral Mixture Analysis (SMA) as inputs into the Random Forests classification model.

![Figure 1 An image showing 1m true color from VHR image data in GEpro (top left) and 10m true color from Sentinel-2 data (top middle). Endmember fractions from Spectral Mixture Analysis applied to Sentinel-2 data showing green vegetation (top right), non-photosynthetic vegetation (bottom left), soil (bottom middle) and shade (bottom right).](https://blog.chc.ucsb.edu/wp-content/uploads/2025/05/sentinel-300x182.jpg)

The foundation of this approach involves a spectral unmixing approach applied to the high resolution Sentinel-2 data that allows for improved differentiation of crops and natural vegetation as they grow and change over time. The high spatial resolution (10m) of Sentinel-2 data also allows for better characterization of smallholder farms, a dominant land cover in sub-Saharan Africa, characterized by farms mixed with forests and grazing land.

**Case Studies**

The CHC crop area mapping approach was first developed for southern and central Malawi where we were able to accurately (87 to 93%) identify locations of natural vegetation classes and crops for smallholder farmers. The crop area map generated in this[study](https://www.frontiersin.org/journals/climate/articles/10.3389/fclim.2021.693653/full)had a strong agreement with statistics from the Malawi government (R2= 0.74) and a remotely sensed product developed by the USGS (R2= 0.79).

In 2024, the approach was then applied in Tigray, Ethiopia to estimate crop area and assess changes due to the civil war. In this[study](https://iopscience.iop.org/article/10.1088/2976-601X/ad3559), the accuracies of crop/no crop area ranged from 80% to 90% for the different districts of Tigray, and the errors were found to be unbiased. The study also identified areas that experienced a reduction in crop area as a result of intense conflict and civil disruption.

**Operationalizing CHC Crop Area Mapping: Application to Zimbabwe**

Given the success that we have had with estimating crop area and monitoring other elements of farming from satellite data using the SMA approach, we decided to implement the model in Zimbabwe. We asked the question, how early in the growing season can we accurately estimate crop area?

However, one challenge in the Malawi and Ethiopia studies was that the Random Forest Classification Model was trained on data derived from manual interpretation of very-high spatial resolution (1m) imagery in Google Earth. With thousands of data points generated, this process is very time consuming and difficult to replicate.

In this context, we developed an efficient two-stage system. First, the Digital Earth Africa crop probability map was categorized to identify crop (probability > 60%) and no-crop (probability < 30%) areas, and random points were selected from this categorized map for each class. This produced an initial crop area map which was reasonable, but had obvious errors. In the second stage, a number of manual points were added to fix erroneous areas of the map. The training point datasets were combined, and applied to each year 2016-2025. Fields fallowed in any given year were removed from the crop class training for that year using a threshold on greenness/GV (Figure 2).

![Figure 2 shows a very-high spatial resolution image from March 30, 2023 of a smallholder farm near Matanda in eastern Zimbabwe, and illustrates the manual training point selection process. The red pin/timeseries identifies a cultivated field in 2023 (vegetation planted in rows, geometric shape to the field, good greenness), the green pin/timeseries a fallow grassland or pasture in 2023 (irregular vegetation, often less green, but not always in the case of weedy areas in a wet year). The inset time series shows the green vegetation value for each month over the nine years of Sentinel data, with the color corresponding to the pin in the image. Based on the red timeseries, the field greens up to a level suggesting successful cropping in most years (we used a GV threshold of 0.35 for Zimbabwe). Both imagery and time series data are used in selecting training data.](https://blog.chc.ucsb.edu/wp-content/uploads/2025/05/GV-1-300x147.jpg)

To test how early in the season a reasonable estimate could be made, a sample estimate was generated using imagery that started in September and went through various points in the season. For example, an estimate was made using imagery from September-December, September-January, and so forth through September-August (Figure 3). This allowed us to identify at what point in the season the estimate stabilized. For 2025, results through September-April are shown.

![Figure 3 shows crop area in ha for the eastern 2/3 of Zimbabwe, where most of the agriculture is located. The agricultural year runs from September to August, and the months in the legend are associated with the year of the harvest, which typically occurs starting as early as mid-April and running through June. The different monthly models tend to follow a similar ranking, with 2017 being a “good” year and 2019 and 2024 being “bad” years.](https://blog.chc.ucsb.edu/wp-content/uploads/2025/05/crop-area-zim-300x182.jpg)

The models using imagery from early in the season (September–December, September-January or September-February) overpredict crop areas, but capture the relative ranking of good and bad years. For example, 2019 and 2024 would be bad years, while 2017 would be a good year. Predictions using imagery from September-March or later were quite stable.

**Did we capture on the ground reality?**

Absolutely! The Zimbabwe Ministry of Lands, Agriculture, Fish, Water, and Rural Development recently released their crop assessment for the 2024-2025 season, and data therein were compared with our 2016-2025 estimates.

As shown in the figure below, there was a strong relationship between cereal production and CHC crop area (R2= 0.85) and a good relationship between cereal area and CHC crop area (R2= 0.58) (Figure 4). Typically, production statistics are based on directly measured values (such as weighing stations) and cropped area and yield statistics are derived from more proximate variables.

![Figure 4 A time series showing Zimbabwe cropped cereal area in hectares (blue), crop production in metric tons (orange) from the government of Zimbabwe, and CHC crop area estimate from Sentinel-2 data (green).](https://blog.chc.ucsb.edu/wp-content/uploads/2025/05/Reported-stats-Zim-300x158.jpg)

By using the SMA approach CHC has been able to produce an accurate in-season estimate of planted area. For Zimbabwe, the September-December map provides a relative (good or bad year) estimate on January 1 for advance planning. The September-March crop area map can be produced on April 1, to produce an accurate in-season estimate. Furthermore, this independent analysis can serve as a point of convergence with official government numbers.

**Future Work**

The results presented here provide a benchmark for future applications of the CHC mapping approach in other countries in sub-Saharan Africa. Significantly, this approach provides an avenue to estimate crop area and subsequently crop yield early in the season. The complexity of image pre-processing to generate the training data has been significantly reduced by using the Digital Earth Africa Crop Probability Map, making the approach easily replicable.

These results have the potential to support early identification of crop production shortfalls and populations at risk enabling timely intervention. In addition, crop maps generated will fill agricultural data gaps in sub-Saharan Africa, and support national scale crop statistics.

**References**

Peterson, Seth, and Greg Husak. “Crop area mapping in southern and central Malawi with google earth engine.” Frontiers in Climate 3 (2021): 693653.

Peterson, Seth, Greg Husak, Shraddhanand Shukla, and Amy McNally. “Crop area change in the context of civil war in Tigray, Ethiopia.” Environmental Research: Food Systems 1, no. 1 (2024): 015003.
