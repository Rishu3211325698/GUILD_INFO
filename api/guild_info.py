#!/usr/bin/env python3
"""
Guild Info API – Root file for Vercel.
Root path shows welcome message. /guild_info returns guild data.
"""

import json
import random
import asyncio
import aiohttp
import os
import re
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ---------- Load accounts (same directory) ----------
ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), 'accounts.json')
try:
    with open(ACCOUNTS_FILE, 'r') as f:
        ACCOUNTS = json.load(f)
    if not isinstance(ACCOUNTS, list):
        ACCOUNTS = []
except:
    ACCOUNTS = []

# ---------- AES configuration ----------
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

# ---------- Varint and encryption ----------
def encode_varint(n):
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def encrypt_data(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def build_clan_request(clan_id):
    tag = (1 << 3) | 0
    tag_varint = encode_varint(tag)
    value_varint = encode_varint(clan_id)
    plain = tag_varint + value_varint
    return encrypt_data(plain)

# ---------- Protobuf parser ----------
def read_varint(data, i):
    shift = 0
    result = 0
    while True:
        b = data[i]
        result |= (b & 0x7F) << shift
        i += 1
        if not (b & 0x80):
            break
        shift += 7
    return result, i

def parse_proto(data, i=0, end=None):
    if end is None:
        end = len(data)
    res = {}
    while i < end:
        key, i = read_varint(data, i)
        field = key >> 3
        wire = key & 7
        if wire == 0:
            val, i = read_varint(data, i)
        elif wire == 2:
            size, i = read_varint(data, i)
            raw = data[i:i+size]
            try:
                val = raw.decode("utf-8")
            except:
                val = parse_proto(raw, 0, len(raw))
            i += size
        else:
            break
        if field in res:
            if isinstance(res[field], list):
                res[field].append(val)
            else:
                res[field] = [res[field], val]
        else:
            res[field] = val
    return res

def format_timestamp(ts):
    try:
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return None

def safe_get(data, key, default=None):
    val = data.get(key, default)
    if isinstance(val, list):
        return val[0] if len(val) == 1 else val
    return val

def decode_hex(value):
    if not isinstance(value, str):
        return value
    try:
        raw = bytes.fromhex(value)
        try:
            return json.loads(raw.decode())
        except:
            return raw.decode("utf-8", errors="ignore")
    except:
        return value

def clean_name(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def smart_decode(value):
    value = decode_hex(value)
    if isinstance(value, str):
        return clean_name(value)
    return value

def map_guild(data):
    # Use the correct field numbers from official dump
    guild_id = safe_get(data, 1)
    
    # region_flag (field 2) – hex encoded string
    region_flag_raw = safe_get(data, 2, '')
    region_flag = smart_decode(region_flag_raw)
    
    # guild_tag – field 5 (small int)
    guild_tag = str(safe_get(data, 5, ''))
    
    # level – field 6
    level = safe_get(data, 6, 0)
    
    # rank_points – field 7
    rank_points = safe_get(data, 7, 0)
    
    # co_leader_uid – field 12 (hex string)
    co_leader_raw = safe_get(data, 12, '')
    co_leader_uid = smart_decode(co_leader_raw)
    
    # description – field 13 (hex or string)
    desc_raw = safe_get(data, 13, '')
    description = smart_decode(desc_raw)
    
    # badge_id – field 14 (JSON hex)
    badge_raw = safe_get(data, 14, {})
    badge_id = smart_decode(badge_raw)
    
    # guild_score – field 15 (hex array)
    score_raw = safe_get(data, 15, [])
    guild_score = smart_decode(score_raw)
    
    # last_active – field 44
    last_active_ts = safe_get(data, 44)
    
    # Created timestamp – unknown, maybe field 24? Not in your dump
    created_ts = safe_get(data, 24, None)
    
    # Members – not clearly present in your dump. 
    # field 20 is 890800 – too large for members. Maybe a different stat.
    # We'll omit or set defaults.
    
    # Guild name – not found in your dump. Could be field 3 or 4 if they are strings.
    # For now, leave empty or try to decode field 3 if it's bytes.
    guild_name = ''
    raw_name = safe_get(data, 3, None)
    if isinstance(raw_name, bytes):
        guild_name = smart_decode(raw_name)
    elif isinstance(raw_name, str):
        guild_name = raw_name
    else:
        guild_name = str(raw_name) if raw_name else ''
    
    return {
        "guild_info": {
            "guild_id": guild_id,
            "guild_name": guild_name,
            "guild_tag": guild_tag,
            "description": description,
            "level": level,
            "rank_points": rank_points,
            "guild_score": guild_score if isinstance(guild_score, str) else str(guild_score),
            "badge_id": badge_id if isinstance(badge_id, str) else json.dumps(badge_id),
            "co_leader_uid": co_leader_uid,
            "region_flag": region_flag,
            "members": {
                "current": safe_get(data, 21, 0),   # unknown if correct
                "maximum": safe_get(data, 20, 0) if safe_get(data, 20, 0) < 1000 else 50
            },
            "created": {
                "timestamp": created_ts,
                "date": format_timestamp(created_ts)
            },
            "last_active": {
                "timestamp": last_active_ts,
                "date": format_timestamp(last_active_ts)
            }
        },
        "statistics": {
            "total_score": safe_get(data, 54, 0),
            "wins": safe_get(data, 55, 0),
            "ranking_points": safe_get(data, 58, 0)
        }
    }

# ---------- Guest login (original URLs) ----------
import my_pb2
import output_pb2

async def get_jwt_from_guest(session, uid, password):
    oauth_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    oauth_payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    oauth_headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    access_token = None
    open_id = None
    for _ in range(3):
        try:
            async with session.post(oauth_url, data=oauth_payload, headers=oauth_headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    access_token = data.get('access_token')
                    open_id = data.get('open_id')
                    break
        except:
            await asyncio.sleep(0.5)
    if not access_token or not open_id:
        return None

    login_url = "https://loginbp.ggblueshark.com/MajorLogin"
    login_headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Content-Type": "application/octet-stream",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53"
    }

    platforms = [8, 3, 4, 6]
    for platform in platforms:
        try:
            game_data = my_pb2.GameData()
            game_data.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.111.1"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = 1280
            game_data.screen_height = 960
            game_data.dpi = "240"
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = 5951
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game_data.ip_address = "172.190.111.97"
            game_data.language = "en"
            game_data.open_id = open_id
            game_data.access_token = access_token
            game_data.platform_type = platform
            game_data.field_99 = str(platform)
            game_data.field_100 = str(platform)

            encrypted_body = encrypt_data(game_data.SerializeToString())
            async with session.post(login_url, data=encrypted_body, headers=login_headers, ssl=False, timeout=6) as r:
                if r.status == 200:
                    resp_data = await r.read()
                    try:
                        response_proto = output_pb2.Garena_420()
                        response_proto.ParseFromString(resp_data)
                        if response_proto.token:
                            return response_proto.token
                    except:
                        text = resp_data.decode('utf-8', errors='ignore')
                        start = text.find("eyJ")
                        if start != -1:
                            end = start
                            while end < len(text) and text[end] not in ['"', ' ', '\n', '\r', '\t', '\x00']:
                                end += 1
                            jwt = text[start:end]
                            if jwt.count('.') >= 2:
                                return jwt
        except:
            pass
        await asyncio.sleep(0.1)
    return None

# ---------- Fetch clan info ----------
async def fetch_clan_info(session, jwt, clan_id):
    url = "https://client.ind.freefiremobile.com/GetClanInfoByClanID"
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Authorization": f"Bearer {jwt}",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53",
        "Content-Type": "application/octet-stream"
    }
    encrypted_req = build_clan_request(clan_id)
    async with session.post(url, headers=headers, data=encrypted_req) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            return None, resp.status, error_text
        raw = await resp.read()
        parsed = parse_proto(raw)
        return map_guild(parsed), resp.status, None

# ---------- Core handler ----------
async def handle_clan_request(clan_id, retry_auth=True):
    if not clan_id:
        return 400, {'error': 'Missing clan_id'}
    try:
        clan_id = int(clan_id)
    except:
        return 400, {'error': 'clan_id must be integer'}

    if not ACCOUNTS:
        return 500, {'error': 'No guest accounts available'}

    account = random.choice(ACCOUNTS)
    uid = str(account.get('uid'))
    password = account.get('password')
    if not uid or not password:
        return 500, {'error': 'Invalid account in JSON'}

    async with aiohttp.ClientSession() as session:
        jwt = await get_jwt_from_guest(session, uid, password)
        if not jwt:
            return 500, {'error': 'Failed to obtain JWT'}

        guild_info, status, error_text = await fetch_clan_info(session, jwt, clan_id)

        if status == 403 and retry_auth:
            new_jwt = await get_jwt_from_guest(session, uid, password)
            if new_jwt:
                guild_info, status, error_text = await fetch_clan_info(session, new_jwt, clan_id)
            else:
                for acc in ACCOUNTS:
                    if acc != account:
                        new_uid = str(acc.get('uid'))
                        new_pwd = acc.get('password')
                        new_jwt = await get_jwt_from_guest(session, new_uid, new_pwd)
                        if new_jwt:
                            guild_info, status, error_text = await fetch_clan_info(session, new_jwt, clan_id)
                            break

        if status != 200:
            return status, {'error': f'Clan info request failed (HTTP {status}): {error_text}'}

        return 200, guild_info

# ---------- Vercel handler with routing ----------
async def async_handler(request):
    path = getattr(request, 'path', request.get('path', '/'))

    # Root path -> welcome message
    if path == '/' or path == '':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Welcome to Guild Info API',
                'endpoints': {
                    'GET /guild_info?clan_id=YOUR_ID': 'Get guild information (JSON)',
                    'GET /guild_info?clan_id=YOUR_ID&format=text': 'Get guild information (text)',
                    'POST /guild_info': 'Send JSON {"clan_id": YOUR_ID}'
                },
                'status': 'active'
            }, indent=2)
        }

    # /guild_info endpoint
    if path.startswith('/guild_info'):
        if request.method == 'POST':
            try:
                body = await request.json()
                clan_id = body.get('clan_id')
            except:
                clan_id = None
        else:
            clan_id = request.query_params.get('clan_id')

        fmt = request.query_params.get('format') if hasattr(request, 'query_params') else None
        status, result = await handle_clan_request(clan_id)

        if fmt == 'text' and status == 200:
            return {
                'statusCode': status,
                'headers': {'Content-Type': 'text/plain'},
                'body': json.dumps(result, indent=2)
            }
        return {
            'statusCode': status,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, indent=2, default=str)
        }

    # 404 for any other path
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Not found'})
    }

def handler(request, context):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(async_handler(request))
    loop.close()
    return response