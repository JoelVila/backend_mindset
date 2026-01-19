from app import create_app, db

def reset_db():
    app = create_app()
    with app.app_context():
        print("Dropping all tables...")
        # Reflect all tables to ensure we drop everything including alembic_version
        db.reflect()
        db.drop_all()
        # Also drop the alembic_version table manually if it persists (though drop_all usually handles it if reflected)
        # But drop_all only drops models. Let's force everything.
        engine = db.engine
        metadata = db.MetaData()
        metadata.reflect(bind=engine)
        metadata.drop_all(bind=engine)
        print("All tables dropped.")

if __name__ == "__main__":
    reset_db()
