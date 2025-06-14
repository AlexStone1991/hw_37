from flask import Flask
from models import initialize_db
from blueprints.masters.routes import masters_bp
from blueprints.appointments.routes import appointments_bp

app = Flask(__name__)

# Регистрация блюпринтов
app.register_blueprint(masters_bp)
app.register_blueprint(appointments_bp)

# Инициализация базы данных при старте приложения
with app.app_context():
    initialize_db()

if __name__ == '__main__':
    app.run(debug=True)
