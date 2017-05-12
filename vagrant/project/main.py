from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem

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

    return render_template('main.html',
                            catalogs = catalogs,
                            items = items.fetchall())

@app.route('/catalog/new', methods=['GET','POST'])
def newCatalog():
    """ Create a new catalog """
    if request.method == 'POST':
        newCatalog = Catalog(name = request.form['name'])
        session.add(newCatalog)
        session.commit()
        flash("New catalog is created successfully.")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCatalog.html')

@app.route('/catalog/<int:catalog_id>/edit', methods=['GET','POST'])
def editCatalog(catalog_id):
    """ Edit the catalog """
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    if request.method == 'POST':
        catalog.name = request.form['name'] # Check empty
        session.commit()
        flash("Update the catalog successfully.")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCatalog.html', catalog = catalog)


@app.route('/catalog/<int:catalog_id>/delete', methods=['GET','POST'])
def deleteCatalog(catalog_id):
    """ Delete the catalog """
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    if request.method == 'POST':
        session.delete(catalog)
        session.commit()
        flash("Delete the catalog successfully.")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCatalog.html', catalog = catalog)

@app.route('/catalog/<int:catalog_id>/items')
def showCatalogItem(catalog_id):
    """ Show all items in the categories """
    catalogs = session.query(Catalog).all()
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id = catalog_id).all()

    itemHeader = "%s items (%d items)" % (catalog.name, len(items))
    return render_template('catalog.html',
                           catalogs = catalogs,
                           catalog = catalog,
                           items = items,
                           itemHeader = itemHeader)

@app.route('/catalog/<int:catalog_id>/<int:item_id>')
def showItem(catalog_id, item_id):
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    return render_template('item.html',
                            item = item,
                            catalog_id = catalog_id,
                            item_id = item_id)

@app.route('/catalog/<int:catalog_id>/items/new/', methods=['GET','POST'])
def newCatalogItem(catalog_id):
    """ Create a new item under the catalog """
    if request.method == 'POST':
        newItem = CatalogItem(name = request.form['name'],
                              catalog_id = catalog_id,
                              description = request.form['description'])
        session.add(newItem)
        session.commit()
        flash("New item is created successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('newItem.html',
                                catalogs = catalogs,
                                catalog_id = catalog_id)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit/', methods=['GET','POST'])
def editCatalogItem(catalog_id, item_id):
    """ Edit a catalog item """
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.catalog_id = request.form['catalog_id']
        session.commit()
        flash("Update the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('editItem.html',
                                catalogs = catalogs,
                                catalog_id = catalog_id,
                                item = item)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET','POST'])
def deleteCatalogItem(catalog_id, item_id):
    """ Delete a catalog item """
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Delete the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        return render_template('deleteItem.html', item = item)

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


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


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

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
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
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)