"""Module Google Business Profile : récupération paginée des avis Google.

Authentification OAuth 2.0 via refresh_token stocké en variable d'environnement.
La Places API plafonne à 5 avis ; ce module accède à TOUS les avis du Business
Profile (74+ pour Le Chérimoya).

Variables d'environnement requises :
    GOOGLE_BUSINESS_CLIENT_ID
    GOOGLE_BUSINESS_CLIENT_SECRET
    GOOGLE_BUSINESS_REFRESH_TOKEN

Variables optionnelles (sinon découvertes à la volée) :
    GOOGLE_BUSINESS_ACCOUNT_ID   ex: "accounts/123456789"
    GOOGLE_BUSINESS_LOCATION_ID  ex: "locations/987654321"
"""
import os
import time
import requests

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
ACCOUNTS_URL = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
LOCATIONS_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"
REVIEWS_URL = "https://mybusiness.googleapis.com/v4"


class GoogleBusinessEngine:
    """Client minimal pour l'API Google Business Profile.

    Le refresh token est échangé contre un access token court (1h) à la
    demande. Les avis sont paginés (50/page) et agrégés dans une seule liste.
    """

    def __init__(self):
        self.client_id = os.getenv('GOOGLE_BUSINESS_CLIENT_ID', '').strip()
        self.client_secret = os.getenv('GOOGLE_BUSINESS_CLIENT_SECRET', '').strip()
        self.refresh_token = os.getenv('GOOGLE_BUSINESS_REFRESH_TOKEN', '').strip()
        self.account_id = os.getenv('GOOGLE_BUSINESS_ACCOUNT_ID', '').strip()
        self.location_id = os.getenv('GOOGLE_BUSINESS_LOCATION_ID', '').strip()
        self._access_token = None
        self._access_token_expires_at = 0

    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def _get_access_token(self):
        if self._access_token and time.time() < self._access_token_expires_at - 60:
            return self._access_token
        resp = requests.post(
            OAUTH_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"OAuth refresh failed: HTTP {resp.status_code} - {resp.text[:300]}")
        data = resp.json()
        self._access_token = data["access_token"]
        self._access_token_expires_at = time.time() + int(data.get("expires_in", 3600))
        return self._access_token

    def _authed_get(self, url, params=None):
        token = self._get_access_token()
        return requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=15)

    def discover_account(self):
        """Renvoie le name du premier compte business (ex: 'accounts/123')."""
        if self.account_id:
            return self.account_id
        resp = self._authed_get(ACCOUNTS_URL)
        if resp.status_code != 200:
            raise RuntimeError(f"List accounts failed: HTTP {resp.status_code} - {resp.text[:300]}")
        accounts = resp.json().get("accounts", [])
        if not accounts:
            raise RuntimeError("Aucun compte Google Business Profile lié à ce refresh token.")
        self.account_id = accounts[0]["name"]
        return self.account_id

    def discover_location(self):
        """Renvoie le name de la première location (ex: 'locations/987')."""
        if self.location_id:
            return self.location_id
        account = self.discover_account()
        url = f"{LOCATIONS_URL}/{account}/locations"
        resp = self._authed_get(url, params={"readMask": "name,title"})
        if resp.status_code != 200:
            raise RuntimeError(f"List locations failed: HTTP {resp.status_code} - {resp.text[:300]}")
        locations = resp.json().get("locations", [])
        if not locations:
            raise RuntimeError("Aucune location trouvée sur ce compte Business Profile.")
        self.location_id = locations[0]["name"]
        return self.location_id

    def fetch_all_reviews(self, max_pages=10):
        """Récupère tous les avis paginés (50/page, max_pages pages = 500 avis).

        Retourne dict : {rating, total, reviews: [{author_name, rating, text,
        publishTime, relative_time}]}
        """
        account = self.discover_account()
        location = self.discover_location()
        url = f"{REVIEWS_URL}/{account}/{location}/reviews"

        all_reviews = []
        page_token = None
        avg_rating = None
        total_count = 0
        for _ in range(max_pages):
            params = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token
            resp = self._authed_get(url, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"List reviews failed: HTTP {resp.status_code} - {resp.text[:300]}")
            payload = resp.json()
            for r in payload.get("reviews", []):
                text = (r.get("comment") or "").strip()
                if not text:
                    continue
                star_map = {
                    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
                    "STAR_RATING_UNSPECIFIED": 0
                }
                stars = star_map.get(r.get("starRating", "STAR_RATING_UNSPECIFIED"), 0)
                reviewer = r.get("reviewer", {}) or {}
                all_reviews.append({
                    "author_name": reviewer.get("displayName", "Client Google"),
                    "rating": stars,
                    "text": text,
                    "publishTime": r.get("createTime", ""),
                    "relative_time": ""  # Business Profile ne fournit pas de chaîne relative
                })
            avg_rating = payload.get("averageRating", avg_rating)
            total_count = payload.get("totalReviewCount", total_count)
            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        # Tri par date décroissante (plus récent en premier)
        all_reviews.sort(key=lambda r: r.get("publishTime", ""), reverse=True)

        return {
            "rating": round(float(avg_rating), 1) if avg_rating is not None else None,
            "total": int(total_count) if total_count else len(all_reviews),
            "reviews": all_reviews,
        }
