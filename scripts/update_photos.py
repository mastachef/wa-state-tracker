#!/usr/bin/env python3
"""Update legislator photos with official WA Legislature photos."""

import json

# Mapping of legislator names to their official IDs from leg.wa.gov
LEGISLATOR_IDS = {
    # Senators
    "Emily Alvarado": 34024,
    "Jessica Bateman": 17117,
    "Matt Boehnke": 29094,
    "John Braun": 17289,
    "Mike Chapman": 26176,
    "Leonard Christian": 18458,
    "Annette Cleveland": 17294,
    "Steve Conway": 972,
    "Adrian Cortes": 35473,
    "Manka Dhingra": 28022,
    "Perry Dozier": 31535,
    "Drew Hansen": 16499,
    "Paul Harris": 15813,
    "Bob Hasegawa": 10030,
    "Jeff Holy": 17223,
    "Victoria Hunt": 35410,
    "Claudia Kauffman": 12073,
    "Curtis King": 13199,
    "Deborah Krishnadasan": 35470,
    "Liz Lovelett": 29548,
    "John Lovick": 3476,
    "Drew MacEwen": 17221,
    "Jamie Pedersen": 12002,
    "Marcus Riccelli": 15706,
    "June Robinson": 18265,
    "Rebecca Saldaña": 29089,
    "Jesse Salomon": 29089,
    "Mark Schoesler": 652,
    "Sharon Shewmake": 29108,
    "Shelly Short": 11952,
    "Vandana Slatter": 27504,
    "Derek Stanford": 15809,
    "Yasmin Trudeau": 20732,
    "Javier Valdez": 27975,
    "Keith Wagoner": 28317,
    "Judy Warnick": 12084,
    "Lisa Wellman": 27211,
    "Claire Wilson": 29090,
    "Jeff Wilson": 31537,
    "Chris Gildon": 29101,
    "Keith Goehner": 29096,
    "Noel Frame": 23902,
    "T'wina Nobles": 31536,
    "Ron Muzzall": 29908,
    "Nikki Torres": 34047,
    "Marko Liias": 13546,
    "Tina Orwall": 14205,
    "Phil Fortunato": 3474,
    "Jim McCune": 2584,

    # House Representatives
    "Peter Abbarno": 31526,
    "Hunter Abell": 35407,
    "Andrew Barkis": 24075,
    "Stephanie Barnard": 34025,
    "April Berg": 31534,
    "Steve Bergquist": 17227,
    "Adam Bernbaum": 34240,
    "Liz Berry": 31531,
    "Dan Bronoske": 31529,
    "Brian Burnett": 35408,
    "Lisa Callan": 29092,
    "Rob Chase": 31521,
    "April Connors": 34027,
    "Chris Corry": 29097,
    "Julio Cortes": 34028,
    "Travis Couture": 34029,
    "Lauren Davis": 29104,
    "Tom Dent": 20761,
    "Beth Doglio": 26175,
    "Brandy Donaghy": 33818,
    "Davina Duerr": 29877,
    "Jeremie Dufault": 29098,
    "Mary Dye": 21490,
    "Andrew Engell": 35409,
    "Debra Entenman": 11403,
    "Carolyn Eslick": 27988,
    "Darya Farivar": 34030,
    "Jake Fey": 17241,
    "Joe Fitzgibbon": 13198,
    "Mary Fosse": 31542,
    "Roger Goodman": 11999,
    "Jenny Graham": 29093,
    "Mia Gregerson": 18264,
    "Dan Griffey": 20752,
    "David Hackney": 31523,
    "Zach Hall": 27391,
    "Natasha Hill": 35429,
    "Cyndy Jacobsen": 31528,
    "Laurie Jinkins": 15817,
    "Michael Keaton": 35411,
    "Mark Klicker": 31524,
    "Shelley Kloba": 26168,
    "Mari Leavitt": 29102,
    "Debra Lekanoff": 29106,
    "John Ley": 35422,
    "Sam Low": 34031,
    "Nicole Macri": 26178,
    "Deb Manjarrez": 35412,
    "Matt Marshall": 35413,
    "Stephanie McClintock": 34032,
    "Joel McEntire": 31525,
    "Sharlett Mena": 27494,
    "Gloria Mendoza": 35414,
    "Melanie Morgan": 29103,
    "Greg Nance": 34760,
    "Edwin Obras": 35464,
    "Ed Orcutt": 7635,
    "Timm Ormsby": 9207,
    "Lillian Ortiz-Self": 18546,
    "Lisa Parshley": 35415,
    "Dave Paul": 29095,
    "Joshua Penner": 35416,
    "Strom Peterson": 20755,
    "Gerry Pollet": 16596,
    "Alex Ramel": 30127,
    "Julia Reed": 34033,
    "Kristine Reeves": 27182,
    "Adison Richards": 20893,
    "Skyler Rude": 20837,
    "Alicia Rule": 31533,
    "Cindy Ryu": 15736,
    "Osman Salahuddin": 35655,
    "Sharon Tomiko Santos": 3483,
    "Joe Schmick": 13209,
    "Suzanne Schmidt": 34035,
    "Shaun Scott": 35430,
    "Clyde Shavers": 34050,
    "Tarra Simmons": 31527,
    "Larry Springer": 10039,
    "Chris Stearns": 34023,
    "Mike Steele": 10546,
    "Drew Stokesbary": 20756,
    "Monica Jurado Stonier": 17279,
    "Chipalo Street": 34036,
    "David Stuebe": 35431,
    "Jamila Taylor": 31530,
    "My-Linh Thai": 29107,
    "Steve Tharinger": 15816,
    "Brianna Thomas": 15410,
    "Joe Timmons": 34037,
    "Michelle Valdez": 20760,
    "Mike Volz": 26170,
    "Amy Walen": 29109,
    "Jim Walsh": 27181,
    "Kevin Waters": 34038,
    "Sharon Wylie": 16462,
    "Alex Ybarra": 29318,
    "Janice Zahn": 35736,
}

def update_photos():
    """Update legislator photos in the JSON file."""
    with open('_data/legislators.json', 'r') as f:
        legislators = json.load(f)

    updated_count = 0
    not_found = []

    for leg in legislators:
        name = leg.get('name', '')
        if name in LEGISLATOR_IDS:
            leg_id = LEGISLATOR_IDS[name]
            leg['photo_url'] = f"https://leg.wa.gov/memberthumbnail/{leg_id}.jpg"
            updated_count += 1
        else:
            not_found.append(name)

    with open('_data/legislators.json', 'w') as f:
        json.dump(legislators, f, indent=2)

    print(f"Updated {updated_count} legislator photos")
    if not_found:
        print(f"\nCould not find IDs for {len(not_found)} legislators:")
        for name in not_found:
            print(f"  - {name}")

if __name__ == '__main__':
    update_photos()
