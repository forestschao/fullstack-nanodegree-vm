from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem

app = Flask(__name__)

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# #Fake Catalog
# currCatalog = {'name': 'The CRUDdy Crab', 'id': '1'}
# catalogs = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


# #Fake Catalog Items
# items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
# item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}

@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """ Show all categories """
    catalogs = session.query(Catalog).all()
    return render_template('catalog.html', catalogs = catalogs)

@app.route('/catalog/new', methods=['GET','POST'])
def newCatalog():
    """ Create a new catalog """
    if request.method == 'POST':
        newCatalog = Catalog(name = request.form['name'])
        session.add(newCatalog)
        session.commit()
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
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCatalog.html', catalog = catalog)

@app.route('/catalog/<int:catalog_id>/items')
def showCatalogItem(catalog_id):
    """ Show all items in the categories """
    catalog = session.query(Catalog).filter_by(id = catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id = catalog_id).all()
    return render_template('item.html', catalog = catalog, items = items)

@app.route('/catalog/<int:catalog_id>/items/new', methods=['GET','POST'])
def newCatalogItem(catalog_id):
    """ Create a new item under the catalog """
    if request.method == 'POST':
        newItem = CatalogItem(name = request.form['name'],
                              catalog_id = catalog_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        return render_template('newItem.html', catalog_id = catalog_id)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit', methods=['GET','POST'])
def editCatalogItem(catalog_id, item_id):
    """ Edit a catalog item """
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        session.commit()
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        return render_template('editItem.html', catalog_id = catalog_id, item = item)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET','POST'])
def deleteCatalogItem(catalog_id, item_id):
    """ Delete a catalog item """
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showCatalogItem', catalog_id = catalog_id))
    else:
        return render_template('deleteItem.html', item = item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)