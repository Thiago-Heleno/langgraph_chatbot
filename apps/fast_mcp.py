import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("Demo 🚀")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

_genre_cache: dict[str, int] | None = None


def _tmdb_get(path: str, params: dict | None = None) -> dict:
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not set in the environment")
    response = httpx.get(
        f"{TMDB_BASE_URL}{path}",
        params={**(params or {}), "api_key": TMDB_API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _get_genre_map() -> dict[str, int]:
    global _genre_cache
    if _genre_cache is None:
        data = _tmdb_get("/genre/movie/list", {"language": "en-US"})
        _genre_cache = {genre["name"].lower(): genre["id"] for genre in data["genres"]}
    return _genre_cache


@mcp.tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '2 + 2 * 3'."""
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: only basic arithmetic is allowed"
    return str(eval(expression))


@mcp.tool
def list_movie_genres() -> list[dict]:
    """List all official TMDB movie genres with their ids and names.

    Call this first to discover valid genre names to pass to recommend_movies.
    """
    data = _tmdb_get("/genre/movie/list", {"language": "en-US"})
    return data["genres"]


@mcp.tool
def search_movie(query: str, limit: int = 5) -> list[dict]:
    """Search for movies by title and return matches with their TMDB movie id.

    Use the returned id with get_similar_movies for 'more like this' recommendations.
    """
    data = _tmdb_get("/search/movie", {"query": query, "language": "en-US", "page": 1})
    results = data.get("results", [])[:limit]
    return [
        {
            "id": movie["id"],
            "title": movie["title"],
            "release_date": movie.get("release_date"),
            "rating": movie.get("vote_average"),
            "overview": movie.get("overview"),
        }
        for movie in results
    ]


@mcp.tool
def recommend_movies(
    genre: str | None = None,
    min_rating: float = 0.0,
    year: int | None = None,
    sort_by: str = "popularity.desc",
    limit: int = 10,
) -> list[dict]:
    """Recommend movies, optionally filtered by genre, minimum rating, and release year.

    genre: a genre name from list_movie_genres, e.g. 'Comedy' or 'Action'.
    sort_by: TMDB discover sort option, e.g. 'popularity.desc', 'vote_average.desc', 'release_date.desc'.
    """
    params = {
        "language": "en-US",
        "sort_by": sort_by,
        "vote_average.gte": min_rating,
        "vote_count.gte": 50,
        "page": 1,
    }
    if genre:
        genre_id = _get_genre_map().get(genre.lower())
        if genre_id is None:
            return [{"error": f"Unknown genre '{genre}'. Call list_movie_genres for valid options."}]
        params["with_genres"] = genre_id
    if year:
        params["primary_release_year"] = year

    data = _tmdb_get("/discover/movie", params)
    results = data.get("results", [])[:limit]
    return [
        {
            "id": movie["id"],
            "title": movie["title"],
            "release_date": movie.get("release_date"),
            "rating": movie.get("vote_average"),
            "overview": movie.get("overview"),
        }
        for movie in results
    ]


@mcp.tool
def get_similar_movies(movie_id: int, limit: int = 10) -> list[dict]:
    """Get movies similar to a given TMDB movie id, for 'more like this' recommendations."""
    data = _tmdb_get(f"/movie/{movie_id}/similar", {"language": "en-US", "page": 1})
    results = data.get("results", [])[:limit]
    return [
        {
            "id": movie["id"],
            "title": movie["title"],
            "release_date": movie.get("release_date"),
            "rating": movie.get("vote_average"),
            "overview": movie.get("overview"),
        }
        for movie in results
    ]


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.environ.get("MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("MCP_PORT", "7000")),
        show_banner=False,
    )
