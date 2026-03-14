window.MAP_DATA = {
  spots: [
    { name: "Lista", lat: 58.0, lon: 6.5 },
    { name: "Pigsty/Piggy", lat: 58.75, lon: 5.25 },
    { name: "Saltstein", lat: 58.75, lon: 9.75 },
    { name: "Ervika", lat: 62.25, lon: 5.0 },
    { name: "Alnes Lighthouse (Godoy)", lat: 62.5, lon: 5.75 },
    { name: "Hustadvika Gjestegard", lat: 63.0, lon: 7.0 },
    { name: "Unstad Beach", lat: 68.25, lon: 13.25 },
    { name: "Persfjord", lat: 70.5, lon: 31.0 },
    { name: "Haugesund", lat: 59.4138, lon: 5.2680, kind: "mandal" },
    { name: "Mandal / Sjosanden", lat: 58.027, lon: 7.453, kind: "mandal" }
  ],
  sources: [
    {
      name: "Lista Fyr",
      provider: "Frost",
      linkedSpot: "Lista",
      lat: 58.109,
      lon: 6.6075,
      status: "good",
      summary: "Serie. Vindstyrke og retning i PT1H og PT6H. Kast som 10-min maks i PT10M."
    },
    {
      name: "Lista Fyr",
      provider: "Kystverket",
      linkedSpot: "Lista",
      lat: 58.109,
      lon: 6.5275,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Sondre Katland",
      provider: "Kystverket",
      linkedSpot: "Lista",
      lat: 58.056939,
      lon: 6.840388,
      status: "good",
      summary: "Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Lindesnes Fyr",
      provider: "Frost",
      linkedSpot: "Lista",
      lat: 57.9815,
      lon: 7.088,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Lindesnes Fyr",
      provider: "Kystverket",
      linkedSpot: "Lista",
      lat: 57.9815,
      lon: 7.008,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Obrestad Fyr",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.6585044,
      lon: 5.5945609,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Obrestad Fyr",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.658504,
      lon: 5.514561,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Vigdel",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.85197,
      lon: 5.55158,
      status: "good",
      summary: "Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Saerheim",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.7605,
      lon: 5.6908,
      status: "good",
      summary: "Serie. PT1H vindstyrke og retning. Ingen gust-serie funnet."
    },
    {
      name: "Saerheim",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.7605,
      lon: 5.6108,
      status: "good",
      summary: "Snapshot. Vindstyrke og retning. Gust ikke tilgjengelig akkurat na."
    },
    {
      name: "Jomfruland",
      provider: "Frost",
      linkedSpot: "Saltstein",
      lat: 58.8565,
      lon: 9.6145,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Jomfruland",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 58.86509,
      lon: 9.55637,
      status: "good",
      summary: "Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Fugloya",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 58.980574,
      lon: 9.803816,
      status: "bad",
      summary: "Snapshot. Kystnaer kandidat for Saltstein. Verdier kom tilbake, men timestamp manglet i svaret, sa jeg kan ikke bekrefte at den er fersk akkurat na."
    },
    {
      name: "Svinoy Fyr",
      provider: "Frost",
      linkedSpot: "Ervika",
      lat: 62.3293,
      lon: 5.308,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Svinoy Fyr",
      provider: "Kystverket",
      linkedSpot: "Ervika",
      lat: 62.3293,
      lon: 5.228,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Krakenes",
      provider: "Frost",
      linkedSpot: "Ervika",
      lat: 62.034,
      lon: 5.0265,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Krakenes",
      provider: "Kystverket",
      linkedSpot: "Ervika",
      lat: 62.034,
      lon: 4.9465,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Fauskane",
      provider: "Kystverket",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.566785,
      lon: 5.726357,
      status: "bad",
      summary: "Snapshot-endepunkt finnes, men siste vinddata som kom tilbake var gamle fra 2021. Ikke egnet na."
    },
    {
      name: "Vigra",
      provider: "Frost",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.5617,
      lon: 6.155,
      status: "good",
      summary: "Serie. PT10M, PT30M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M og PT30M."
    },
    {
      name: "Vigra",
      provider: "Kystverket",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.5617,
      lon: 6.075,
      status: "good",
      summary: "Snapshot. Vindstyrke og retning er ferske. Gust var ikke tilgjengelig akkurat na."
    },
    {
      name: "Ona II",
      provider: "Frost",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.8585,
      lon: 6.5778,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Ona II",
      provider: "Kystverket",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.8585,
      lon: 6.4978,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Finnoya",
      provider: "Kystverket",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.80422,
      lon: 6.509046,
      status: "good",
      summary: "Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Leknes Lufthavn",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 68.1557873,
      lon: 13.65214,
      status: "good",
      summary: "Serie. PT1M, PT10M, PT30M, PT1H og PT6H for vindstyrke og retning. Kast i PT1M, PT10M og PT30M."
    },
    {
      name: "Leknes Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 68.155787,
      lon: 13.57214,
      status: "good",
      summary: "Snapshot. Vindstyrke og retning er ferske. Gust-feltet svarte med ugyldig timestamp akkurat na."
    },
    {
      name: "Vaeroy Heliport",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 67.6527,
      lon: 12.7228,
      status: "good",
      summary: "Kystnaer sorgevestlig supplement for Unstad. Serie. PT10M, PT30M, PT1H og PT6H for vind og retning. Gust i PT10M og PT30M."
    },
    {
      name: "Vaeroy Heliport",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 67.6527,
      lon: 12.6428,
      status: "bad",
      summary: "Snapshot. Kystverket speiler stasjonen, men svartypen manglet timestamp i sjekken min, sa jeg markerer den som ikke verifisert akkurat na."
    },
    {
      name: "Hekkingen Fyr",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 69.6005,
      lon: 17.8312,
      status: "good",
      summary: "Kystnaer nordvestlig supplement mot Sommaroy-siden. Serie. PT10M, PT1H og PT6H for vind og retning. Gust i PT10M."
    },
    {
      name: "Hekkingen Fyr",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 69.6005,
      lon: 17.7512,
      status: "good",
      summary: "Snapshot. Vindstyrke, retning og kraftigste vindkast siste 10 min svarte med brukbare live-verdier."
    },
    {
      name: "Vardo Radio",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.3707,
      lon: 31.1362,
      status: "good",
      summary: "Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Vardo Radio",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.3707,
      lon: 31.0562,
      status: "good",
      summary: "Snapshot. Siste vindstyrke, retning og kraftigste vindkast siste 10 min."
    },
    {
      name: "Vardo Lufthavn",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.3512896,
      lon: 31.0902314,
      status: "good",
      summary: "Serie. PT30M og PT1H for vindstyrke og retning. Gust i PT30M."
    },
    {
      name: "Vardo Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.35129,
      lon: 31.010231,
      status: "good",
      summary: "Snapshot. Vindstyrke og retning er ferske. Ingen gust i dette svaret akkurat na."
    },
    {
      name: "Makkaur Fyr",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.7057,
      lon: 30.11,
      status: "good",
      summary: "Serie. PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Makkaur Fyr",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.7057,
      lon: 30.03,
      status: "good",
      summary: "Snapshot. Vindstyrke og retning er ferske. Gust-feltet hadde ugyldig timestamp akkurat na."
    },
    {
      name: "Tregde",
      provider: "Kartverket / MET tide",
      linkedSpot: "Lista",
      lat: 58.006377,
      lon: 7.554759,
      status: "good",
      summary: "Naermeste permanente tide gauge for Lista i første versjon. Brukes for astronomisk tide fra Kartverket og TOTAL/SURGE/TIDE fra MET stormflo."
    },
    {
      name: "Sirevag",
      provider: "Kartverket / MET tide",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.504806,
      lon: 5.801103,
      status: "good",
      summary: "Permanent tide gauge valgt for Pigsty/Piggy i foerste versjon. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Helgeroa",
      provider: "Kartverket / MET tide",
      linkedSpot: "Saltstein",
      lat: 58.995212,
      lon: 9.856379,
      status: "good",
      summary: "Naermeste permanente tide gauge for Saltstein. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Maloy",
      provider: "Kartverket / MET tide",
      linkedSpot: "Ervika",
      lat: 61.933776,
      lon: 5.11331,
      status: "good",
      summary: "Naermeste permanente tide gauge for Ervika. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Alesund",
      provider: "Kartverket / MET tide",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.469414,
      lon: 6.151946,
      status: "good",
      summary: "Naermeste permanente tide gauge for Alnes. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Kristiansund",
      provider: "Kartverket / MET tide",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 63.11392,
      lon: 7.73614,
      status: "good",
      summary: "Naermeste permanente tide gauge for Hustadvika. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Kabelvag",
      provider: "Kartverket / MET tide",
      linkedSpot: "Unstad Beach",
      lat: 68.212639,
      lon: 14.482149,
      status: "good",
      summary: "Naermeste permanente tide gauge for Unstad. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Vardo",
      provider: "Kartverket / MET tide",
      linkedSpot: "Persfjord",
      lat: 70.374978,
      lon: 31.104015,
      status: "good",
      summary: "Naermeste permanente tide gauge for Persfjord. Brukes for astronomisk tide fra Kartverket og vaerkorrigert vannstand fra MET."
    },
    {
      name: "Oksoy Fyr",
      provider: "Frost",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.0732,
      lon: 8.0932,
      status: "good",
      summary: "Ekstra Mandal-kandidat. Serie. PT10M, PT1H og PT6H for vindstyrke og retning. Kast i PT10M."
    },
    {
      name: "Oksoy",
      provider: "Kystverket",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.07307,
      lon: 8.014014,
      status: "good",
      summary: "Ekstra Mandal-kandidat. Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Kristiansand Havn",
      provider: "Kystverket",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.140201,
      lon: 7.988873,
      status: "good",
      summary: "Ekstra Mandal-kandidat. Snapshot. WINDSPD, WINDDIR, WINDGUS og WINDGUSDIR med ferske sensorverdier."
    },
    {
      name: "Rovar",
      provider: "Frost",
      linkedSpot: "Haugesund",
      lat: 59.4382,
      lon: 5.0780,
      status: "good",
      summary: "Kystnaer Haugesund-kandidat. Serie. Vindstyrke og retning i PT1H. Gust som 10-min maks."
    },
    {
      name: "Rovar",
      provider: "Kystverket",
      linkedSpot: "Haugesund",
      lat: 59.4403,
      lon: 4.9980,
      status: "good",
      summary: "Snapshot. Eksponert kystpunkt vest for Haugesund med ferske live-verdier."
    },
    {
      name: "Utsira Fyr",
      provider: "Frost",
      linkedSpot: "Haugesund",
      lat: 59.3065,
      lon: 4.8723,
      status: "good",
      summary: "Kystnaer Haugesund-kandidat. Serie. PT10M, PT1H og PT6H for vind og retning. Gust i PT10M."
    },
    {
      name: "Utsira Fyr",
      provider: "Kystverket",
      linkedSpot: "Haugesund",
      lat: 59.3065,
      lon: 4.7923,
      status: "bad",
      summary: "Snapshot. Vind svarte, men retning og gust manglet i sjekken min, sa den er ikke fullt brukbar akkurat na."
    },
    {
      name: "Slatteroy Fyr",
      provider: "Frost",
      linkedSpot: "Haugesund",
      lat: 59.9070,
      lon: 5.0668,
      status: "good",
      summary: "Eksponert regional kystproxy nord for Haugesund. Serie. PT10M, PT1H og PT6H for vind og retning. Gust i PT10M."
    },
    {
      name: "Slatteroy Fyr",
      provider: "Kystverket",
      linkedSpot: "Haugesund",
      lat: 59.9070,
      lon: 4.9868,
      status: "good",
      summary: "Snapshot. Vind, retning og gust svarte med brukbare live-verdier i sjekken min."
    }
  ]
};
