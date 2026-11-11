# NYC charter schools map

An interactive map of New York City charter schools, with a Success Academy filter. It is a static page: one HTML file, no server, no API key, public data only.

**Live page:** add your GitHub Pages link here once it is published.

## What it does

- Shows 288 charter schools as pins. Success Academy schools are large and indigo; all other charters are small and grey.
- Filters: All charters / Success Academy, borough, network, and a search box (school name, borough or district).
- Updates the count and the school list as filters change. Click a school in the list to zoom to it.
- Has an "About this data" section on the page that states sources, dates and limits.

## Data

| What | Source |
| --- | --- |
| Locations and names | NYC Department of Education school points file dated 2024-08-28 (from NYC Open Data). Charter schools are the 288 records with district code 84 in the school code. |
| Open Success Academy charters | NYS Education Department charter school list, updated 2025-10-02, used to cross-check the Success Academy names. |
| Borough | Taken from the letter in the school code (K, M, X, Q, R). |
| Network | Matched by words in the school name only. |

`charters.csv` is the cleaned dataset behind the map. `build_data.py` is the script that produced it.

## Known gaps

- **Two Success Academy names are unconfirmed.** The DOE file has "Fort Greene" and "Harlem 6". The state list has "Sheepshead Bay" and "Norwood" instead, and no Fort Greene or Harlem 6. These two show a note in their popups. Check them against Success Academy's own school list, then correct the names and remove the note.
- **Three Success Academy charters are not on the map.** NYC 15, NYC 17 and NYC 18 were approved to open in September 2026. Neither source has their locations.
- **The location data is from August 2024.** Schools that opened, closed or renamed since then may be missing or out of date. Schools other than Success Academy have not been checked against the state list.
- **No grades, enrollment or test results.** The location file does not include them.

## Publish on GitHub Pages

1. Put `index.html` (and the other files) in the root of a repository.
2. In the repository, open Settings, then Pages.
3. Under "Build and deployment", choose "Deploy from a branch", pick `main` and `/ (root)`, and save.
4. The page appears at `https://<your-username>.github.io/<repository-name>/` within a few minutes.

The map library is bundled inside `index.html`. Only the street map tiles (from CARTO) and the font (from Google Fonts) load from the internet, so the page needs a connection to show the street map. Without one, the pins and filters still work on a plain background.

## How this was built

- **Problem:** show where NYC charter schools are, with Success Academy easy to isolate, using only public data.
- **Tools:** built with Claude. Leaflet draws the map. The data is embedded in the page, so it needs no backend.
- **Data work:** found the public sources, extracted the charter records, finished names the file cut off at 50 characters, derived each borough from the school code, and cross-checked Success Academy against the state list.
- **Governance:** public data only. No student-level data. No API key or user data is stored or sent anywhere.
- **Checks:** no duplicate school codes, every record has a name, borough and district, and every coordinate falls inside New York City. In a headless browser, the filters returned the expected counts (38 Success Academy schools, 11 of them in Manhattan, 9 KIPP schools), and the empty state and popups worked.
- **What I would measure in a real internal tool:** how often people use each filter, how often they find the school they came for, and how often they report a wrong name or location.
