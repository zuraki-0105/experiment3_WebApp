import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, func, select, union_all

# 元データ
CSV_TXT_RANKING = 'aozora/ranking_txt.csv'
CSV_XHTML_RANKING = 'aozora/ranking_xhtml.csv'
CSV_BOOK_LIST = 'aozora/list_person_all_extended_utf8.csv'

# データベースが格納されるファイル
DATABASE_FILE = 'library.db'

# SQLAlchemyの起動
engine = create_engine(f'sqlite:///{DATABASE_FILE}')
metadata = MetaData()

# テキスト形式へのアクセス数の表
txt_ranking_temp = Table('txt_ranking_temp', metadata,
    Column('作品名', String),
    Column('アクセス数', Integer)
)

# XHTML形式へのアクセス数の表
xhtml_ranking_temp = Table('xhtml_ranking_temp', metadata,
    Column('作品名', String),
    Column('アクセス数', Integer)
)

# 本に関する一時的なデータの格納場所
book_list_temp = Table('book_list_temp', metadata,
    Column('作品ID', String),
    Column('作品名', String),
    Column('著者姓', String),
    Column('著者名', String),
    Column('著者生年', Integer),
    Column('著者没年', Integer),
    Column('出版年', Integer),
    Column('html_url', String)
)

# 本に関する最終的なデータの表
books_table = Table('books', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('作品ID', Integer),
    Column('作品名', String),
    Column('著者姓', String),
    Column('著者名', String),
    Column('著者生年', Integer),
    Column('著者没年', Integer),
    Column('出版年', Integer),
    Column('アクセス数合計', Integer),
    Column('html_url', String)
)

# --- 始まり ---
with engine.connect() as conn:
    # データベースを更地にする
    metadata.drop_all(conn)
    # すべての表を作る
    metadata.create_all(conn)

    # CSVから仮の表へデータを移す（txt形式へのアクセス数）
    with open(CSV_TXT_RANKING, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            conn.execute(txt_ranking_temp.insert().values(作品名=row[1], アクセス数=row[4]))

    # CSVから仮の表へデータを移す（XHTML形式へのアクセス数）
    with open(CSV_XHTML_RANKING, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            conn.execute(xhtml_ranking_temp.insert().values(作品名=row[1], アクセス数=row[4]))

    # 本のリストのデータを読み込み仮の表に書き込む
    with open(CSV_BOOK_LIST, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            try:
                birth_year=int(row[24].split('-')[0]) if row[24] else None
            except Exception:
                birth_year=None
            try:
                death_year=int(row[25].split('-')[0]) if row[24] else None
            except Exception:
                death_year=None
            try:
                publish_year = int(row[11].split('-')[0]) if row[11] else None
            except Exception:
                publish_year = None

            conn.execute(book_list_temp.insert().values(作品ID=row[0], 
                                                        作品名=row[1], 
                                                        著者姓=row[15], 
                                                        著者名=row[16], 
                                                        著者生年=birth_year,
                                                        著者没年=death_year,
                                                        出版年 = publish_year,
                                                        html_url=row[13]))

    # TXTとXHTMLのランキングをUNIONでひとつにまとめる
    u = union_all(
        select(txt_ranking_temp.c.作品名, txt_ranking_temp.c.アクセス数),
        select(xhtml_ranking_temp.c.作品名, xhtml_ranking_temp.c.アクセス数)
    ).alias('union_table')

    # 作品名でグループ化してアクセス数を合計する
    total_access = select(
        u.c.作品名,
        func.sum(u.c.アクセス数).label('total_access')
    ).group_by(u.c.作品名).alias('total_access_table')

    # 本のリストと合計したランキングをLEFT JOINで結びつける
    final_query = select(
        book_list_temp.c.作品ID,
        book_list_temp.c.作品名,
        book_list_temp.c.著者姓,
        book_list_temp.c.著者名,
        book_list_temp.c.著者生年,
        book_list_temp.c.著者没年,
        book_list_temp.c.出版年, 
        total_access.c.total_access,
        book_list_temp.c.html_url
    ).select_from(
        book_list_temp.outerjoin(total_access, book_list_temp.c.作品名 == total_access.c.作品名)
    )

    # 本の表に結果を書き込む
    conn.execute(books_table.insert().from_select(
        ['作品ID', '作品名', '著者姓', '著者名', '著者生年', '著者没年', '出版年', 'アクセス数合計', 'html_url'],
        final_query
    ))

    # トランザクションを確定する
    conn.commit()


print(f"本のデータベースを'{DATABASE_FILE}' に作成したよ！")