from flask import request, jsonify
from database import Route, Part, Point, engine
from sqlalchemy.orm import sessionmaker, joinedload
from model import route_schema, routes_schema, app
from werkzeug.utils import secure_filename
import os, uuid, json

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
    name = request.form.get('name')
    chars = app.config["NOT_ALLOWED_CHARS"]
    if name is None or len(name) == 0:
        resp = jsonify({'message' : 'No route name given'})
        resp.status_code = 400
        return resp

    for char in name:
        if char in chars:
            resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
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
    try:
        route = request.form
        name = route.get('name')
        chars = app.config["NOT_ALLOWED_CHARS"]
        if name is None or len(name) == 0:
            resp = jsonify({'message' : 'No route name given'})
            resp.status_code = 400
            return resp

        for char in name:
            if char in chars:
                resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
                resp.status_code = 400
                return resp

        # open database session
        Session = sessionmaker(bind=engine, autoflush=False)
        sessionobj = Session()
        # check if name is already used
        in_use = sessionobj.query(Route).filter(Route.name == name).one_or_none()
        if in_use is not None:
            resp = jsonify({'message' : 'Route name already in use'})
            resp.status_code = 400
            return resp
            
        description = route.get('description')
        if description is not None and len(description) != 0:
            for char in description:
                if char in chars:
                    resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
                    resp.status_code = 400
                    return resp

        image = None
        files = request.files.getlist('file')
        # list to hold current uploaded files to revert if an error occurs
        current_uploaded_files = []
        # check if a image was given
        if len(files) > 0:
            for file in files:
                # check if file is image
                if image_file(secure_filename(file.filename)):
                    filepath = upload_file(file)
                    image = filepath
                    current_uploaded_files.append(image)

                if image == "no-upload":
                    delete_current_uploaded_files(current_uploaded_files)
                    resp = jsonify({'message' : 'No file selected for uploading'})
                    resp.status_code = 400
                    return resp

        # else:
        #     resp = jsonify({'message' : "No file in the request"})
        #     resp.status_code = 400
        #     return resp

        # create new route
        new_route = Route(name=name, description=description, image=image)
        sessionobj.add(new_route)
        sessionobj.flush()
        try:
            parts = json.loads(route.get('parts'))
        except:
            delete_current_uploaded_files(current_uploaded_files)
            resp = jsonify({'message' : 'JSON format expected for parts'})
            resp.status_code = 400
            return resp
        
        # parts for new route
        for part in parts:

            # check if all required fields exist
            try:
                start = part['start']
                end = part['end']
                try:
                    sx = float(start['x'])
                    sy = float(start['y'])
                    ex = float(end['x'])
                    ey = float(end['y'])
                except:
                    delete_current_uploaded_files(current_uploaded_files)
                    resp = jsonify({'message' : 'x and y in start and end need to be a number (float)'})
                    resp.status_code = 400
                    return resp
                try:
                    maxDistance = int(part['maxDistance'])
                except:
                    delete_current_uploaded_files(current_uploaded_files)
                    resp = jsonify({'message' : 'maxDistance needs to be a number (int)'})
                    resp.status_code = 400
                    return resp
            except:
                delete_current_uploaded_files(current_uploaded_files)
                resp = jsonify({'message' : 'Missing required fields'})
                resp.status_code = 400
                return resp

            soundRange = None
            soundFile = None
            
            # check if soundRange and soundFile were given for start
            if "soundRange" in start:
                try:
                    soundRange = int(start['soundRange'])
                except:
                    delete_current_uploaded_files(current_uploaded_files)
                    resp = jsonify({'message' : 'soundRange needs to be a number (int)'})
                    resp.status_code = 400
                    return resp

            if "soundFile" in start:
                # check if audio was given
                if len(files) > 0:
                    for file in files:
                        if secure_filename(file.filename) == secure_filename(start['soundFile']):
                            # check if file is audio
                            if audio_file(secure_filename(file.filename)):
                                filepath = upload_file(file)
                                soundFile = filepath
                                current_uploaded_files.append(soundFile)
                                
                            if soundFile == "no-upload":
                                delete_current_uploaded_files(current_uploaded_files)
                                resp = jsonify({'message' : 'No file selected for uploading'})
                                resp.status_code = 400
                                return resp

                # else:
                #     resp = jsonify({'message' : "No file in the request"})
                #     resp.status_code = 400
                #     return resp
            
            # create start
            new_start = Point(x=sx, y=sy, soundFile=soundFile, soundRange=soundRange)
            sessionobj.add(new_start)
            sessionobj.flush()
            # get new start id
            startId = sessionobj.query(Point).order_by(Point.id.desc()).first().id

            soundFile = None
            soundRange = None
            
            # check if soundRange and soundFile were given for end
            if "soundRange" in end:
                try:
                    soundRange = int(end['soundRange'])
                except:
                    delete_current_uploaded_files(current_uploaded_files)
                    resp = jsonify({'message' : 'soundRange needs to be a number (int)'})
                    resp.status_code = 400
                    return resp

            if "soundFile" in end:
                # check if audio was given
                if len(files) > 0:
                    for file in files:
                        if secure_filename(file.filename) == secure_filename(end['soundFile']):
                            # check if file is audio
                            if audio_file(secure_filename(file.filename)):
                                filepath = upload_file(file)
                                soundFile = filepath
                                current_uploaded_files.append(soundFile)

                            if soundFile == "no-upload":
                                delete_current_uploaded_files(current_uploaded_files)
                                resp = jsonify({'message' : 'No file selected for uploading'})
                                resp.status_code = 400
                                return resp

                # else:
                #     resp = jsonify({'message' : "No file in the request"})
                #     resp.status_code = 400
                #     return resp
            
            # create end
            new_end = Point(x=ex, y=ey, soundFile=soundFile, soundRange=soundRange)
            sessionobj.add(new_end)
            sessionobj.flush()
            # get new end id
            endId = sessionobj.query(Point).order_by(Point.id.desc()).first().id
            
            # get new route id
            routeId = sessionobj.query(Route).order_by(Route.id.desc()).first().id

            # create new part
            new_part = Part(routeId=routeId, startId=startId, endId=endId, maxDistance=maxDistance)
            sessionobj.add(new_part)
            sessionobj.flush()
        # get new created route
        new_route = sessionobj.query(Route).order_by(Route.id.desc()).first()

        # save all to database
        sessionobj.commit()
        #return new route
        resp = route_schema.jsonify(new_route)
        resp.status_code = 201
        return resp
    except:
        resp = jsonify({'message' : "Route name already in use"})
        resp.status_code = 400
        return resp
    
@app.route('/update', methods=['POST'])
def update():
    route = request.form
    name = route.get('name')
    new_name = route.get('new_name')
    new_description = route.get('new_description')
    chars = app.config["NOT_ALLOWED_CHARS"]
    # check if the old name was given to get the record
    if name is None or len(name) == 0:
        resp = jsonify({'message' : 'No route name given'})
        resp.status_code = 400
        return resp
    
    # check if something is given to update the record
    if new_name is None and new_description is None and len(request.files) == 0:
        resp = jsonify({'message' : 'Nothing to update'})
        resp.status_code = 200
        return resp

    for char in name:
        if char in chars:
            resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
            resp.status_code = 400
            return resp
    
    if new_name is not None and len(new_name) != 0:
        for char in new_name:
            if char in chars:
                resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
                resp.status_code = 400
                return resp
    
    if new_description is not None and len(new_description) != 0:
        for char in new_description:
            if char in chars:
                resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
                resp.status_code = 400
                return resp

    Session = sessionmaker(bind=engine)
    sessionobj = Session()
    
    # try to get the route via name
    try:
        update_route = sessionobj.query(Route).filter(Route.name == route.get('name')).one()
    except:
        resp = jsonify({'message' : 'Could not find route'})
        resp.status_code = 400
        return resp
    
    # update the name and or description and or image
    if new_name is not None:
        update_route.name = new_name
    
    if new_description is not None:
        update_route.description = new_description
    
    # list to hold current uploaded files to revert if an error occurs
    current_uploaded_files = []
    
    file_amount = request.files.getlist('file')
    if file_amount is not None and len(file_amount) > 0:
        if len(file_amount) < 2:
            # check if file is image
            if not image_file(secure_filename(request.files['file'].filename)):
                resp = jsonify({'message' : 'Allowed file types are ' + str(app.config['IMAGE_EXTENTIONS'])})
                resp.status_code = 400
                return resp

            file = upload_file(request.files['file'])
            current_uploaded_files.append(file)
            
            if file == "no-upload":
                resp = jsonify({'message' : 'No file selected for uploading'})
                resp.status_code = 400
                return resp
        else:
            resp = jsonify({'message' : 'Only one image file is allowed'})
            resp.status_code = 400
            return resp
        
        # update image link
        update_route.image = file

    # try to save update
    try:
        sessionobj.commit()
    except:
        delete_current_uploaded_files(current_uploaded_files)
        resp = jsonify({'message' : 'Could not update route'})
        resp.status_code = 400
        return resp
    
    # remove old image
    try:
        os.remove(os.path.join(app.config['IMAGE_FOLDER'], update_route.image.rsplit('/static/image/', 1)[1]))
    except:
        pass
    # return updated route
    resp = route_schema.jsonify(update_route)
    resp.status_code = 200
    return resp

@app.route('/delete', methods=['POST'])
def delete():
    route = request.form
    name = route.get('name')
    chars = app.config["NOT_ALLOWED_CHARS"]
    
    # check if name is given
    if name is not None and len(name) > 0:
        for char in name:
            if char in chars:
                resp = jsonify({'message' : 'These characters are not allowed: [' + chars + ']'})
                resp.status_code = 400
                return resp

        # try to get route and delete it
        try:
            Session = sessionmaker(bind=engine)
            sessionobj = Session()            
            delete_route = sessionobj.query(Route).options(joinedload(Route.parts).subqueryload(Part.start), joinedload(Route.parts).subqueryload(Part.end)).filter(Route.name == name).one()
            
            # get all files to delete
            delete_files = []
            if delete_route.image is not None:
                delete_files.append(delete_route.image)
            for x in delete_route.parts:
                if x.start.soundFile is not None:
                    delete_files.append(x.start.soundFile)
                if x.end.soundFile is not None:
                    delete_files.append(x.end.soundFile)

            sessionobj.delete(delete_route)
            sessionobj.commit()
            delete_current_uploaded_files(delete_files)
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

def upload_file(file):
    
    # check if a file is selected
    if not file and file.filename == '':
        return "no-upload"
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400
        return resp

    # save audio file
    if audio_file(secure_filename(file.filename)):
        file_id = str(uuid.uuid4())
        filename = file_id + "." + file.filename.rsplit('.', 1)[1].lower()
        file.save(os.path.join(app.config['AUDIO_FOLDER'], filename))
        return "/static/audio/" + filename
        resp = jsonify({'message' : '/static/audio/' + filename})
        resp.status_code = 201
        return resp

    # save image file
    elif image_file(secure_filename(file.filename)):
        file_id = str(uuid.uuid4())
        filename = file_id + "." + file.filename.rsplit('.', 1)[1].lower()
        file.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
        return "/static/image/" + filename
        resp = jsonify({'message' : '/static/image/' + filename})
        resp.status_code = 201
        return resp

    # file not allowed
    else:
        return "not-allowed-extention"
        resp = jsonify({'message' : 'Allowed file types are ' + str(app.config['AUDIO_EXTENTIONS']) + ' for audio and ' + str(app.config['IMAGE_EXTENTIONS']) + ' for images'})
        resp.status_code = 400
        return resp

def audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["AUDIO_EXTENTIONS"]

def image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["IMAGE_EXTENTIONS"]

def delete_current_uploaded_files(temp):
    if len(temp) > 0:
        for x in temp:
            if audio_file(x):
                try:
                    os.remove(os.path.join(app.config['AUDIO_FOLDER'], x.rsplit('/static/audio/', 1)[1]))
                except:
                    pass
            elif image_file(x):
                try:
                    os.remove(os.path.join(app.config['IMAGE_FOLDER'], x.rsplit('/static/image/', 1)[1]))
                except:
                    pass

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=80, debug=True)
    app.run(debug=True)