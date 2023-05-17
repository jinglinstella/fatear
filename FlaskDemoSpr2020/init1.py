# Import Flask Library
import datetime
import hashlib
import os

from flask import Flask, render_template, request, session, url_for, redirect, flash
# import sys
# sys.path.append("c:\python310\lib\site-packages")

import pymysql.cursors
from pymysql import IntegrityError

# for uploading photo:
from app import app
# from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=8889,
                       user='root',
                       password='root',
                       db='project',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/my_profile')
def my_profile():
    username = session['username']
    my_profile_query = '''
        SELECT * FROM user
        WHERE username = %s
    '''

    cursor = conn.cursor()
    cursor.execute(my_profile_query, (username))
    data = cursor.fetchall()
    cursor.close()

    return render_template('my_profile.html', username = username, profiles=data)

@app.route('/my_reviews')
def my_reviews():
    username = session['username']

    my_reviews_query = '''
        SELECT * FROM user 
        INNER JOIN reviewsong ON user.username = reviewsong.username
        NATURAL JOIN song
        WHERE user.username = %s        
    '''
    cursor = conn.cursor()
    cursor.execute(my_reviews_query, (username))
    data = cursor.fetchall()
    cursor.close()

    return render_template('my_reviews.html', username = username, reviews = data)




# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM user WHERE username = %s and pwd = %s'
    cursor.execute(query, (username, hashed_password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    # cursor.close()
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        # associate username with the string username
        session['username'] = username

        prev_login_time_query = 'SELECT lastlogin FROM user WHERE username = %s'
        cursor.execute(prev_login_time_query, (username))

        # need to reformat prev_login_time to appropriate mysql format
        prev_login_time = cursor.fetchone()['lastlogin']

        if prev_login_time is not None:
            prev_login_time = prev_login_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            prev_login_time = '1970-01-01 00:00:00'

        session['last_login'] = prev_login_time

        print("Session variables:", session['username'], session['last_login'])

        print("username: ", username, "lastlogin: ", prev_login_time)


        update_time_query = 'UPDATE user SET lastlogin = NOW() WHERE username = %s'
        cursor.execute(update_time_query, (username))
        conn.commit()
        # cursor.close()
        # session['prev_login_time'] = prev_login_time
        return redirect(url_for('home'))

    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        cursor.close()
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    nickname = request.form['nickname']

    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO user (username, pwd, fname, lname,nickname) VALUES(%s, %s, %s, %s,%s)'
        cursor.execute(ins, (username, hashed_password, fname, lname, nickname))
        conn.commit()
        # when we update we want to commit to make sure data is stored properly in the database
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    # it tries to fetch the username from the session dictionary
    cursor = conn.cursor()
    # query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    # query = 'SELECT '
    song_query = 'SELECT songID, title FROM song'
    # cursor.execute(query, (user))
    cursor.execute(song_query)
    # data = cursor.fetchall()
    songs = cursor.fetchall()
    cursor.close()
    # when we are done, send back to the user
    # return render_template('home.html', username=user, posts=data)
    # in the home.html file, iterate through posts

    return render_template('home.html', username=user, songs=songs)


@app.route('/new_reviews')
def new_reviews():
    username = session['username']
    last_login = session['last_login']

    print("In new_reviews():", username, last_login)
    print(last_login)

    # cursor.execute(last_login_time_query, (username))
    # last_login = cursor.fetchall()[0]['lastlogin']
    # The result of fetchall() is a list of dictionaries
    new_reviews_query = '''
        SELECT u.username, s.title, r.reviewText, r.reviewDate
        FROM reviewsong r
        NATURAL JOIN song s
        INNER JOIN user u ON r.username = u.username
        WHERE r.reviewDate >= %s AND u.username IN (
            SELECT f.user2 FROM friend f
            WHERE f.user1 = %s AND f.acceptStatus = "Accepted"
            UNION
            SELECT f.user1 FROM friend f
            WHERE f.user2 = %s AND f.acceptStatus = "Accepted"
            UNION
            SELECT follows FROM follows fo
            WHERE fo.follower = %s
        )
    '''
    print(new_reviews_query)
    cursor = conn.cursor()
    # cursor.execute(new_reviews_query, (last_login, username, username, username))
    cursor.execute(new_reviews_query, (last_login, username, username, username))
    print(last_login, username, username, username)
    data = cursor.fetchall()
    print(data)
    cursor.close()
    return render_template('new_reviews.html', username = username, posts=data)


@app.route('/new_songs')
def new_songs():
    username = session['username']
    last_login = session['last_login']
    # last_login_time_query = 'SELECT lastlogin FROM user WHERE username = %s'
    cursor = conn.cursor()
    # cursor.execute(last_login_time_query, (username))
    # last_login = cursor.fetchall()[0]['lastlogin']
    # The result of fetchall() is a list of dictionaries
    new_songs_query = '''
        SELECT fname, lname, title, releaseDate, songURL
        FROM userfanofartist ufa
        NATURAL JOIN artistperformssong aps
        NATURAL JOIN song s       
        NATURAL JOIN artist a
        WHERE releaseDate >= %s AND username = %s
    '''
    cursor.execute(new_songs_query, (last_login, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('favorite_artists_new_songs.html', username = username, posts=data)


@app.route('/show_songs_to_review')
def show_songs_to_review():
    username = session['username']
    cursor = conn.cursor()
    song_query = 'SELECT songID, title FROM song'
    cursor.execute(song_query)
    songs = cursor.fetchall()
    cursor.close()
    return render_template('show_songs_to_review.html', username=username, songs=songs)


@app.route('/submit_review', methods=['POST'])
def submit_review():
    username = session['username']
    songID = request.form['songID']
    review_text = request.form['review']
    timestamp = datetime.datetime.now()

    cursor = conn.cursor()
    review_query = 'INSERT INTO reviewsong (username, songID, reviewText,reviewDate) VALUES (%s, %s, %s, %s)'

    try:
        cursor.execute(review_query, (username, songID, review_text, timestamp))
        print("username: ", username, "review submitted at: ", timestamp)
        conn.commit()
        cursor.close()

        return redirect(url_for('show_songs_to_review'))

    except IntegrityError:
        cursor.close()
        error = "Duplicate review! You have already reviewed this song."
        # return render_template('show_songs_to_review.html', error=error)
        return error


@app.route('/show_songs_to_rate')
def show_songs_to_rate():
    username = session['username']
    cursor = conn.cursor()
    song_query = 'SELECT songID, title FROM song'
    cursor.execute(song_query)
    songs = cursor.fetchall()
    ratings = [1, 2, 3, 4, 5]
    cursor.close()
    return render_template('show_songs_to_rate.html', username = username, ratings=ratings, songs=songs)


@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    username = session['username']
    songID = request.form['songID']
    # review_text = request.form['review']
    rating = request.form['star']
    timestamp = datetime.datetime.now()

    cursor = conn.cursor()
    review_query = 'INSERT INTO ratesong (username, songID, stars,ratingDate) VALUES (%s, %s, %s, %s)'

    try:
        cursor.execute(review_query, (username, songID, rating, timestamp))
        conn.commit()
        cursor.close()

        return redirect(url_for('show_songs_to_rate'))

    except IntegrityError:
        cursor.close()
        error = "Duplicate rating! You have already rated this song."
        # return render_template('show_songs_to_rate.html',error=error)
        return error



@app.route('/select_criteria')
def select_criteria():
    # check that user is logged in
    # username = session['username']
    # should throw exception if username not found

    # when user click "Search", direct to select_criteria and fetch all search options from db
    # pass the value to html to display the options

    cursor = conn.cursor();
    genre_query = 'SELECT DISTINCT genre FROM songgenre'
    cursor.execute(genre_query)
    genre_data = cursor.fetchall()

    artist_query = 'SELECT DISTINCT fname, lname FROM artist'
    cursor.execute(artist_query)
    artist_data = [{'artist': f"{artist['fname']} {artist['lname']}"} for artist in cursor.fetchall()]

    cursor.close()

    return render_template('select_criteria.html', genre_list=genre_data, artist_list=artist_data)


@app.route('/select_criteria_loggedin')
def select_criteria_loggedin():
    # check that user is logged in
    username = session['username']
    # should throw exception if username not found

    # when user click "Search", direct to select_criteria and fetch all search options from db
    # pass the value to html to display the options

    cursor = conn.cursor();
    genre_query = 'SELECT DISTINCT genre FROM songgenre'
    cursor.execute(genre_query)
    genre_data = cursor.fetchall()

    artist_query = 'SELECT DISTINCT fname, lname FROM artist'
    cursor.execute(artist_query)
    artist_data = [{'artist': f"{artist['fname']} {artist['lname']}"} for artist in cursor.fetchall()]

    cursor.close()

    return render_template('select_criteria_loggedin.html', username = username, genre_list=genre_data, artist_list=artist_data)


@app.route('/display_songs', methods=["GET", "POST"])
def display_songs():
    # in select_criteria html, when click submit, redirect to show_songs
    # submit means sending the frontend variable to backend
    # genre, artist and rating value get passed to "request"
    # fetch the song info from the db based on search option
    genre = request.args.get('genre', None)
    artist = request.args.get('artist', None)
    rating = request.args.get('rating', None)
    cursor = conn.cursor();

    base_query = '''
        SELECT title, fname, lname, albumID
        FROM songgenre NATURAL JOIN song
        NATURAL JOIN artistperformssong
        NATURAL JOIN artist
        NATURAL JOIN songinalbum
        LEFT JOIN (SELECT songID, AVG(stars) as avg_rating FROM ratesong GROUP BY songID) as avg_ratings
        ON song.songID = avg_ratings.songID
        WHERE 1
    '''

    query_parameters = []

    if genre:
        base_query += ' AND genre = %s'
        query_parameters.append(genre)

    if artist:
        fname, lname = artist.split(' ', 1)
        base_query += ' AND fname = %s AND lname = %s'
        query_parameters.extend([fname, lname])

    if rating:
        rating_threshold = float(rating)
        # upper_bound = lower_bound + 1.0
        base_query += ' AND avg_rating > %s'
        query_parameters.append(rating_threshold)

    print(base_query)
    print(query_parameters)

    cursor.execute(base_query, tuple(query_parameters))
    data = cursor.fetchall()
    print(data)
    cursor.close()
    return render_template('display_songs.html', poster_name=f"Genre: {genre}, Artist: {artist}, Rating: {rating}",
                           posts=data)

@app.route('/show_artists_to_fan')
def show_artists_to_fan():
    username = session['username']
    cursor = conn.cursor()
    artist_query = 'SELECT artistID, fname, lname FROM artist'
    cursor.execute(artist_query)
    artists = cursor.fetchall()
    cursor.close()
    return render_template('show_artists_to_fan.html', username=username, artists=artists)

@app.route('/fan_an_artist', methods=['POST'])
def fan_an_artist():
    username = session['username']
    artistID = request.form['artistID']
    cursor = conn.cursor()
    check_request_query = '''
        SELECT * FROM userfanofartist
        WHERE username = %s AND artistID = %s
    '''
    cursor.execute(check_request_query, (username, artistID))
    result = cursor.fetchone()

    if result:
        cursor.close()
        return "Duplicate request!"

    fan_an_artist_query = '''
        INSERT INTO userfanofartist VALUES (%s, %s)

    '''
    cursor.execute(fan_an_artist_query, (username, artistID))
    conn.commit()
    cursor.close()

    return redirect(url_for('show_artists_to_fan'))


@app.route('/show_users_to_follow')
def show_users_to_follow():
    username = session['username']
    cursor = conn.cursor()
    user_query = 'SELECT username FROM user WHERE username != %s'
    cursor.execute(user_query, (username))
    users = cursor.fetchall()
    cursor.close()
    return render_template('show_users_to_follow.html', username=username, users=users)


@app.route('/follow_others', methods=['POST'])
def follow_others():
    username = session['username']
    follows = request.form['userID']
    timestamp = datetime.datetime.now()
    cursor = conn.cursor()

    check_request_query = '''
        SELECT * FROM follows
        WHERE follower = %s AND follows = %s
    '''

    print(check_request_query)

    cursor.execute(check_request_query, (username, follows))
    result = cursor.fetchone()
    print(result)

    if result:
        cursor.close()
        return "Duplicate request!"

    follow_others_query = '''
        INSERT INTO follows VALUES (%s, %s, %s)

    '''
    cursor.execute(follow_others_query, (username, follows, timestamp))
    conn.commit()
    cursor.close()

    return redirect(url_for('show_users_to_follow'))


@app.route('/show_users')
def show_users_to_friend():
    username = session['username']
    cursor = conn.cursor()
    user_query = 'SELECT username FROM user WHERE username != %s'
    cursor.execute(user_query, (username))
    users = cursor.fetchall()
    cursor.close()
    return render_template('show_users_to_friend.html', username=username, users=users)


@app.route('/submit_friend_request', methods=["POST"])
def submit_friend_request():
    username = session['username']
    userID = request.form['userID']
    timestamp = datetime.datetime.now()
    cursor = conn.cursor()

    # Check if the friend request already exists in the database
    check_request_query = '''
        SELECT * FROM friend
        WHERE (user1 = %s AND user2 = %s) OR (user1 = %s AND user2 = %s)
    '''

    cursor.execute(check_request_query, (username, userID, userID, username))
    result = cursor.fetchone()

    if result:
        cursor.close()
        return "Duplicate request!"

    submit_friend_request_query = '''
        INSERT INTO friend VALUES (%s, %s, "Pending", %s, %s, null)

    '''
    cursor.execute(submit_friend_request_query, (username, userID, username, timestamp))
    conn.commit()
    cursor.close()

    return redirect(url_for('show_users_to_friend'))


@app.route('/incoming_requests')
def incoming_request():
    username = session['username']
    last_login_time_query = 'SELECT lastlogin FROM user WHERE username = %s'
    cursor = conn.cursor()
    cursor.execute(last_login_time_query, (username))
    last_login = cursor.fetchall()[0]['lastlogin']
    # The result of fetchall() is a list of dictionaries
    new_friends_query = '''
        SELECT user1 as username, fname, lname, nickname
        FROM friend INNER JOIN user ON user1=user.username
        WHERE createdAt >= %s AND user2 = %s AND acceptStatus = "Pending" 
    '''
    cursor.execute(new_friends_query, (last_login, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('incoming_requests.html', username = username, posts=data)


@app.route('/process_request', methods=['POST'])
def process_request():
    username = session['username']
    requesting_user = request.form['requesting_user']
    action = request.form['action']
    timestamp = datetime.datetime.now()
    cursor = conn.cursor()

    if action == "Accept":
        update_query = '''
            UPDATE friend
            SET acceptStatus = "Accepted", updatedAt = %s
            WHERE user1 = %s AND user2 = %s
        '''
    elif action == "Reject":
        update_query = '''
            UPDATE friend
            SET acceptStatus = "Rejected", updatedAt = %s
            WHERE user1 = %s AND user2 = %s
        '''

    cursor.execute(update_query, (timestamp, requesting_user, username))
    conn.commit()
    cursor.close()

    return redirect(url_for('incoming_request'))

@app.route('/logout')
def logout():
    session.pop('username')
    # so that it no longer has a username in the dictionary
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
