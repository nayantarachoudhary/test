"""Build the cleaned charter-school dataset from the NYC DOE school points shapefile.

Usage: python3 -I build_data.py <shapefile base path (no extension)> <output dir>
"""
import csv
import json
import re
import sys
from collections import Counter

import shapefile

BOROUGH = {"K": "Brooklyn", "M": "Manhattan", "X": "Bronx", "Q": "Queens", "R": "Staten Island"}

# The DOE file cuts names off at 50 characters. These fixes only finish the cut-off
# words; they do not rename anything.
NAME_FIXES = {
    "84K406": "EMBER Charter School for Mindful Education, Innovation and Transformation",
    "84K517": "Leadership Preparatory Bedford Stuyvesant Charter School",
    "84K593": "Excellence Boys Charter School of Bedford Stuyvesant",
    "84K733": "Math, Engineering, and Science Academy Charter High School",
    "84K784": "Achievement First North Brooklyn Preparatory Charter School",
    "84K792": "Cultural Arts Academy Charter School At Spring Creek",
    "84K807": "Collegiate Academy for Mathematics and Personal Awareness Charter School",
    "84K966": "Bedford Stuyvesant New Beginnings Charter School 2",
    "84K911": "Edmund W. Gordon Brooklyn Laboratory Charter School",
    "84M265": "Success Academy Charter School - Washington Heights",
    "84M284": "Harlem Children's Zone Promise Academy Charter School",
    "84M341": "Harlem Children's Zone Promise Academy II Charter School",
    "84Q339": "Success Academy Charter School - Springfield Gardens",
    "84R070": "Lois and Richard Nicotra Early College Charter School",
    "84X309": "South Bronx Charter School for International Cultures and the Arts",
    "84X389": "Bronx Global Learning Institute for Girls Charter School",
    "84X395": "NYC Charter High School for Architecture, Engineering & Construction Industries",
    "84X482": "Dr. Richard Izquierdo Health and Science Charter School",
    "84X611": "AECI II: NYC Charter High School for Computer Engineering and Innovation",
    "84X635": "Earl Monroe New Renaissance Basketball Charter School",
    # Four schools share this cut-off name; the borough shown beside it tells them apart.
    "84K738": "New Visions Charter High School for Advanced Math and Science",
    "84Q320": "New Visions Charter High School for Advanced Math and Science",
    "84X202": "New Visions Charter High School for Advanced Math and Science",
    "84X539": "New Visions Charter High School for Advanced Math and Science",
    "84K739": "New Visions Charter High School for the Humanities",
    "84Q373": "New Visions Charter High School for the Humanities",
    "84X208": "New Visions Charter High School for the Humanities",
    "84X553": "New Visions Charter High School for the Humanities",
}

# Networks are matched by words in the school name only.
NETWORK_RULES = [
    ("Success Academy", "success academy"),
    ("KIPP", "kipp"),
    ("Achievement First", "achievement first"),
    ("Ascend", "ascend"),
    ("Icahn", "icahn"),
    ("Zeta", "zeta charter"),
    ("Brilla", "brilla"),
    ("Democracy Prep", "democracy prep"),
    ("Harlem Village Academy", "harlem village academy"),
    ("Harlem Children's Zone", "harlem children"),
    ("DREAM", "dream charter"),
    ("Explore Schools", "explore "),
    ("Family Life Academy", "family life academy"),
    ("South Bronx Classical", "south bronx classical"),
    ("Brooklyn Prospect", "brooklyn prospect"),
]
OTHER = "Independent or other"

# Open Success Academy charters on the NYSED list updated Oct 2, 2025 (38).
NYSED_SA = [
    "Bed Stuy 1", "Bed Stuy 2", "Bed-Stuy 3", "Bensonhurst", "Bergen Beach", "Bronx 1", "Bronx 2",
    "Bronx 3", "Bronx 4", "Bronx 5 Lower", "Bronx 5 Upper", "Bushwick", "Cobble Hill",
    "Crown Heights", "Far Rockaway", "Flatbush", "Harlem 1", "Harlem 2", "Harlem 3", "Harlem 4",
    "Harlem 5", "Hell's Kitchen", "Hudson Yards", "Norwood", "NYC 12", "NYC 14", "NYC 5", "NYC 6",
    "NYC 7", "Prospect Heights", "Rosedale", "Sheepshead Bay", "South Jamaica",
    "Springfield Gardens", "Union Square", "Upper West", "Washington Heights", "Williamsburg",
]


def key(s):
    s = re.sub(r"(?i)^success academy charter school", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def network(name):
    low = name.lower()
    for label, needle in NETWORK_RULES:
        if low.startswith(needle) or needle in low:
            return label
    return OTHER


def main(shp_base, out_dir):
    r = shapefile.Reader(shp_base)
    fields = [f[0] for f in r.fields[1:]]
    rows = [dict(zip(fields, rec)) for rec in r.records()]
    charters = [x for x in rows if str(x["ATS"]).startswith("84")]

    out, problems = [], []
    nysed_keys = {key(n): n for n in NYSED_SA}
    matched_sa = set()
    for x in sorted(charters, key=lambda x: x["ATS"]):
        ats = str(x["ATS"]).strip()
        name = NAME_FIXES.get(ats, str(x["Name"]).strip())
        if len(str(x["Name"]).strip()) >= 49 and ats not in NAME_FIXES:
            problems.append(f"possible truncated name not fixed: {ats} {name}")
        boro = BOROUGH.get(ats[2])
        lat, lon = float(x["Latitude"]), float(x["Longitude"])
        if boro is None:
            problems.append(f"no borough for {ats}")
        if not (40.45 < lat < 40.95 and -74.3 < lon < -73.65):
            problems.append(f"coords outside NYC: {ats} {lat},{lon}")
        is_sa = name.lower().startswith("success academy")
        note = ""
        if is_sa:
            k = key(name)
            if k in nysed_keys:
                matched_sa.add(k)
            else:
                note = "Name unconfirmed: it is not on the NYS Education Department list from October 2025."
        out.append({
            "id": ats, "n": name, "b": boro, "d": int(x["Geographic"]),
            "la": round(lat, 6), "lo": round(lon, 6), "sa": is_sa,
            "nw": network(name), "note": note,
        })

    sa_rows = [o for o in out if o["sa"]]
    unmatched_nysed = [n for k, n in nysed_keys.items() if k not in matched_sa]

    with open(f"{out_dir}/charters.json", "w") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    with open(f"{out_dir}/charters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ats_code", "name", "borough", "community_school_district", "latitude",
                    "longitude", "success_academy", "network_by_name", "note"])
        for o in out:
            w.writerow([o["id"], o["n"], o["b"], o["d"], o["la"], o["lo"],
                        "yes" if o["sa"] else "no", o["nw"], o["note"]])

    print("charter records:", len(out))
    print("by borough:", dict(Counter(o["b"] for o in out)))
    print("success academy records:", len(sa_rows))
    print("SA matched to NYSED names:", len(matched_sa), "of", len(NYSED_SA))
    print("SA in DOE file but not on NYSED list:", [o["n"] for o in sa_rows if o["note"]])
    print("NYSED SA names with no DOE record:", unmatched_nysed)
    print("networks:", dict(Counter(o["nw"] for o in out).most_common()))
    print("duplicate ids:", [k for k, v in Counter(o["id"] for o in out).items() if v > 1])
    print("empty fields:", sum(1 for o in out if not o["n"] or not o["b"]))
    print("problems:", problems or "none")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
