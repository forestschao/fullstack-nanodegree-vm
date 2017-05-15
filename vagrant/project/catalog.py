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