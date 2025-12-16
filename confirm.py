from sqlalchemy import create_engine, inspect, text

DATABASE_FILE = "restaurants.db"

engine = create_engine(f"sqlite:///{DATABASE_FILE}")

# --- DB の中身確認 ---
with engine.connect() as conn:
    inspector = inspect(conn)

    # 1. テーブル一覧
    print("■ テーブル一覧")
    tables = inspector.get_table_names()
    print(tables)

    # 2. restaurants テーブルのカラム情報aaa
    print("\n■ restaurants テーブルのカラム")
    for column in inspector.get_columns("restaurants"):
        print(f"{column['name']} ({column['type']})")

    # 3. レコード数
    print("\n■ レコード数")
    result = conn.execute(text("SELECT COUNT(*) FROM restaurants"))
    print(result.scalar())

    # 4. 最初の 5 件を表示
    result = conn.execute(text("SELECT * FROM restaurants"))
    for row in result:
        print(row)
