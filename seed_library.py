"""
Seed GyanVault with 20 hand curated educational resources.

Every cover uses a direct Unsplash image URL (no API key, no copyright issue).
Running the script twice is safe — rows are inserted with INSERT OR IGNORE.

Usage:
    python seed_library.py            # add anything that is missing
    python seed_library.py --reset    # wipe and rebuild the whole vault
"""

from __future__ import annotations

import argparse

from database import connect, init_db

CATEGORIES = [
    ("Python", "python", "code"),
    ("Cyber Security", "cyber-security", "shield"),
    ("Linux", "linux", "terminal"),
    ("Web Development", "web-development", "globe"),
    ("Data Structures", "data-structures", "layers"),
    ("Mathematics", "mathematics", "sigma"),
    ("Data Science & AI", "data-science-ai", "sparkles"),
    ("Databases", "databases", "database"),
    ("DevOps", "devops", "workflow"),
    ("Competitive Programming", "competitive-programming", "trophy"),
]


def _img(photo: str, width: int = 900) -> str:
    """Build a directly usable Unsplash delivery URL."""
    return f"https://images.unsplash.com/{photo}?auto=format&fit=crop&w={width}&q=80"


RESOURCES = [
    {
        "title": "Python Crash Course — Complete Beginner Notes",
        "category": "Python",
        "format": "PDF Notes",
        "difficulty": "Beginner",
        "description": "A 60-page structured cheat sheet covering syntax, loops, functions and your first three mini projects.",
        "image_url": _img("photo-1516321318423-f06f85e504b3"),
        "resource_url": "https://docs.python.org/3/tutorial/",
        "tags": "python, basics, syntax, beginner, pdf",
        "views": 1842,
        "downloads": 612,
    },
    {
        "title": "Python Roadmap 2026 — From Zero to Deploy",
        "category": "Python",
        "format": "GitHub Repo",
        "difficulty": "Intermediate",
        "description": "Community maintained learning path with projects, reading order and interview checkpoints.",
        "image_url": _img("photo-1498050108023-c5249f4df085"),
        "resource_url": "https://roadmap.sh/python",
        "tags": "python, roadmap, projects, interview",
        "views": 2310,
        "downloads": 940,
    },
    {
        "title": "Python Data Science Handbook (Jupyter Book)",
        "category": "Data Science & AI",
        "format": "Free eBook",
        "difficulty": "Intermediate",
        "description": "Jake VanderPlas's full handbook: NumPy, pandas, visualisation and machine learning in one place.",
        "image_url": _img("photo-1551288049-bebda4e38f71"),
        "resource_url": "https://github.com/jakevdp/PythonDataScienceHandbook",
        "tags": "python, data science, numpy, pandas, ebook",
        "views": 1567,
        "downloads": 733,
    },
    {
        "title": "OWASP Top 10 — Web Security Field Guide",
        "category": "Cyber Security",
        "format": "Cheat Sheet",
        "difficulty": "Intermediate",
        "description": "The ten most critical web application risks explained with payload examples and fix checklists.",
        "image_url": _img("photo-1550751827-4bd374c3f58b"),
        "resource_url": "https://owasp.org/www-project-top-ten/",
        "tags": "security, owasp, web, injection, cheat sheet",
        "views": 3021,
        "downloads": 1188,
    },
    {
        "title": "Ethical Hacking Lab Setup Notes",
        "category": "Cyber Security",
        "format": "PDF Notes",
        "difficulty": "Advanced",
        "description": "Build an isolated pentest lab with virtual machines, networking modes and a safe practice checklist.",
        "image_url": _img("photo-1526374965328-7f61d4dc18c5"),
        "resource_url": "https://www.hackthebox.com/",
        "tags": "security, lab, networking, pentest, pdf",
        "views": 1289,
        "downloads": 476,
    },
    {
        "title": "Linux Command Line Mastery — 120 Commands",
        "category": "Linux",
        "format": "Cheat Sheet",
        "difficulty": "Beginner",
        "description": "One page for files, processes, permissions, grep, awk and sed — with real terminal examples.",
        "image_url": _img("photo-1518770660439-4636190af475"),
        "resource_url": "https://explainshell.com/",
        "tags": "linux, bash, terminal, commands, cheat sheet",
        "views": 2674,
        "downloads": 1024,
    },
    {
        "title": "Linux Journey — Free Interactive Course",
        "category": "Linux",
        "format": "Video Course",
        "difficulty": "Beginner",
        "description": "A guided track from the shell to system administration, with short lessons and quizzes.",
        "image_url": _img("photo-1563986768609-322da13575f3"),
        "resource_url": "https://linuxjourney.com/",
        "tags": "linux, course, administration, free",
        "views": 998,
        "downloads": 312,
    },
    {
        "title": "MDN Web Docs — HTML & CSS Deep Dive",
        "category": "Web Development",
        "format": "Free eBook",
        "difficulty": "Beginner",
        "description": "The reference every frontend developer keeps open: semantics, layout, flexbox, grid and accessibility.",
        "image_url": _img("photo-1547658719-da2b51169166"),
        "resource_url": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
        "tags": "web, html, css, frontend, mdn",
        "views": 3450,
        "downloads": 1410,
    },
    {
        "title": "React Patterns & Hooks Cheat Sheet",
        "category": "Web Development",
        "format": "Cheat Sheet",
        "difficulty": "Intermediate",
        "description": "Useful patterns for state, effects, context, memoisation and component composition.",
        "image_url": _img("photo-1633356122544-f134324a6cee"),
        "resource_url": "https://react.dev/reference/react",
        "tags": "react, javascript, hooks, frontend",
        "views": 1876,
        "downloads": 689,
    },
    {
        "title": "Data Structures Visualised — Big-O Poster",
        "category": "Data Structures",
        "format": "PDF Notes",
        "difficulty": "Intermediate",
        "description": "Arrays to graphs with complexity tables and step-by-step algorithm animations reference.",
        "image_url": _img("photo-1461749280684-dccba630e2f6"),
        "resource_url": "https://visualgo.net/en",
        "tags": "dsa, algorithms, big-o, visualisation",
        "views": 2411,
        "downloads": 967,
    },
    {
        "title": "GeeksforGeeks DSA — Interview Compendium",
        "category": "Data Structures",
        "format": "GitHub Repo",
        "difficulty": "Advanced",
        "description": "Curated problem sets grouped by topic with clean reference implementations in C++ and Python.",
        "image_url": _img("photo-1555066931-4365d14bab8c"),
        "resource_url": "https://www.geeksforgeeks.org/data-structures/",
        "tags": "dsa, interview, cpp, python, problems",
        "views": 1988,
        "downloads": 812,
    },
    {
        "title": "Linear Algebra for Machine Learning Notes",
        "category": "Mathematics",
        "format": "PDF Notes",
        "difficulty": "Advanced",
        "description": "Vectors, matrices, eigenvalues and SVD explained with geometric intuition and numpy examples.",
        "image_url": _img("photo-1509228468518-180dd4864904"),
        "resource_url": "https://www.khanacademy.org/math/linear-algebra",
        "tags": "math, linear algebra, ml, numpy",
        "views": 1455,
        "downloads": 554,
    },
    {
        "title": "Discrete Mathematics — Logic & Proofs",
        "category": "Mathematics",
        "format": "Video Course",
        "difficulty": "Intermediate",
        "description": "Propositional logic, sets, relations, combinatorics and induction with worked examples.",
        "image_url": _img("photo-1635070041078-e363dbe005cb"),
        "resource_url": "https://www.youtube.com/playlist?list=PLFD0EB975A0A0E746",
        "tags": "math, logic, proofs, discrete, video",
        "views": 1132,
        "downloads": 398,
    },
    {
        "title": "Kaggle Learn — 5 Free Micro-Courses",
        "category": "Data Science & AI",
        "format": "Video Course",
        "difficulty": "Beginner",
        "description": "Hands-on Python, data exploration, feature engineering and intro ML — each under two hours.",
        "image_url": _img("photo-1555949963-aa79dcee981c"),
        "resource_url": "https://www.kaggle.com/learn",
        "tags": "data science, ml, python, kaggle, free",
        "views": 2890,
        "downloads": 1103,
    },
    {
        "title": "scikit-learn Algorithm Cheat Sheet",
        "category": "Data Science & AI",
        "format": "Cheat Sheet",
        "difficulty": "Intermediate",
        "description": "Pick the right estimator fast: classification, regression, clustering and dimensionality reduction.",
        "image_url": _img("photo-1504384308090-c894fdcc538d"),
        "resource_url": "https://scikit-learn.org/stable/cheat_sheet.html",
        "tags": "ml, scikit-learn, algorithms, cheat sheet",
        "views": 1765,
        "downloads": 742,
    },
    {
        "title": "PostgreSQL Documentation — SQL Basics to Advanced",
        "category": "Databases",
        "format": "Free eBook",
        "difficulty": "Intermediate",
        "description": "Authoritative reference for queries, joins, indexes, transactions and performance tuning.",
        "image_url": _img("photo-1481627834876-b7833e8f5570"),
        "resource_url": "https://www.postgresql.org/docs/current/",
        "tags": "sql, postgres, database, queries",
        "views": 1344,
        "downloads": 501,
    },
    {
        "title": "SQLBolt — Interactive SQL Lessons",
        "category": "Databases",
        "format": "Video Course",
        "difficulty": "Beginner",
        "description": "Fourteen browser based lessons that take you from SELECT to outer joins in one sitting.",
        "image_url": _img("photo-1499750310107-5fef28a66643"),
        "resource_url": "https://sqlbolt.com/",
        "tags": "sql, beginner, interactive, database",
        "views": 2098,
        "downloads": 876,
    },
    {
        "title": "Docker in 30 Minutes — Hands-On Notes",
        "category": "DevOps",
        "format": "PDF Notes",
        "difficulty": "Beginner",
        "description": "Images, containers, volumes, networks and a first docker-compose stack explained simply.",
        "image_url": _img("photo-1531297484001-80022131f5a1"),
        "resource_url": "https://docs.docker.com/get-started/",
        "tags": "docker, devops, containers, pdf",
        "views": 1602,
        "downloads": 645,
    },
    {
        "title": "Git & GitHub Survival Guide",
        "category": "DevOps",
        "format": "Cheat Sheet",
        "difficulty": "Beginner",
        "description": "Branching, rebasing, resolving conflicts and recovering lost commits — the commands that matter.",
        "image_url": _img("photo-1517694712202-14dd9538aa97"),
        "resource_url": "https://github.com/git-guides",
        "tags": "git, github, version control, cheat sheet",
        "views": 2755,
        "downloads": 1089,
    },
    {
        "title": "Competitive Programming Starter Kit",
        "category": "Competitive Programming",
        "format": "GitHub Repo",
        "difficulty": "Advanced",
        "description": "Template library, common tricks and a 30-day practice plan for Codeforces and CodeChef.",
        "image_url": _img("photo-1434030216411-0b793f4b4173"),
        "resource_url": "https://codeforces.com/blog/entry/56091",
        "tags": "cp, contest, templates, algorithms",
        "views": 1219,
        "downloads": 458,
    },
]


def seed(reset: bool = False) -> None:
    init_db()
    conn = connect()
    try:
        if reset:
            conn.execute("DELETE FROM bookmarks")
            conn.execute("DELETE FROM resources")
            conn.execute("DELETE FROM categories")
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name IN ('resources','categories')"
            )
            conn.commit()

        conn.executemany(
            "INSERT OR IGNORE INTO categories (name, slug, icon) VALUES (?, ?, ?)",
            CATEGORIES,
        )
        before = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

        conn.executemany(
            """
            INSERT OR IGNORE INTO resources
                (title, category, format, description, image_url, resource_url,
                 difficulty, tags, views, downloads)
            VALUES
                (:title, :category, :format, :description, :image_url, :resource_url,
                 :difficulty, :tags, :views, :downloads)
            """,
            RESOURCES,
        )
        conn.commit()

        after = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        cats = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        print(f"GyanVault seed complete: +{after - before} resources ({after} total), {cats} categories.")
        print("Run `python app.py` and open http://127.0.0.1:5000")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the GyanVault SQLite vault")
    parser.add_argument("--reset", action="store_true", help="wipe before seeding")
    seed(parser.parse_args().reset)
