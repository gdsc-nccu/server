import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('server.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# 函數：向 Firestore 資料庫添加新社課筆記
def add_note(name, date, link):
    note_ref = db.collection('notes').document()
    note_ref.set({
        'name': name,
        'date': date,
        'link': link
    })
    return note_ref

# 函數：向 Firestore 資料庫添加新表單
def add_form(name, expired_at, link):
    form_ref = db.collection('forms').document()
    form_ref.set({
        'name': name,
        'expired_at': expired_at,
        'link': link
    })
    return form_ref

# 函數：向 Firestore 資料庫添加新專案
def add_project(name, description, slides_link):
    project_ref = db.collection('projects').document()
    project_ref.set({
        'name': name,
        'description': description,
        'slides': slides_link,
        'team_members': [],  # 初始化為空的團隊成員列表
        'project_manager': None  # 初始化為沒有項目經理
    })
    return project_ref

# 函數：向 Firestore 資料庫添加新用戶
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
        'projects_involved': [],  # 初始化為沒有參與的專案
        'managed_projects': []  # 初始化為沒有管理的專案
    })
    return user_ref

# 函數：將用戶指派為專案成員
def assign_member_to_project(user_ref, project_ref):
    project_ref.update({
        'team_members': firestore.ArrayUnion([user_ref])
    })
    user_ref.update({
        'projects_involved': firestore.ArrayUnion([project_ref])
    })

# 函數：將用戶指派為項目經理
def assign_project_manager(user_ref, project_ref):
    project_ref.update({
        'project_manager': user_ref
    })
    user_ref.update({
        'managed_projects': firestore.ArrayUnion([project_ref])
    })

# 函數：為測試目的向 Firestore 資料庫添加一些假數據
def add_fake_data():
    # 創建示例社課筆記
    notes_data = [
        {
            "name": "Tech Note",
            "date": "2023/11/26",
            "link": "http://gdsc.com/note1126"
        }
    ]
    for note in notes_data:
        add_note(note['name'], note['date'], note['link'])

    # 創建示例表單
    forms_data = [
        {
            "expired_at": "Sun, 05 Dec 2023 19:06:46 GMT",
            "link": "http://example.com/form",
            "name": "Form 1203"
        }
    ]
    for form in forms_data:
        add_form(form['name'], form['expired_at'], form['link'])

    # 創建示例用戶
    user_ref = add_user('sample@email.com', 'Sample Member', 'http://example.com/picture', '123456', 'Sample Role', 100, 'Sample Major and Grade')
    # 創建示例專案
    project_ref = add_project('Sample Project', 'Sample project description', 'http://example.com/slides')

    # 將示例用戶指派為示例專案的成員和經理
    assign_member_to_project(user_ref, project_ref)
    assign_project_manager(user_ref, project_ref)

add_fake_data()
