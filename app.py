from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
from werkzeug.utils import secure_filename
import json
import os
import requests
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'products')
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = False  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


FIREBASE_SVC_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
if not FIREBASE_SVC_PATH:
    default_path = os.path.join(os.path.dirname(__file__), 'serviceAccount.json')
    if os.path.exists(default_path):
        FIREBASE_SVC_PATH = default_path

USE_FIREBASE_ADMIN = False
if FIREBASE_SVC_PATH:
    try:
        import firebase_admin
        from firebase_admin import credentials, auth as firebase_auth
        cred = credentials.Certificate(FIREBASE_SVC_PATH)
        firebase_admin.initialize_app(cred)
        USE_FIREBASE_ADMIN = True
        print('Firebase Admin initialized using', FIREBASE_SVC_PATH)
    except Exception as e:
        print('Failed to initialize Firebase Admin:', e)
        USE_FIREBASE_ADMIN = False
else:
    print('FIREBASE_SERVICE_ACCOUNT not set and serviceAccount.json not found — Firebase Admin disabled.')

FEATURED_PRODUCTS = [
    {
        'id': 1,
        'name': 'TX304 커브드 배기 벌룬 데님 (블랙)',
        'category': 'BOTTOM',
        'price': 34000,
        'image_url': 'images/product1.jpg',
        'badge': 'NEW',
        'description': '고급스러운 소재와 세련된 디자인이 특징인 검은색 데님 팬츠입니다. 편안한 착용감과 함께 스타일리시한 룩을 연출할 수 있습니다.',
        'specs': {'소재': '100% 면', '생산지': 'Made in Korea', '세탁': '30도 약한 물 세탁 권장', '핏': 'Regular Fit'}
    },
    {
        'id': 2,
        'name': '스웨이드 레더 무스탕 자켓_BROWN',
        'category': 'OUTWEAR',
        'price': 49000,
        'image_url': 'images/product2.jpg',
        'badge': 'SALE',
        'description': '부드러운 스웨이드 스타일의 고급 무스탕 자켓입니다. 갈색 톤으로 어떤 옷과도 잘 어울나며, 따뜻하고 편안한 착용 경험을 제공합니다.',
        'specs': {'소재': '스웨이드 레더', '생산지': 'Made in Korea', '세탁': '드라이클리닝 권장', '핏': 'Regular Fit'}
    },
    {
        'id': 3,
        'name': '브루니 커브드 코튼 팬츠 (3color)',
        'category': 'BOTTOM',
        'price': 89000,
        'image_url': 'images/product3.jpg',
        'badge': 'BEST',
        'description': '프리미엄 코튼 소재로 만든 편안하고 스타일리시한 팬츠입니다. 3가지 색상(검정, 흰색, 네이비)으로 선택 가능하며, 다리를 길어 보이게 하는 커브드 디자인이 특징입니다.',
        'specs': {'소재': '100% 유기농 면', '생산지': 'Made in Korea', '세탁': '30도 약한 물 세탁 권장', '핏': 'Slim Fit'}
    }
]

CATEGORIES = [
    {'name': 'BEST', 'url': '#'},
    {'name': 'Board', 'url': '#'},
    {'name': 'OUTWEAR', 'url': '#'},
    {'name': 'TOP', 'url': '#'},
    {'name': 'BOTTOM', 'url': '#'},
    {'name': 'ACC', 'url': '#'},
    {'name': 'Shoes', 'url': '#'}
]

@app.route('/')
def home():
    return render_template('index.html', featured_products=FEATURED_PRODUCTS, categories=CATEGORIES)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    
    product = next((p for p in FEATURED_PRODUCTS if p['id'] == product_id), None)
    if not product:
        return render_template('404.html', categories=CATEGORIES), 404
    
    
    product['description'] = '고급스러운 소재와 세련된 디자인이 특징인 상품입니다.'
    product['specs'] = {
        '소재': '100% 면',
        '생산지': 'Made in Korea',
        '세탁': '30도 약한 물 세탁 권장',
        '핏': 'Regular Fit'
    }
    product['reviews'] = [
        {'user': '김준호', 'rating': 5, 'text': '정말 좋은 상품입니다!', 'date': '2026-02-18'},
        {'user': '박지현', 'rating': 4, 'text': '색상이 예뻐요', 'date': '2026-02-17'},
    ]
    product['sizes'] = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    product['colors'] = ['검정', '흰색', '네이비']
    return render_template('product_detail.html', product=product, categories=CATEGORIES)

@app.route('/api/products')
def get_products():
    return jsonify({'products': FEATURED_PRODUCTS})

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    return jsonify({'success': True, 'message': '장바구니에 추가되었습니다.'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error = '아이디와 비밀번호를 모두 입력해주세요.'
        else:
            
            success = f'{username}님, 로그인 성공(샘플).'
    return render_template('login.html', error=error, success=success, categories=CATEGORIES)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if not username or not email or not password or not password2:
            error = '모든 항목을 입력해주세요.'
        elif password != password2:
            error = '비밀번호가 일치하지 않습니다.'
        else:
            
            success = f'{username}님, 회원가입이 완료되었습니다 (샘플).'
    return render_template('signup.html', error=error, success=success, categories=CATEGORIES)



@app.route('/sessionLogin', methods=['POST'])
def session_login():
    if not USE_FIREBASE_ADMIN:
        print('[/sessionLogin] ERROR: Firebase Admin not configured')
        return jsonify({'error': 'Firebase Admin not configured'}), 500
    data = request.get_json() or {}
    id_token = data.get('idToken')
    if not id_token:
        print('[/sessionLogin] ERROR: idToken required')
        return jsonify({'error': 'idToken required'}), 400
    try:
        print(f'[/sessionLogin] Verifying ID token (first 20 chars: {id_token[:20]}...)')
        decoded = firebase_auth.verify_id_token(id_token)
        
        user = {
            'uid': decoded.get('uid') or decoded.get('user_id') or decoded.get('sub'),
            'name': decoded.get('name'),
            'email': decoded.get('email'),
            'picture': decoded.get('picture')
        }
        session['user'] = user
        session.permanent = True  
        print(f'[/sessionLogin] SUCCESS: User {user.get("email")} logged in')
        return jsonify({'success': True})
    except Exception as e:
        print(f'[/sessionLogin] ERROR verifying token: {type(e).__name__}: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'invalid token', 'details': str(e)}), 400


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.permanent = False
    return redirect(url_for('home'))


@app.route('/api/auth/status')
def auth_status():
    
    user = session.get('user')
    return jsonify({'loggedIn': user is not None, 'user': user})


@app.route('/mypage')
def mypage():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    orders = []
    return render_template('mypage.html', user=user, orders=orders, categories=CATEGORIES)



@app.context_processor
def inject_globals():
    return {'categories': CATEGORIES, 'current_user': session.get('user')}


@app.route('/auth/kakao', methods=['POST'])
def auth_kakao():
    data = request.get_json() or {}
    access_token = data.get('access_token')
    if not access_token:
        return jsonify({'error': 'access_token required'}), 400

    
    kakao_user_url = 'https://kapi.kakao.com/v2/user/me'
    headers = {'Authorization': f'Bearer {access_token}'}
    resp = requests.get(kakao_user_url, headers=headers)
    if resp.status_code != 200:
        return jsonify({'error': 'failed to fetch kakao user', 'details': resp.text}), 400

    user_info = resp.json()
    kakao_id = user_info.get('id')
    if not kakao_id:
        return jsonify({'error': 'invalid kakao response'}), 400

    uid = f'kakao:{kakao_id}'

    
    if not USE_FIREBASE_ADMIN:
        return jsonify({'error': 'Firebase Admin not configured on server'}), 500

    try:
        custom_token = firebase_auth.create_custom_token(uid)
        
        token_str = custom_token.decode('utf-8')
        return jsonify({'customToken': token_str})
    except Exception as e:
        return jsonify({'error': 'failed to create custom token', 'details': str(e)}), 500



@app.route('/admin')
def admin():
    
    
    return render_template('admin.html', categories=CATEGORIES)


@app.route('/admin/products', methods=['GET'])
def admin_get_products():
    
    return jsonify({'products': FEATURED_PRODUCTS})


@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    
    data = request.get_json() or {}
    new_product = {
        'id': max([p['id'] for p in FEATURED_PRODUCTS]) + 1 if FEATURED_PRODUCTS else 1,
        'name': data.get('name'),
        'category': data.get('category'),
        'price': int(data.get('price', 0)),
        'image_url': data.get('image_url', 'images/placeholder.jpg'),
        'badge': data.get('badge', '')
    }
    FEATURED_PRODUCTS.append(new_product)
    return jsonify({'success': True, 'product': new_product})


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    
    global FEATURED_PRODUCTS
    FEATURED_PRODUCTS = [p for p in FEATURED_PRODUCTS if p['id'] != product_id]
    return jsonify({'success': True})


@app.route('/admin/products/upload', methods=['POST'])
def admin_upload_product():
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PNG, JPG, JPEG, GIF allowed'}), 400
    
    try:
        
        filename = secure_filename(file.filename)
        import uuid
        filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        
        name = request.form.get('name')
        category = request.form.get('category')
        price = int(request.form.get('price', 0))
        badge = request.form.get('badge', '')
        
        new_product = {
            'id': max([p['id'] for p in FEATURED_PRODUCTS]) + 1 if FEATURED_PRODUCTS else 1,
            'name': name,
            'category': category,
            'price': price,
            'image_url': f'images/products/{filename}',
            'badge': badge
        }
        FEATURED_PRODUCTS.append(new_product)
        return jsonify({'success': True, 'product': new_product})
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/admin/products/get/<int:product_id>', methods=['GET'])
def admin_get_product(product_id):
    
    product = next((p for p in FEATURED_PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'success': True, 'product': product})


@app.route('/admin/products/update/<int:product_id>', methods=['POST'])
def admin_update_product(product_id):
    
    data = request.get_json() or {}
    
    
    product = next((p for p in FEATURED_PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    
    if 'name' in data:
        product['name'] = data['name']
    if 'price' in data:
        product['price'] = int(data['price'])
    if 'category' in data:
        product['category'] = data['category']
    if 'badge' in data:
        product['badge'] = data['badge']
    if 'description' in data:
        product['description'] = data['description']
    if 'specs' in data:
        product['specs'] = data['specs']
    
    return jsonify({'success': True, 'product': product})


@app.route('/admin/orders')
def admin_get_orders():
    
    orders = [
        {'id': 1, 'user': '홍길동', 'items': 2, 'total': 150000, 'status': '배송중'},
        {'id': 2, 'user': '김철수', 'items': 1, 'total': 89000, 'status': '배송완료'},
    ]
    return render_template('admin.html', categories=CATEGORIES, orders=orders)


if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)
