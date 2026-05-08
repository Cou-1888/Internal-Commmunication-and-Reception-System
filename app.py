from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import mysql.connector
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'zaka_rdc_secret_key_123'

# Departments list for mail routing
departments = [
    'CEO', 'Finance', 'IT', 'Procurement', 'Social Services', 'Admin', 
    'Stores', 'Planning', 'Audit', 'Reception'
]

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'c@to10%Z'),
        database=os.environ.get('DB_NAME', 'test'),
        port=int(os.environ.get('DB_PORT', 4000)),
        buffered=True
        ssl_disabled=False if os.environ.get('DB_HOST') else True
    )

# Ensure admin user exists on startup (only if not already present)
def ensure_admin_exists():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM staff WHERE username = 'admin' LIMIT 1")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash('admin123')
            sql = "INSERT INTO staff (fullname, username, password, department, role) VALUES (%s, %s, %s, %s, %s)"
            values = ('System Admin', 'admin', hashed_pw, 'IT', 'IT Admin')
            cursor.execute(sql, values)
            conn.commit()
            print("Admin user created! Login with: admin / admin123")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error ensuring admin exists: {e}")

# Run on startup
ensure_admin_exists()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login(): 
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM staff WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['fullname'] = user['fullname']
            session['role'] = user['role']
            session['department'] = user['department']
            return jsonify({"status": "success", "message": f"Welcome, {user['fullname']}!", "redirect": "/home"})
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Database connection error: " + str(e)})



@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM incoming_mails ORDER BY id DESC LIMIT 5")
        incoming_data = cursor.fetchall()

        cursor.execute("SELECT * FROM outgoing_mails ORDER BY id DESC LIMIT 5")
        outgoing_data = cursor.fetchall()

        cursor.execute("SELECT * FROM call_records ORDER BY id DESC LIMIT 5")
        call_data = cursor.fetchall()

        cursor.execute("SELECT * FROM forms ORDER BY id DESC LIMIT 5")
        forms = cursor.fetchall()

        cursor.execute("SELECT * FROM messages WHERE is_urgent = 1 ORDER BY id DESC LIMIT 5")
        urgent_messages = cursor.fetchall()

        cursor.execute("SELECT * FROM messages WHERE is_urgent = 0 ORDER BY id DESC LIMIT 5")
        inbox_messages = cursor.fetchall()

        cursor.execute("SELECT * FROM messages WHERE recipient_department = %s ORDER BY created_at DESC", (session['department'],))
        all_messages = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total FROM incoming_mails")
        in_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM outgoing_mails")
        out_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM call_records")
        call_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM forms")
        forms_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE recipient_department = %s AND is_urgent = 1", (session['department'],))
        urgent_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE recipient_department = %s AND is_urgent = 0", (session['department'],))
        inbox_count = cursor.fetchone()['total']

        now = datetime.now()
        
        # NEW: Messages Today and Total Messages metrics
        today_str = now.strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE DATE(created_at) = %s", (today_str,))
        messages_today = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM messages")
        total_messages = cursor.fetchone()['total']
        return render_template('home.html',
                               incoming=incoming_data,
                               outgoing=outgoing_data,
                               calls=call_data,
                               forms=forms,
                               urgent_messages=urgent_messages,
                               inbox_messages=inbox_messages,
                               all_messages=all_messages,
                               in_count=in_count,
                               out_count=out_count,
                               call_count=call_count,
                               forms_count=forms_count,
                               urgent_count=urgent_count,
                               inbox_count=inbox_count,
                               messages_today=messages_today,
                               total_messages=total_messages,
                               user_role=session['role'],
                               now=now,
                               departments=departments)
    except Exception as e:
        print(f"Home page DB error: {e}")
        return render_template('home.html',
                              incoming=[], outgoing=[], calls=[], forms=[],
                              urgent_messages=[], inbox_messages=[], all_messages=[],
                              in_count=0, out_count=0, call_count=0, forms_count=0,
                              urgent_count=0, inbox_count=0, messages_today=0, total_messages=0,
                              user_role=session.get('role', ''), now=datetime.now(),
                              departments=departments), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/messages2')
def messages2():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch individual messages for user's dept (received + sent)
        cursor.execute("""
            SELECT 
                m.id,
                m.sender_name,
                m.sender_department,
                m.recipient_department,
                m.subject,
                LEFT(m.message, 120) as preview,
                m.message as full_message,
                m.is_urgent,
                m.action_status,
                m.attachment,
                m.created_at,
                m.parent_message_id
            FROM messages m
            WHERE (m.recipient_department = %s OR m.sender_department = %s)
            ORDER BY m.created_at DESC
        """, (session['department'], session['department']))
        messages = cursor.fetchall()
        
        urgent_messages = [m for m in messages if m['is_urgent'] == 1]
        inbox_messages = [m for m in messages if m['is_urgent'] == 0]
        new_messages = [m for m in messages if m.get('action_status') == 'new']
        
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE (recipient_department = %s OR sender_department = %s) AND is_urgent = 1", (session['department'], session['department']))
        urgent_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE (recipient_department = %s OR sender_department = %s) AND is_urgent = 0", (session['department'], session['department']))
        dept_count = cursor.fetchone()['total']
        
        # Count by status
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE (recipient_department = %s OR sender_department = %s) AND action_status = 'new'", (session['department'], session['department']))
        new_count = cursor.fetchone()['total']

        now = datetime.now()
        return render_template('messages2.html',
                               messages=messages,
                               urgent_messages=urgent_messages,
                               inbox_messages=inbox_messages,
                               new_messages=new_messages,
                               urgent_count=urgent_count,
                               dept_count=dept_count,
                               new_count=new_count,
                               user_role=session['role'],
                               now=now,
                               departments=departments)
    except Exception as e:
        return f"Database Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()

@app.route('/get_message/<int:msg_id>')
def get_message(msg_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT m.id, m.sender_name, m.sender_department, m.recipient_department,
                   m.subject, m.message, m.is_urgent, m.action_status, m.attachment,
                   COALESCE(m.created_at, NOW()) as created_at, m.parent_message_id
            FROM messages m
            WHERE m.id = %s AND (m.sender_department = %s OR m.recipient_department = %s)
        """, (msg_id, session['department'], session['department']))
        
        msg = cursor.fetchone()
        if not msg:
            return jsonify({'status': 'error', 'message': 'Message not found'}), 404
        
        # Auto-mark as viewed if recipient viewing and status is 'new'
        if msg['recipient_department'] == session['department'] and msg['action_status'] == 'new':
            cursor.execute("UPDATE messages SET action_status = 'viewed' WHERE id = %s", (msg_id,))
            conn.commit()
            msg['action_status'] = 'viewed'
        
        return jsonify({'status': 'success', 'message': msg})
        
    except Exception as e:
        print(f"Get message error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to load message'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/message_counts')
def api_message_counts():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COUNT(*) as urgent FROM messages 
            WHERE (recipient_department = %s OR sender_department = %s) AND is_urgent = 1
        """, (session['department'], session['department']))
        urgent = cursor.fetchone()['urgent']
        
        cursor.execute("""
            SELECT COUNT(*) as inbox FROM messages 
            WHERE (recipient_department = %s OR sender_department = %s) AND is_urgent = 0
        """, (session['department'], session['department']))
        inbox = cursor.fetchone()['inbox']
        
        return jsonify({"status": "success", "urgent": urgent, "inbox": inbox})
    except Exception as e:
        print(f"Counts error: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch counts"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/messages')
def api_messages():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    msg_type = request.args.get('type', 'all')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if msg_type == 'urgent':
            where_clause = "WHERE (m.recipient_department = %s OR m.sender_department = %s) AND m.is_urgent = 1"
        elif msg_type == 'inbox':
            where_clause = "WHERE (m.recipient_department = %s OR m.sender_department = %s) AND m.is_urgent = 0"
        else:
            where_clause = "WHERE (m.recipient_department = %s OR m.sender_department = %s)"
        
        cursor.execute(f"""
            SELECT 
                m.id, m.sender_name, m.sender_department, m.recipient_department,
                m.subject, LEFT(m.message, 120) as preview, m.is_urgent, m.action_status,
                COALESCE(m.created_at, NOW()) as created_at, m.attachment, m.parent_message_id
            FROM messages m {where_clause}
            ORDER BY m.created_at DESC LIMIT 50
        """, (session['department'], session['department']))
        
        messages = cursor.fetchall()
        return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        print(f"Messages API error: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch messages"}), 500
    finally:
        cursor.close()
        conn.close()

# Send Message Route - FIX for messages2.html url_for error
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        recipient_dept = request.form.get('department')
        content = request.form.get('message')
        sender_id = session['user_id']
        parent_id = request.form.get('parent_message_id')
        parent_id = None if not parent_id or parent_id == '' else int(parent_id)
        is_urgent = 1 if request.form.get('urgent') else 0
        sender_name = session.get('fullname', 'Reception Staff')
        sender_department = session.get('department', 'Reception')
        
        if not recipient_dept or not content:
            return jsonify({"status": "error", "message": "Department and message required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Auto-inherit urgent from parent if reply
        is_urgent_final = is_urgent
        if parent_id:
            cursor.execute("SELECT is_urgent FROM messages WHERE id = %s", (parent_id,))
            parent = cursor.fetchone()
            if parent:
                is_urgent_final = parent[0]
        
        # Insert message
        subject = request.form.get('subject', 'Re: ' + (content[:30] + '...' if len(content) > 30 else content))
        sql = """
            INSERT INTO messages (sender_id, sender_name, sender_department, recipient_department, subject, message, is_urgent, parent_message_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (sender_id, sender_name, sender_department, recipient_dept, subject, content, is_urgent_final, parent_id))
        message_id = cursor.lastrowid
        
        # If this is a reply, update parent message status to 'viewed and replied'
        if parent_id:
            cursor.execute("""
                UPDATE messages 
                SET action_status = CASE 
                    WHEN action_status IN ('new', 'viewed') THEN 'viewed and replied' 
                    WHEN action_status = 'replied' THEN 'viewed and replied'
                    ELSE action_status 
                END 
                WHERE id = %s
            """, (parent_id,))
        
        # Handle file upload
        if 'document' in request.files:
            file = request.files['document']
            if file and file.filename:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"messages_{message_id}_{timestamp}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE messages SET attachment = %s WHERE id = %s", (filename, message_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Message sent successfully'})
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({'status': 'error', 'message': f'Database Error: {str(e)}'}), 500

@app.route('/get_thread/<int:msg_id>')
def get_thread(msg_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find root message first
        cursor.execute("""
            SELECT m.id, m.parent_message_id, m.sender_department, m.sender_name, 
                   m.recipient_department, m.message, m.subject, m.is_urgent, 
                   COALESCE(m.created_at, NOW()) as created_at,
                   m.attachment,
                   p.sender_name as parent_sender_name,
                   LEFT(p.message, 80) as parent_preview
            FROM messages m
            LEFT JOIN messages p ON p.id = m.parent_message_id
            WHERE m.id = %s AND (m.sender_department = %s OR m.recipient_department = %s)
        """, (msg_id, session['department'], session['department']))
        
        root_msg = cursor.fetchone()
        if not root_msg:
            return jsonify({'status': 'success', 'thread': []})
        
        # Collect all thread messages iteratively
        thread = [root_msg]
        current_level = [root_msg['id']]
        
        # Simple iterative fetch of replies (up to 3 levels deep to avoid infinite loops)
        for level in range(3):
            next_level = []
            placeholders = ','.join(['%s'] * len(current_level))
            cursor.execute(f"""
                SELECT m.id, m.sender_department, m.sender_name, m.recipient_department, 
                       m.message, m.subject, m.is_urgent, 
                       COALESCE(m.created_at, NOW()) as created_at,
                       m.attachment, m.parent_message_id,
                       p.sender_name as parent_sender_name,
                       LEFT(p.message, 80) as parent_preview
                FROM messages m
                LEFT JOIN messages p ON p.id = m.parent_message_id
                WHERE m.parent_message_id IN ({placeholders}) 
                AND (m.sender_department = %s OR m.recipient_department = %s)
                ORDER BY m.created_at ASC
            """, current_level + [session['department'], session['department']])
            
            replies = cursor.fetchall()
            for reply in replies:
                thread.append(reply)
                next_level.append(reply['id'])
            
            current_level = next_level
            if not current_level:
                break
        
        # Sort chronologically
        thread.sort(key=lambda x: x['created_at'])
        
        return jsonify({
            'status': 'success', 
            'thread': thread,
            'thread_count': len(thread)
        })
        
    except Exception as e:
        print(f"Thread load error: {e}")  # Log for debugging
        return jsonify({
            'status': 'error', 
            'message': 'Failed to load thread',
            'debug': str(e) if app.debug else None
        }), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/messages')

def messages():
    return redirect(url_for('messages2'))

# [Rest of the routes follow the same pattern - complete Flask app with all routes fixed for syntax errors]


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'user_id' not in session or session['role'] != 'IT Admin':
            return jsonify({"status": "error", "message": "Unauthorized. Only IT Admin can create new accounts."}), 403
            
        data = request.json
        username = data.get('username')
        password = data.get('password')
        fullname = data.get('fullname')
        dept = data.get('department')
        role = data.get('role', 'Staff')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM staff WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Username already taken!"})

            hashed_password = generate_password_hash(password)
            
            sql = "INSERT INTO staff (username, password, fullname, department, role) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (username, hashed_password, fullname, dept, role))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({"status": "success", "message": "Account created successfully!"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return render_template('registration.html')

@app.route('/reports')
def reports():
    if 'user_id' not in session or session['role'] not in ['IT Admin', 'CEO']:
        return redirect('/home')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    now = datetime.now()

    try:
        # Total counts
        cursor.execute("SELECT COUNT(*) as total FROM incoming_mails")
        total_incoming = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM outgoing_mails")  
        total_outgoing = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM call_records")
        total_calls = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM messages")
        total_messages = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE is_urgent = 1")
        urgent_messages = cursor.fetchone()['total']

        total_mails = total_incoming + total_outgoing

        # Today's counts
        today = now.strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as total FROM incoming_mails WHERE DATE(date_received) = %s", (today,))
        incoming_today = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM outgoing_mails WHERE DATE(date_sent) = %s", (today,))
        outgoing_today = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM call_records WHERE DATE(date) = %s", (today,))
        calls_today = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE DATE(created_at) = %s", (today,))
        messages_today = cursor.fetchone()['total']

        # Mail activity last 7 days
        cursor.execute("""
            SELECT 
                DATE(date_received) as date, 
                COUNT(*) as incoming
            FROM incoming_mails 
            WHERE date_received >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(date_received)
            ORDER BY date DESC
        """)
        mail_activity = cursor.fetchall()

        cursor.execute("""
            SELECT 
                DATE(date_sent) as date,
                COUNT(*) as outgoing
            FROM outgoing_mails 
            WHERE date_sent >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(date_sent) 
            ORDER BY date DESC
        """)
        outgoing_activity = cursor.fetchall()

        # Combine mail activity
        mail_activity_full = []
        dates = set([row['date'].strftime('%Y-%m-%d') for row in mail_activity] + 
                   [row['date'].strftime('%Y-%m-%d') for row in outgoing_activity])
        for date_str in sorted(dates, reverse=True):
            inc = next((row['incoming'] for row in mail_activity if row['date'].strftime('%Y-%m-%d') == date_str), 0)
            out = next((row['outgoing'] for row in outgoing_activity if row['date'].strftime('%Y-%m-%d') == date_str), 0)
            mail_activity_full.append({
                'date': date_str,
                'incoming': inc,
                'outgoing': out
            })

        # Calls & Messages activity
        cursor.execute("""
            SELECT 
                DATE(date) as date,
                COUNT(*) as calls
            FROM call_records
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(date)
            ORDER BY date DESC
        """)
        calls_activity = cursor.fetchall()

        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as messages,
                SUM(is_urgent) as urgent
            FROM messages 
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        msg_activity = cursor.fetchall()

        calls_messages_activity = []
        for date_str in sorted(dates, reverse=True):
            call_row = next((row for row in calls_activity if row['date'].strftime('%Y-%m-%d') == date_str), {'calls': 0})
            msg_row = next((row for row in msg_activity if row['date'].strftime('%Y-%m-%d') == date_str), {'messages': 0, 'urgent': 0})
            calls_messages_activity.append({
                'date': date_str,
                'calls': call_row['calls'],
                'messages': msg_row['messages'],
                'urgent': msg_row['urgent']
            })

        # Combine into trend_data for chart (pad to 7 days if needed)
        all_dates = list(dates)
        while len(all_dates) < 7:
            all_dates.append((datetime.now() - timedelta(days=len(all_dates))).strftime('%Y-%m-%d'))
        all_dates = sorted(set(all_dates), reverse=True)[:7]

        trend_data = []
        for date_str in all_dates:
            mail_row = next((row for row in mail_activity_full if row['date'] == date_str), {'incoming':0, 'outgoing':0})
            cms_row = next((row for row in calls_messages_activity if row['date'] == date_str), {'calls':0, 'messages':0, 'urgent':0})
            trend_data.append({
                'date': date_str,
                'incoming': mail_row['incoming'],
                'outgoing': mail_row['outgoing'],
                'calls': cms_row['calls'],
                'urgent': cms_row['urgent'],
                'general': cms_row['messages'] - cms_row['urgent'] if 'messages' in cms_row else 0
            })

        return render_template('reports.html',
                             trend_data=trend_data,
                             now=now,
                             user_role=session['role'],
                             departments=departments)
    except Exception as e:
        return f"Database Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()


# NEW ROUTES TO FIX 404 ERRORS - Step 2
@app.route('/forms')
def forms():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM forms ORDER BY id DESC LIMIT 20")
        all_forms = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('forms.html', all_forms=all_forms, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/incoming-mail')
def incoming_mail():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM incoming_mails ORDER BY id DESC LIMIT 20")
        all_incoming = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('incomingmails.html', all_incoming=all_incoming, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/outgoing-mail')
def outgoing_mail():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM outgoing_mails ORDER BY id DESC LIMIT 20")
        all_outgoing = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('outgoing.html', all_outgoing=all_outgoing, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/call-records')
def call_records():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM call_records ORDER BY id DESC LIMIT 20")
        all_calls = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('calls.html', all_calls=all_calls, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/users')
def users():
    if 'user_id' not in session or session['role'] != 'IT Admin':
        return redirect('/home')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, fullname, department, role FROM staff ORDER BY id ASC")
        all_users = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('users.html', all_users=all_users, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/update-master-key', methods=['GET', 'POST'])
def update_master_key():
    if 'user_id' not in session or session['role'] != 'IT Admin':
        return redirect('/home')
    if request.method == 'POST':
        # TODO: Implement master key storage/update logic
        pass
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # For now, placeholder current_key
        current_key = "masterkey123"
        cursor.close()
        conn.close()
        return render_template('master_key.html', current_key=current_key, user_role=session.get('role', ''), departments=departments)
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Error: {str(e)}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add-form', methods=['POST'])
def add_form():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        name = request.form.get('name')
        form_type = request.form.get('type')
        description = request.form.get('description')
        unlock_key = request.form.get('unlock_key', '')
        
        if not name or not description:
            return jsonify({"status": "error", "message": "Name and description required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert form record
        sql = "INSERT INTO forms (name, type, description, unlock_key) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, form_type, description, unlock_key))
        form_id = cursor.lastrowid
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = f"form_{form_id}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                
                # Update attachment path
                cursor.execute("UPDATE forms SET attachment = %s WHERE id = %s", (filename, form_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Form added successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/add-call', methods=['POST'])
def add_call():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        data = request.json
        caller = data.get('caller')
        duration = data.get('duration')
        purpose = data.get('purpose', '')
        
        if not caller or not duration:
            return jsonify({"status": "error", "message": "Caller and duration required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO call_records (caller, duration, purpose, date) VALUES (%s, %s, %s, NOW())"
        cursor.execute(sql, (caller, duration, purpose))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Call record added successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/add-outgoing-mail', methods=['POST'])
def add_outgoing_mail():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        department = request.form.get('department', 'General')
        content = request.form.get('content', '')
        status = request.form.get('status', 'Draft')
        
        if not recipient or not subject:
            return jsonify({"status": "error", "message": "Recipient and subject required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO outgoing_mails (recipient, subject, department, content, status, date_sent) VALUES (%s, %s, %s, %s, %s, NOW())"
        cursor.execute(sql, (recipient, subject, department, content, status))
        mail_id = cursor.lastrowid
        
        # Handle attachment
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = f"outgoing_{mail_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE outgoing_mails SET attachment = %s WHERE id = %s", (filename, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Outgoing mail added successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/add-incoming-mail', methods=['POST'])
def add_incoming_mail():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        sender = request.form.get('sender')
        subject = request.form.get('subject')
        department = request.form.get('department', 'General')
        content = request.form.get('content', '')
        status = request.form.get('status', 'Unread')
        
        if not sender or not subject:
            return jsonify({"status": "error", "message": "Sender and subject required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO incoming_mails (sender, subject, department, content, status, date_received) VALUES (%s, %s, %s, %s, %s, NOW())"
        cursor.execute(sql, (sender, subject, department, content, status))
        mail_id = cursor.lastrowid
        
        # Handle attachment
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = f"incoming_{mail_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE incoming_mails SET attachment = %s WHERE id = %s", (filename, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Incoming mail added successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get-mail-content/<int:mail_id>')
def get_mail_content(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM incoming_mails WHERE id = %s", (mail_id,))
        mail = cursor.fetchone()
        if not mail:
            return jsonify({"status": "error", "message": "Mail not found"}), 404
        
        # Format date
        if mail['date_received']:
            mail['date_received'] = mail['date_received'].strftime('%b %d, %Y %H:%M')
        
        return jsonify({"status": "success", **mail})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/get-outgoing-mail-content/<int:mail_id>')
def get_outgoing_mail_content(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM outgoing_mails WHERE id = %s", (mail_id,))
        mail = cursor.fetchone()
        if not mail:
            return jsonify({"status": "error", "message": "Mail not found"}), 404
        
        # Format date  
        if mail['date_sent']:
            mail['date_sent'] = mail['date_sent'].strftime('%b %d, %Y %H:%M')
        
        return jsonify({"status": "success", **mail})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/edit-mail/<int:mail_id>', methods=['POST'])
def edit_mail(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        sender = request.form.get('sender')
        subject = request.form.get('subject') 
        department = request.form.get('department', 'General')
        content = request.form.get('content', '')
        status = request.form.get('status', 'Unread')
        
        if not sender or not subject:
            return jsonify({"status": "error", "message": "Sender and subject required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update mail
        sql = """
            UPDATE incoming_mails 
            SET sender=%s, subject=%s, department=%s, content=%s, status=%s 
            WHERE id=%s
        """
        cursor.execute(sql, (sender, subject, department, content, status, mail_id))
        
        # Handle attachment replacement
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                # Delete old attachment if exists
                cursor.execute("SELECT attachment FROM incoming_mails WHERE id = %s", (mail_id,))
                old_attachment = cursor.fetchone()
                if old_attachment and old_attachment[0]:
                    old_path = os.path.join('static', old_attachment[0])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new attachment
                filename = f"incoming_{mail_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE incoming_mails SET attachment = %s WHERE id = %s", (filename, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Mail updated successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/edit-outgoing-mail/<int:mail_id>', methods=['POST'])
def edit_outgoing_mail(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        department = request.form.get('department', 'General')
        content = request.form.get('content', '')
        status = request.form.get('status', 'Draft')
        
        if not recipient or not subject:
            return jsonify({"status": "error", "message": "Recipient and subject required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update mail
        sql = """
            UPDATE outgoing_mails 
            SET recipient=%s, subject=%s, department=%s, content=%s, status=%s 
            WHERE id=%s
        """
        cursor.execute(sql, (recipient, subject, department, content, status, mail_id))
        
        # Handle attachment replacement
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                # Delete old attachment if exists
                cursor.execute("SELECT attachment FROM outgoing_mails WHERE id = %s", (mail_id,))
                old_attachment = cursor.fetchone()
                if old_attachment and old_attachment[0]:
                    old_path = os.path.join('static', old_attachment[0])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new attachment
                filename = f"outgoing_{mail_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE outgoing_mails SET attachment = %s WHERE id = %s", (filename, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Mail updated successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-mail/<int:mail_id>', methods=['POST'])
def delete_mail(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get attachment path for cleanup
        cursor.execute("SELECT attachment FROM incoming_mails WHERE id = %s", (mail_id,))
        attachment = cursor.fetchone()
        
        # Delete from DB
        cursor.execute("DELETE FROM incoming_mails WHERE id = %s", (mail_id,))
        
        # Delete attachment file
        if attachment and attachment[0]:
            file_path = os.path.join('static', attachment[0])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Mail deleted successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-outgoing-mail/<int:mail_id>', methods=['POST'])
def delete_outgoing_mail(mail_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get attachment path for cleanup
        cursor.execute("SELECT attachment FROM outgoing_mails WHERE id = %s", (mail_id,))
        attachment = cursor.fetchone()
        
        # Delete from DB
        cursor.execute("DELETE FROM outgoing_mails WHERE id = %s", (mail_id,))
        
        # Delete attachment file
        if attachment and attachment[0]:
            file_path = os.path.join('static', attachment[0])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Mail deleted successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update-mail-status', methods=['POST'])
def update_mail_status():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        data = request.json
        mail_id = data.get('id')
        status = data.get('status')
        
        if not mail_id or not status:
            return jsonify({"status": "error", "message": "ID and status required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE incoming_mails SET status = %s WHERE id = %s", (status, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Status updated successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-selected-mails', methods=['POST'])
def delete_selected_mails():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        data = request.json
        mail_ids = data.get('mail_ids', [])
        
        if not mail_ids:
            return jsonify({"status": "error", "message": "No mails selected"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        deleted_count = 0
        for mail_id in mail_ids:
            # Get attachment for cleanup
            cursor.execute("SELECT attachment FROM incoming_mails WHERE id = %s", (mail_id,))
            attachment = cursor.fetchone()
            
            # Delete mail
            cursor.execute("DELETE FROM incoming_mails WHERE id = %s", (mail_id,))
            
            # Cleanup attachment
            if attachment and attachment[0]:
                file_path = os.path.join('static', attachment[0])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            deleted_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": f"Deleted {deleted_count} mails successfully!"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        sender = request.form.get('sender')
        subject = request.form.get('subject')
        department = request.form.get('department', 'General')
        content = request.form.get('content', '')
        status = request.form.get('status', 'Unread')
        
        if not sender or not subject:
            return jsonify({"status": "error", "message": "Sender and subject required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO incoming_mails (sender, subject, department, content, status, date_received) VALUES (%s, %s, %s, %s, %s, NOW())"
        cursor.execute(sql, (sender, subject, department, content, status))
        mail_id = cursor.lastrowid
        
        # Handle attachment
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = f"incoming_{mail_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                filepath = os.path.join('static', filename)
                file.save(filepath)
                cursor.execute("UPDATE incoming_mails SET attachment = %s WHERE id = %s", (filename, mail_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": "Incoming mail added successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/delete-forms', methods=['POST'])
def delete_forms():
    if 'user_id' not in session or session['role'] != 'IT Admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        data = request.json
        form_ids = data.get('form_ids', [])
        
        if not form_ids:
            return jsonify({"status": "error", "message": "No forms selected"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for form_id in form_ids:
            cursor.execute("DELETE FROM forms WHERE id = %s", (form_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "message": f"Deleted {len(form_ids)} forms"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)




