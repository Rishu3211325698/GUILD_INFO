#!/usr/bin/env python3
"""
Guild Info API – Root file for Vercel.
Embeds protobuf definitions, loads accounts.json from root.
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
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# ========== EMBEDDED PROTOBUF DEFINITIONS (no external files) ==========
_sym_db = _symbol_database.Default()

# GameData protobuf (my.proto)
GAMEDATA_DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x08my.proto\"\xae\t\n\x08GameData\x12\x11\n\ttimestamp\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x14\n\x0cgame_version\x18\x05 \x01(\x05\x12\x14\n\x0cversion_code\x18\x07 \x01(\t\x12\x0f\n\x07os_info\x18\x08 \x01(\t\x12\x13\n\x0b\x64\x65vice_type\x18\t \x01(\t\x12\x18\n\x10network_provider\x18\n \x01(\t\x12\x17\n\x0f\x63onnection_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\x05\x12\x15\n\rscreen_height\x18\r \x01(\x05\x12\x0b\n\x03\x64pi\x18\x0e \x01(\t\x12\x10\n\x08\x63pu_info\x18\x0f \x01(\t\x12\x11\n\ttotal_ram\x18\x10 \x01(\x05\x12\x10\n\x08gpu_name\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x0f\n\x07user_id\x18\x13 \x01(\t\x12\x12\n\nip_address\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x15\n\rplatform_type\x18\x17 \x01(\x05\x12\x1a\n\x12\x64\x65vice_form_factor\x18\x18 \x01(\t\x12\x14\n\x0c\x64\x65vice_model\x18\x19 \x01(\t\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x1d \x01(\t\x12\x18\n\x10unknown_field_30\x18\x1e \x01(\x05\x12\"\n\x1asecondary_network_provider\x18) \x01(\t\x12!\n\x19secondary_connection_type\x18* \x01(\t\x12\x11\n\tunique_id\x18\x39 \x01(\t\x12\x10\n\x08\x66ield_60\x18< \x01(\x05\x12\x10\n\x08\x66ield_61\x18= \x01(\x05\x12\x10\n\x08\x66ield_62\x18> \x01(\x05\x12\x10\n\x08\x66ield_63\x18? \x01(\x05\x12\x10\n\x08\x66ield_64\x18@ \x01(\x05\x12\x10\n\x08\x66ield_65\x18\x41 \x01(\x05\x12\x10\n\x08\x66ield_66\x18\x42 \x01(\x05\x12\x10\n\x08\x66ield_67\x18\x43 \x01(\x05\x12\x10\n\x08\x66ield_70\x18\x46 \x01(\x05\x12\x10\n\x08\x66ield_73\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x10\n\x08\x66ield_76\x18L \x01(\x05\x12\x10\n\x08\x61pk_info\x18M \x01(\t\x12\x10\n\x08\x66ield_78\x18N \x01(\x05\x12\x10\n\x08\x66ield_79\x18O \x01(\x05\x12\x17\n\x0fos_architecture\x18Q \x01(\t\x12\x14\n\x0c\x62uild_number\x18S \x01(\t\x12\x10\n\x08\x66ield_85\x18U \x01(\x05\x12\x18\n\x10graphics_backend\x18V \x01(\t\x12\x19\n\x11max_texture_units\x18W \x01(\x05\x12\x15\n\rrendering_api\x18X \x01(\x05\x12\x18\n\x10\x65ncoded_field_89\x18Y \x01(\t\x12\x10\n\x08\x66ield_92\x18\\ \x01(\x05\x12\x13\n\x0bmarketplace\x18] \x01(\t\x12\x16\n\x0e\x65ncryption_key\x18^ \x01(\t\x12\x15\n\rtotal_storage\x18_ \x01(\x05\x12\x10\n\x08\x66ield_97\x18\x61 \x01(\x05\x12\x10\n\x08\x66ield_98\x18\x62 \x01(\x05\x12\x10\n\x08\x66ield_99\x18\x63 \x01(\t\x12\x11\n\tfield_100\x18\x64 \x01(\tb\x06proto3'
)
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(GAMEDATA_DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(GAMEDATA_DESCRIPTOR, 'my_pb2', _globals)
GameData = _sym_db.GetSymbol('GameData')

# Garena_420 protobuf (jwt_generator.proto)
GARENA420_DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x13jwt_generator.proto\"\xd2\x02\n\nGarena_420\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x0e\n\x06region\x18\x02 \x01(\t\x12\r\n\x05place\x18\x03 \x01(\t\x12\x10\n\x08location\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\n\n\x02id\x18\t \x01(\x05\x12\x0b\n\x03\x61pi\x18\n \x01(\t\x12\x0e\n\x06number\x18\x0c \x01(\x05\x12\x1e\n\tGarena420\x18\x0f \x01(\x0b\x32\x0b.Garena_420\x12\x0c\n\x04\x61rea\x18\x10 \x01(\t\x12\x11\n\tmain_area\x18\x12 \x01(\t\x12\x0c\n\x04\x63ity\x18\x13 \x01(\t\x12\x0c\n\x04name\x18\x14 \x01(\t\x12\x11\n\ttimestamp\x18\x15 \x01(\x03\x12\x0e\n\x06\x62inary\x18\x16 \x01(\x0c\x12\x13\n\x0b\x62inary_data\x18\x17 \x01(\x0c\x1a\"\n\x12\x44\x65\x63rypted_Payloads\x12\x0c\n\x04type\x18\x01 \x01(\x05b\x06proto3'
)
_builder.BuildMessageAndEnumDescriptors(GARENA420_DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(GARENA420_DESCRIPTOR, 'output_pb2', _globals)
Garena_420 = _sym_db.GetSymbol('Garena_420')

# ========== Load accounts (from root) ==========
ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), 'accounts.json')
try:
    with open(ACCOUNTS_FILE, 'r') as f:
        ACCOUNTS = json.load(f)
    if not isinstance(ACCOUNTS, list):
        ACCOUNTS = []
except:
    ACCOUNTS = []

# ========== AES configuration ==========
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

def build_clan_request(clan_id):
    tag = (1 << 3) | 0
    tag_varint = encode_varint(tag)
    value_varint = encode_varint(clan_id)
    plain = tag_varint + value_varint
    return encrypt_data(plain)

# ========== Protobuf parser ==========
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
    guild_id = safe_get(data, 1)
    region_flag_raw = safe_get(data, 2, '')
    region_flag = smart_decode(region_flag_raw)
    guild_tag = str(safe_get(data, 5, ''))
    level = safe_get(data, 6, 0)
    rank_points = safe_get(data, 7, 0)
    co_leader_raw = safe_get(data, 12, '')
    co_leader_uid = smart_decode(co_leader_raw)
    desc_raw = safe_get(data, 13, '')
    description = smart_decode(desc_raw)
    badge_raw = safe_get(data, 14, {})
    badge_id = smart_decode(badge_raw)
    score_raw = safe_get(data, 15, [])
    guild_score = smart_decode(score_raw)
    last_active_ts = safe_get(data, 44)
    created_ts = safe_get(data, 24, None)

    guild_name = ''
    raw_name = safe_get(data, 3, None)
    if isinstance(raw_name, bytes):
        guild_name = smart_decode(raw_name)
    elif isinstance(raw_name, str):
        guild_name = raw_name
    else:
        guild_name = str(raw_name) if raw_name else ''

    max_members = safe_get(data, 20, 0)
    if max_members > 1000:
        max_members = 50

    return {
        "guild_info": {
            "guild_id": guild_id,
            "guild_name": guild_name,
            "guild_tag": guild_tag,
            "description": description,
            "level": level,
            "rank_points": rank_points,
            "guild_score": str(guild_score),
            "badge_id": str(badge_id),
            "co_leader_uid": co_leader_uid,
            "region_flag": region_flag,
            "members": {
                "current": safe_get(data, 21, 0),
                "maximum": max_members
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

# ========== JWT generation using embedded protobufs ==========
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
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
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
            game = GameData()
            game.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            game.game_name = "free fire"
            game.game_version = 1
            game.version_code = "2.124.1"
            game.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game.device_type = "Handheld"
            game.network_provider = "Verizon Wireless"
            game.connection_type = "WIFI"
            game.screen_width = 1280
            game.screen_height = 960
            game.dpi = "240"
            game.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game.total_ram = 5951
            game.gpu_name = "Adreno (TM) 640"
            game.gpu_version = "OpenGL ES 3.0"
            game.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game.ip_address = "172.190.111.97"
            game.language = "en"
            game.open_id = open_id
            game.access_token = access_token
            game.platform_type = platform
            game.field_99 = str(platform)
            game.field_100 = str(platform)

            encrypted_body = encrypt_data(game.SerializeToString())
            async with session.post(login_url, data=encrypted_body, headers=login_headers, ssl=False, timeout=6) as r:
                if r.status == 200:
                    resp_data = await r.read()
                    msg = Garena_420()
                    msg.ParseFromString(resp_data)
                    if msg.token:
                        return msg.token
        except:
            pass
        await asyncio.sleep(0.1)
    return None

# ========== Fetch clan info ==========
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

# ========== Core handler ==========
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

# ========== Vercel handler ==========
async def async_handler(request):
    path = getattr(request, 'path', request.get('path', '/'))

    # Welcome message at root
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