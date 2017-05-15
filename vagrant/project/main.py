from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem, User

from functools import wraps

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def user_signedin(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user_id = login_session['user_id']
        if user_id:
            return function(*args, **kwargs)
        else:
            return render_template("error.html",
                                    message = "Please login first.")
    return wrapper

def item_exisited(function):
    @wraps(function)
    def wrapper(item_id = None, *args, **kwargs):
        if item_id:
            item = session.query(CatalogItem).filter_by(id = item_id).one()
            if item:
                return function(item_id = item_id, *args, **kwargs)

        return render_template("error.html",
                                message = "This item doesn't exist.")
    return wrapper

def user_own_item(function):
    @wraps(function)
    def wrapper(item_id = None, *args, **kwargs):
        item = session.query(CatalogItem).filter_by(id = item_id).one()
        user_id = login_session['user_id']
        if user_id == item.user_id:
            return function(item_id = item_id, *args, **kwargs)
        else:
            return render_template("error.html",
                                    message = "You don't have auhtorization to change this item")
    return wrapper

@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """ Show all categories """
    catalogs = session.query(Catalog).all()
    items = session.execute("""
        SELECT i.id, i.name, i.catalog_id, c.name AS catalog_name
        FROM Item i
        INNER JOIN Catalog c
        ON i.catalog_id = c.id
        ORDER BY i.created DESC
        LIMIT 10
        """)

    if not login_session['state']:
        # Create anti-forgery state token
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state

    if 'user_id' in login_session:
        user_id = login_session['user_id']
    else:
        user_id = None

    return render_template('main.html',
                            catalogs = catalogs,
                            items = items.fetchall(),
                            STATE = login_session['state'],
                            user_id = user_id)

@app.route('/catalog/<int:catalog_id>/items')
def showCatalogItem(catalog_id):
    """ Show all items in the categories """
    user_id = login_session['user_id']

    catalogs = session.query(Catalog).all()
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id = catalog_id).all()

    itemHeader = "%s items (%d items)" % (catalog.name, len(items))

    return render_template('catalog.html',
                           catalogs = catalogs,
                           catalog = catalog,
                           items = items,
                           itemHeader = itemHeader,
                           user_id = user_id)

@app.route('/catalog/<int:catalog_id>/<int:item_id>')
@item_exisited
def showItem(catalog_id, item_id):
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    user_id = login_session['user_id']

    if user_id == item.user_id:
        return render_template('item_authorized.html',
                                item = item,
                                catalog_id = catalog_id,
                                item_id = item_id,
                                user_id = user_id)
    else:
        return render_template('item.html',
                                item = item,
                                catalog_id = catalog_id,
                                item_id = item_id,
                                user_id = user_id)

@app.route('/catalog/<int:catalog_id>/items/new/', methods=['GET','POST'])
@user_signedin
def newCatalogItem(catalog_id):
    """ Create a new item under the catalog """
    user_id = login_session['user_id']

    if request.method == 'POST':
        user_id = login_session['user_id']
        newItem = CatalogItem(name = request.form['name'],
                              catalog_id = catalog_id,
                              description = request.form['description'],
                              user_id = user_id)
        session.add(newItem)
        session.commit()
        flash("New item is created successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('newItem.html',
                                catalogs = catalogs,
                                catalog_id = catalog_id,
                                user_id = user_id)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit/', methods=['GET','POST'])
@user_signedin
@item_exisited
@user_own_item
def editCatalogItem(catalog_id, item_id):
    """ Edit a catalog item """
    user_id = login_session['user_id']

    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        user_id = login_session['user_id']

        item.name = request.form['name']
        item.description = request.form['description']
        item.catalog_id = request.form['catalog_id']
        item.user_id = user_id

        session.commit()
        flash("Update the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('editItem.html',
                                catalogs = catalogs,
                                catalog_id = catalog_id,
                                item = item,
                                user_id = user_id)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET','POST'])
@user_signedin
@item_exisited
@user_own_item
def deleteCatalogItem(catalog_id, item_id):
    """ Delete a catalog item """
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Delete the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        return render_template('deleteItem.html',
                                item = item,
                                user_id = user_id)

@app.route('/catalog/<int:catalog_id>/items/JSON')
def catalogItemJSON(catalog_id):
    """ Show all items in the categories """
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id = catalog_id).all()
    return jsonify(CatelogItems=[i.serialize for i in items])

@app.route('/catalog/JSON')
def catalogJSON():
    serial_catalogs = []
    catalogs = session.query(Catalog).all()

    for c in catalogs:
        serial_c = c.serialize

        items = session.query(CatalogItem).filter_by(catalog_id = c.id).all()
        serial_c['items'] = [i.serialize for i in items]
        serial_catalogs.append(serial_c)

    return jsonify(Catalog=serial_catalogs)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        login_session['state'] = None
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])

    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        return render_template("error.html",
                                message = "Current user not connected.")

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        login_session['user_id'] = None
        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showCatalog'))
    else:
        return render_template("error.html",
                                message = "Failed to revoke token for given user.")

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)