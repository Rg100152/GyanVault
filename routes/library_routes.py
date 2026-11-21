"""Server rendered pages: library, saved vault and the admin publisher."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import connect

library_bp = Blueprint("library", __name__)

FORMATS = ["PDF Notes", "Video Course", "GitHub Repo", "Cheat Sheet", "Free eBook"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]


def _overview():
    """Small aggregate used by the bento stat cards."""
    conn = connect()
    try:
        stats = conn.execute(
            """
            SELECT COUNT(*)                       AS total,
                   COALESCE(SUM(views), 0)        AS views,
                   COALESCE(SUM(downloads), 0)    AS downloads
            FROM resources
            """
        ).fetchone()
        category_count = conn.execute(
            "SELECT COUNT(DISTINCT category) AS n FROM resources"
        ).fetchone()["n"]
        categories = conn.execute(
            "SELECT name, slug, icon FROM categories ORDER BY name"
        ).fetchall()
        format_counts = {
            row["format"]: row["n"]
            for row in conn.execute(
                "SELECT format, COUNT(*) AS n FROM resources GROUP BY format"
            ).fetchall()
        }
    finally:
        conn.close()
    return stats, category_count, categories, format_counts


@library_bp.route("/")
def home():
    stats, category_count, categories, format_counts = _overview()
    return render_template(
        "index.html",
        stats=stats,
        category_count=category_count,
        categories=categories,
        format_counts=format_counts,
        formats=FORMATS,
        difficulties=DIFFICULTIES,
        saved_only=False,
    )


@library_bp.route("/saved")
def saved():
    """Same grid, but the JS layer starts in 'saved only' mode."""
    stats, category_count, categories, format_counts = _overview()
    return render_template(
        "index.html",
        stats=stats,
        category_count=category_count,
        categories=categories,
        format_counts=format_counts,
        formats=FORMATS,
        difficulties=DIFFICULTIES,
        saved_only=True,
    )


@library_bp.route("/add", methods=["GET", "POST"])
def add_resource():
    conn = connect()
    try:
        categories = conn.execute(
            "SELECT name FROM categories ORDER BY name"
        ).fetchall()
        if request.method == "POST":
            data = {
                key: (request.form.get(key) or "").strip()
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
            if not data["title"] or not data["category"] or not data["resource_url"]:
                flash("Title, category and resource link are required.", "error")
            else:
                try:
                    conn.execute(
                        """
                        INSERT INTO resources
                            (title, category, format, description, image_url,
                             resource_url, difficulty, tags)
                        VALUES (:title, :category, :format, :description, :image_url,
                                :resource_url, :difficulty, :tags)
                        """,
                        data,
                    )
                    conn.commit()
                    flash(f"“{data['title']}” is now indexed in the vault.", "success")
                    return redirect(url_for("library.home"))
                except Exception as exc:  # e.g. duplicate title
                    conn.rollback()
                    flash(f"Could not publish resource: {exc}", "error")
    finally:
        conn.close()

    return render_template(
        "add_resource.html",
        categories=categories,
        formats=FORMATS,
        difficulties=DIFFICULTIES,
    )
