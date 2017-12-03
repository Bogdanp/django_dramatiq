import multiprocessing
import os
import sys

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import module_has_submodule

#: The number of available CPUs.
CPU_COUNT = multiprocessing.cpu_count()


class Command(BaseCommand):
    help = "Runs Dramatiq workers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-reload",
            action="store_false",
            dest="use_watcher",
            help="Disable autoreload.",
        )
        parser.add_argument(
            "--reload-use-polling",
            action="store_true",
            dest="use_polling_watcher",
            help=(
                "Use a poll-based file watcher for autoreload (useful under "
                "Vagrant and Docker for Mac)."
            ),
        )
        parser.add_argument(
            "--use-gevent",
            action="store_true",
            help="Use gevent for worker concurrency.",
        )
        parser.add_argument(
            "--processes", "-p",
            default=CPU_COUNT,
            type=int,
            help=f"The number of processes to run (default: {CPU_COUNT})."
        )
        parser.add_argument(
            "--threads", "-t",
            default=CPU_COUNT,
            type=int,
            help=f"The number of threads per process to use (default: {CPU_COUNT})."
        )

    def handle(self, use_watcher, use_polling_watcher, use_gevent, processes, threads, verbosity, *args, **options):
        executable_name = "dramatiq-gevent" if use_gevent else "dramatiq"
        executable_path = self._resolve_executable(executable_name)
        watch_args = ["--watch", os.getcwd()] if use_watcher else []
        if watch_args and use_polling_watcher:
            watch_args.append("--watch-use-polling")

        verbosity_args = ["-v"] * (verbosity - 1)
        tasks_modules = self.discover_tasks_modules()
        process_args = [
            executable_name,
            "--processes", str(processes),
            "--threads", str(threads),

            # --watch /path/to/project [--watch-use-polling]
            *watch_args,

            # -v -v ...
            *verbosity_args,

            # django_dramatiq.tasks app1.tasks app2.tasks ...
            *tasks_modules,
        ]

        self.stdout.write(f' * Running dramatiq: "{" ".join(process_args)}"\n\n')
        os.putenv("PYTHONPATH", f"{settings.BASE_DIR}")
        os.execvp(executable_path, process_args)

    def discover_tasks_modules(self):
        app_configs = apps.get_app_configs()
        tasks_modules = ["django_dramatiq.setup"]
        for conf in app_configs:
            if conf.name == "django_dramatiq":
                continue

            if module_has_submodule(conf.module, 'tasks'):
                module = f"{conf.name}.tasks"
                tasks_modules.append(module)
                self.stdout.write(f" * Discovered tasks module: {module!r}")
        return tasks_modules

    def _resolve_executable(self, exec_name):
        bin_dir = os.path.dirname(sys.executable)
        if bin_dir:
            return os.path.join(bin_dir, exec_name)
        return exec_name
