from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem, User

from functools import wraps

from flask import session as login_session
import random
import string

from catalogJSON import catalog_json
from authorization import authorization

app = Flask(__name__)
app.register_blueprint(catalog_json)
app.register_blueprint(authorization)

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def user_signedin(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user_id = login_session.get('user_id')
        if user_id:
            return function(*args, **kwargs)
        else:
            return render_template("error.html",
                                   message="Please login first.")
    return wrapper


def item_exisited(function):
    @wraps(function)
    def wrapper(item_id=None, *args, **kwargs):
        if item_id:
            item = session.query(CatalogItem).filter_by(id=item_id).one()
            if item:
                return function(item_id=item_id, *args, **kwargs)

        return render_template("error.html",
                               message="This item doesn't exist.")
    return wrapper


def user_own_item(function):
    @wraps(function)
    def wrapper(item_id=None, *args, **kwargs):
        item = session.query(CatalogItem).filter_by(id=item_id).one()
        user_id = login_session.get('user_id')
        if user_id == item.user_id:
            return function(item_id=item_id, *args, **kwargs)
        else:
            message = "You don't have auhtorization to change this item"
            return render_template("error.html",
                                   message=message)
    return wrapper


def getState():
    if login_session.get('state') is None:
        # Create anti-forgery state token
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state

    return login_session.get('state')


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

    user_id = login_session.get('user_id')

    return render_template('main.html',
                           catalogs=catalogs,
                           items=items.fetchall(),
                           STATE=getState(),
                           user_id=user_id)


@app.route('/catalog/<int:catalog_id>/items')
def showCatalogItem(catalog_id):
    """ Show all items in the categories """
    user_id = login_session.get('user_id')

    catalogs = session.query(Catalog).all()
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id=catalog_id).all()

    itemHeader = "%s items (%d items)" % (catalog.name, len(items))

    return render_template('catalog.html',
                           catalogs=catalogs,
                           catalog=catalog,
                           items=items,
                           itemHeader=itemHeader,
                           STATE=getState(),
                           user_id=user_id)


@app.route('/catalog/<int:catalog_id>/<int:item_id>')
@item_exisited
def showItem(catalog_id, item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).one()
    user_id = login_session.get('user_id')

    if user_id == item.user_id:
        return render_template('item_authorized.html',
                               item=item,
                               catalog_id=catalog_id,
                               item_id=item_id,
                               STATE=getState(),
                               user_id=user_id)
    else:
        return render_template('item.html',
                               item=item,
                               catalog_id=catalog_id,
                               item_id=item_id,
                               STATE=getState(),
                               user_id=user_id)


@app.route('/catalog/<int:catalog_id>/items/new/', methods=['GET', 'POST'])
@user_signedin
def newCatalogItem(catalog_id):
    """ Create a new item under the catalog """
    user_id = login_session.get('user_id')

    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'],
                              catalog_id=catalog_id,
                              description=request.form['description'],
                              user_id=user_id)
        session.add(newItem)
        session.commit()
        flash("New item is created successfully.")
        return redirect(url_for('showCatalogItem', catalog_id=catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('newItem.html',
                               catalogs=catalogs,
                               catalog_id=catalog_id,
                               STATE=getState(),
                               user_id=user_id)


@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit/',
           methods=['GET', 'POST'])
@user_signedin
@item_exisited
@user_own_item
def editCatalogItem(catalog_id, item_id):
    """ Edit a catalog item """
    user_id = login_session.get('user_id')

    item = session.query(CatalogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.catalog_id = request.form['catalog_id']
        item.user_id = user_id

        session.commit()
        flash("Update the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id=catalog_id))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('editItem.html',
                               catalogs=catalogs,
                               catalog_id=catalog_id,
                               item=item,
                               STATE=getState(),
                               user_id=user_id)


@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
@user_signedin
@item_exisited
@user_own_item
def deleteCatalogItem(catalog_id, item_id):
    """ Delete a catalog item """
    item = session.query(CatalogItem).filter_by(id=item_id).one()

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Delete the item successfully.")
        return redirect(url_for('showCatalogItem', catalog_id=catalog_id))
    else:
        user_id = login_session.get('user_id')
        return render_template('deleteItem.html',
                               item=item,
                               STATE=getState(),
                               user_id=user_id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
