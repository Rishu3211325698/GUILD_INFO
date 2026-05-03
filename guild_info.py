import json
from flask import Flask, request, jsonify
import random
import asyncio
import aiohttp
import os
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import my_pb2
import output_pb2

app = Flask(__name__)

# ---------- Load accounts ----------
ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), 'accounts.json')
try:
    with open(ACCOUNTS_FILE, 'r') as f:
        ACCOUNTS = json.load(f)
    if not isinstance(ACCOUNTS, list):
        ACCOUNTS = []
except:
    ACCOUNTS = []

# ---------- AES config ----------
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV  = b'6oyZDr22E3ychjM%'

def encrypt_data(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

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

# ---------- Guest login ----------
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

# ---------- Build encrypted request for clan info ----------
def build_clan_request(clan_id):
    # Protobuf: field 1, wire type 0 (varint)
    tag = (1 << 3) | 0
    tag_varint = encode_varint(tag)
    value_varint = encode_varint(clan_id)
    plain = tag_varint + value_varint
    return encrypt_data(plain)

# ---------- Protobuf parser (full from claninfo.py) ----------
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

def clean_text(text):
    if not isinstance(text, str):
        return text
    return ''.join(c for c in text if c.isprintable()).strip()

def parse_members(members):
    result = []
    if not members:
        return result
    if not isinstance(members, list):
        members = [members]
    for m in members:
        if not isinstance(m, dict):
            continue
        stats = m.get(3, {})
        result.append({
            "role_id": m.get(1),
            "level": m.get(2),
            "position": m.get(4),
            "stats": {
                "matches_played": stats.get(2),
                "performance_score": stats.get(3),
                "rank": stats.get(4),
                "status": stats.get(5)
            }
        })
    return result

def map_guild(data):
    created_ts = data.get(24)
    active_ts = data.get(44)
    return {
        "guild_info": {
            "guild_id": data.get(1),
            "guild_name": clean_text(data.get(3)),
            "guild_tag": clean_text(data.get(5)),
            "guild_label": clean_text(data.get(50)),
            "description": clean_text(data.get(13)),
            "level": data.get(6),
            "rank_points": data.get(7),
            "guild_score": data.get(15),
            "badge_id": data.get(14),
            "leader_uid": data.get(11),
            "co_leader_uid": data.get(12),
            "region_id": data.get(48),
            "region_flag": data.get(2),
            "members": {
                "current": data.get(21),
                "maximum": data.get(20)
            },
            "created": {
                "timestamp": created_ts,
                "date": format_timestamp(created_ts)
            },
            "last_active": {
                "timestamp": active_ts,
                "date": format_timestamp(active_ts)
            }
        },
        "statistics": {
            "total_score": data.get(54),
            "wins": data.get(55),
            "ranking_points": data.get(58)
        },
        "members_preview": parse_members(data.get(61))
    }

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
        # Response is plain protobuf
        parsed = parse_proto(raw)
        return map_guild(parsed), resp.status, None

# ---------- Vercel handler ----------
import asyncio
import json
import random
import aiohttp

async def handler(request):
    path = request.url.path  # get endpoint path

    # Parse input (GET + POST)
    if request.method == 'POST':
        body = await request.json()
    else:
        body = request.query_params

    # Route handling
    if path == "/request/guild/info":
        clan_id = body.get('clan_id')

        if not clan_id:
            return response(400, {'error': 'Missing clan_id'})

        try:
            clan_id = int(clan_id)
        except:
            return response(400, {'error': 'clan_id must be integer'})

        if not ACCOUNTS:
            return response(500, {'error': 'No guest accounts available'})

        account = random.choice(ACCOUNTS)
        uid = str(account.get('uid'))
        password = account.get('password')

        if not uid or not password:
            return response(500, {'error': 'Invalid account in JSON'})

        async with aiohttp.ClientSession() as session:
            jwt = await get_jwt_from_guest(session, uid, password)
            if not jwt:
                return response(500, {'error': 'Failed to obtain JWT'})

            guild_info, status, error_text = await fetch_clan_info(session, jwt, clan_id)

            if status != 200:
                return response(status, {'error': f'Clan info request failed: {error_text}'})

            return response(200, guild_info)

    # Unknown route
    return response(404, {'error': 'Invalid endpoint'})


def response(status, data):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data, indent=2, default=str)
    }


def main(request):
    return asyncio.run(handler(request))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)    