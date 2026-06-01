from flask import Flask, render_template, request, redirect, session, send_from_directory
import os, hashlib, sys, webbrowser
from threading import Timer
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))
app.secret_key = os.urandom(32)

VAULT_DIR = "Aadi_Vault"
PWD_FILE = os.path.join(VAULT_DIR, "shadow.txt")
KEY_FILE = os.path.join(VAULT_DIR, "master.key")

if not os.path.exists(VAULT_DIR): os.makedirs(VAULT_DIR)

def get_aes_key():
    if not os.path.exists(KEY_FILE):
        key = os.urandom(32)
        with open(KEY_FILE, "wb") as f: f.write(key)
        return key
    with open(KEY_FILE, "rb") as f: return f.read()

def clean_vault():
    """Temporary UNLOCKED files ko delete karne ke liye taaki speed bani rahe"""
    if os.path.exists(VAULT_DIR):
        for f in os.listdir(VAULT_DIR):
            if f.startswith("UNLOCKED_"):
                try: os.remove(os.path.join(VAULT_DIR, f))
                except: pass

@app.route('/')
def index():
    if not os.path.exists(PWD_FILE): return render_template('index.html', mode="setup")
    if 'auth' not in session: return render_template('index.html', mode="login")
    
    clean_vault() # Dashboard aate hi purana kachra saaf
    files = [f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')]
    return render_template('index.html', mode="dashboard", files=files)

@app.route('/gatekeeper', methods=['POST'])
def gatekeeper():
    user_input = request.form.get('master_key_field')
    if not user_input: return redirect('/')
    
    hashed = hashlib.sha256(user_input.encode()).hexdigest()
    
    if not os.path.exists(PWD_FILE):
        with open(PWD_FILE, "w") as f: f.write(hashed)
        return redirect('/')
    
    with open(PWD_FILE, "r") as f:
        if f.read().strip() == hashed:
            session['auth'] = True
            session.permanent = True # Session ko secure rakhne ke liye
            return redirect('/')
            
    return render_template('index.html', mode="login", error="INVALID KEY!")

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'auth' not in session: return redirect('/')
    file = request.files.get('file')
    if file:
        # User Protection: Filename se double extension hatana
        name = file.filename.replace("UNLOCKED_", "").replace(".aadi", "")
        key = get_aes_key()
        cipher = AES.new(key, AES.MODE_CBC)
        data = file.read()
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        
        with open(os.path.join(VAULT_DIR, name + ".aadi"), "wb") as f:
            f.write(cipher.iv + ct_bytes)
    return redirect('/')

@app.route('/decrypt/<filename>')
def decrypt_file(filename):
    if 'auth' not in session: return redirect('/')
    file_path = os.path.join(VAULT_DIR, filename)
    if not os.path.exists(file_path): return redirect('/')

    key = get_aes_key()
    with open(file_path, "rb") as f:
        iv, data = f.read(16), f.read()
    
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        pt = unpad(cipher.decrypt(data), AES.block_size)
        
        temp_name = "UNLOCKED_" + filename.replace(".aadi", "")
        temp_path = os.path.join(VAULT_DIR, temp_name)
        
        with open(temp_path, "wb") as f: f.write(pt)
        return send_from_directory(VAULT_DIR, temp_name, as_attachment=True)
    except:
        return "Error in Decryption!"

@app.route('/logout')
def logout():
    clean_vault()
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000/')).start()
    # speed boost aur stability ke liye threaded=True
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
