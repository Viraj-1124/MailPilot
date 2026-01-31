from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///feedback.db")

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS email_tasks"))
    conn.commit()
