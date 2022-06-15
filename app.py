from flask import request, jsonify
from database import Route, Part, Point, engine
from sqlalchemy.orm import sessionmaker, joinedload
from model import route_schema, routes_schema, app
from werkzeug.utils import secure_filename
import os

@app.route('/', methods=['GET'])
def all_routes():
    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    routes = sessionobj.query(Route).options(joinedload(Route.parts).subqueryload(Part.start), joinedload(Route.parts).subqueryload(Part.end)).all()
    if len(routes) == 0:
        resp = jsonify({'message' : 'No routes in database'})
        resp.status_code = 404
        return resp

    resp = routes_schema.jsonify(routes)
    resp.status_code = 200
    return resp

@app.route('/one', methods=['POST'])
def one_route():
    if request.json is None:
        resp = jsonify({'message' : 'json format expected'})
        resp.status_code = 400
        return resp

    try:
        name = request.json['name']
    except:
        resp = jsonify({'message' : 'No name given'})
        resp.status_code = 400
        return resp

    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    try:
        route = sessionobj.query(Route).filter(Route.name == name).one()
    except:
        resp = jsonify({'message' : 'No route found'})
        resp.status_code = 404
        return resp

    resp = route_schema.jsonify(route)
    resp.status_code = 200
    return resp

@app.route('/create', methods=['POST'])
def create_route():
    # check if request is json
    route = request.json
    if route is None:
        resp = jsonify({'message' : 'json format expected'})
        resp.status_code = 400
        return resp

    # open database session
    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    
    # check if name is already used
    in_use = sessionobj.query(Route).filter(Route.name == route['name']).one_or_none()
    if in_use is not None:
        resp = jsonify({'message' : 'Route name already in use'})
        resp.status_code = 400
        return resp

    description = None
    
    # check if a description was given
    if "description" in route:
        description = route['description']

    # create new route
    new_route = Route(name=route['name'], description=description)
    sessionobj.add(new_route)

    # parts for new route
    for part in route['parts']:

        # check if all required fields exist
        try:
            start = part['start']
            end = part['end']
            sx = start['x']
            sy = start['y']
            ex = end['x']
            ey = end['y']
            maxDistance = part['maxDistance']
        except:
            resp = jsonify({'message' : 'Missing required fields'})
            resp.status_code = 400
            return resp

        soundRange = None
        soundFile = None
        
        # check if soundRange and soundFile were given for start
        if "soundRange" in start:
            soundRange = start['soundRange']
        if "soundFile" in start:
            soundFile = start['soundFile']
        
        # create start
        new_start = Point(x=sx, y=sy, soundFile=soundFile, soundRange=soundRange)
        sessionobj.add(new_start)
        
        # get new start id
        startId = sessionobj.query(Point).order_by(Point.id.desc()).first().id

        soundFile = None
        soundRange = None
        
        # check if soundRange and soundFile were given for end
        if "soundRange" in end:
            soundRange = end['soundRange']
        if "soundFile" in end:
            soundFile = end['soundFile']
        
        # create end
        new_end = Point(x=ex, y=ey, soundFile=soundFile, soundRange=soundRange)
        sessionobj.add(new_end)

        # get new end id
        endId = sessionobj.query(Point).order_by(Point.id.desc()).first().id
        
        # get new route id
        routeId = sessionobj.query(Route).order_by(Route.id.desc()).first().id

        # create new part
        new_part = Part(routeId=routeId, startId=startId, endId=endId, maxDistance=maxDistance)
        sessionobj.add(new_part)

    # get new created route
    new_route = sessionobj.query(Route).order_by(Route.id.desc()).first()

    # save all to database
    sessionobj.commit()

    #return new route
    resp = route_schema.jsonify(new_route)
    resp.status_code = 201
    return resp
    
@app.route('/update', methods=['Post'])
def update():
    route = request.json
    if route is None:
        resp = jsonify({'message' : 'json format expected'})
        resp.status_code = 400
        return resp
    
    # check if the old name was given to get the record
    if "old_name" not in route:
        resp = jsonify({'message' : 'No old_name was given'})        
        resp.status_code = 400
        return resp
    
    # check if something is given to update the record
    if "new_name" not in route and "description" not in route:
        resp = jsonify({'message' : 'Nothing to update'})
        resp.status_code = 200
        return resp

    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    
    # try to get the route via name
    try:
        update_route = sessionobj.query(Route).filter(Route.name == route['old_name']).one()
    except:
        resp = jsonify({'message' : 'Could not find route'})
        resp.status_code = 400
        return resp
    
    # update the name and or description
    if "new_name" in route:
        update_route.name = route["new_name"]
    
    if "description" in route:
        update_route.description = route["description"]
    
    # try to save update
    try:
        sessionobj.commit()
    except:
        resp = jsonify({'message' : 'Could not update route'})
        resp.status_code = 400
        return resp
    
    # return updated route
    resp = route_schema.jsonify(update_route)
    resp.status_code = 200
    return resp

@app.route('/delete', methods=['get', 'POST'])
def delete():
    route = request.json
    if route is None:
        resp = jsonify({'message' : 'json format expected'})
        resp.status_code = 400
        return resp
    
    # check if name is given
    if 'name' in route:

        # try to get route and delete it
        try:
            Session = sessionmaker(bind=engine)
            sessionobj = Session()            
            delete_route = sessionobj.query(Route).options(joinedload(Route.parts).subqueryload(Part.start), joinedload(Route.parts).subqueryload(Part.end)).filter(Route.name == route['name']).one()
            
            # delete all audio files for this route
            for x in delete_route.parts:
                if x.start.soundFile is not None:
                    try:
                       os.remove(os.path.join(app.config['UPLOAD_FOLDER'], x.start.soundFile))
                    except:
                        pass
                if x.end.soundFile is not None:
                    try:
                      os.remove(os.path.join(app.config['UPLOAD_FOLDER'], x.end.soundFile))
                    except:
                        pass
            sessionobj.delete(delete_route)
            sessionobj.commit()
            resp = jsonify({'message' : 'Successfuly deleted route'})
            resp.status_code = 410
            return resp
        except:
            resp = jsonify({'message' : 'Could not delete route'})
            resp.status_code = 404
            return resp
    else:
        resp = jsonify({'message' : 'No name given'})
        resp.status_code = 400
        return resp
    

@app.route('/upload', methods=['POST'])
def upload_audio():
    # check if the post request has the file part
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp

	file = request.files['file']
	if not file and file.filename == '':
		resp = jsonify({'message' : 'No file selected for uploading'})
		resp.status_code = 400
		return resp

	if allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		resp = jsonify({'message' : 'File successfully uploaded'})
		resp.status_code = 201
		return resp

	else:
		resp = jsonify({'message' : 'Allowed file types are ' + str(app.config["ALLOWED_EXTENTIONS"])})
		resp.status_code = 400
		return resp

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ["wav", "mp3"]

if __name__ == '__main__':
    app.run(debug=True)