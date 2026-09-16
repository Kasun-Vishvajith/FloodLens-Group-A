export const pageGuides={
 overview:[
  ['Start here','Choose a location and dates above. The top cards summarise coverage, unusual locations, selected-period rain and the latest river flow.'],
  ['Map & locations','Click a map point or a location in the list to explore it. Historical colours describe the selected final day; “Next 16 days” switches to provider forecast signals. Colours do not show flooded areas.'],
  ['Rainfall chart','Read months along the bottom and rainfall in millimetres up the side. Taller bars mean more rain within your selected dates; partial months contain only the selected days.'],
  ['The signal behind the status','This panel explains which weather or river measure stands out. Longer bars mean a more unusual value for that location and season, not a higher flood probability.']
 ],
 weather:[
  ['Location & freshness','Choose a reference location or search for a town. Check the retrieval banner first; use Refresh weather if the saved forecast is stale. The historical date filter does not apply.'],
  ['Cards & daily outlook','The top cards show current or saved conditions and total forecast rain. The day cards show temperature, rain and wind; scroll sideways to see every day.'],
  ['Forecast rainfall','Dates run left to right; height shows rain in millimetres. Dots and numbers show each day’s forecast. The dashed line is a historical comparison level, not another forecast.'],
  ['River-discharge outlook','The solid line shows the middle river-flow forecast; dashed lines show the spread between model members. Higher values mean more water passing per second, not flood depth. Read the signal summary alongside these charts.']
 ],
 history:[
  ['Choose what to compare','Set a location and date range, then select rainfall, temperature, humidity, wind or pressure. The summary cards and charts update to that variable.'],
  ['Daily chart','Dates run left to right and the selected unit is on the vertical axis. Peaks mark higher daily values; a gap means missing data, not zero.'],
  ['Monthly & seasonal charts','Monthly comparison groups your selected days: rainfall is added up, other variables are averaged. Seasonal baseline shows typical daily values for each month in 2016 to 2026, so its rain bars are not monthly totals.'],
  ['Compare monitoring locations','The table compares daily averages and maximum values over the same dates. Check “Valid days” for coverage and click a location to view its charts.']
 ],
 flood:[
  ['Summary & river flow','Choose a location and dates. The cards summarise its indicators; the main chart shows daily river flow. A solid line above the dashed historical level means unusually high flow for that season, not a confirmed flood.'],
  ['Rainfall accumulation','The two lines add rain over the previous 3 and 7 days. Read dates along the bottom and millimetres up the side to see whether several wet days are building up.'],
  ['Rainfall–discharge lag','Each bar compares rainfall with river flow a number of days later. Positive values suggest they tend to rise together; this does not prove rainfall caused a particular flood.'],
  ['Location comparison','Use the tables to compare indicators and choose a reference point. Missing flow stays unavailable; rainfall alone cannot describe the whole river basin.']
 ],
 events:[
  ['Choose an episode','Select a reference location, event type and dated episode. These are unusual periods found in the historical data; the shared date range does not control this page.'],
  ['Replay controls','Press Play to advance one day at a time, Pause to stop, or drag the slider directly to a day. The date and story panel follow your selection.'],
  ['Timeline charts','The upper chart shows the selected event measure; the lower bars show daily rainfall. Read dates horizontally and the labelled units vertically. The charts reveal the episode up to the replay day.'],
  ['Story & daily values','The right-hand panel explains that day’s signal and lists rain, river flow and temperature. These episodes are analytical findings, not independently confirmed disasters.']
 ],
 analysis:[
  ['Distribution & summary','Choose a location and variable. This page uses the full archive. Each bar counts days within a value range; longer bars show the most common conditions. The table summarises typical values and variation.'],
  ['Correlation matrix','Find two variables where their row and column meet. Values near +1 mean they tend to rise together, near −1 mean opposite movement, and near 0 mean little straight-line relationship. This does not establish cause.'],
  ['Monsoons & years','Compare average daily conditions between seasons. In the yearly table, compare rates as well as counts because partial years contain fewer days.'],
  ['District screening','The final table highlights locations with stronger recent rain/flow signals. Check the date and whether a score uses rain alone; click a location to inspect it. The score is not a percentage chance of flooding.']
 ],
 explore:[
  ['Find a place','Search for a town, use GPS, or enter coordinates. Enable Global view to search beyond Sri Lanka. This page uses its own location instead of the shared district selection.'],
  ['Use the map','Click the map to fill in latitude and longitude, then press Load location. Moving the map by itself does not retrieve new data.'],
  ['Read the results','After loading, cards show current provider conditions and elevation. The table lists each date’s rain, temperatures, wind and river flow; scroll sideways for extra columns.'],
  ['Unavailable results','Some providers or river grid points may have no values. A dash means unavailable, not zero. If GPS is denied, search or enter coordinates instead.']
 ],
 quality:[
  ['Coverage cards','The top cards show archive size, dates, weather completeness and how many reference points have river data. This page describes the whole project, not the selected location.'],
  ['Downloads','Download historical records and saved forecasts separately. JSON files contain coverage and comparison levels; they are supporting data rather than charts.'],
  ['Processing & performance','The pipeline and method sections explain how API data becomes daily charts. The benchmark table shows measured processing time as the number of rows increases.'],
  ['Sources & limitations','Expand the source notes to understand missing data, model changes and geographic limits. Assignment coverage and contribution notes describe the project’s scope, not additional weather findings.']
 ]
};
