from flask import *
import os
import util
from database import DBManager

app = Flask(__name__)
database = DBManager()
host = '0.0.0.0'
port = int(os.environ['PORT']) if 'PORT' in os.environ else 5000
base_url = "%s:%d" % (host, port)

@app.route('/')
def index():
    return render_template('halloween.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route('/create-event')
def create_event():
    if request.args:
        eventname = request.args.get('eventName')
        username = request.args.get('name')
        lat_s = request.args.get('long')
        long_s = request.args.get('lat')
        if "" in [ lat_s, long_s]:
            return render_template("no_location.html", user=username,
                    event=eventname)
        lat = float(lat_s)
        long = float(long_s)
        id, auth = database.create_event(eventname)
        database.add_person(id, username, long, lat)
        return redirect('/view-event/' + str(id) + '/' + auth + '/' + username + '?sharing=true')
    return render_template('createEvent.html')

@app.route('/create-event', methods = ['GET', 'POST'])
def create_event_action():
    print request.args
    return render_template('createEvent.html')

@app.route('/join-event/<int:id>')
def join_event(id):
    if request.args:
        auth = request.args.get('auth')
        name = request.args.get('name')
        lat_s = request.args.get('long')
        long_s = request.args.get('lat')
        if "" in [ lat_s, long_s]:
            return render_template("no_location.html", user=name)
        lat = float(lat_s)
        long = float(long_s)

        if database.authenticate(id, auth):
            database.add_person(id, name, long, lat)
            return redirect(url_for('view_event', id=id, auth=auth, name=name))
        else:
            return render_template("unauthorized.html")
    return render_template('joinEvent.html', id=id)

@app.route('/view-event/<int:id>/<auth>/<name>')
def view_event(id, auth, name):
    if database.authenticate(id, auth):
        share_url = base_url + '/join-event/' + str(id)
        locations = database.get_all_people_in_event(id)
        cleaned_list = []
        for aname, long, lat in locations:
            cleaned_list.append((lat, long))

        ctr = list(util.geographical_midpoint(cleaned_list))
        ctr[0], ctr[1] = ctr[1],ctr[0]

        meetup_places = util.get_list_of_locations(cleaned_list)
        esri_people = {
                "type": "FeatureCollection",
                "features": []
                }
        for aname, long, lat in locations:
            object = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lat, long]
                    },
                "properties": {
                    "name": aname,
                    'me': False
                    }
                }
            if aname == name:
                object['properties']['me'] = True

            esri_people['features'].append(object)

        esri_people = json.dumps(esri_people)

        return render_template('viewEvent.html', link = share_url, id=id, auth=auth, name=name, locs = esri_people, places = meetup_places, center = ctr)
    else:
        return render_template("unauthorized.html")

if (__name__ == '__main__'):
    app.run(host=host, port=port, debug=True)

