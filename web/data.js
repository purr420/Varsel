window.MAP_DATA = {
  spots: [
    { name: "Lista", lat: 58.006104, lon: 6.468337, noaaUsed: { lat: 58.006104, lon: 6.468337 } },
    { name: "Pigsty/Piggy", lat: 58.767823, lon: 5.288713, noaaUsed: { lat: 58.767823, lon: 5.288713 } },
    { name: "Saltstein", lat: 58.770031, lon: 9.792522, noaaUsed: { lat: 58.770031, lon: 9.792522 } },
    { name: "Ervika", lat: 62.222712, lon: 4.966103, noaaUsed: { lat: 62.222712, lon: 4.966103 } },
    { name: "Alnes Lighthouse (Godoy)", lat: 62.506226, lon: 5.702142, noaaUsed: { lat: 62.506226, lon: 5.702142 } },
    { name: "Hustadvika Gjestegard", lat: 62.992319, lon: 7.028400, noaaUsed: { lat: 62.992319, lon: 7.028400 } },
    { name: "Unstad Beach", lat: 68.277434, lon: 13.221921, noaaUsed: { lat: 68.277434, lon: 13.221921 } },
    { name: "Persfjord", lat: 70.450232, lon: 31.046501, noaaUsed: { lat: 70.450232, lon: 31.046501 } },
    { name: "Mandal / Sjosanden", lat: 57.874278, lon: 7.313109, kind: "mandal", markerStyle: "noaa", noaaUsed: { lat: 57.874278, lon: 7.313109 } }
  ],
  sources: [
    {
      name: "Lista Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Lista",
      lat: 58.10917,
      lon: 6.56667,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast brukt som vindkilde i forecast-tabellen for Lista."
    },
    {
      name: "Lista gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Lista",
      lat: 58.000000,
      lon: 6.500000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Lista. Ligger ca. 12,8 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Lista ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Lista",
      lat: 58.125000,
      lon: 6.562500,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Lista. Ligger ca. 1,8 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Lista NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Lista",
      lat: 58.073828,
      lon: 6.629160,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid til Yr-vindpunktet ved Lista. Ligger ca. 5,4 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Lista DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Lista",
      lat: 58.100000,
      lon: 6.583335,
      status: "good",
      summary: "Naermeste DMI WAM NSB-grid for vind ved Lista. Ligger ca. 1,4 km fra Yr-vindpunktet og gir time-for-time vind lenger fram enn dagens grovere Yr-steg."
    },
    {
      name: "Reve havn Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.771,
      lon: 5.515,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast tilgjengelig under Vind for pa spot-siden for Jaeren. Dette er standardvalget."
    },
    {
      name: "Kvassheim Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.544,
      lon: 5.680,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Jaeren."
    },
    {
      name: "Solastranda Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.888,
      lon: 5.601,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Jaeren."
    },
    {
      name: "Piggy gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.750000,
      lon: 5.500000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Pigsty/Piggy. Ligger ca. 0,3 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og GFS wave."
    },
    {
      name: "Piggy ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.750000,
      lon: 5.500000,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Pigsty/Piggy. Ligger ca. 0,3 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Piggy NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.760601,
      lon: 5.436810,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid til Yr-vindpunktet ved Pigsty/Piggy. Ligger ca. 3,7 km fra Yr-punktet og brukes til vindsammenlikning mot Yr."
    },
    {
      name: "Saltstein Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Saltstein",
      lat: 58.975000,
      lon: 9.820000,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast brukt som vindkilde i forecast-tabellen for Saltstein."
    },
    {
      name: "Saltstein gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Saltstein",
      lat: 58.750000,
      lon: 9.750000,
      status: "good",
      summary: "Manuelt flyttet GFS 0.25 atmos-grid lenger sor for Saltstein for a representere en mer apen plassering ute mot havet."
    },
    {
      name: "Saltstein ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Saltstein",
      lat: 58.750000,
      lon: 9.812500,
      status: "good",
      summary: "Manuelt flyttet DWD ICON-EU-grid lenger sor for Saltstein for a representere en mer apen plassering ute mot havet."
    },
    {
      name: "Saltstein NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Saltstein",
      lat: 58.922376,
      lon: 9.843391,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid med faktisk ws/wdir-data til Yr-vindpunktet ved Saltstein. Ligger ca. 6,0 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Saltstein DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Saltstein",
      lat: 58.900000,
      lon: 9.750002,
      status: "good",
      summary: "Bedre DMI WAM NSB-grid for vind ved Saltstein. Dette punktet ligger sorvest for dagens Yr-vindpunkt og matcher Yr langt bedre enn den gamle cellen lenger inne i fjorden."
    },
    {
      name: "Sjosanden Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.020000,
      lon: 7.450000,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast brukt som vindkilde i forecast-tabellen for Mandal / Sjosanden."
    },
    {
      name: "Sjosanden gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.000000,
      lon: 7.500000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Sjosanden. Ligger ca. 3,7 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Sjosanden ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.000000,
      lon: 7.437500,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Sjosanden. Ligger ca. 2,3 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Sjosanden NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Mandal / Sjosanden",
      lat: 57.940692,
      lon: 7.475091,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid med faktisk ws/wdir-data til Yr-vindpunktet ved Sjosanden. Ligger ca. 8,9 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Sjosanden DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.000000,
      lon: 7.416668,
      status: "good",
      summary: "Naermeste DMI WAM NSB-grid for vind ved Sjosanden. Ligger ca. 3,0 km fra Yr-vindpunktet og dekker time-for-time videre enn dagens Yr-opplosning i popupen."
    },
    {
      name: "Hoddevik Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Ervika",
      lat: 62.123,
      lon: 5.161,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast tilgjengelig under Vind for pa spot-siden for Stad. Dette er standardvalget."
    },
    {
      name: "Ervik Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Ervika",
      lat: 62.166,
      lon: 5.114,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Stad."
    },
    {
      name: "Ervika gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Ervika",
      lat: 62.250000,
      lon: 5.000000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Ervika. Ligger ca. 11,1 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Ervika ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Ervika",
      lat: 62.187500,
      lon: 5.125000,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Ervika. Ligger ca. 2,4 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Ervika NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Ervika",
      lat: 62.215805,
      lon: 5.133561,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid med faktisk ws/wdir-data til Yr-vindpunktet ved Ervika. Ligger ca. 5,6 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Ervika DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Ervika",
      lat: 62.150000,
      lon: 5.083335,
      status: "good",
      summary: "Naermeste DMI WAM NSB-grid for vind ved Ervika. Ligger ca. 2,4 km fra Yr-vindpunktet og ser ut som en brukbar DMI-kandidat."
    },
    {
      name: "Alnes fyr Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.489,
      lon: 5.962,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast tilgjengelig under Vind for pa spot-siden for Alesund. Dette er standardvalget."
    },
    {
      name: "Flø Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.406,
      lon: 5.849,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Alesund."
    },
    {
      name: "Vigra Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.559,
      lon: 6.113,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Alesund."
    },
    {
      name: "Alnes gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.500000,
      lon: 6.000000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Alnes / Godoy. Ligger ca. 2,0 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Alnes ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.500000,
      lon: 5.937500,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Alnes / Godoy. Ligger ca. 1,8 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Alnes NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.490154,
      lon: 6.040122,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid til Yr-vindpunktet ved Alnes / Godoy. Ligger ca. 3,8 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Alnes DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.500000,
      lon: 6.000001,
      status: "good",
      summary: "Naermeste DMI WAM NSB-grid for vind ved Alnes / Godoy. Ligger ca. 2,0 km fra Yr-vindpunktet og gir time-for-time DMI-vind."
    },
    {
      name: "Hustadvika Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.991667,
      lon: 7.150000,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast brukt som vindkilde i forecast-tabellen for Hustadvika."
    },
    {
      name: "Hustadvika gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 63.000000,
      lon: 7.250000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Hustadvika. Ligger ca. 5,1 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Hustadvika ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 63.000000,
      lon: 7.125000,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Hustadvika. Ligger ca. 1,6 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Hustadvika NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.992319,
      lon: 7.028400,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid med faktisk ws/wdir-data til Yr-vindpunktet ved Hustadvika. Ligger ca. 6,1 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Hustadvika DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 63.000000,
      lon: 7.166668,
      status: "good",
      summary: "Naermeste DMI WAM NSB-grid for vind ved Hustadvika. Ligger ca. 1,3 km fra Yr-vindpunktet og er den naermeste DMI-kandidaten jeg fant."
    },
    {
      name: "Unstad Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Unstad Beach",
      lat: 68.269,
      lon: 13.582,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast tilgjengelig under Vind for pa spot-siden for Lofoten. Dette er standardvalget."
    },
    {
      name: "Flakstad Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Unstad Beach",
      lat: 68.104,
      lon: 13.288,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Lofoten."
    },
    {
      name: "Laukvika Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Unstad Beach",
      lat: 68.390,
      lon: 14.408,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Lofoten."
    },
    {
      name: "Bleik Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Unstad Beach",
      lat: 69.272,
      lon: 15.942,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Lofoten."
    },
    {
      name: "Unstad gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Unstad Beach",
      lat: 68.250000,
      lon: 13.500000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Unstad. Ligger ca. 3,6 km fra Yr-punktet og brukes til vindsammenlikning mot Yr, GFS wave og DMI."
    },
    {
      name: "Unstad ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Unstad Beach",
      lat: 68.250000,
      lon: 13.562500,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Unstad. Ligger ca. 2,0 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Unstad NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Unstad Beach",
      lat: 68.258937,
      lon: 13.432605,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid med faktisk ws/wdir-data til Yr-vindpunktet ved Unstad. Ligger ca. 5,9 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og DMI."
    },
    {
      name: "Unstad DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Unstad Beach",
      lat: 68.250000,
      lon: 13.500000,
      status: "ok",
      summary: "Naermeste DMI WAM NATLANT-grid for vind ved Unstad. Ligger ca. 3,6 km fra Yr-vindpunktet; dette var den eneste DMI-kilden med fornuftig nordlig dekning her."
    },
    {
      name: "Vardø Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Persfjord",
      lat: 70.366,
      lon: 31.126,
      status: "good",
      summary: "Punktvarsel fra Yr locationforecast tilgjengelig under Vind for pa spot-siden for Varanger. Dette er standardvalget."
    },
    {
      name: "Berlevåg Yr vindpunkt",
      provider: "Yr",
      linkedSpot: "Persfjord",
      lat: 70.857,
      lon: 29.100,
      status: "good",
      summary: "Alternativt Yr-punkt tilgjengelig under Vind for pa spot-siden for Varanger."
    },
    {
      name: "Persfjord gfs atmos 0.25 punkt",
      provider: "gfs atmos 0.25",
      linkedSpot: "Persfjord",
      lat: 70.250000,
      lon: 31.000000,
      status: "good",
      summary: "Naermeste GFS 0.25 atmos-grid til Yr-vindpunktet ved Persfjord. Ligger ca. 12,0 km fra Yr-punktet og brukes til vindsammenlikning mot Yr og GFS wave. DMI-kolonnen holdes tom her fordi DMI-punktet ikke er brukbart."
    },
    {
      name: "Persfjord ICON-EU punkt",
      provider: "ICON-EU",
      linkedSpot: "Persfjord",
      lat: 70.375000,
      lon: 31.062500,
      status: "good",
      summary: "Naermeste DWD ICON-EU-grid til Yr-vindpunktet ved Persfjord. Ligger ca. 2,1 km fra Yr-punktet og brukes til vindsammenlikning i popup-tabellen."
    },
    {
      name: "Persfjord NOAA vindpunkt",
      provider: "NOAA vind",
      linkedSpot: "Persfjord",
      lat: 70.339363,
      lon: 31.128288,
      status: "good",
      summary: "Naermeste NOAA GFS Wave Arctic 9km-grid til Yr-vindpunktet ved Persfjord. Ligger ca. 3,5 km fra Yr-punktet og brukes til vindsammenlikning mot Yr. DMI-kolonnen holdes tom her fordi DMI-punktet ikke er brukbart."
    },
    {
      name: "Persfjord DMI vindpunkt",
      provider: "DMI vind",
      linkedSpot: "Persfjord",
      lat: 70.250000,
      lon: 30.000000,
      status: "bad",
      summary: "Beste DMI WAM NATLANT-snap jeg fant rundt Persfjord ligger ca. 41 km fra Yr-vindpunktet. Forsok nord og ost snapper enten tilbake hit eller til 70.50 / 30.00, og de aktuelle WAM-svarene kommer med null vindverdier, sa punktet er ikke en brukbar erstatning."
    },
    {
      name: "Lista Fyr",
      provider: "Frost",
      linkedSpot: "Lista",
      lat: 58.109,
      lon: 6.5675,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Lista Fyr",
      provider: "Kystverket",
      linkedSpot: "Lista",
      lat: 58.109,
      lon: 6.5675,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Søndre Katland",
      provider: "Kystverket",
      linkedSpot: "Lista",
      lat: 58.056939,
      lon: 6.840388,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Lindesnes Fyr",
      provider: "Frost",
      linkedSpot: "Mandal / Sjosanden",
      lat: 57.9815,
      lon: 7.048,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Lindesnes Fyr",
      provider: "Kystverket",
      linkedSpot: "Mandal / Sjosanden",
      lat: 57.9815,
      lon: 7.048,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Eigerøya",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.43517,
      lon: 5.87183,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Eigerøya",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.43517,
      lon: 5.87183,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Obrestad Fyr",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.6585044,
      lon: 5.554561,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Obrestad Fyr",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.658504,
      lon: 5.5553,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vigdel",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.85197,
      lon: 5.55158,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Sola",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.8843,
      lon: 5.637,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Sola",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.8843,
      lon: 5.637,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Kvitsøy - Nordbø",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.0705,
      lon: 5.4122,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Kvitsøy - Nordbø",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.0705,
      lon: 5.4122,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Hemnes",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.203132,
      lon: 5.171293,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Hemnes",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.203132,
      lon: 5.171293,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Utsira Fyr",
      provider: "Frost",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.3065,
      lon: 4.8723,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Utsira Fyr",
      provider: "Kystverket",
      linkedSpot: "Pigsty/Piggy",
      lat: 59.3065,
      lon: 4.8723,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Jomfruland",
      provider: "Frost",
      linkedSpot: "Saltstein",
      lat: 58.86509,
      lon: 9.59637,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Jomfruland",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 58.86509,
      lon: 9.59637,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Fugløya",
      provider: "Frost",
      linkedSpot: "Saltstein",
      lat: 58.980574,
      lon: 9.803816,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Fugløya",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 58.980574,
      lon: 9.803816,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Svenner Fyr",
      provider: "Frost",
      linkedSpot: "Saltstein",
      lat: 58.9688,
      lon: 10.148,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Svenner Fyr",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 58.9688,
      lon: 10.148,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Strømtangen Fyr",
      provider: "Frost",
      linkedSpot: "Saltstein",
      lat: 59.151546,
      lon: 10.828299,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Strømtangen Fyr",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 59.151546,
      lon: 10.828299,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vikertangen",
      provider: "Kystverket",
      linkedSpot: "Saltstein",
      lat: 59.032431,
      lon: 10.945201,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vågsfjorden",
      provider: "Kystverket",
      linkedSpot: "Ervika",
      lat: 61.93608,
      lon: 5.00729,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Kråkenes",
      provider: "Frost",
      linkedSpot: "Ervika",
      lat: 62.034,
      lon: 4.9865,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Kråkenes",
      provider: "Kystverket",
      linkedSpot: "Ervika",
      lat: 62.034,
      lon: 4.9865,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Svinøy Fyr",
      provider: "Frost",
      linkedSpot: "Ervika",
      lat: 62.3293,
      lon: 5.268,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner, og gjenbrukes også for Ålesund."
    },
    {
      name: "Svinøy Fyr",
      provider: "Kystverket",
      linkedSpot: "Ervika",
      lat: 62.3293,
      lon: 5.268,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner, og gjenbrukes også for Ålesund."
    },
    {
      name: "Svinøy Fyr",
      provider: "Frost",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.3293,
      lon: 5.268,
      status: "good",
      summary: "Serie fra Frost. Gjenbrukes for Ålesund fordi stasjonen også skal kunne brukes for Alnes."
    },
    {
      name: "Svinøy Fyr",
      provider: "Kystverket",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.3293,
      lon: 5.268,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Gjenbrukes for Ålesund fordi stasjonen også skal kunne brukes for Alnes."
    },
    {
      name: "Vigra",
      provider: "Frost",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.5617,
      lon: 6.115,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vigra",
      provider: "Kystverket",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.5617,
      lon: 6.115,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Ona II",
      provider: "Frost",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.8585,
      lon: 6.5378,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Ona II",
      provider: "Kystverket",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.8585,
      lon: 6.5378,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Finnøya",
      provider: "Frost",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.80422,
      lon: 6.509046,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Finnøya",
      provider: "Kystverket",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 62.80422,
      lon: 6.509046,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Røst Lufthavn",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 67.5267,
      lon: 12.1038,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Røst Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 67.5267,
      lon: 12.1038,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Bodø Havn",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 67.284552,
      lon: 14.364365,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Helligvær II",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 67.4048,
      lon: 13.8958,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Helligvær II",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 67.4048,
      lon: 13.8958,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Leknes Lufthavn",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 68.1557873,
      lon: 13.61214,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Leknes Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 68.155787,
      lon: 13.61214,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Værøy Heliport",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 67.6527,
      lon: 12.7228,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Værøy Heliport",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 67.6527,
      lon: 12.7228,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Bø I Vesterålen III",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 68.6072,
      lon: 14.4347,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Anda fyr",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 69.066442,
      lon: 15.17019,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Anda fyr",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 69.066442,
      lon: 15.17019,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Andøya",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 69.3073,
      lon: 16.1312,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Andøya",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 69.3073,
      lon: 16.1312,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Hekkingen Fyr",
      provider: "Frost",
      linkedSpot: "Unstad Beach",
      lat: 69.6005,
      lon: 17.83117,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Hekkingen Fyr",
      provider: "Kystverket",
      linkedSpot: "Unstad Beach",
      lat: 69.6005,
      lon: 17.83117,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vadsø Lufthavn",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.0653,
      lon: 29.8352,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vadsø Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.0653,
      lon: 29.8352,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Slettnes Fyr",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 71.0888,
      lon: 28.217,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Slettnes Fyr",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 71.0888,
      lon: 28.217,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Berlevåg Lufthavn",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.873148,
      lon: 29.042397,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Berlevåg Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.873148,
      lon: 29.042397,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Makkaur Fyr",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.7057,
      lon: 30.07,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Makkaur Fyr",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.7057,
      lon: 30.07,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vardø Lufthavn",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.3512896,
      lon: 31.0502314,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vardø Lufthavn",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.35129,
      lon: 31.050231,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vardø Radio",
      provider: "Frost",
      linkedSpot: "Persfjord",
      lat: 70.3707,
      lon: 31.0962,
      status: "good",
      summary: "Serie fra Frost. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Vardø Radio",
      provider: "Kystverket",
      linkedSpot: "Persfjord",
      lat: 70.3707,
      lon: 31.0962,
      status: "good",
      summary: "Øyeblikks- og frioppløste vinddata fra Kystverket. Brukes i sammenslått live-kolonne for observasjoner."
    },
    {
      name: "Tregde",
      provider: "Kartverket tidevann",
      linkedSpot: "Lista",
      lat: 58.006377,
      lon: 7.554759,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Lista. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Sandnes",
      provider: "Kartverket tidevann",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.868232,
      lon: 5.746613,
      status: "good",
      summary: "Valgt permanente tidevannsstasjon for Jæren/Piggy. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Helgeroa",
      provider: "Kartverket tidevann",
      linkedSpot: "Saltstein",
      lat: 58.995212,
      lon: 9.856379,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Saltstein. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Maloy",
      provider: "Kartverket tidevann",
      linkedSpot: "Ervika",
      lat: 61.933776,
      lon: 5.113310,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Ervika. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Alesund",
      provider: "Kartverket tidevann",
      linkedSpot: "Alnes Lighthouse (Godoy)",
      lat: 62.469414,
      lon: 6.151946,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Alnes/Godoy. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Kristiansund",
      provider: "Kartverket tidevann",
      linkedSpot: "Hustadvika Gjestegard",
      lat: 63.113920,
      lon: 7.736140,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Hustadvika. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Kabelvag",
      provider: "Kartverket tidevann",
      linkedSpot: "Unstad Beach",
      lat: 68.212639,
      lon: 14.482149,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Unstad. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Vardo",
      provider: "Kartverket tidevann",
      linkedSpot: "Persfjord",
      lat: 70.374978,
      lon: 31.104015,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Persfjord. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Sjosanden DKSS testpunkt",
      provider: "DMI DKSS",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.011000,
      lon: 7.455000,
      status: "good",
      summary: "Lokalt testpunkt for Sjosanden. Returnerer DKSS-serie og brukes kun til test mot Tregde akkurat na."
    },
    {
      name: "Tregde",
      provider: "Kartverket tidevann",
      linkedSpot: "Mandal / Sjosanden",
      lat: 58.006377,
      lon: 7.554759,
      status: "good",
      summary: "Naermeste permanente tidevannsstasjon for Mandal / Sjosanden. Brukes for tidevann ved stasjonen."
    },
    {
      name: "Lista DKSS gridpunkt",
      provider: "DMI DKSS",
      linkedSpot: "Lista",
      lat: 58.090000,
      lon: 6.560000,
      status: "good",
      summary: "Manuelt testpunkt for DMI sea-mean-deviation ved Lista. Fungerende kandidat soervest for forrige testpunkt, brukt for aa sammenlikne gammel laast DKSS-celle mot nytt punkt."
    },
    {
      name: "Jaeren DKSS gridpunkt",
      provider: "DMI DKSS",
      linkedSpot: "Pigsty/Piggy",
      lat: 58.751998,
      lon: 5.471719,
      status: "good",
      summary: "Manuelt testpunkt for DMI sea-mean-deviation ved Jaeren/Piggy. Brukes for aa sammenlikne gammel laast DKSS-celle mot nytt punkt."
    },
    {
      name: "Saltstein DKSS gridpunkt",
      provider: "DMI DKSS",
      linkedSpot: "Saltstein",
      lat: 58.967206,
      lon: 9.809798,
      status: "good",
      summary: "Manuelt testpunkt for DMI sea-mean-deviation ved Saltstein. Brukes for aa sammenlikne gammel laast DKSS-celle mot nytt punkt."
    }
  ]
};
