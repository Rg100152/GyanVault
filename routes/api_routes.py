"""JSON API for live search, filtering, counters and publishing."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from database import connect, get_db

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLOWED_SORTS = {
    "latest": "created_at DESC, id DESC",
    "popular": "downloads DESC, views DESC, id DESC",
    "viewed": "views DESC, id DESC",
    "title": "title COLLATE NOCASE ASC",
}


@api_bp.route("/resources")
def list_resources():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    fmt = request.args.get("format", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    sort = request.args.get("sort", "latest").strip()
    try:
        limit = max(1, min(int(request.args.get("limit", 250)), 250))
    except (TypeError, ValueError):
        limit = 250

    clauses: list[str] = []
    params: list[str] = []

    if query:
        clauses.append(
            "(title LIKE ? OR description LIKE ? OR tags LIKE ? OR category LIKE ?)"
        )
        like = f"%{query}%"
        params.extend([like, like, like, like])
    if category:
        clauses.append("category = ?")
        params.append(category)
    if fmt:
        clauses.append("format = ?")
        params.append(fmt)
    if difficulty:
        clauses.append("difficulty = ?")
        params.append(difficulty)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = ALLOWED_SORTS.get(sort, ALLOWED_SORTS["latest"])
    sql = f"SELECT * FROM resources {where} ORDER BY {order} LIMIT ?"
    params.append(limit)

    conn = connect()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    resources = [dict(row) for row in rows]
    return jsonify(
        {
            "resources": resources,
            "total": len(resources),
            "filters": {
                "q": query,
                "category": category,
                "format": fmt,
                "difficulty": difficulty,
                "sort": sort,
            },
        }
    )


@api_bp.route("/resources/<int:resource_id>")
def get_resource(resource_id: int):
    row = get_db().execute(
        "SELECT * FROM resources WHERE id = ?", (resource_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "Resource not found"}), 404
    return jsonify({"resource": dict(row)})


@api_bp.route("/stats")
def stats():
    row = get_db().execute(
        """
        SELECT COUNT(*)                    AS total,
               COUNT(DISTINCT category)    AS categories,
               COALESCE(SUM(views), 0)     AS views,
               COALESCE(SUM(downloads), 0) AS downloads
        FROM resources
        """
    ).fetchone()
    return jsonify(dict(row))


@api_bp.route("/categories")
def categories():
    rows = get_db().execute(
        "SELECT name, slug, icon FROM categories ORDER BY name"
    ).fetchall()
    return jsonify({"categories": [dict(row) for row in rows]})


def _bump(resource_id: int, column: str):
    if column not in {"views", "downloads"}:
        return jsonify({"error": "Invalid counter"}), 400
    db = get_db()
    row = db.execute(
        f"SELECT {column} FROM resources WHERE id = ?", (resource_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "Resource not found"}), 404
    db.execute(
        f"UPDATE resources SET {column} = {column} + 1 WHERE id = ?", (resource_id,)
    )
    db.commit()
    return jsonify({"id": resource_id, column: row[column] + 1})


@api_bp.route("/resources/<int:resource_id>/view", methods=["POST"])
def record_view(resource_id: int):
    return _bump(resource_id, "views")


@api_bp.route("/resources/<int:resource_id>/download", methods=["POST"])
def record_download(resource_id: int):
    return _bump(resource_id, "downloads")


@api_bp.route("/resources", methods=["POST"])
def create_resource():
    payload = request.get_json(silent=True) or request.form.to_dict()
    required = ("title", "category", "format", "resource_url")
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    clean = {
        key: str(payload.get(key, "") or "").strip()
        for key in (
            "title",
            "category",
            "format",
            "description",
            "image_url",
            "resource_url",
            "difficulty",
            "tags",
        )
    }
    clean["difficulty"] = clean["difficulty"] or "Beginner"
    clean["image_url"] = (
        clean["image_url"]
        or "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=80"
    )

    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO resources
                (title, category, format, description, image_url,
                 resource_url, difficulty, tags)
            VALUES (:title, :category, :format, :description, :image_url,
                    :resource_url, :difficulty, :tags)
            """,
            clean,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 409

    row = db.execute("SELECT * FROM resources WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"resource": dict(row)}), 201
