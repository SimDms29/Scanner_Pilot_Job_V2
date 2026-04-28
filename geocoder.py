import sqlite3
import logging

log = logging.getLogger(__name__)

DB_FILE = "aerowatch.db"
FALLBACK = (48.5, 10.0)

KNOWN_COORDS: dict[str, tuple[float, float]] = {
    # France
    "paris cdg": (49.0097, 2.5478),
    "paris orly": (48.7262, 2.3652),
    "paris": (48.8566, 2.3522),
    "le bourget": (48.9697, 2.4411),
    "guyancourt": (48.7729, 2.0696),
    "nice": (43.7102, 7.2620),
    "lyon": (45.7640, 4.8357),
    "marseille": (43.2965, 5.3698),
    "toulouse": (43.6047, 1.4442),
    "rennes": (48.1173, -1.6778),
    "nantes": (47.2184, -1.5536),
    "bordeaux": (44.8378, -0.5792),
    "brest": (48.3904, -4.8861),
    "strasbourg": (48.5734, 7.7521),
    "mulhouse": (47.7508, 7.3359),
    "bâle-mulhouse": (47.5896, 7.5290),
    "chambéry": (45.5646, 5.9178),
    "chambery": (45.5646, 5.9178),
    "clermont-ferrand": (45.7772, 3.0870),
    "saint-denis": (-20.8823, 55.4504),
    "réunion": (-20.8823, 55.4504),
    "france": (46.2276, 2.2137),
    # Suisse
    "genève": (46.2044, 6.1432),
    "geneve": (46.2044, 6.1432),
    "geneva": (46.2044, 6.1432),
    "zurich": (47.3769, 8.5417),
    "berne": (46.9481, 7.4474),
    "lugano": (46.0037, 8.9511),
    "meyrin": (46.2338, 6.0622),
    "lausanne": (46.5197, 6.6323),
    "kloten": (47.4500, 8.5667),
    # Luxembourg
    "luxembourg": (49.6117, 6.1319),
    "senningerberg": (49.6333, 6.2167),
    # Belgique
    "bruxelles": (50.8503, 4.3517),
    "charleroi": (50.4614, 4.4446),
    "liège": (50.6292, 5.5797),
    "liege": (50.6292, 5.5797),
    "belgium": (50.8503, 4.3517),
    # Allemagne
    "francfort": (50.1109, 8.6821),
    "frankfurt": (50.1109, 8.6821),
    "munich": (48.1351, 11.5820),
    "berlin": (52.5200, 13.4050),
    "düsseldorf": (51.2217, 6.7762),
    "dusseldorf": (51.2217, 6.7762),
    "cologne": (50.9333, 6.9500),
    "köln": (50.9333, 6.9500),
    "koln": (50.9333, 6.9500),
    "stuttgart": (48.7758, 9.1829),
    "hambourg": (53.5753, 10.0153),
    "hamburg": (53.5753, 10.0153),
    "zweibrücken": (49.2092, 7.3600),
    "zweibrucken": (49.2092, 7.3600),
    # Pays-Bas
    "amsterdam": (52.3676, 4.9041),
    # UK
    "londres heathrow": (51.4700, -0.4543),
    "Londres Heathrow": (51.4700, -0.4543),
    "london heathrow": (51.4700, -0.4543),
    "london, gb": (51.5074, -0.1278),
    "london": (51.5074, -0.1278),
    "londres": (51.5074, -0.1278),
    "oxford": (51.7520, -1.2577),
    "manchester": (53.3498, -2.2799),
    # Espagne
    "madrid": (40.4168, -3.7038),
    "barcelone": (41.3851, 2.1734),
    "barcelona": (41.3851, 2.1734),
    # Portugal
    "lisbonne": (38.7223, -9.1393),
    "lisbon": (38.7223, -9.1393),
    # Italie
    "milan malpensa": (45.6301, 8.7231),
    "milan linate": (45.4449, 9.2766),
    "milan": (45.4654, 9.1859),
    "rome": (41.9028, 12.4964),
    # Autriche
    "vienne": (48.2082, 16.3738),
    "vienna": (48.2082, 16.3738),
    # République Tchèque
    "prague": (50.0755, 14.4378),
    # Scandinavie
    "copenhague": (55.6761, 12.5683),
    "oslo": (59.9139, 10.7522),
    "stockholm": (59.3293, 18.0686),
    # Défaut
    "europe": (48.5, 10.0),
    "n/c": (48.5, 10.0),
    "new york": (40.7128, -74.0060),
}

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    _geolocator = Nominatim(user_agent="aerowatch/1.0")
    _geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1)
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


def _nominatim_lookup(location: str) -> tuple[float, float] | None:
    if not GEOPY_AVAILABLE:
        return None
    try:
        result = _geocode(location)
        if result:
            return result.latitude, result.longitude
    except Exception as e:
        log.warning(f"Nominatim error for '{location}': {e}")
    return None


def get_coords(location: str) -> tuple[float, float]:
    if not location:
        return FALLBACK

    loc_clean = location.strip()
    loc_low = loc_clean.lower()

    # 1. Static dict (fast path)
    for key, coords in KNOWN_COORDS.items():
        if key in loc_low:
            return coords

    # 2. SQLite geocache
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT lat, lon FROM geocache WHERE LOWER(location) = ?", (loc_low,)
        ).fetchone()
        if row:
            return row[0], row[1]

    # 3. Nominatim (rate-limited, result cached)
    coords = _nominatim_lookup(loc_clean)
    if coords:
        lat, lon = coords
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO geocache (location, lat, lon) VALUES (?, ?, ?)",
                (loc_low, lat, lon),
            )
        return lat, lon

    return FALLBACK
