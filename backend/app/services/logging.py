"""推荐日志和后台查询。"""

import json

from src.db.schema import get_connection


def log_recommendations(user_id, model_name, items, request_context=None):
    if not items:
        return
    request_context = request_context or {}
    rows = []
    for item in items:
        rows.append((
            user_id,
            item["id"],
            model_name,
            float(item.get("score") or 0),
            json.dumps(item.get("source_models") or [], ensure_ascii=False),
            item.get("reason") or "",
            json.dumps(request_context, ensure_ascii=False),
        ))
    conn = get_connection()
    conn.executemany(
        """INSERT INTO recommendation_logs
           (user_id, track_id, model_name, score, source_models, reason, request_context)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()


def admin_recommendation_logs(page=1, size=50, search="", model_name=""):
    conn = get_connection()
    params = []
    where = ["1=1"]
    if model_name:
        where.append("rl.model_name LIKE ?")
        params.append(f"%{model_name}%")
    if search:
        like = f"%{search}%"
        where.append("(u.username LIKE ? OR u.display_name LIKE ? OR t.title LIKE ? OR a.name LIKE ? OR rl.reason LIKE ?)")
        params.extend([like, like, like, like, like])
    where_sql = " AND ".join(where)
    total = conn.execute(
        f"""SELECT COUNT(*) FROM recommendation_logs rl
            LEFT JOIN users u ON rl.user_id=u.id
            JOIN tracks t ON rl.track_id=t.id
            JOIN artists a ON t.artist_id=a.id
            WHERE {where_sql}""",
        params,
    ).fetchone()[0]
    rows = conn.execute(
        f"""SELECT rl.*, u.username, u.display_name, t.title AS track_title,
                  a.name AS artist_name, t.genre
           FROM recommendation_logs rl
           LEFT JOIN users u ON rl.user_id=u.id
           JOIN tracks t ON rl.track_id=t.id
           JOIN artists a ON t.artist_id=a.id
           WHERE {where_sql}
           ORDER BY rl.created_at DESC LIMIT ? OFFSET ?""",
        params + [size, (page - 1) * size],
    ).fetchall()
    conn.close()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item["source_models"] = json.loads(item.get("source_models") or "[]")
        except json.JSONDecodeError:
            item["source_models"] = []
        items.append(item)
    return {"items": items, "total": total, "page": page, "size": size}


def log_user_action(
    user_id=None,
    session_id="",
    action_type="",
    entity_type="",
    entity_id=None,
    status="",
    page_url="",
    message="",
    metadata=None,
):
    metadata = metadata or {}
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_action_logs
           (user_id, session_id, action_type, entity_type, entity_id, status, page_url, message, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            session_id or "",
            action_type,
            entity_type or "",
            entity_id,
            status or "",
            page_url or "",
            message or "",
            json.dumps(metadata, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


def admin_action_logs(page=1, size=100, action_type="", status="", search=""):
    conn = get_connection()
    params = []
    where = ["1=1"]
    if action_type:
        where.append("al.action_type=?")
        params.append(action_type)
    if status:
        where.append("al.status=?")
        params.append(status)
    if search:
        like = f"%{search}%"
        where.append("(al.message LIKE ? OR al.page_url LIKE ? OR al.entity_type LIKE ? OR CAST(al.entity_id AS TEXT) LIKE ? OR al.metadata LIKE ? OR al.session_id LIKE ? OR u.username LIKE ? OR u.display_name LIKE ?)")
        params.extend([like, like, like, like, like, like, like, like])
    where_sql = " AND ".join(where)
    total = conn.execute(
        f"""SELECT COUNT(*) FROM user_action_logs al
            LEFT JOIN users u ON al.user_id=u.id
            WHERE {where_sql}""",
        params,
    ).fetchone()[0]
    rows = conn.execute(
        f"""SELECT al.*, u.username, u.display_name
            FROM user_action_logs al
            LEFT JOIN users u ON al.user_id=u.id
            WHERE {where_sql}
            ORDER BY al.created_at DESC LIMIT ? OFFSET ?""",
        params + [size, (page - 1) * size],
    ).fetchall()
    conn.close()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.get("metadata") or "{}")
        except json.JSONDecodeError:
            item["metadata"] = {}
        items.append(item)
    return {"items": items, "total": total, "page": page, "size": size}
