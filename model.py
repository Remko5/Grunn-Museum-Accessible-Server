from flask import Flask
from flask_marshmallow import Marshmallow
from marshmallow import fields
import os

app = Flask(__name__)
app.config["BASE_FOLDER"] = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(app.config["BASE_FOLDER"], "static/audio")
app.config["ALLOWED_EXTENTIONS"] = ["wav", "mp3"]

ma = Marshmallow(app)

class PointSchema(ma.Schema):
        class Meta:
                fields = ("x", "y", "soundRange", "soundFile")

class PartSchema(ma.Schema):
    start = fields.Nested(PointSchema) 
    end = fields.Nested(PointSchema)
    maxDistance = fields.String()

class RouteSchema(ma.Schema):
        name = fields.String()
        description = fields.String()
        parts = fields.List(fields.Nested(PartSchema))

route_schema = RouteSchema()
routes_schema = RouteSchema(many=True)
