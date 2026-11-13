# Employee work-location import fix

Work location uses `site` for client-site workers and `inhouse` for own-office staff. It is not an employment-contract classification (permanent/contractual) or a site name.

Employee migration now normalizes case and accepts `In-house`, `In house` and `in_house`. Invalid select values return the field name and allowed values; unknown classifications are still rejected. Pay basis accepts case variations of monthly/daily/hourly/piece. Downloaded template guides show the permitted choices, and the example row uses site. Mapping recognizes Work location type as a column header.

Validation: 3 focused regression tests and all 272 existing migration tests passed. Backend-only change; deploy backend and worker. No database changes. Specific rejected source file not supplied.
