#!/usr/bin/env python3
"""Capture native application windows with isolated, fictional demonstration data."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=('en_US', 'pt_BR'), required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/screenshots')
    parser.add_argument('--video', type=Path, help='Record an MP4 demonstration instead of screenshots')
    args = parser.parse_args()
    if args.video is not None:
        if args.language != 'en_US':
            parser.error('--video currently supports --language en_US')
        os.environ['GSK_RENDERER'] = 'cairo'
    os.environ['LANGUAGE'] = args.language
    os.environ['LC_ALL'] = args.language + '.UTF-8'
    os.environ.setdefault('GDK_BACKEND', 'x11')
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gtasks-screenshots-') as folder:
        temporary = Path(folder)
        catalog = temporary / 'locale/pt_BR/LC_MESSAGES/gtasks.mo'
        catalog.parent.mkdir(parents=True)
        subprocess.run(['msgfmt', '--check', '-o', str(catalog), str(ROOT / 'po/pt_BR.po')], check=True)
        os.environ['GTASKS_LOCALEDIR'] = str(temporary / 'locale')
        schemas = temporary / 'schemas'
        schemas.mkdir()
        shutil.copy(ROOT / 'data/io.github.rafatosta.gtasks.gschema.xml', schemas)
        subprocess.run(['glib-compile-schemas', str(schemas)], check=True)
        capture(args.language, args.output, temporary, schemas, args.video)


def capture(language, output, temporary, schemas, video=None):
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    gi.require_version('GdkX11', '4.0')
    from gi.repository import Adw, Gio, GLib, Gtk, GdkX11
    from gtasks.controllers.task_controller import TaskController
    from gtasks.repositories.memory import InMemoryTaskRepository
    from gtasks.repositories.registry import RepositoryRegistry
    from gtasks.repositories.cache import RemoteTaskCache
    from gtasks.services.task_service import TaskService
    from gtasks.views.main_window import MainWindow
    from window_capture import capture_x11

    pt = language == 'pt_BR'
    def text(english, portuguese):
        return portuguese if pt else english
    Adw.init()
    app = Adw.Application(application_id='io.github.rafatosta.gtasks.Screenshots',
                          flags=Gio.ApplicationFlags.NON_UNIQUE)
    app.register(None)
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        str(schemas), Gio.SettingsSchemaSource.get_default(), False)
    settings = Gio.Settings.new_full(schema_source.lookup('io.github.rafatosta.gtasks', False),
                                     Gio.memory_settings_backend_new(), None)
    settings.set_boolean('sync-on-startup', False)
    settings.set_boolean('restore-last-list', False)
    settings.set_boolean('show-completed', True)
    settings.set_int('sync-interval', 0)
    settings.set_string('spelling-language', language)
    source = 'google:demonstration'
    remote = InMemoryTaskRepository(source)
    sources = [(source, 'alex@example.org', remote)]
    registry = RepositoryRegistry({'local': InMemoryTaskRepository()},
                                  discover_remote=lambda: sources,
                                  cache=RemoteTaskCache(temporary / 'cache.db'))
    service = TaskService(registry)
    service.register_remote(sources)
    for name in (text('Inbox', 'Entrada'), text('Personal', 'Pessoal'), text('Reading', 'Leituras')):
        service.create_list(name)
    trip = service.create_list(text('Weekend trip', 'Viagem de fim de semana'), source)
    service.create_list(text('Work', 'Trabalho'), source)
    service.create_list(text('Shopping', 'Compras'), source)
    stay = service.create_task(trip, text('Choose a place to stay', 'Escolher onde ficar'))
    service.update_task(trip, stay.id, stay.title,
                        text('Compare quiet places near the city center', 'Comparar lugares tranquilos perto do centro'),
                        (date.today() + timedelta(days=2)).isoformat())
    tickets = service.create_task(trip, text('Book train tickets', 'Reservar passagens de trem'))
    tickets = service.update_task(trip, tickets.id, tickets.title,
        text('Leave on Friday afternoon and return on Sunday.\nCheck the departure times and save the tickets.',
             'Sair na sexta à tarde e voltar no domingo.\nConferir os horários e salvar as passagens.'),
        (date.today() + timedelta(days=3)).isoformat())
    pack = service.create_task(trip, text('Pack for the weekend', 'Preparar a mala'))
    service.update_task(trip, pack.id, pack.title,
                        text('Travel light and check the weather', 'Levar pouca bagagem e conferir a previsão'), None)
    service.create_subtask(trip, pack.id, text('Bring a rain jacket', 'Levar uma capa de chuva'))
    service.create_subtask(trip, pack.id, text('Charge the camera', 'Carregar a câmera'))
    itinerary = service.create_task(trip, text('Save the itinerary', 'Salvar o roteiro'))
    service.set_completed(trip, itinerary.id, True)

    def dispatch(callback):
        return GLib.idle_add(lambda: (callback(), GLib.SOURCE_REMOVE)[1])
    controller = TaskController(service, dispatch=dispatch)
    controller.select_list(trip.id, source)
    window = MainWindow(app, controller, settings)
    window.set_default_size(900, 640)
    window.present()
    def settle():
        loop = GLib.MainLoop()
        GLib.timeout_add(900, lambda: (loop.quit(), GLib.SOURCE_REMOVE)[1])
        loop.run()
    def save(name):
        settle()
        surface = window.get_surface()
        if not isinstance(surface, GdkX11.X11Surface):
            raise RuntimeError('Run this capture tool with GDK_BACKEND=x11')
        path = output / f'{name}-{language}.png'
        capture_x11(surface.get_xid(), path)
        print(path, flush=True)
    settle()
    window.set_focus(window._task_panel._entry)
    window._select_list(source, trip.id)
    window._refresh_lists()
    settle()
    if video is not None:
        from record_demo import record_demo
        record_demo(window, tickets, source, trip, temporary, video)
        window.close()
        settle()
        return
    save('tasks')
    window._task_action(tickets, 'edit')
    save('editor')
    window.get_visible_dialog().close()
    settle()
    window.set_default_size(420, 640)
    window._split_view.set_show_content(True)
    save('compact')
    window.close()
    settle()


if __name__ == '__main__':
    main()
