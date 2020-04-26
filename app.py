#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# print(app.config['SQLALCHEMY_DATABASE_URI'])

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    # print(value)
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues', methods=['GET'])
def venues():
    # TODO: replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per
    # venue.
    areas = db.session.query(Venue.city, Venue.state).distinct()
    data = []
    cityState = set()
    for a in areas:
        venues_ = Venue.query.filter_by(city=a[0], state=a[1]).all()
        for v in venues_:
            venues = []
            shows = v.shows
            showId = set()
            num_upcoming_shows = 0
            for show in shows:
                if (show.venue_id in showId):
                    if (show.start_time > datetime.now()):
                        current_show["num_upcoming_shows"] = current_show["num_upcoming_shows"] + 1
                else:
                    showId.add(show.venue_id)
                    current_show = {
                        "id": show.venue_id,
                        "name": Venue.query.filter_by(
                            id=show.venue_id).first().name,
                        "num_upcoming_shows": num_upcoming_shows}
                    venues.append(current_show)
            cityStatePair = v.city + ', ' + v.state
            if (cityStatePair not in cityState):
                data.append({
                    "city": v.city,
                    "state": v.state,
                    "venues": venues
                })
                cityState.add(cityStatePair)
            else:
                for d in data:
                    if ((d["city"] + ', ' + d["state"]) == cityStatePair):
                        for v in venues:
                            d["venues"].append(v)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"
    response = {
        "data": []
    }
    venues = db.session.query(Venue.name, Venue.id).all()
    for venue in venues:
        name = venue[0]
        id = venue[1]
        if name.find(request.form.get('search_term', '')) != -1:
            shows = Show.query.filter_by(venue_id=id).all()
            upcoming_shows_count = 0
            for show in shows:
                if show.start_time > datetime.now():
                    upcoming_shows_count = upcoming_shows_count + 1
            response['data'].append({
                'name': name,
                'id': id,
                'num_upcoming_shows': upcoming_shows_count
            })
    response['count'] = len(response['data'])
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.filter_by(id=venue_id).first()
    shows = Show.query.filter_by(venue_id=venue.id).all()
    upcoming_shows = []
    past_shows = []
    for show in shows:
        current_start_time = show.start_time
        artist = Artist.query.filter_by(id=show.artist_id).first()
        show_start_time = show.start_time
        current_time = datetime.now()
        if (show_start_time <= current_time):
            past_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show_start_time
            })
        else:
            upcoming_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show_start_time
            })
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data
        )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        flash(f'An error occurred. Show could not be listed. Error: {e}')
        db.session.rollback()
        return render_template('forms/new_venue.html', form=form)
    finally:
        db.session.close()


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    # TODO: [COMPLETED] Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as e:
        error = True
        print(f'Error ==> {e}')
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash(f'An error occurred. Venue {venue_id} could not be deleted.')
            abort(400)
        else:
            flash(f'Venue {venue_id} was successfully deleted.')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists', methods=['GET'])
def artists():
    # TODO: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    response = {
        "data": []
    }
    artists = db.session.query(Artist.name, Artist.id).all()
    for artist in artists:
        name = artist[0]
        id = artist[1]
        if name.find(request.form.get('search_term', '')) != -1:
            shows = Show.query.filter_by(artist_id=id).all()
            upcoming_shows_count = 0
            for show in shows:
                if show.start_time > datetime.now():
                    upcoming_shows_count = upcoming_shows_count + 1
            response['data'].append({
                'name': name,
                'id': id,
                'num_upcoming_shows': upcoming_shows_count
            })
    response['count'] = len(response['data'])
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.filter_by(id=artist_id).first()
    shows = Show.query.filter_by(artist_id=artist_id).all()
    upcoming_shows = []
    past_shows = []
    for show in shows:
        show_start_time = show.start_time
        current_time = datetime.now()
        if (show_start_time > current_time):
            venues = Venue.query.filter_by(id=show.venue_id).all()
            for v in venues:
                upcoming_shows.append({
                    "venue_id": v.id,
                    "venue_name": v.name,
                    "venue_image_link": v.image_link,
                    "start_time": str(show_start_time)
                })
        else:
            venues = Venue.query.filter_by(id=show.venue_id).all()
            for v in venues:
                past_shows.append({
                    "venue_id": v.id,
                    "venue_name": v.name,
                    "venue_image_link": v.image_link,
                    "start_time": str(show_start_time)
                })
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows_count": len(past_shows)
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        form = ArtistForm()
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        db.session.commit()
        return redirect(url_for('show_artist', form=form, artist_id=artist_id))
    except Exception as e:
        flash(
            f'An error occurred. Artist ' +
            request.form['name'] +
            ' could not be listed.')
        db.session.rollback()
        return redirect(url_for('show_artist', form=form, artist_id=artist_id))
    finally:
        db.session.close()


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm()
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data,
        venue.city = form.city.data,
        venue.state = form.state.data,
        venue.address = form.address.data,
        venue.phone = form.phone.data,
        venue.genres = form.genres.data,
        venue.facebook_link = form.facebook_link.data
        db.session.commit()
        return redirect(url_for('show_venue', venue_id=venue_id))
    except Exception as e:
        flash(
            f'An error occurred. Venue ' +
            request.form['name'] +
            ' could not be listed.')
        db.session.rollback()
        return redirect(url_for('show_venue', venue_id=venue_id))
    finally:
        db.session.close()

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm()
    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data
        )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        flash(
            f'An error occurred. Artist ' +
            data.name +
            ' could not be listed. Error: {e}')
        db.session.rollback()
        return render_template('forms/new_artist.html', form=form)
    finally:
        db.session.close()

#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    data = []
    shows = Show.query.all()
    for show in shows:
        current_venue = Venue.query.filter_by(id=show.venue_id).first()
        current_artist = Artist.query.filter_by(id=show.artist_id).first()
        current_obj = {
            "venue_id": show.venue_id,
            "venue_name": current_venue.name,
            "artist_id": show.artist_id,
            "artist_name": current_artist.name,
            "artist_image_link": current_artist.image_link,
            "start_time": show.start_time
        }
        data.append(current_obj)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing
    # form
    try:
        form = ShowForm()
        show = Show(
            venue_id=form.venue_id.data,
            artist_id=form.artist_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        flash(f'An error occurred. Show could not be listed. Error: {e}')
        db.session.rollback()
        return render_template('forms/new_show.html', form=form)
    finally:
        db.session.close()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
