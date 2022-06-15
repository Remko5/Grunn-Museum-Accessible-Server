from tokenize import Double
from typing_extensions import Required
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Column, String, Float, Text
from sqlalchemy.orm import sessionmaker, relationship

base=declarative_base()
#engine = create_engine('sqlite:///groninger_museum.db')
engine = create_engine('postgres://cbwfvybmoyqbeo:3a3785fdae3a3445c2116b1c4bf6501a9fcd9528c9b80aaaa4aca7643f0d648f@ec2-54-170-90-26.eu-west-1.compute.amazonaws.com:5432/d5hja7i8d6c0t8')
class Route(base):
    
    __tablename__ = 'route'

    id = Column(Integer,primary_key=True)
    name = Column(String(45), nullable=False, unique=True)
    description = Column(Text)
    parts = relationship("Part", cascade="all, delete")

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

class Part(base):
    
    __tablename__ = 'part'

    id = Column(Integer,primary_key=True)
    routeId = Column(Integer, ForeignKey("route.id"))
    startId = Column(Integer, ForeignKey("point.id"))
    endId = Column(Integer, ForeignKey("point.id"))
    start = relationship("Point", foreign_keys=[startId], uselist=False, cascade="all, delete")
    end = relationship("Point", foreign_keys=[endId], uselist=False, cascade="all, delete")
    maxDistance = Column(Integer)

    def __init__(self, routeId, startId, endId, maxDistance):
        self.routeId = routeId
        self.startId = startId
        self.endId = endId
        self.maxDistance = maxDistance

class Point(base):

    __tablename__ = 'point'
    
    id = Column(Integer,primary_key=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    soundRange = Column(Integer)
    soundFile = Column(String)

    def __init__(self, x, y, soundRange=None, soundFile=None):
        self.x = x
        self.y = y
        self.soundRange = soundRange
        self.soundFile = soundFile

if __name__=='__main__':
    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    base.metadata.create_all(engine)
    
    point1 = Point(x="20", y="200", soundRange=400, soundFile="1.mp3")
    point2 = Point(x="100", y="400")
    point3 = Point(x="100", y="400", soundRange=200, soundFile="sound3")
    point4 = Point(x="300", y="600")
    point5 = Point(x="300", y="600", soundRange=300, soundFile="sound2")
    point6 = Point(x="700", y="400")
    part1 = Part(routeId=1, startId=1, endId=2, maxDistance=200)
    part2 = Part(routeId=1, startId=3, endId=4, maxDistance=100)
    part3 = Part(routeId=1, startId=5, endId=6, maxDistance=300)
    route1 = Route('route1', "desc1")
    route2 = Route('route2', "desc2")
    route3 = Route('route3', "desc3")
    sessionobj.add_all([route1,route2,route3,part1,part2,part3,point1,point2,point3,point4,point5,point6])

    sessionobj.commit()