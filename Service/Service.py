from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1.document import DocumentReference
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

# cred = credentials.Certificate('/home/testforgdsc/mysite/server.json')
cred = credentials.Certificate('Scripts/server.json')
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

@app.route('/google_login', methods=['POST'])
def google_login():
    id_token = request.json.get('idToken')
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_email = decoded_token['email']
        access_token = create_access_token(identity=user_email)
        print(access_token)
        return jsonify(access_token=access_token), 200
    except:
        return jsonify(message="Google login failed"), 401

@app.route('/create', methods=['POST'])
def create_document():
    collection_name = request.json['collection']
    data = request.json['data']

    # Check Index
    unique_index_field = None
    if collection_name == 'forms':
        unique_index_field = 'name'
    elif collection_name == 'notes':
        unique_index_field = 'name'
    elif collection_name == 'projects':
        unique_index_field = 'name'
    elif collection_name == 'users':
        unique_index_field = 'email'

    if unique_index_field and unique_index_field in data:
        existing_doc = db.collection(collection_name).where(unique_index_field, '==', data[unique_index_field]).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": f"{unique_index_field} already exists"}), 400

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

    result = []
    for doc in documents:
        doc_data = serialize_doc(doc.to_dict())

        if collection_name == 'users':
            if 'managed_projects' in doc_data:
                managed_project_names = []
                for project_ref in doc_data['managed_projects']:
                    project_data = db.collection('projects').document(project_ref).get()
                    if project_data.exists:
                        managed_project_names.append(project_data.to_dict().get('name', 'Unknown'))
                doc_data['managed_projects'] = managed_project_names

            if 'projects_involved' in doc_data:
                involved_project_names = []
                for project_ref in doc_data['projects_involved']:
                    project_data = db.collection('projects').document(project_ref).get()
                    if project_data.exists:
                        involved_project_names.append(project_data.to_dict().get('name', 'Unknown'))
                doc_data['projects_involved'] = involved_project_names

        elif collection_name == 'projects':
            if 'project_manager' in doc_data:
                pm_ref = doc_data['project_manager']
                if pm_ref:
                    pm_data = db.collection('users').document(pm_ref).get()
                    if pm_data.exists:
                        doc_data['project_manager'] = pm_data.to_dict().get('email', 'Unknown')

            if 'team_members' in doc_data:
                team_member_emails = []
                for member_ref in doc_data['team_members']:
                    member_data = db.collection('users').document(member_ref).get()
                    if member_data.exists:
                        team_member_emails.append(member_data.to_dict().get('email', 'Unknown'))
                doc_data['team_members'] = team_member_emails

        result.append({doc.id: doc_data})

    return jsonify(result), 200

@app.route('/read_project/<name>', methods=['GET'])
def read_project(name):
    document = db.collection('projects').where('name', '==', name).stream()
    for doc in document:
        project_data = serialize_doc(doc.to_dict())

        if 'project_manager' in project_data:
            pm_ref = project_data['project_manager']
            if pm_ref:
                pm_data = db.collection('users').document(pm_ref).get()
                if pm_data.exists:
                    project_data['project_manager'] = pm_data.to_dict().get('email', 'Unknown')

        if 'team_members' in project_data:
            team_member_emails = []
            for member_ref in project_data['team_members']:
                member_data = db.collection('users').document(member_ref).get()
                if member_data.exists:
                    team_member_emails.append(member_data.to_dict().get('email', 'Unknown'))
            project_data['team_members'] = team_member_emails

        return jsonify(project_data), 200
    return jsonify({"message": "Project not found"}), 404

@app.route('/read_member/<email>', methods=['GET'])
def read_member(email):
    document = db.collection('users').where('email', '==', email).stream()
    for doc in document:
        user_data = serialize_doc(doc.to_dict())

        if 'managed_projects' in user_data:
            managed_project_names = []
            for project_ref in user_data['managed_projects']:
                project_data = db.collection('projects').document(project_ref).get()
                if project_data.exists:
                    managed_project_names.append(project_data.to_dict().get('name', 'Unknown'))
            user_data['managed_projects'] = managed_project_names

        if 'projects_involved' in user_data:
            involved_project_names = []
            for project_ref in user_data['projects_involved']:
                project_data = db.collection('projects').document(project_ref).get()
                if project_data.exists:
                    involved_project_names.append(project_data.to_dict().get('name', 'Unknown'))
            user_data['projects_involved'] = involved_project_names

        return jsonify(user_data), 200
    return jsonify({"message": "Member not found"}), 404

@app.route('/update_project/<project_name>', methods=['PUT'])
def update_project(project_name):
    data = request.json
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()

    project_doc = next(project_ref, None)
    if not project_doc:
        return jsonify({"message": "Project not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != project_name:
        existing_doc = db.collection('projects').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Project name already exists"}), 400

    project_doc.reference.update(data)
    return jsonify({"message": "Project updated successfully"}), 200

@app.route('/update_member/<email>', methods=['PUT'])
def update_member(email):
    data = request.json
    user_ref = db.collection('users').where('email', '==', email).limit(1).stream()

    user_doc = next(user_ref, None)
    if not user_doc:
        return jsonify({"message": "Member not found"}), 404

    # Check Index
    if 'email' in data and data['email'] != email:
        existing_doc = db.collection('users').where('email', '==', data['email']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Email already exists"}), 400

    user_doc.reference.update(data)
    return jsonify({"message": "Member updated successfully"}), 200

@app.route('/update_note/<note_name>', methods=['PUT'])
def update_note(note_name):
    data = request.json
    note_ref = db.collection('notes').where('name', '==', note_name).limit(1).stream()

    note_doc = next(note_ref, None)
    if not note_doc:
        return jsonify({"message": "Note not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != note_name:
        existing_doc = db.collection('notes').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Note name already exists"}), 400

    note_doc.reference.update(data)
    return jsonify({"message": "Note updated successfully"}), 200

@app.route('/update_form/<form_name>', methods=['PUT'])
def update_form(form_name):
    data = request.json
    form_ref = db.collection('forms').where('name', '==', form_name).limit(1).stream()

    form_doc = next(form_ref, None)
    if not form_doc:
        return jsonify({"message": "Form not found"}), 404

    # Check Index
    if 'name' in data and data['name'] != form_name:
        existing_doc = db.collection('forms').where('name', '==', data['name']).limit(1).get()
        if len(existing_doc) > 0:
            return jsonify({"message": "Form name already exists"}), 400

    form_doc.reference.update(data)
    return jsonify({"message": "Form updated successfully"}), 200

@app.route('/delete_form/<form_name>', methods=['DELETE'])
def delete_form(form_name):
    form_ref = db.collection('forms').where('name', '==', form_name).limit(1).stream()
    form_doc = next(form_ref, None)
    if form_doc:
        form_doc.reference.delete()
        return jsonify({"message": "Form deleted successfully"}), 200
    else:
        return jsonify({"message": "Form not found"}), 404

@app.route('/delete_note/<note_name>', methods=['DELETE'])
def delete_note(note_name):
    note_ref = db.collection('notes').where('name', '==', note_name).limit(1).stream()
    note_doc = next(note_ref, None)
    if note_doc:
        note_doc.reference.delete()
        return jsonify({"message": "Note deleted successfully"}), 200
    else:
        return jsonify({"message": "Note not found"}), 404

@app.route('/delete_project/<project_name>', methods=['DELETE'])
def delete_project(project_name):
    project_ref = db.collection('projects').where('name', '==', project_name).limit(1).stream()
    project_doc = next(project_ref, None)
    if project_doc:
        project_doc.reference.delete()
        return jsonify({"message": "Project deleted successfully"}), 200
    else:
        return jsonify({"message": "Project not found"}), 404

@app.route('/delete_member/<member_email>', methods=['DELETE'])
def delete_member(member_email):
    member_ref = db.collection('users').where('email', '==', member_email).limit(1).stream()
    member_doc = next(member_ref, None)
    if member_doc:
        member_doc.reference.delete()
        return jsonify({"message": "Member deleted successfully"}), 200
    else:
        return jsonify({"message": "Member not found"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", threaded=True)
