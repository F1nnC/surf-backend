from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.spot import Spot


class SpotForecastData(db.Model):  # Use db.Model to enable Flask-SQLAlchemy features
    __tablename__ = "spot_forecast"

    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String, nullable=False)
    spot_name = db.Column(db.String, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    surf_min = db.Column(db.Float, nullable=True)
    surf_max = db.Column(db.Float, nullable=True)
    wave_height = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_direction = db.Column(db.Float, nullable=True)
    surf_optimalScore = db.Column(db.Float, nullable=True)

    def spot_name_set(self):
        spot = Spot()
        spot_data = spot.get_spot_id_name_dict()
        self.spot_name = spot_data.get(self.spot_id)
        return self.spot_name