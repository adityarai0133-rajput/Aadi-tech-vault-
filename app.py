import os
import hashlib
import sys
import webbrowser
import threading
import time
import io
from flask import Flask, render_template, request, redirect, session, send_file
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception: 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))
app.secret_key = os.urandom(32)

# Persistent Documents Storage Path
DOCUMENTS_DIR = os.path.join(os.path.expanduser('~'), 'Documents')
VAULT_DIR = os.path.join(DOCUMENTS_DIR, "Aadi_Vault_Storage")
os.makedirs(VAULT_DIR, exist_ok=True)

PWD_FILE = os.path.join(VAULT_DIR, "shadow.dat")
KEY_FILE = os.path.join(VAULT_DIR, "master.key")

def get_aes_key():
    if not os.path.exists(KEY_FILE):
        key = os.urandom(32)
        with open(KEY_FILE, "wb") as f: 
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f: 
        return f.read()

@app.route('/')
def index():
    if not os.path.exists(PWD_FILE): 
        return render_template('index.html', mode="setup")
    if 'auth' not in session: 
        return render_template('index.html', mode="login")
    
    files = [f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')]
    return render_template('index.html', mode="dashboard", files=files)

@app.route('/gatekeeper', methods=['POST'])
def gatekeeper():
    user_input = request.form.get('master_key_field', '').strip()
    if not user_input: 
        return redirect('/')
    
    hashed = hashlib.sha256(user_input.encode('utf-8')).hexdigest()
    
    if not os.path.exists(PWD_FILE):
        with open(PWD_FILE, "w", encoding='utf-8') as f: 
            f.write(hashed)
        session['auth'] = True
        session.permanent = True
        return redirect('/')
    
    with open(PWD_FILE, "r", encoding='utf-8') as f:
        if f.read().strip() == hashed:
            session['auth'] = True
            session.permanent = True
            return redirect('/')
            
    return render_template('index.html', mode="login", error="INVALID ACCESS KEY!")

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'auth' not in session: 
        return redirect('/')
        
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename:
        filename = os.path.basename(uploaded_file.filename)
        clean_name = filename.replace(".aadi", "")
        
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return redirect('/')
            
        key = get_aes_key()
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_bytes = cipher.encrypt(pad(file_bytes, AES.block_size))
        
        target_path = os.path.join(VAULT_DIR, clean_name + ".aadi")
        with open(target_path, "wb") as f:
            f.write(cipher.iv + encrypted_bytes)
            
    return redirect('/')

@app.route('/decrypt/<filename>')
def decrypt_file(filename):
    if 'auth' not in session: 
        return redirect('/')
        
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(VAULT_DIR, safe_filename)
    
    if not os.path.exists(file_path): 
        return redirect('/')

    key = get_aes_key()
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        if len(file_data) <= 16:
            return render_template('index.html', mode="dashboard", files=[f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')], error="CORRUPTED NODE FILE!")
            
        iv = file_data[:16]
        encrypted_payload = file_data[16:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        decrypted_original = unpad(cipher.decrypt(encrypted_payload), AES.block_size)
        
        original_filename = safe_filename.replace(".aadi", "")
        
        # Save restored file to system vault folder
        restored_path = os.path.join(VAULT_DIR, original_filename)
        with open(restored_path, "wb") as f:
            f.write(decrypted_original)
        
        # Trigger direct download
        return send_file(
            io.BytesIO(decrypted_original),
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/octet-stream'
        )
    except Exception:
        return render_template('index.html', mode="dashboard", files=[f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')], error="DECRYPTION FAILED: KEY MISMATCH!")

@app.route('/reset-password', methods=['POST'])
def reset_password():
    if 'auth' not in session:
        return redirect('/')
        
    old_p = request.form.get("old_password", "").strip()
    new_p = request.form.get("new_password", "").strip()
    cnf_p = request.form.get("confirm_password", "").strip()
    files = [f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')]
    
    if not old_p or not new_p or not cnf_p:
        return render_template('index.html', mode="dashboard", files=files, error="ALL FIELDS REQUIRED!")
        
    if new_p != cnf_p:
        return render_template('index.html', mode="dashboard", files=files, error="NEW PASSWORDS DO NOT MATCH!")
        
    if len(new_p) < 4:
        return render_template('index.html', mode="dashboard", files=files, error="KEY MUST BE AT LEAST 4 CHARACTERS!")

    if not os.path.exists(PWD_FILE):
        return render_template('index.html', mode="dashboard", files=files, error="SHADOW STORAGE MISSING!")

    with open(PWD_FILE, "r", encoding='utf-8') as f:
        current_hash = f.read().strip()
        
    if hashlib.sha256(old_p.encode('utf-8')).hexdigest() != current_hash:
        return render_template('index.html', mode="dashboard", files=files, error="INCORRECT CURRENT ACCESS KEY!")

    with open(PWD_FILE, "w", encoding='utf-8') as f:
        f.write(hashlib.sha256(new_p.encode('utf-8')).hexdigest())
        
    return render_template('index.html', mode="dashboard", files=files, msg="MASTER ACCESS KEY ROTATED SUCCESSFULLY!")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
