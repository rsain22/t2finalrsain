from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
db = SQLAlchemy(app)

class ArtistModel(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.String(22), primary_key = True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    #albums = db.relationship('Album', lazy='dynamic')
    albums = db.Column(db.String(100))
    tracks = db.Column(db.String(100))    
    self = db.Column(db.String(100))

    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.id = b64encode(self.name.encode()).decode('utf-8')[0:22]
        self.albums = f"http://t2finalrsain.herokuapp.com/artists/{self.id}/albums"
        self.tracks = f"http://t2finalrsain.herokuapp.com/artists/{self.id}/tracks"
        self.self = f"http://t2finalrsain.herokuapp.com/artists/{self.id}"

class AlbumModel(db.Model):
    __tablename__ = 'album'

    id = db.Column(db.String(22), primary_key = True)
    artist_id = db.Column(db.String(22), db.ForeignKey('artist.id'))
    name = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    artist = db.Column(db.String(100))
    tracks = db.Column(db.String(100))
    self = db.Column(db.String(100))

    def __init__(self, name, genre, artist_id):
        self.name = name
        self.genre = genre
        self.artist_id = artist_id
        self.id = b64encode((self.name+":"+artist_id).encode()).decode('utf-8')[0:22]
        self.artist = f"http://t2finalrsain.herokuapp.com/artists/{self.artist_id}"
        self.tracks = f"http://t2finalrsain.herokuapp.com/artists/{self.artist_id}/tracks"
        self.self = f"http://t2finalrsain.herokuapp.com/albums/{self.id}"

class TrackModel(db.Model):
    __tablename__ = 'track'

    id = db.Column(db.String(22), primary_key = True)
    album_id = db.Column(db.String(22), db.ForeignKey('album.id'))
    name = db.Column(db.String(100))
    duration = db.Column(db.Float())
    times_played = db.Column(db.Integer())
    artist = db.Column(db.String(100))
    album = db.Column(db.String(100))
    self = db.Column(db.String(100))

    def __init__(self, name, duration, artist_id, album_id):
        self.name = name
        self.duration = duration
        self.times_played = 0
        self.album_id = album_id
        self.id = b64encode((self.name+":"+album_id).encode()).decode('utf-8')[0:22]
        self.artist = f"http://t2finalrsain.herokuapp.com/artists/{artist_id}"
        self.album = f"http://t2finalrsain.herokuapp.com/albums/{self.album_id}"
        self.self = f"http://t2finalrsain.herokuapp.com/tracks/{self.id}"

db.create_all()

artist_post_args = reqparse.RequestParser()
artist_post_args.add_argument("name", type=str, required = True)
artist_post_args.add_argument("age", type=int, required = True)


artist_fields = {
    'name': fields.String,
    'age': fields.Integer,
    'albums': fields.String,
    'tracks': fields.String,
    'self': fields.String
}

album_post_args = reqparse.RequestParser()
album_post_args.add_argument("name", type=str, required = True)
album_post_args.add_argument("genre", type=str, required = True)

album_fields = {
    'name': fields.String,
    'genre': fields.String,
    'artist': fields.String,
    'tracks': fields.String,
    'self': fields.String
}

track_post_args = reqparse.RequestParser()
track_post_args.add_argument("name", type=str, required=True)
track_post_args.add_argument("duration", type=float, required=True)

track_fields = {
    'name': fields.String,
    'duration': fields.Float,
    'times_played': fields.Integer,
    'artist': fields.String,
    'album': fields.String,
    'self': fields.String
}

class Artists(Resource):
    @marshal_with(artist_fields)
    def get(self):
        artists = ArtistModel.query.all()
        return artists, 200
    @marshal_with(artist_fields)
    def post(self):
        args = artist_post_args.parse_args()
        if not args['name'] or not args['age']:
            return {}, 400
        if not isinstance(args['name'], str) or not isinstance(args['age'],int):
            return {}, 400
        artist = ArtistModel(name=args['name'], age=args['age'])
        busqueda = ArtistModel.query.filter_by(id=artist.id).first()
        if busqueda:
            return busqueda, 409

        db.session.add(artist)
        db.session.commit()

        return artist, 201    

class Artist(Resource):
    @marshal_with(artist_fields)
    def get(self, artist_id):
        artist = ArtistModel.query.filter_by(id=artist_id).first()
        if not artist:
            return artist, 404
        return artist, 200
 
    @marshal_with(artist_fields)
    def delete(self, artist_id):
        artist = ArtistModel.query.get(artist_id)
        if not artist:
            return artist, 404
        albums = AlbumModel.query.filter_by(artist_id = artist_id)
        for album in albums:
            tracks = TrackModel.query.filter_by(album_id = album.id)
            for track in tracks:
                db.session.delete(track)
            db.session.delete(album)
        db.session.delete(artist)
        db.session.commit()
        return artist, 204



class Albums(Resource):
    @marshal_with(album_fields)
    def get(self):
        albums = AlbumModel.query.all()
        return albums, 200

class Album(Resource):
    @marshal_with(album_fields)
    def get(self, album_id):
        album = AlbumModel.query.filter_by(id=album_id).first()
        if not album:
            return album, 404
        return album, 200
 
    @marshal_with(album_fields)
    def delete(self, album_id):
        album = AlbumModel.query.get(album_id)
        if not album:
            return album, 404
        tracks = TrackModel.query.filter_by(album_id = album_id)
        for track in tracks:
            db.session.delete(track)
        db.session.delete(album)
        db.session.commit()
        return album, 204

class AlbumByArtist(Resource):
    @marshal_with(album_fields)
    def get(self, artist_id):
        artist = ArtistModel.query.get(artist_id)
        if not artist:
            return artist, 404
        albums = AlbumModel.query.filter_by(artist_id = artist_id)
        albums_list = []
        for album in albums:
            albums_list.append(album)
        return albums_list, 200
    @marshal_with(album_fields)
    def post(self, artist_id):
        args = album_post_args.parse_args()
        if not args['name'] or not args['genre']:
            return {}, 400
        if not isinstance(args['name'], str) or not isinstance(args['genre'],str):
            return {}, 400

        artist = ArtistModel.query.get(artist_id)
        if not artist:
            return {}, 422        
        album = AlbumModel(name=args['name'], genre=args['genre'], artist_id=artist_id)
        busqueda = AlbumModel.query.filter_by(id=album.id).first()
        if busqueda:
            return busqueda, 409

        db.session.add(album)
        db.session.commit()

        return album, 201





class Tracks(Resource):
    @marshal_with(track_fields)
    def get(self):
        tracks = TrackModel.query.all()
        return tracks, 200   

class Track(Resource):
    @marshal_with(track_fields)
    def get(self, track_id):
        track = TrackModel.query.filter_by(id=track_id).first()
        if not track:
            return track, 404
        return track, 200
 
    @marshal_with(track_fields)
    def delete(self, track_id):
        track = TrackModel.query.get(track_id)
        if not track:
            return track, 404
        db.session.delete(track)
        db.session.commit()
        return track, 204 

class TracksByAlbum(Resource):
    @marshal_with(track_fields)
    def get(self, album_id):
        album = AlbumModel.query.get(album_id)
        if not album:
            return album, 404

        tracks = TrackModel.query.filter_by(album_id = album_id)
        track_list = []
        for track in tracks:
            track_list.append(track)
        return track_list, 200

    @marshal_with(track_fields)
    def post(self, album_id):
        args = track_post_args.parse_args()
        if not args['name'] or not args['duration']:
            return {}, 400
        if not isinstance(args['name'], str) or not isinstance(args['duration'],float):
            return {}, 400        
        album = AlbumModel.query.filter_by(id=album_id).first()
        if not album:
            return {}, 422
        track = TrackModel(name=args['name'], duration=args['duration'], artist_id = album.artist_id, album_id=album_id)
        busqueda = TrackModel.query.filter_by(id=track.id).first()
        if busqueda:
            return busqueda, 409

        db.session.add(track)
        db.session.commit()

        return track, 201

class TracksByArtist(Resource):
    @marshal_with(track_fields)
    def get(self, artist_id):
        artist = ArtistModel.query.get(artist_id)
        if not artist:
            return artist, 404
        albums = AlbumModel.query.filter_by(artist_id = artist_id)
        track_list = []
        for album in albums:
            print(album.id)
            tracks = TrackModel.query.filter_by(album_id = album.id)
            for track in tracks:
                print(track.id)
                track_list.append(track)
        return track_list, 200

class PlayArtist(Resource):
    @marshal_with(track_fields)
    def put(self, artist_id):
        artist = ArtistModel.query.get(artist_id)
        if not artist:
            return artist, 404
        albums = AlbumModel.query.filter_by(artist_id = artist_id)
        track_list = []
        for album in albums:
            print(album.id)
            tracks = TrackModel.query.filter_by(album_id = album.id)
            for track in tracks:
                track.times_played += 1
                track_list.append(track)
        db.session.commit()
        return track_list, 200  

class PlayAlbum(Resource):
    @marshal_with(track_fields)
    def put(self, album_id):
        album = AlbumModel.query.get(album_id)
        if not album:
            return album, 404

        tracks = TrackModel.query.filter_by(album_id = album_id)
        track_list = []
        for track in tracks:
            track.times_played += 1
            track_list.append(track)
        db.session.commit()
        return track_list, 200

class PlayTrack(Resource):
    @marshal_with(track_fields)
    def put(self, track_id):
        track = TrackModel.query.get(track_id)
        if not track:
            return track, 404
        track.times_played += 1
        db.session.commit()
        return track, 200
        

api.add_resource(Artists, '/artists')
api.add_resource(Artist, '/artists/<artist_id>')
api.add_resource(Albums, '/albums')
api.add_resource(Album, '/albums/<album_id>')
api.add_resource(AlbumByArtist, '/artists/<artist_id>/albums')
api.add_resource(Tracks, '/tracks')
api.add_resource(Track, '/tracks/<track_id>')
api.add_resource(TracksByAlbum, '/albums/<album_id>/tracks')
api.add_resource(TracksByArtist, '/artists/<artist_id>/tracks')
api.add_resource(PlayArtist, '/artists/<artist_id>/albums/play')
api.add_resource(PlayAlbum, '/albums/<album_id>/tracks/play')
api.add_resource(PlayTrack, '/tracks/<track_id>/play')
#db.create_all()

if __name__ == '__main__':
    app.run(debug=True)