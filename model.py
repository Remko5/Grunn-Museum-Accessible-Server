from flask import Flask
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask_cors import CORS
import os, string, re

app = Flask(__name__)
app.config["BASE_FOLDER"] = os.path.abspath(os.path.dirname(__file__))
app.config["AUDIO_FOLDER"] = os.path.join(app.config["BASE_FOLDER"], "static/audio")
app.config["IMAGE_FOLDER"] = os.path.join(app.config["BASE_FOLDER"], "static/image")
app.config["AUDIO_EXTENTIONS"] = ["wav", "mp3"]
app.config["IMAGE_EXTENTIONS"] = ["jpg", "jpeg", "gif", "png"]
#app.config["NOT_ALLOWED_CHARS"] = re.escape(string.punctuation)

ma = Marshmallow(app)
CORS(app)

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
        image = fields.String()
        parts = fields.List(fields.Nested(PartSchema))

route_schema = RouteSchema()
routes_schema = RouteSchema(many=True)
