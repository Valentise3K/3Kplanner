from database.pool import get_pool


async def get_user_categories(chat_id: int) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM categories WHERE chat_id = $1 ORDER BY is_default DESC, id ASC",
        chat_id,
    )
    return [dict(r) for r in rows]


async def create_category(chat_id: int, name: str, emoji: str = "📌") -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO categories (chat_id, name, emoji) VALUES ($1,$2,$3) RETURNING id",
        chat_id, name, emoji,
    )
    return row["id"]


async def delete_category(category_id: int, chat_id: int) -> None:
    pool = await get_pool()
    # Unlink tasks before deleting
    await pool.execute(
        "UPDATE tasks SET category_id = NULL WHERE category_id = $1 AND chat_id = $2",
        category_id, chat_id,
    )
    await pool.execute(
        "DELETE FROM categories WHERE id = $1 AND chat_id = $2 AND is_default = FALSE",
        category_id, chat_id,
    )


async def count_user_categories(chat_id: int) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT COUNT(*) as cnt FROM categories WHERE chat_id = $1", chat_id
    )
    return row["cnt"]
