# 🛡️ Aadi-Tech Vault (ATV)
**Military-Grade AES-256 Offline File Encryption | Resource-Zero Optimized**

![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![Security](https://img.shields.io/badge/Security-SHA--256%20%26%20AES--256-red.svg)

**Aadi-Tech Vault** ek high-security encryption tool hai jo aapke files, images, aur `.exe` files ko 100% offline environment mein protect karta hai. Yeh tool **Localhost** par chalta hai, yani aapka data kabhi internet par nahi jata.

---

## 🛠️ User Manual: Kaise Chalu Karein?

Isse use karna bahut simple hai, bas ye steps follow karein:

### 1. Initial Setup (First Time Only)
* Jab aap pehli baar tool kholenge, aapko ek **Master Key (Password)** create karni hogi.
* Ye password **SHA-256** hashing ke saath aapke PC mein save ho jayega.
* Verification ke liye aapko wahi password dubara dalna hoga, jisse aapki unique identity file generate ho sake.

### 2. Encryption (File Lock Kaise Karein?)
* **Choose File:** Apne browser dashboard par 'Choose File' par click karein.
* **Select:** Kisi bhi file, image ya executable (.exe) ko select karein.
* **Encrypt as Lock:** 'Encrypt' button dabayein. 
* **Result:** Aapki file turant `.aadi` format mein badal jayegi (e.g., `photo.jpg.aadi`). Isse kholne par sirf kachra (garbage data) dikhega.

### 3. Decryption (File Unlock Kaise Karein?)
* Aapke dashboard par encrypt kari hui file ke aage **'Decrypt'** ka option dikhega.
* Us par click karte hi file wapas apne purane format mein aa jayegi.

### 4. Storage
* System apne aap ek folder banayega: `Aadi Tech Vault`. 
* Aapki saari locked (Encrypted) aur unlocked (Decrypted) files isi folder mein milengi.

---

## 🧠 Technical Details & Security
* **Algorithm:** AES-256 bit encryption (Duniya ka sabse tagda standard).
* **Master Key:** SHA-256 hash logic se secured.
* **Zero Cloud:** Koi server nahi, koi login nahi. Sirf aapka PC aur aapka code.
* **OS Integrity:** Windows/Linux ki security policies ko dhyan mein rakh kar banaya gaya hai.

---

## ⚠️ Important Disclaimer (Must Read)

1. **Master Key Responsibility:** Agar aap apni Master Key bhool gaye, toh aapka data **hamesha ke liye lock** ho jayega. Humne koi back-door nahi banaya hai (Privacy ke liye), isliye recovery namumkin hai.
2. **Backup:** Kisi bhi file ko lock karne se pehle uska original backup rakhna user ki apni zimmedari hai.
3. **Sharing:** Agar aap apna password kisi ko batate hain, toh usse hone wale kisi bhi nuksan ke liye **Aadi-Tech** ya **Aditya Rai** zimmedar nahi honge.
4. **No Warranty:** Apache License 2.0 ke tahat, ye software "AS IS" diya gaya hai. Iska upyog aap apni samajhdaari se karein.

---

## 👤 About the Author
**Aditya Rai** *Founder, Aadi-Tech* Building lightweight and secure tools for the future.

[Product Hunt](https://www.producthunt.com/@adityarai) | [Dev.to](https://dev.to/adityarai)
