from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    if inspector.has_table('pacientes'):
        columns = inspector.get_columns('pacientes')
        print("Columns in 'pacientes' table:")
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
    else:
        print("Table 'pacientes' does not exist.")
