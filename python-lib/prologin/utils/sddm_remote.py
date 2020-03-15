#!/opt/prologin/venv/bin/python

import aiohttp
import asyncio
import hmac
import json
import os
from aiohttp import web

admins = set()
sddms = set()


async def broadcast_to(client_set: set, msg: str):
    if not client_set:
        return
    await asyncio.wait([ws.send_str(msg) for ws in client_set])


def base_handler(client_set: set, entity_name: str, func, on_connect=None):
    async def handle(request: web.Request):
        if on_connect is not None:
            try:
                on_connect(request)
            except Exception as e:
                return aiohttp.web.HTTPBadRequest(text=str(e))

        ws = web.WebSocketResponse()
        ws.request = request

        try:
            await ws.prepare(request)
            print(f"{entity_name} joined: {request.remote}")
            client_set.add(ws)

            async for msg in ws:
                await func(ws, msg)

            return ws

        finally:
            print(f"{entity_name} gone: {ws}")
            client_set.discard(ws)

    return handle


async def on_sddm_reply(ws, msg):
    if msg.type == aiohttp.WSMsgType.TEXT:
        await broadcast_to(admins, msg.data)


def on_admin_connect(secret: str):
    def check(request: web.Request):
        try:
            auth = aiohttp.BasicAuth.decode(request.headers.getone('Authorization', ''))
            if auth.login == 'prologin' and hmac.compare_digest(auth.password, secret):
                return
        except Exception:
            pass
        raise ValueError("Wrong secret")

    return check


async def on_admin_message(ws, msg):
    if msg.type == aiohttp.WSMsgType.TEXT:
        command = json.loads(msg.data)
        await broadcast_to(sddms, json.dumps(command))


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=20180)
    p.add_argument('--admin-secret', default=os.getenv('ADMIN_SECRET'))

    args = p.parse_args()

    app = web.Application()
    app.add_routes([
        web.get('/remotectl', base_handler(sddms, "Remote SDDM", on_sddm_reply)),
        web.get('/admin', base_handler(admins, "Admin", on_admin_message, on_admin_connect(args.admin_secret))),
    ])
    web.run_app(app, host=args.host, port=args.port)
