import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('server.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_note(name, date, link):
    note_ref = db.collection('notes').document()
    note_ref.set({
        'name': name,
        'date': date,
        'link': link
    })
    return note_ref

def add_form(name, expired_at, link):
    form_ref = db.collection('forms').document()
    form_ref.set({
        'name': name,
        'expired_at': expired_at,
        'link': link
    })
    return form_ref

def add_project(name, description, slides_link):
    project_ref = db.collection('projects').document()
    project_ref.set({
        'name': name,
        'description': description,
        'slides': slides_link,
        'team_members': [],
        'project_manager': None
    })
    return project_ref

def add_user(email, name, picture, student_id, role, payment, major_n_grade):
    user_ref = db.collection('users').document()
    user_ref.set({
        'email': email,
        'name': name,
        'picture': picture,
        'student_id': student_id,
        'role': role,
        'payment': payment,
        'paid': True,
        'major_n_grade': major_n_grade,
        'projects_involved': [],
        'managed_projects': []
    })
    return user_ref

def assign_member_to_project(user_ref, project_ref):
    project_ref.update({
        'team_members': firestore.ArrayUnion([user_ref])
    })
    user_ref.update({
        'projects_involved': firestore.ArrayUnion([project_ref])
    })

def assign_project_manager(user_ref, project_ref):
    project_ref.update({
        'project_manager': user_ref
    })
    user_ref.update({
        'managed_projects': firestore.ArrayUnion([project_ref])
    })

def add_fake_data():
    notes_data = [
        {
            "name": "Tech Note",
            "date": "2023/11/26",
            "link": "http://gdsc.com/note1126"
        }
    ]
    for note in notes_data:
        add_note(note['name'], note['date'], note['link'])

    forms_data = [
        {
            "expired_at": "Sun, 05 Dec 2023 19:06:46 GMT",
            "link": "http://example.com/form",
            "name": "Form 1203"
        }
    ]
    for form in forms_data:
        add_form(form['name'], form['expired_at'], form['link'])

    user_ref = add_user('sample@email.com', 'Sample Member', 'http://example.com/picture', '123456', 'Sample Role', 100, 'Sample Major and Grade')
    project_ref = add_project('Sample Project', 'Sample project description', 'http://example.com/slides')

    assign_member_to_project(user_ref, project_ref)
    assign_project_manager(user_ref, project_ref)

add_fake_data()
