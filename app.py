import os
import hashlib
import sys
import threading
import time
import io
from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import webview

def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception: 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))
app.secret_key = os.urandom(32)

# Persistent Documents Storage (Fixes Program Files Permission Error)
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
            
    return render_template('index.html', mode="login", error="INVALID MASTER KEY!")

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
            return "<h3 style='color:#ff4444;text-align:center;'>Corrupted File!</h3>", 400
            
        iv = file_data[:16]
        encrypted_payload = file_data[16:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        decrypted_original = unpad(cipher.decrypt(encrypted_payload), AES.block_size)
        
        original_filename = safe_filename.replace(".aadi", "")
        
        return send_file(
            io.BytesIO(decrypted_original),
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/octet-stream'
        )
    except Exception:
        return "<h3 style='color:#ff4444;text-align:center;'>Decryption Failed!</h3>", 400

@app.route('/reset-password', methods=['POST'])
def reset_password():
    if 'auth' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    old_p = data.get("old_password", "").strip()
    new_p = data.get("new_password", "").strip()
    cnf_p = data.get("confirm_password", "").strip()
    
    if not old_p or not new_p or not cnf_p:
        return jsonify({"success": False, "message": "All fields required!"}), 400
        
    if new_p != cnf_p:
        return jsonify({"success": False, "message": "Passwords do not match!"}), 400
        
    if len(new_p) < 4:
        return jsonify({"success": False, "message": "Min 4 characters required!"}), 400

    if not os.path.exists(PWD_FILE):
        return jsonify({"success": False, "message": "Password storage missing!"}), 500

    with open(PWD_FILE, "r", encoding='utf-8') as f:
        current_hash = f.read().strip()
        
    if hashlib.sha256(old_p.encode('utf-8')).hexdigest() != current_hash:
        return jsonify({"success": False, "message": "Wrong old password!"}), 400

    with open(PWD_FILE, "w", encoding='utf-8') as f:
        f.write(hashlib.sha256(new_p.encode('utf-8')).hexdigest())
        
    return jsonify({"success": True, "message": "Password changed successfully!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Auto-inject floating Settings ⚙️ button
@app.after_request
def inject_settings(response):
    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        if 'auth' in session:
            settings_ui = """
            <div id="cfg-gear" style="position:fixed;top:18px;right:18px;z-index:99999;cursor:pointer;background:#0d1117;border:1px solid #00f3ff;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 12px rgba(0,243,255,0.4);font-size:20px;">⚙️</div>
            <div id="cfg-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:100000;justify-content:center;align-items:center;">
                <div style="background:#0d1117;border:2px solid #00f3ff;border-radius:12px;padding:24px;width:310px;text-align:center;box-shadow:0 0 25px rgba(0,243,255,0.3);font-family:sans-serif;color:#fff;">
                    <h3 style="margin:0 0 16px 0;color:#00f3ff;letter-spacing:1px;">RESET MASTER KEY</h3>
                    <input type="password" id="old_p" placeholder="Old Password" style="width:90%;padding:9px;margin-bottom:10px;background:#161b22;border:1px solid #30363d;color:#fff;border-radius:6px;outline:none;">
                    <input type="password" id="new_p" placeholder="New Password" style="width:90%;padding:9px;margin-bottom:10px;background:#161b22;border:1px solid #30363d;color:#fff;border-radius:6px;outline:none;">
                    <input type="password" id="cnf_p" placeholder="Confirm New Password" style="width:90%;padding:9px;margin-bottom:12px;background:#161b22;border:1px solid #30363d;color:#fff;border-radius:6px;outline:none;">
                    <div id="rst-msg" style="font-size:12px;min-height:18px;margin-bottom:10px;"></div>
                    <button onclick="doReset()" style="background:#00f3ff;color:#000;border:none;padding:9px 18px;font-weight:bold;border-radius:6px;cursor:pointer;margin-right:8px;">Save</button>
                    <button onclick="document.getElementById('cfg-modal').style.display='none'" style="background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:9px 14px;border-radius:6px;cursor:pointer;">Cancel</button>
                </div>
            </div>
            <script>
                document.getElementById('cfg-gear').onclick = () => { document.getElementById('cfg-modal').style.display='flex'; document.getElementById('rst-msg').innerText=''; };
                async function doReset(){
                    const old_password = document.getElementById('old_p').value;
                    const new_password = document.getElementById('new_p').value;
                    const confirm_password = document.getElementById('cnf_p').value;
                    const msg = document.getElementById('rst-msg');
                    msg.style.color = '#e3b341'; msg.innerText = 'Updating...';
                    try {
                        const r = await fetch('/reset-password', {
                            method:'POST',
                            headers:{'Content-Type':'application/json'},
                            body: JSON.stringify({old_password, new_password, confirm_password})
                        });
                        const res = await r.json();
                        if(r.ok){
                            msg.style.color='#3fb950'; msg.innerText=res.message;
                            setTimeout(()=>{ document.getElementById('cfg-modal').style.display='none'; }, 1200);
                        } else {
                            msg.style.color='#f85149'; msg.innerText=res.message;
                        }
                    } catch(e){
                        msg.style.color='#f85149'; msg.innerText='Error updating password';
                    }
                }
            </script>
            """
            html = response.get_data(as_text=True)
            if "</body>" in html:
                html = html.replace("</body>", f"{settings_ui}</body>")
                response.set_data(html)
    return response

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in dedicated background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    time.sleep(0.8)
    
    # Launch Clean Native Desktop Window
    webview.create_window('Aadi Vault', 'http://127.0.0.1:5000', width=1050, height=720, resizable=True)
    webview.start()
