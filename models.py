from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobOffer:
    id: str
    title: str
    link: str
    source: str
    location: str = "N/C"
    status: str = "active"   # active | full | expired
    lat: float = 48.5
    lon: float = 10.0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    notified: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "source": self.source,
            "location": self.location,
            "status": self.status,
            "lat": self.lat,
            "lon": self.lon,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }
