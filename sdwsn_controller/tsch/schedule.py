from sdwsn_controller.common import common
from rich.table import Table
import types
import logging

# Protocols encapsulated in sdn IP packet
logger = logging.getLogger(f'main.{__name__}')
cell_type = types.SimpleNamespace()
cell_type.UC_RX = 2
cell_type.UC_TX = 1

# ---------------------------------------------------------------------------


class TSCHSchedule():
    def __init__(
        self,
        schedule_type=None,
        dst_id=None,
        ch=None,
        ts=None
    ) -> None:
        assert isinstance(schedule_type, int)
        assert isinstance(dst_id, int | type(None))
        assert isinstance(ch, int)
        assert isinstance(ts, int)
        self.schedule_type = schedule_type
        self.dst_id = dst_id
        self.ch = ch
        self.ts = ts
# ---------------------------------------------------------------------------


class TSCHScheduleTable():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.clear()

    def clear(self):
        self.tsch_schedules = {}
        self.slotframe_size = 0
        self.last_ts = 0
        self.last_ch = 0

    def size(self):
        return len(self.tsch_schedules)

    def get_schedule(self, ch, ts):
        self.tsch_schedules.get((ch, ts))

    def get_destination(self, dst_id) -> bool:
        for schedule in self.tsch_schedules.values():
            if schedule.dst_id == dst_id:
                return True
        return False

    def timeslot_free(self, ts) -> bool:
        for schedule in self.tsch_schedules.values():
            if schedule.ts == ts:
                return False
        return True

    def add_tsch_schedule(self, schedule_type, ch, ts, dst=None) -> TSCHSchedule:
        if self.tsch_schedules.get((ch, ts)):
            return
        logger.debug(
            f'Node {self.node.id}: add TSCH schedule of type {schedule_type} at ch {ch}, ts {ts} and dst {dst}')
        tsch_schedule = TSCHSchedule(
            schedule_type=schedule_type, dst_id=dst, ch=ch, ts=ts)
        self.tsch_schedules.update({(ch, ts): tsch_schedule})
        if ts > self.last_ts:
            self.last_ts = ts
        if ch > self.last_ch:
            self.last_ch = ch
        return tsch_schedule

    def remove_tsch_schedule(self, ch, ts):
        logger.debug(
            f"Node {self.node.id}: remove TSCH schedule, ch {ch}, ts {ts}")
        if (ch, ts) in self.tsch_schedules:
            del self.tsch_schedules[(ch, ts)]

    def link_exists(self, dst_id) -> bool:
        for key in self.tsch_schedules:
            tsch_schedule = self.tsch_schedules.get(key)
            if tsch_schedule.dst_id == dst_id:
                return True
        return False

    def print(self):
        table = Table(title=f"TSCH schedules for node: {self.node.id}")

        table.add_column("Type", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Channel", justify="center", style="magenta")
        table.add_column("Timeoffset", justify="center", style="magenta")
        table.add_column("destination", justify="center", style="magenta")
        for key in self.tsch_schedules:
            tsch_schedule = self.tsch_schedules.get(key)
            if tsch_schedule.schedule_type == 2:
                sch_type = 'Rx'
            if tsch_schedule.schedule_type == 1:
                sch_type = 'Tx'
            table.add_row(sch_type, str(tsch_schedule.ch),
                          str(tsch_schedule.ts), str(tsch_schedule.dst_id))

        logger.debug(f"TSCH schedules\n{common.log_table(table)}")
