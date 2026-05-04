#!/usr/bin/env python3
"""
Guild Info API – Flask + Vercel compatible.
Original API URLs kept. Added 403 retry logic.
"""

import json
import random
import asyncio
import aiohttp
import os
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import my_pb2
import output_pb2

# ---------- Load accounts ----------
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
    tag = (1 << 3) | 0          # field 1, varint
    tag_varint = encode_varint(tag)
    value_varint = encode_varint(clan_id)
    plain = tag_varint + value_varint
    return encrypt_data(plain)

# ---------- Protobuf parser ----------
from datetime import datetime
import json
import re


# ------------------ CORE PROTO PARSER ------------------ #

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
            raw = data[i:i + size]

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


# ------------------ UTILITIES ------------------ #

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


# ------------------ HEX + NAME DECODER ------------------ #

def decode_hex(value):
    """Decode hex → string / json / list"""
    if not isinstance(value, str):
        return value

    try:
        raw = bytes.fromhex(value)

        # Try JSON
        try:
            return json.loads(raw.decode())
        except:
            pass

        # Try UTF-8 string
        return raw.decode("utf-8", errors="ignore")

    except:
        return value


def clean_name(text):
    """Remove FF symbols and keep clean names like RISHU ROLEX"""
    if not isinstance(text, str):
        return text

    # remove decorative unicode / symbols
    text = re.sub(r'[^\w\s]', '', text)

    return text.strip()


def smart_decode(value):
    """Auto decode everything"""
    value = decode_hex(value)

    if isinstance(value, str):
        return clean_name(value)

    return value


# ------------------ MAIN MAPPER ------------------ #

def map_guild(data):

    created_ts = safe_get(data, 24)
    active_ts = safe_get(data, 44)

    # decode important fields
    name = smart_decode(safe_get(data, 2, ""))
    tag = smart_decode(safe_get(data, 12, ""))
    desc = smart_decode(safe_get(data, 13, ""))
    badge = smart_decode(safe_get(data, 14, {}))
    id_list = smart_decode(safe_get(data, 15, []))

    return {
        "guild_info": {
            "guild_id": safe_get(data, 1),

            # 🔥 CLEAN NAMES HERE
            "guild_name": name,
            "guild_tag": tag,
            "description": desc,

            "level": safe_get(data, 5, 0),
            "rank": safe_get(data, 6, 0),
            "members": safe_get(data, 7, 0),

            "leader_uid": safe_get(data, 4),

            "region_flag": smart_decode(safe_get(data, 2, "")),

            "created": {
                "timestamp": created_ts,
                "date": format_timestamp(created_ts)
            },
            "last_active": {
                "timestamp": active_ts,
                "date": format_timestamp(active_ts)
            }
        },

        "extra_data": {
            "metadata": badge,        # decoded JSON
            "id_list": id_list,      # decoded list
            "score": safe_get(data, 20),
            "likes": safe_get(data, 23),
            "power": safe_get(data, 36),
            "ranking": safe_get(data, 37),
            "tier": safe_get(data, 38)
        }
    }


# ------------------ FINAL OUTPUT ------------------ #

def pretty(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


# ------------------ USAGE ------------------ #

# raw_bytes = your decrypted protobuf bytes
# decoded = parse_proto(raw_bytes)
# final = map_guild(decoded)
# print(pretty(final))

# ---------- Guest login to get JWT (original URLs) ----------
async def get_jwt_from_guest(session, uid, password):
    # Original OAuth endpoint
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

    # Original MajorLogin endpoint
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
                    # Try protobuf first
                    try:
                        response_proto = output_pb2.Garena_420()
                        response_proto.ParseFromString(resp_data)
                        if response_proto.token:
                            return response_proto.token
                    except:
                        pass
                    # Fallback: search for JWT in raw text
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

# ---------- Fetch clan info (original URL) ----------
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

# ---------- Core handler with 403 retry ----------
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

        # If 403 and we haven't retried yet, refresh JWT and try once more
        if status == 403 and retry_auth:
            new_jwt = await get_jwt_from_guest(session, uid, password)
            if new_jwt:
                guild_info, status, error_text = await fetch_clan_info(session, new_jwt, clan_id)
            else:
                # Try a different account if available
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

# ---------- Pretty text formatter ----------
def format_guild_chart(guild_info):
    g = guild_info["guild_info"]
    s = guild_info["statistics"]

    lines = []
    lines.append("╔════════════════════════════════════════════════════════════════╗")
    lines.append("║                    GUILD INFORMATION                           ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Name        : {g['guild_name'][:50]:<50} ║")
    lines.append(f"║ Guild ID    : {g['guild_id']:<50} ║")
    lines.append(f"║ Region      : {g['region_flag'][:50]:<50} ║")
    lines.append(f"║ Leader UID  : {g['leader_uid'] if g['leader_uid'] else 'None':<50} ║")
    lines.append(f"║ Co-Leader   : {g['co_leader_uid'][:50] if g['co_leader_uid'] else 'None':<50} ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append("║ LEVEL & MEMBERS                                                 ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Level       : {g['level']:<50} ║")
    lines.append(f"║ Rank Points : {g['rank_points']:<50} ║")
    lines.append(f"║ Members     : {g['members']['current'] if g['members']['current'] else 0} / {g['members']['maximum']:<41} ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append("║ STATS                                                          ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Guild Score : {g['guild_score'][:46]:<46} ║")
    lines.append(f"║ Total Score : {s['total_score'] if s['total_score'] else 0:<46} ║")
    lines.append(f"║ Wins        : {s['wins'] if s['wins'] else 0:<46} ║")
    lines.append(f"║ Ranking Pts : {s['ranking_points'] if s['ranking_points'] else 0:<46} ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append("║ DESCRIPTION & BADGE                                            ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Badge ID    : {g['badge_id'][:50]:<50} ║")
    lines.append(f"║ Description : {g['description'][:48]:<48} ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append("║ TIMESTAMPS                                                     ║")
    lines.append("╠════════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Created     : {g['created']['date'] if g['created']['date'] else 'Unknown':<50} ║")
    lines.append(f"║ Last Active : {g['last_active']['date'] if g['last_active']['date'] else 'Unknown':<50} ║")
    lines.append("╚════════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)

# ---------- Flask local server ----------
def start_flask():
    from flask import Flask, request, jsonify, Response
    app = Flask(__name__)

    @app.route('/guild_info', methods=['GET', 'POST'])
    def guild_info_route():
        if request.method == 'POST':
            data = request.get_json()
            clan_id = data.get('clan_id') if data else None
        else:
            clan_id = request.args.get('clan_id')

        if not clan_id:
            if request.args.get('format') == 'text':
                return Response("Missing clan_id", status=400, mimetype='text/plain')
            return jsonify({'error': 'Missing clan_id'}), 400

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status, result = loop.run_until_complete(handle_clan_request(clan_id))
        loop.close()

        if status != 200:
            if request.args.get('format') == 'text':
                return Response(f"Error: {result.get('error', 'Unknown')}", status=status, mimetype='text/plain')
            return jsonify(result), status

        if request.args.get('format') == 'text':
            chart = format_guild_chart(result)
            return Response(chart, status=200, mimetype='text/plain')

        return jsonify(result), 200

    print("🚀 Local server running at http://127.0.0.1:9090")
    print("Example (JSON): curl 'http://127.0.0.1:9090/guild_info?clan_id=1234567890'")
    print("Example (chart): curl 'http://127.0.0.1:9090/guild_info?clan_id=1234567890&format=text'")
    app.run(host='0.0.0.0', port=9090, debug=False)

# ---------- Vercel handler ----------
async def handler(request):
    if request.method == 'POST':
        try:
            body = await request.json()
            clan_id = body.get('clan_id')
        except:
            clan_id = None
    else:
        clan_id = request.query_params.get('clan_id')

    status, result = await handle_clan_request(clan_id)
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result, indent=2, default=str)
    }

if __name__ == '__main__':
    start_flask()