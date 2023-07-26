
import collections
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = None  # Variable para almacenar la base de datos actual
selected_database = None  # Variable para almacenar el nombre de la base de datos seleccionada
selected_collection = None  # Variable para almacenar el nombre de la colección seleccionada

@app.route('/')
def index():
    # Obtener la lista de nombres de bases de datos
    database_names = client.list_database_names()
    collections = None

    if selected_database:
        db= client[selected_database]
        collections = db.list_collection_names()

    return render_template('index.html', database_names=database_names, selected_database=selected_database, selected_collection=selected_collection, collections=collections)

@app.route('/createDatabaseCollection', methods=['POST'])
def create_database_collection():
    global db, selected_database, selected_collection
    database_name = request.form.get('databaseName')
    collection_name = request.form.get('collectionName')

    #if not database_name or not collection_name:
        #return jsonify({"error": "Debe proporcionar un nombre de base de datos y un nombre de colección"}), 400

    # Crear la base de datos si no existe
    db = client[database_name]

    #if collection_name in db.list_collection_names():
        #return jsonify({"error": f"La colección '{collection_name}' ya existe en la base de datos '{database_name}'"}), 400

    # Crear la colección en la base de datos
    db.create_collection(collection_name)
    collections = db.list_collection_names()

    selected_database = database_name
    selected_collection = collection_name

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()

    # Pasa la variable db al contexto de la plantilla
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db)

@app.route('/selectDatabase', methods=['POST'])
def select_database():
    global db, selected_database, selected_collection
    database_name = request.form.get('databaseName')

    #if not database_name:
        #return jsonify({"error": "Debe proporcionar un nombre de base de datos"}), 400

    db = client[database_name]
    selected_database = database_name
    selected_collection = None  # Restablecer la selección de colección al cambiar de base de datos

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()

    # Pasa la variable db al contexto de la plantilla
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db)


@app.route('/deleteDatabase', methods=['POST'])
def delete_database():
    global db, selected_database, selected_collection

    if not selected_database:
        return jsonify({"error": "No se ha seleccionado ninguna base de datos"}), 400

    # Eliminar la base de datos actual
    client.drop_database(selected_database)
    db = None
    selected_database = None
    selected_collection = None

    return redirect(url_for('index'))

@app.route('/createCollection', methods=['POST'])
def create_collection():
    global db, selected_database, selected_collection

    database_name = request.form.get('databaseName')
    collection_name = request.form.get('newCollectionName')

    if not database_name or not collection_name:
        return jsonify({"error": "Debe proporcionar un nombre de base de datos y un nombre de colección"}), 400

    db = client[database_name]

    if collection_name in db.list_collection_names():
        return jsonify({"error": f"La colección '{collection_name}' ya existe en la base de datos '{database_name}'"}), 400

    # Crear la colección en la base de datos
    db.create_collection(collection_name)

    selected_database = database_name
    selected_collection = collection_name

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()

    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db)


@app.route('/deleteCollection', methods=['POST'])
def delete_collection():
    global db, selected_database, selected_collection

    collection_name = request.form.get('collectionName')
    if not collection_name:
        return jsonify({"error": "Debe proporcionar el nombre de la colección a eliminar"}), 400

    if not selected_database:
        return jsonify({"error": "No se ha seleccionado ninguna base de datos"}), 400

    # Eliminar la colección de la base de datos actual
    db.drop_collection(collection_name)

    # Actualizar la lista de colecciones en el contexto
    collections = db.list_collection_names()

    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db)
    
@app.route('/selectCollection', methods=['POST'])
def select_collection():
    global selected_collection
    selected_collection = request.form.get('collectionName')
    return redirect(url_for('index'))

@app.route('/showDocuments', methods=['POST'])
def show_documents():
    global db, selected_database, selected_collection

    # Obtener los nombres de la base de datos y de la colección del cuerpo JSON de la solicitud
    database_name = request.json['databaseName']
    collection_name = request.json['collectionName']

    #if not database_name or not collection_name:
        #return jsonify({"error": "Debe seleccionar una base de datos y una colección"}), 400

    client= MongoClient("mongodb://localhost:27017/")
    db = client[database_name]
    collection = db[collection_name]

    documents = list(collection.find({}))

    if not documents:
        return jsonify({"message": "No hay documentos disponibles"})

    # Convertir el ObjectId a una representación serializable para JSON
    for document in documents:
        document['_id'] = str(document['_id'])

    return jsonify(documents)



@app.route('/toggleDocuments', methods=['GET'])
def toggle_documents():
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db)

def get_documents():
    global db, selected_database, selected_collection

    if selected_database and selected_collection:
        collection = db[selected_collection]
        documents = list(collection.find({}))

        # Convertir el ObjectId a una representación serializable para JSON
        for document in documents:
            document['_id'] = str(document['_id'])

        return jsonify(documents)
    else:
        return jsonify({"error": "No se ha seleccionado una base de datos o una colección"}), 400


@app.route('/insertDocuments', methods=['POST'])
def insert_documents():
    global db, selected_database, selected_collection

    database_name = request.form.get('databaseName')
    collection_name = request.form.get('collectionName')
    new_documents = request.form.get('newDocuments')

    if not database_name or not collection_name or not new_documents:
        return jsonify({"error": "Debe proporcionar el nombre de la base de datos, el nombre de la colección y los documentos a insertar"}), 400

    db = client[database_name]
    collection = db[collection_name]

    try:
        documents = json.loads(new_documents)
        if isinstance(documents, dict):
            collection.insert_one(documents)
        elif isinstance(documents, list):
            collection.insert_many(documents)
        else:
            return jsonify({"error": "Los documentos deben ser un objeto JSON o una lista de objetos JSON"}), 400
    except json.JSONDecodeError:
        return jsonify({"error": "Los documentos deben estar en formato JSON válido"}), 400

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()
    # Obtener los documentos actualizados de la colección seleccionada
    documents = get_documents()
    
    # Redirigir a la página principal con los datos actualizados
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db, documents=documents)



@app.route('/deleteDocuments', methods=['POST'])
def delete_documents():
    global db, selected_database, selected_collection

    database_name = request.form.get('databaseName')
    collection_name = request.form.get('collectionName')
    delete_condition = request.form.get('deleteCondition')

    if not database_name or not collection_name or not delete_condition:
        return jsonify({"error": "Debe proporcionar el nombre de la base de datos, el nombre de la colección y la condición de eliminación"}), 400

    db = client[database_name]
    collection = db[collection_name]

    try:
        delete_condition = json.loads(delete_condition)
    except json.JSONDecodeError:
        return jsonify({"error": "La condición de eliminación debe estar en formato JSON válido"}), 400

    # Eliminar los documentos que coinciden con la condición
    result = collection.delete_many(delete_condition)
    deleted_count = result.deleted_count

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()

    # Obtener los documentos actualizados de la colección seleccionada
    documents = get_documents()

    # Redirigir a la página principal con los datos actualizados
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db, documents=documents)

    #return jsonify({"message": f"Se eliminaron {deleted_count} documentos que coinciden con la condición"})

@app.route('/updateDocuments', methods=['POST'])
def update_documents():
    global db, selected_database, selected_collection

    database_name = request.form.get('databaseName')
    collection_name = request.form.get('collectionName')
    update_condition = request.form.get('updateCondition')
    update_value = request.form.get('updateValue')

    if not database_name or not collection_name or not update_condition or not update_value:
        return jsonify({"error": "Debe proporcionar el nombre de la base de datos, el nombre de la colección, la condición de búsqueda y el valor de actualización"}), 400

    db = client[database_name]
    collection = db[collection_name]

    try:
        update_condition = json.loads(update_condition)
        update_value = json.loads(update_value)
    except json.JSONDecodeError:
        return jsonify({"error": "La condición de búsqueda y el valor de actualización deben estar en formato JSON válido"}), 400

    # Actualizar los documentos que coinciden con la condición
    result = collection.update_many(update_condition, {"$set": update_value})
    modified_count = result.modified_count

    # Obtener la lista de colecciones en la base de datos seleccionada
    collections = db.list_collection_names()

    # Obtener los documentos actualizados de la colección seleccionada
    documents = get_documents()

    # Redirigir a la página principal con los datos actualizados
    return render_template('index.html', database_names=client.list_database_names(), selected_database=selected_database, selected_collection=selected_collection, collections=collections, db=db, documents=documents)



   # return jsonify({"message": f"Se actualizaron {modified_count} documentos que coinciden con la condición"})

@app.route('/showDocumentsWithCondition', methods=['POST'])
def show_documents_with_condition():
    global db, selected_database, selected_collection

    database_name = request.form.get('databaseName')
    collection_name = request.form.get('collectionName')
    query_condition = request.form.get('queryCondition')

    if not database_name or not collection_name or not query_condition:
        return jsonify({"error": "Debe proporcionar el nombre de la base de datos, el nombre de la colección y la condición de búsqueda"}), 400

    db = client[database_name]
    collection = db[collection_name]

    try:
        query_condition = json.loads(query_condition)
    except json.JSONDecodeError:
        return jsonify({"error": "La condición de búsqueda debe estar en formato JSON válido"}), 400

    documents = list(collection.find(query_condition))

    if not documents:
        return jsonify({"message": "No se encontraron documentos que cumplan con la condición"})

    # Convertir el ObjectId a una representación serializable para JSON
    for document in documents:
        document['_id'] = str(document['_id'])

    return jsonify(documents)


if __name__ == '__main__':
    app.run(debug=True)

