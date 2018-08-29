import multiprocessing
import os
import sys

from django.apps import apps
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
            help="The number of processes to run (default: %d)." % CPU_COUNT,
        )
        parser.add_argument(
            "--threads", "-t",
            default=CPU_COUNT,
            type=int,
            help="The number of threads per process to use (default: %d)." % CPU_COUNT,
        )
        parser.add_argument(
            "--path", "-P",
            default=".",
            nargs="*",
            type=str,
            help="The import path (default: .).",
        )
        parser.add_argument(
            "--queues", "-Q",
            nargs="*",
            type=str,
            help="listen to a subset of queues (default: all queues)",
        )
        parser.add_argument(
            "--pid-file",
            type=str,
            help="write the PID of the master process to a file (default: no pid file)",
        )
        parser.add_argument(
            "--log-file",
            type=str,
            help="write all logs to a file (default: sys.stderr)",
        )

    def handle(self, use_watcher, use_polling_watcher, use_gevent, path, processes, threads, verbosity, queues,
               pid_file, log_file, **options):
        executable_name = "dramatiq-gevent" if use_gevent else "dramatiq"
        executable_path = self._resolve_executable(executable_name)
        watch_args = ["--watch", "."] if use_watcher else []
        if watch_args and use_polling_watcher:
            watch_args.append("--watch-use-polling")

        verbosity_args = ["-v"] * (verbosity - 1)
        tasks_modules = self.discover_tasks_modules()
        process_args = [
            executable_name,
            "--path", *path,
            "--processes", str(processes),
            "--threads", str(threads),

            # --watch /path/to/project [--watch-use-polling]
            *watch_args,

            # -v -v ...
            *verbosity_args,

            # django_dramatiq.tasks app1.tasks app2.tasks ...
            *tasks_modules,
        ]

        if queues:
            process_args.extend(["--queues", *queues])

        if pid_file:
            process_args.extend(["--pid-file", pid_file])

        if log_file:
            process_args.extend(["--log-file", log_file])

        self.stdout.write(' * Running dramatiq: "%s"\n\n' % " ".join(process_args))
        os.execvp(executable_path, process_args)

    def discover_tasks_modules(self):
        app_configs = apps.get_app_configs()
        tasks_modules = ["django_dramatiq.setup"]
        for conf in app_configs:
            if module_has_submodule(conf.module, "tasks"):
                module = conf.name + ".tasks"
                tasks_modules.append(module)
                self.stdout.write(" * Discovered tasks module: %r" % module)
        return tasks_modules

    def _resolve_executable(self, exec_name):
        bin_dir = os.path.dirname(sys.executable)
        if bin_dir:
            return os.path.join(bin_dir, exec_name)
        return exec_name
