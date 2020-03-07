# -*- encoding: utf-8 -*-
# This file is part of Prologin-SADM.
#
# Copyright (c) 2013-2015 Antoine Pietri <antoine.pietri@prologin.org>
# Copyright (c) 2011 Pierre Bourdon <pierre.bourdon@prologin.org>
# Copyright (c) 2011 Association Prologin <info@prologin.org>
#
# Prologin-SADM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prologin-SADM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prologin-SADM.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import os.path
import prologin.rpc.server
import random
import time

from base64 import b64decode

from .concoursquery import ConcoursQuery
from .monitoring import (
    masternode_bad_result,
    masternode_client_done_file,
    masternode_match_done_db,
    masternode_match_done_file,
    masternode_request_compilation_task,
    masternode_task_redispatch,
    masternode_task_discard,
    masternode_worker_timeout,
)
from .task import MatchTask, CompilationTask
from .task import champion_compiled_path, match_path, clog_path
from .worker import Worker


class MasterNode(prologin.rpc.server.BaseRPCApp):
    def __init__(self, *args, config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.workers = {}
        self.db = ConcoursQuery(config)

    def run(self):
        logging.info("master listening on %s", self.config["master"]["port"])
        self.janitor = asyncio.Task(self.janitor_task())
        self.dbwatcher_compilations = asyncio.Task(
            self.dbwatcher_task("compilation", self.get_requested_compilations)
        )
        self.dbwatcher_matches = asyncio.Task(
            self.dbwatcher_task("matches", self.get_requested_matches)
        )
        super().run(port=self.config["master"]["port"])

    @prologin.rpc.remote_method
    async def status(self):
        d = []
        for (host, port), w in self.workers.items():
            d.append((host, port, w.slots, w.max_slots))
        return d

    async def register_worker(self, key, w):
        if await w.reachable():
            logging.warning("registered new worker: %s:%s", w.hostname, w.port)
            self.workers[key] = w
        else:
            logging.warning("dropped unreachable worker: %s:%s", w.hostname, w.port)

    @prologin.rpc.remote_method
    async def update_worker(self, worker):
        hostname, port, slots, max_slots = worker
        key = hostname, port
        if key not in self.workers:
            w = Worker(hostname, port, slots, max_slots, self.config)
            await self.register_worker(key, w)
        else:
            logging.debug(
                "updating worker: %s:%s %s/%s", hostname, port, slots, max_slots
            )
            self.workers[key].update(slots, max_slots)

    @prologin.rpc.remote_method
    async def heartbeat(self, worker, first):
        hostname, port, slots, max_slots = worker
        usage = 1.0 - slots / max_slots
        logging.debug(
            "received heartbeat from %s:%s, usage is %.2f%%",
            hostname,
            port,
            usage * 100,
        )
        if first and (hostname, port) in self.workers:
            await self.redispatch_worker(self.workers[(hostname, port)])
        await self.update_worker(worker)

    @prologin.rpc.remote_method
    async def compilation_result(self, worker, cid, user, ret, b64compiled, log):
        hostname, port, slots, max_slots = worker
        w = self.workers[(hostname, port)]

        task = w.get_compilation_task(cid)
        # Ignore the tasks we already redispatched
        if task is None:
            return
        w.remove_compilation_task(task)

        status = "ready" if ret else "error"
        if ret:
            with open(champion_compiled_path(self.config, user, cid), "wb") as f:
                f.write(b64decode(b64compiled))
        with open(clog_path(self.config, user, cid), "w") as f:
            f.write(log)
        logging.info("compilation of champion %s: %s", cid, status)
        await self.db.execute(
            "set_champion_status", {"champion_id": cid, "champion_status": status}
        )

    @prologin.rpc.remote_method
    async def match_done(
        self, worker, mid, result, dumper_stdout, server_stdout, players_stdout
    ):
        hostname, port, slots, max_slots = worker
        w = self.workers[(hostname, port)]

        task = w.get_match_task(mid)
        # Ignore the tasks we already redispatched
        if task is None:
            return
        w.remove_match_task(task)

        logging.info("match %s ended", mid)

        # Write player logs
        for pl_id, (champ_id, retcode, log) in players_stdout.items():
            logname = "log-champ-{}-{}.log".format(pl_id, champ_id)
            logpath = os.path.join(match_path(self.config, mid), logname)
            with masternode_client_done_file.time(), open(logpath, "w") as fplayer:
                fplayer.write(log)

        # Write server logs and dumper log
        serverpath = os.path.join(match_path(self.config, mid), "server.log")
        dumppath = os.path.join(match_path(self.config, mid), "dump.json.gz")
        with masternode_match_done_file.time(), open(serverpath, "w") as fserver, open(
            dumppath, "wb"
        ) as fdump:
            fserver.write(server_stdout)
            fdump.write(b64decode(dumper_stdout))

        match_status = {"match_id": mid, "match_status": "done"}
        try:
            player_scores = [
                {
                    "player_id": r["player"],
                    "player_score": r["score"],
                    "player_timeout": r["nb_timeout"] != 0,
                }
                for r in result
            ]
        except KeyError:
            masternode_bad_result.inc()
            return

        start = time.monotonic()
        await self.db.execute("set_match_status", match_status)
        await self.db.executemany("set_player_score", player_scores)
        masternode_match_done_db.observe(time.monotonic() - start)

    async def redispatch_worker(self, worker):
        masternode_task_redispatch.inc(len(worker.tasks))

        if worker.tasks:
            logging.info("redispatching tasks for %s: %s", worker, worker.tasks)
            for task in worker.tasks:
                await task.redispatch()

        del self.workers[(worker.hostname, worker.port)]

    async def resubmit_timeout_tasks(self, worker):
        tasks_to_discard = set()
        for t in worker.tasks:
            if t.has_timeout():
                max_tries = self.config["worker"]["max_task_tries"]
                if t.executions < max_tries:
                    msg = "resubmitted (try {}/{})".format(t.executions, max_tries)
                    await t.execute(self, worker)
                else:
                    msg = "maximum number of retries exceeded, bailing out"
                    tasks_to_discard.add(t)
                logging.info("task %s of %s timeout: %s", t, worker, msg)

        masternode_task_discard.inc(len(tasks_to_discard))
        worker.tasks.discard(tasks_to_discard)
        for task in tasks_to_discard:
            await task.discard()

    async def janitor_task(self):
        while True:
            try:
                for worker in list(self.workers.values()):
                    if not worker.is_alive(self.config["worker"]["timeout_secs"]):
                        masternode_worker_timeout.inc()
                        logging.warning("timeout detected for worker %s", worker)
                        await self.redispatch_worker(worker)
                    await self.resubmit_timeout_tasks(worker)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Janitor task triggered an exception")
            await asyncio.sleep(1)

    async def get_requested_compilations(self, status="new"):
        rows = await self.db.execute("get_champions", {"champion_status": status})

        tasks = []
        for row in rows:
            logging.info("requested compilation for %s / %s", row[1], row[0])
            t = CompilationTask(self.config, self.db, row[1], row[0])
            tasks.append(t)

        return tasks

    async def get_requested_matches(self, status="new"):
        rows = await self.db.execute("get_matches", {"match_status": status})

        tasks = []
        for row in rows:
            logging.info("request match id %s launch", row[0])
            mid = row[0]
            map_contents = row[1]
            players = list(zip(row[2], row[3], row[4]))
            try:
                t = MatchTask(self.config, self.db, mid, players, map_contents)
                tasks.append(t)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Unable to create task for match %s", mid)

        return tasks

    async def dbwatcher_task(self, name, fetcher):
        while True:
            try:
                # Restart pending tasks
                tasks = await fetcher("pending")
                if tasks:
                    await self.dispatch_tasks(f"pending {name}", tasks)

                while True:
                    tasks = await fetcher()
                    if tasks:
                        await self.dispatch_tasks(name, tasks)
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("DB Watcher task triggered an exception")
                await asyncio.sleep(5)
                continue

    def find_worker_for(self, task):
        available = list(self.workers.values())
        available = [w for w in available if w.can_add_task(task)]
        random.shuffle(available)
        available.sort(key=lambda w: w.usage)
        if not available:
            return None
        else:
            return available[0]

    async def dispatch_tasks(self, queue_name, tasks):
        logging.info("%d tasks in %s queue", len(tasks), queue_name)

        for task in tasks:
            w = self.find_worker_for(task)
            if w is None:
                logging.info("no worker available for task %s", task)
                break
            else:
                w.add_task(self, task)
                logging.debug("task %s got to %s", task, w)
