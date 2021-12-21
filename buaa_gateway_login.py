#!/usr/bin/env python3
'''
@Description: login gw.buaa.edu.cn in Command line mode
    based on https://github.com/luoboganer 2019-09-01
    based on https://coding.net/u/huxiaofan1223/p/jxnu_srun/git

'''


import requests
import socket
import time
import math
import hmac
import hashlib
import getpass
import json
import urllib3

urllib3.disable_warnings()


def get_jsonp(url, params):
    """
    Send jsonp request and decode response

    About jsonp: https://stackoverflow.com/questions/2067472/what-is-jsonp-and-why-was-it-created
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76.0.3809.100 Safari/537.36",
    }
    callback_name = "jQuery112406951885120277062_" + str(int(time.time() * 1000))
    params['callback'] = callback_name
    resp = requests.get(url, params=params, headers=headers, verify=False)
    return json.loads(resp.text[len(callback_name) + 1:-1])


def get_IP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]


def get_ip_token(username):
    get_challenge_url = "https://gw.buaa.edu.cn/cgi-bin/get_challenge"
    get_challenge_params = {
        "username": username,
        "ip": '0.0.0.0',
        "_": int(time.time() * 1000)
    }
    res = get_jsonp(get_challenge_url, get_challenge_params)
    return res["client_ip"], res["challenge"],


def get_info(username, password, ip):
    params = {
        'username': username,
        'password': password,
        'ip': ip,
        'acid': '1',
        "enc_ver": 'srun_bx1'
    }
    info = json.dumps(params)
    return info


def force(msg):
    ret = []
    for w in msg:
        ret.append(ord(w))
    return bytes(ret)


def ordat(msg, idx):
    if len(msg) > idx:
        return ord(msg[idx])
    return 0


def sencode(msg, key):
    l = len(msg)
    pwd = []
    for i in range(0, l, 4):
        pwd.append(
            ordat(msg, i) | ordat(msg, i + 1) << 8 | ordat(msg, i + 2) << 16
            | ordat(msg, i + 3) << 24)
    if key:
        pwd.append(l)
    return pwd


def lencode(msg, key):
    l = len(msg)
    ll = (l - 1) << 2
    if key:
        m = msg[l - 1]
        if m < ll - 3 or m > ll:
            return
        ll = m
    for i in range(0, l):
        msg[i] = chr(msg[i] & 0xff) + chr(msg[i] >> 8 & 0xff) + chr(
            msg[i] >> 16 & 0xff) + chr(msg[i] >> 24 & 0xff)
    if key:
        return "".join(msg)[0:ll]
    return "".join(msg)


def get_xencode(msg, key):
    if msg == "":
        return ""
    pwd = sencode(msg, True)
    pwdk = sencode(key, False)
    if len(pwdk) < 4:
        pwdk = pwdk + [0] * (4 - len(pwdk))
    n = len(pwd) - 1
    z = pwd[n]
    y = pwd[0]
    c = 0x86014019 | 0x183639A0
    m = 0
    e = 0
    p = 0
    q = math.floor(6 + 52 / (n + 1))
    d = 0
    while 0 < q:
        d = d + c & (0x8CE0D9BF | 0x731F2640)
        e = d >> 2 & 3
        p = 0
        while p < n:
            y = pwd[p + 1]
            m = z >> 5 ^ y << 2
            m = m + ((y >> 3 ^ z << 4) ^ (d ^ y))
            m = m + (pwdk[(p & 3) ^ e] ^ z)
            pwd[p] = pwd[p] + m & (0xEFB8D130 | 0x10472ECF)
            z = pwd[p]
            p = p + 1
        y = pwd[0]
        m = z >> 5 ^ y << 2
        m = m + ((y >> 3 ^ z << 4) ^ (d ^ y))
        m = m + (pwdk[(p & 3) ^ e] ^ z)
        pwd[n] = pwd[n] + m & (0xBB390742 | 0x44C6F8BD)
        z = pwd[n]
        q = q - 1
    return lencode(pwd, False)


_PADCHAR = "="
_ALPHA = "LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA"


def _getbyte(s, i):
    x = ord(s[i])
    if (x > 255):
        print("INVALID_CHARACTER_ERR: DOM Exception 5")
        exit(0)
    return x


def get_base64(s):
    i = 0
    b10 = 0
    x = []
    imax = len(s) - len(s) % 3
    if len(s) == 0:
        return s
    for i in range(0, imax, 3):
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8) | _getbyte(s, i + 2)
        x.append(_ALPHA[(b10 >> 18)])
        x.append(_ALPHA[((b10 >> 12) & 63)])
        x.append(_ALPHA[((b10 >> 6) & 63)])
        x.append(_ALPHA[(b10 & 63)])
    i = imax
    if len(s) - imax == 1:
        b10 = _getbyte(s, i) << 16
        x.append(_ALPHA[(b10 >> 18)] +
                 _ALPHA[((b10 >> 12) & 63)] + _PADCHAR + _PADCHAR)
    elif len(s) - imax == 2:
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8)
        x.append(_ALPHA[(b10 >> 18)] + _ALPHA[((b10 >> 12) & 63)] + _ALPHA[((b10 >> 6) & 63)] + _PADCHAR)
    return "".join(x)


def get_md5(password, token):
    return hmac.new(token.encode(), password.encode(), hashlib.md5).hexdigest()


def get_sha1(value):
    return hashlib.sha1(value.encode()).hexdigest()


def login(username, password):
    srun_portal_url = "https://gw.buaa.edu.cn/cgi-bin/srun_portal"
    ip, token = get_ip_token(username)
    info = get_info(username, password, ip)

    # import IPython
    # IPython.embed()
    data = {
        "action": "login",
        "username": username,
        "password": "{MD5}" + get_md5(password, token),
        "ac_id": 1,
        "ip": ip,
        "info": "{SRBX1}" + get_base64(get_xencode(info, token)),
        "n": "200",
        "type": "1",
        "os": "Linux.Hercules",
        "name": "Linux",
        "double_stack": '',
        "_": int(time.time() * 1000)
    }
    chkstr = token + username
    chkstr += token + get_md5(password, token)
    chkstr += token + '1'
    chkstr += token + ip
    chkstr += token + '200'
    chkstr += token + '1'
    chkstr += token + "{SRBX1}" + get_base64(get_xencode(info, token))
    data['chksum'] = get_sha1(chkstr)

    return get_jsonp(srun_portal_url, data)


if __name__ == "__main__":
    print('gw.buaa.edu.cn portal login...')
    username = input('username: ')
    password = getpass.getpass('password: ')

    login_info = login(username, password)
    print(json.dumps(login_info, indent=4, ensure_ascii=False))


