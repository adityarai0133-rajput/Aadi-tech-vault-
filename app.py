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

# Auto-created Dedicated System Vault Directory
USER_DOCS = os.path.join(os.path.expanduser('~'), 'Documents')
VAULT_DIR = os.path.join(USER_DOCS, "Aadi_Vault")
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
    
    # List all encrypted .aadi files from system vault
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
            
    return render_template('index.html', mode="login", error="INVALID MASTER KEY!")

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'auth' not in session: 
        return redirect('/')
        
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename:
        raw_name = os.path.basename(uploaded_file.filename)
        clean_name = raw_name.replace(".aadi", "")
        
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return redirect('/')
            
        key = get_aes_key()
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_bytes = cipher.encrypt(pad(file_bytes, AES.block_size))
        
        # Save directly in System Vault folder
        encrypted_filename = clean_name + ".aadi"
        target_path = os.path.join(VAULT_DIR, encrypted_filename)
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
            return "<h3 style='color:red;'>File Error</h3>", 400
            
        iv = file_data[:16]
        encrypted_payload = file_data[16:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_payload), AES.block_size)
        
        original_filename = safe_filename.replace(".aadi", "")
        
        # Save the restored decrypted original file directly in the Vault folder
        restored_path = os.path.join(VAULT_DIR, original_filename)
        with open(restored_path, "wb") as f:
            f.write(decrypted_bytes)
        
        # Also send download trigger to user
        return send_file(
            io.BytesIO(decrypted_bytes),
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/octet-stream'
        )
    except Exception:
        return "<h3 style='color:red;'>Decryption Error! Key Mismatch.</h3>", 400

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
