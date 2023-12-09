from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.document import DocumentReference

app = Flask(__name__)

cred = credentials.Certificate('/home/testforgdsc/mysite/server.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def serialize_doc(doc):
    if isinstance(doc, DocumentReference):
        return doc.id
    elif isinstance(doc, dict):
        for key, value in doc.items():
            doc[key] = serialize_doc(value)
        return doc
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    else:
        return doc

@app.route('/')
def main_root():
    return "Service is ready!"

@app.route('/create', methods=['POST'])
def create_document():
    collection_name = request.json['collection']
    data = request.json['data']
    ref = db.collection(collection_name)
    ref.add(data)
    return jsonify({"message": "Document added successfully"}), 201

@app.route('/assign_member_to_project', methods=['POST'])
def assign_member_to_project():
    user_email = request.json['user_email']
    project_name = request.json['project_name']
    
    user_ref = db.collection('users').where('email', '==', user_email).limit(1).stream()
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    user_doc = next(user_ref, None)
    project_doc = next(project_ref, None)

    if not user_doc or not project_doc:
        return jsonify({"message": "User or Project not found"}), 404

    project_doc.reference.update({
        'team_members': firestore.ArrayUnion([user_doc.reference])
    })
    user_doc.reference.update({
        'projects_involved': firestore.ArrayUnion([project_doc.reference])
    })

    return jsonify({"message": "Member assigned to project successfully"}), 200

@app.route('/assign_pm', methods=['POST'])
def assign_project_manager():
    user_email = request.json['user_email']
    project_name = request.json['project_name']
    
    user_ref = db.collection('users').where('email', '==', user_email).limit(1).stream()
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    user_doc = next(user_ref, None)
    project_doc = next(project_ref, None)

    if not user_doc or not project_doc:
        return jsonify({"message": "User or Project not found"}), 404

    project_doc.reference.update({
        'project_manager': user_doc.reference
    })
    user_doc.reference.update({
        'managed_projects': firestore.ArrayUnion([project_doc.reference])
    })

    return jsonify({"message": "Project manager assigned successfully"}), 200

@app.route('/read', methods=['GET'])
def read_documents():
    collection_name = request.args.get('collection')
    documents = db.collection(collection_name).stream()
    result = [{doc.id: serialize_doc(doc.to_dict())} for doc in documents]
    return jsonify(result), 200

@app.route('/read_project/<name>', methods=['GET'])
def read_project(name):
    document = db.collection('projects').where('name', '==', name).stream()
    for doc in document:
        return jsonify(serialize_doc(doc.to_dict())), 200
    return jsonify({"message": "Project not found"}), 404

@app.route('/read_member/<email>', methods=['GET'])
def read_member(email):
    document = db.collection('users').where('email', '==', email).stream()
    for doc in document:
        return jsonify(serialize_doc(doc.to_dict())), 200
    return jsonify({"message": "Member not found"}), 404

@app.route('/read_project_manager/<project_name>', methods=['GET'])
def read_project_manager(project_name):
    document = db.collection('projects').where('name', '==', project_name).stream()
    for doc in document:
        project_data = serialize_doc(doc.to_dict())
        if 'project_manager' in project_data:
            pm_ref = project_data['project_manager']
            if pm_ref:
                pm_data = db.collection('users').document(pm_ref).get().to_dict()
                return jsonify(serialize_doc(pm_data)), 200
    return jsonify({"message": "Project Manager not found"}), 404

@app.route('/read_projects_of_member/<member_email>', methods=['GET'])
def read_projects_of_member(member_email):
    document = db.collection('users').where('email', '==', member_email).stream()
    for doc in document:
        user_data = serialize_doc(doc.to_dict())
        if 'projects_involved' in user_data:
            projects = [db.collection('projects').document(proj_ref).get().to_dict() for proj_ref in user_data['projects_involved']]
            return jsonify([serialize_doc(proj) for proj in projects]), 200
    return jsonify({"message": "Member not involved in any projects"}), 404

@app.route('/update/<collection>/<doc_id>', methods=['PUT'])
def update_document(collection, doc_id):
    data = request.json
    ref = db.collection(collection).document(doc_id)
    ref.update(data)
    return jsonify({"message": "Document updated successfully"}), 200

@app.route('/delete/<collection>/<doc_id>', methods=['DELETE'])
def delete_document(collection, doc_id):
    db.collection(collection).document(doc_id).delete()
    return jsonify({"message": "Document deleted successfully"}), 200

if __name__ == '__main__':
    app.run(threaded=True)
