# UI functionality review

Verified in Chrome against the local application:

- 28 functional assertions: shared selection, quick/custom/invalid dates, map mounting and control availability, ranking selection, five historical variables, CSV contents, methodology dialog, replay scrub/play/pause, flood panels, EDA selection, simulated search/refresh/provider failures, invalid coordinates, simulated GPS rejection and four downloadable assets.
- Live Colombo geocoding and searched-location forecast succeeded.
- Live Hanwella weather and flood refresh succeeded in the QA browser. This updates that browser cache only, not bundled datasets or every district.
- 40 layout combinations (8 routes × 5 widths) passed overflow and grid-alignment measurements.
- Mobile menu, Escape focus return, route selection, reduced motion and transparency checks passed.
- Frontend build, JavaScript syntax, core analytical tests and 150 location/view DOM combinations passed.

Fixed: an invalid-date warning was not cleared when a valid quick range was selected.

Evidence: functionality.json, results.json and interactions.json. Scripts: tools/functionality-qa.mjs, tools/layout-qa.mjs and tests/react.test.mjs.

Limits: GPS hardware success was not tested; rejection was simulated. Map controls were exercised but exact zoom bounds were not asserted. Live provider checks cover selected locations at test time, not every location or guaranteed future availability. Backend/cloud deployment and historical pipeline execution are outside this UI check. Bundled historical data was not refreshed.
