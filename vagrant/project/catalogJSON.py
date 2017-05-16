from flask import Blueprint, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem, User

catalog_json = Blueprint('catalog_json', __name__,
                         template_folder='templates')

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@catalog_json.route('/catalog/<int:catalog_id>/items/JSON')
def catalogItemJSON(catalog_id):
    """ Show all items in the categories """
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(CatalogItem).filter_by(
        catalog_id=catalog_id).all()
    return jsonify(CatelogItems=[i.serialize for i in items])


@catalog_json.route('/catalog/JSON')
def catalogJSON():
    serial_catalogs = []
    catalogs = session.query(Catalog).all()

    for c in catalogs:
        serial_c = c.serialize

        items = session.query(CatalogItem).filter_by(catalog_id=c.id).all()
        serial_c['items'] = [i.serialize for i in items]
        serial_catalogs.append(serial_c)

    return jsonify(Catalog=serial_catalogs)
