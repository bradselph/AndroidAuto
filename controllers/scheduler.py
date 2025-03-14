import threading
import time
import datetime
import json
import os
from enum import Enum


class ScheduleType(Enum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"


class TaskScheduler:

    def __init__(self, action_player, logger):
        self.action_player = action_player
        self.logger = logger
        self.tasks = []
        self.running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.tasks_file = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
                "scheduled_tasks.json"
        ))

        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)

        self.load_tasks()

    def start(self):
        if self.running:
            return False

        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        self.running = True
        return True

    def stop(self):
        if not self.running:
            return False

        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        self.running = False
        return True

    def _scheduler_loop(self):
        while not self.stop_event.is_set():
            now = datetime.datetime.now()

            for task in self.tasks:
                if self._should_run_task(task, now):
                    self._run_task(task)

                    task['last_run'] = now.isoformat()

                    if task['schedule_type'] == ScheduleType.ONE_TIME.value:
                        task['enabled'] = False

            self.save_tasks()

            time.sleep(30)

    def _should_run_task(self, task, now):
        if not task.get('enabled', False):
            return False

        schedule_type = task.get('schedule_type')
        schedule_data = task.get('schedule_data', {})

        last_run = None
        if 'last_run' in task and task['last_run']:
            try:
                last_run = datetime.datetime.fromisoformat(task['last_run'])
            except (ValueError, TypeError):
                last_run = None

        # One-time schedule
        if schedule_type == ScheduleType.ONE_TIME.value:
            scheduled_time = datetime.datetime.fromisoformat(schedule_data.get('datetime', ''))
            return now >= scheduled_time and (last_run is None or scheduled_time > last_run)

        # Daily schedule
        elif schedule_type == ScheduleType.DAILY.value:
            time_str = schedule_data.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If scheduled time is in the past, it's for tomorrow
            if scheduled_time < now:
                return False

            # Check if already run today
            if last_run and last_run.date() == now.date() and last_run.time() >= scheduled_time.time():
                return False

            return now.time() >= scheduled_time.time()

        # Weekly schedule
        elif schedule_type == ScheduleType.WEEKLY.value:
            days = schedule_data.get('days', [])
            time_str = schedule_data.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))

            # Check if today is a scheduled day
            weekday = now.strftime('%A').lower()
            if weekday not in days:
                return False

            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If scheduled time is in the past, it's for next week
            if scheduled_time < now:
                return False

            # Check if already run today
            if last_run and last_run.date() == now.date() and last_run.time() >= scheduled_time.time():
                return False

            return now.time() >= scheduled_time.time()

        # Interval schedule
        elif schedule_type == ScheduleType.INTERVAL.value:
            hours = int(schedule_data.get('hours', 0))
            minutes = int(schedule_data.get('minutes', 0))

            # Calculate interval in seconds
            interval_seconds = hours * 3600 + minutes * 60

            # Check if enough time has passed since last run
            if last_run:
                elapsed_seconds = (now - last_run).total_seconds()
                return elapsed_seconds >= interval_seconds

            return True

        return False

    def _run_task(self, task):
        try:
            # Get the actions from the task
            actions = task.get('actions', [])

            if not actions:
                self.logger.log(f"Task '{task.get('name', 'Unnamed')}' has no actions to run")
                return

            # Log the task execution
            self.logger.log(f"Running scheduled task: {task.get('name', 'Unnamed')}")

            # Load the actions into the action player
            self.action_player.load_actions(actions)

            # Run the actions
            speed_factor = task.get('speed_factor', 1.0)
            self.action_player.play(speed_factor)

        except Exception as e:
            self.logger.log(f"Error running scheduled task: {str(e)}")

    def add_task(self, name, actions, schedule_type, schedule_data, enabled=True, speed_factor=1.0):
        task = {
                'name':          name,
                'actions':       actions,
                'schedule_type': schedule_type.value if isinstance(schedule_type, ScheduleType) else schedule_type,
                'schedule_data': schedule_data,
                'enabled':       enabled,
                'speed_factor':  speed_factor,
                'created':       datetime.datetime.now().isoformat(),
                'last_run':      None
        }

        self.tasks.append(task)
        self.save_tasks()
        return len(self.tasks) - 1

    def update_task(self, index, task_data):
        if 0 <= index < len(self.tasks):
            self.tasks[index].update(task_data)
            self.save_tasks()
            return True
        return False

    def remove_task(self, index):
        if 0 <= index < len(self.tasks):
            self.tasks.pop(index)
            self.save_tasks()
            return True
        return False

    def get_tasks(self):
        return self.tasks

    def save_tasks(self):
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False

    def load_tasks(self):
        if not os.path.exists(self.tasks_file):
            self.tasks = []
            return True

        try:
            with open(self.tasks_file, 'r') as f:
                self.tasks = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self.tasks = []
            return False