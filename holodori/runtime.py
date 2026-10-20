"""Run one unchanged upstream UI in its own interpreter and Tk container."""
from __future__ import annotations

import argparse
import ctypes
import importlib
import importlib.util
import os
import re
from pathlib import Path
import runpy
import sys
import traceback

from holodori.channel import read_json, write_json
from holodori.modules import BY_ID

LANGUAGES = ('繁體中文', 'English', '日本語', '한국어', 'Indonesian', '简体中文')
_HOTKEY_CONTRACT = None


def validate_shared_settings(language, start_key, stop_key):
    """Use the unchanged Windows physical-key parser for every component."""
    global _HOTKEY_CONTRACT
    if language not in LANGUAGES:
        raise ValueError(f'Unsupported language: {language}')
    if _HOTKEY_CONTRACT is None:
        path = BY_ID['high_low'].path / 'hotkey_settings.py'
        spec = importlib.util.spec_from_file_location('_holodori_hotkey_contract', path)
        _HOTKEY_CONTRACT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_HOTKEY_CONTRACT)
    first, first_key = _HOTKEY_CONTRACT.parse_stop_hotkey(start_key)
    second, second_key = _HOTKEY_CONTRACT.parse_stop_hotkey(stop_key)
    if first_key == second_key and (set(first) <= set(second) or set(second) <= set(first)):
        raise ValueError('Start and stop shortcuts conflict')


def shortcut_values(app):
    result = {}
    for name in ('start_key', 'stop_key'):
        value = getattr(app, name, None)
        result[name] = value.get() if hasattr(value, 'get') else value
    return result


def shortcut_widgets(app):
    widgets = [widget for name in ('start_key_label', 'stop_key_label', 'start_shortcut_label',
               'shortcut_label', 'start_entry', 'stop_entry', 'start_shortcut_entry', 'shortcut_entry')
               if (widget := getattr(app, name, None)) is not None]
    widgets.extend(getattr(app, 'shortcut_entries', ()))
    frames = getattr(app, 'field_frames', {})
    widgets.extend(frames[name] for name in ('start', 'stop') if name in frames)
    return tuple(dict.fromkeys(widgets))


def language_variable(app, module_id):
    return getattr(app, 'game_language' if module_id == 'fishing' else 'language', None)


def widget_disabled(widget):
    if hasattr(widget, 'instate'):
        return widget.instate(['disabled'])
    return str(widget.cget('state')) == 'disabled'


def language_enabled(app):
    choice = getattr(app, 'language_choice', None)
    return choice is None or not widget_disabled(choice)


def hide_shared_controls(app):
    """Replace original language/shortcut rows with the shared host controls."""
    widgets = tuple(widget for name in ('language_label', 'language_choice')
                    if (widget := getattr(app, name, None)) is not None)
    widgets += shortcut_widgets(app)
    widgets += chrome_widgets(app)
    for name in ('form_rows', 'form_labels'):
        rows = getattr(app, name, None)
        if isinstance(rows, list):
            rows[:] = [widget for widget in rows if widget not in widgets]
    for widget in widgets:
        if widget.winfo_manager() == 'grid':
            widget.grid_remove()
        elif widget.winfo_manager() == 'pack':
            widget.pack_forget()
    return all(not widget.winfo_manager() for widget in widgets)


def chrome_widgets(app):
    """Move introductory text to the host and hide repeated headings/versions."""
    widgets = []
    for name in ('title_label','subtitle','title'):
        heading = getattr(getattr(app,name,None),'master',None)
        if heading is not None:
            widgets.append(heading)
    widgets.extend(widget for name in ('instructions','status','version_label')
                   if (widget := getattr(app,name,None)) is not None)
    root = getattr(app,'root',None)
    if root is not None and hasattr(root,'winfo_children'):
        pending = list(root.winfo_children())
        while pending:
            widget = pending.pop()
            pending.extend(widget.winfo_children())
            if 'text' in widget.keys() and re.fullmatch(r'[vV]\d+\.\d+(?:\.\d+)?', str(widget.cget('text')).strip()):
                widgets.append(widget)
    return tuple(dict.fromkeys(widgets))


def intro_status(app):
    def label_value(name, option):
        widget = getattr(app,name,None)
        return str(widget.cget(option)) if widget is not None else ''
    return dict(instructions=label_value('instructions','text'),
                display_status=label_value('status','text'),
                status_color=label_value('status','foreground'))


def language_selector_hidden(app):
    return all(not widget.winfo_manager() for name in ('language_label', 'language_choice')
               if (widget := getattr(app, name, None)) is not None)


def shortcuts_enabled(app, module_id, *, shared_capture=False):
    if busy(app, module_id) or (module_id == 'cooking' and getattr(app, 'child', None) is not None):
        return False
    if any(getattr(app, name, False) for name in ('closing', '_closing', 'reset_confirming')):
        return False
    if any(getattr(app, name, None) is not None for name in ('help_dialog', '_developer_help_dialog')):
        return False
    if not shared_capture and any(getattr(app, name, False) for name in (
            'capture_target', '_shortcut_capturing', '_capturing', 'capturing')):
        return False
    for name in ('start_entry', 'stop_entry', 'start_shortcut_entry', 'shortcut_entry'):
        widget = getattr(app, name, None)
        if widget is not None and widget_disabled(widget):
            return False
    return True


def suspend_shortcuts(app, module_id, target='start'):
    """Match original capture guards as well as disabling native listeners."""
    if module_id == 'high_low':
        if app.capture_target != target:
            app.capture_target = target
            app.configure_hotkeys()  # Invalidates already queued shortcut messages.
        app.start_hotkey.configure(enabled=False)
        app.stop_hotkey.configure(enabled=False)
    elif module_id == 'fishing':
        app._shortcut_capturing = True
        app._hotkey_enabled = False
        app._hotkey.configure(enabled=False)
    elif module_id == 'jump_rope':
        if not app._capturing:
            app._hotkey_generation += 1
        app._capturing = True
        app.hotkey.configure(enabled=False)
    else:
        app.capturing = app.start_key if target == 'start' else app.stop_key
        app.configure_hotkeys()
        app.start_listener.configure(enabled=False)
        app.stop_listener.configure(enabled=False)


def resume_shortcuts(app, module_id):
    if module_id == 'fishing':
        app._end_shortcut_capture()
        app._snapshot_settings()
        app._poll_start_hotkey()
    else:
        app.end_capture()


def apply_shared_settings(app, module_id, language, start_key, stop_key):
    """Validate all fields before changing native listeners or Tk variables."""
    validate_shared_settings(language, start_key, stop_key)
    suspend_shortcuts(app, module_id)
    if module_id == 'high_low':
        app.start_key, app.stop_key = start_key, stop_key
    else:
        app.start_key.set(start_key)
        app.stop_key.set(stop_key)
    for name, value in (('start_display', start_key), ('stop_display', stop_key),
                        ('start_shortcut_display', start_key), ('shortcut_display', stop_key)):
        display = getattr(app, name, None)
        if display is not None:
            display.set(value)
    change_language(app, module_id, language)
    if module_id == 'high_low':
        app.configure_hotkeys()
        app.save_settings()
    elif module_id == 'fishing':
        app._snapshot_settings()
    elif module_id == 'cooking':
        app.save_settings()
        app.configure_hotkeys()
    resume_shortcuts(app, module_id)
    hide_shared_controls(app)


def change_language(app, module_id, language):
    if language not in LANGUAGES:
        raise ValueError(f'Unsupported language: {language}')
    variable = language_variable(app, module_id)
    if variable is None:
        raise ValueError(f'Missing language variable for {module_id}')
    variable.set(language)
    handler = {'high_low': 'change_language', 'fishing': '_apply_language',
               'jump_rope': 'apply_language', 'cooking': 'translate'}[module_id]
    getattr(app, handler)()
    hide_shared_controls(app)


def dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        pass


def activate_source(module_id):
    module = BY_ID[module_id]
    if not (module.path / (module.entry + '.py')).is_file():
        raise FileNotFoundError(f'Missing upstream/{module_id}. Run git submodule update --init --recursive.')
    os.chdir(module.path)
    sys.path.insert(0, str(module.path))
    return module


def cooking_worker():
    module = activate_source('cooking')
    runpy.run_path(str(module.path / 'gui.py'), run_name='__main__')


def snapshot(app, spec):
    saved = {name: getattr(app, name).get() for name in spec.fields}
    # Keep the displayed result when returning to a stopped function.
    if spec.id == 'high_low':
        saved['_keys'] = dict(start=app.start_key, stop=app.stop_key)
    elif spec.id == 'fishing':
        saved['_counter'] = dict(total=app.counter.total, run_catches=app.counter.run_catches)
    elif spec.id == 'jump_rope':
        saved['_summary'] = (dict(done=app.session.completed_rounds,
            target=app.session.config.rounds, inputs=app.session.inputs)
            if app.session else getattr(app, '_holodori_summary', None))
    elif spec.id == 'cooking':
        saved['_completed'] = app.completed
    return saved


def restore(app, spec, saved):
    for name in spec.fields:
        if name in saved:
            getattr(app, name).set(saved[name])
    if spec.id == 'fishing':
        for name, value in saved.get('_counter', {}).items():
            setattr(app.counter, name, value)
        app._apply_language()
        app._snapshot_settings()
    elif spec.id == 'jump_rope':
        app._holodori_summary = saved.get('_summary')
        if app._holodori_summary:
            import types
            original_refresh = app.refresh_counts
            def refresh_counts(self):
                if self.session or not self._holodori_summary:
                    return original_refresh()
                summary = self._holodori_summary
                self.counter.configure(text=self.tr('counter', done=summary['done'], target=summary['target']))
                self.inputs_label.configure(text=self.tr('inputs', count=summary['inputs']))
            app.refresh_counts = types.MethodType(refresh_counts, app)
        app.apply_language()
        app.set_controls(False)
    elif spec.id == 'cooking':
        app.completed = saved.get('_completed', 0)
        app.translate()
        app.set_controls()
    elif spec.id == 'high_low':
        keys = saved.get('_keys', {})
        app.start_key = keys.get('start', app.start_key)
        app.stop_key = keys.get('stop', app.stop_key)
        app.start_display.set(app.start_key)
        app.stop_display.set(app.stop_key)
        app.start_hotkey.configure(value=app.start_key)
        app.stop_hotkey.configure(value=app.stop_key)
        app.apply_language()


def busy(app, module_id):
    if module_id == 'cooking':
        return app.child is not None and app.run_state not in ('ready', 'idle', 'error', 'completed')
    worker = getattr(app, 'worker', None)
    return bool(worker and worker.is_alive())


class EmbeddedSession:
    def __init__(self, root, app, spec, channel, *, smoke=False):
        self.root, self.app, self.spec, self.channel = root, app, spec, channel
        self.request = 0
        self.closing = False
        self.errors = []
        self.smoke = smoke
        self.last_state = 'ready'
        self.status_extra = {}
        self.permission_signature = None
        self.hide_job = None
        self.capture_active = False
        self.capture_target = 'start'
        root.report_callback_exception = self.callback_error
        hide_shared_controls(app)
        if hasattr(root, 'bind'):
            root.bind('<Configure>', self.schedule_hide_language, add='+')
        self.publish('ready')
        root.after(75, self.poll)

    def language_status(self):
        variable = language_variable(self.app, self.spec.id)
        hidden = hide_shared_controls(self.app)
        return dict(language=variable.get() if variable is not None else None,
                    language_enabled=language_enabled(self.app),
                    language_selector_hidden=language_selector_hidden(self.app),
                    shared_controls_hidden=hidden,
                    embedded_chrome_hidden=all(not widget.winfo_manager() for widget in chrome_widgets(self.app)),
                    shortcuts_enabled=shortcuts_enabled(self.app, self.spec.id, shared_capture=self.capture_active),
                    capture_active=self.capture_active, **shortcut_values(self.app), **intro_status(self.app))

    def publish(self, state, **extra):
        self.last_state = state
        self.status_extra.update(extra)
        language = self.language_status()
        active = busy(self.app, self.spec.id)
        self.permission_signature = (active, *language.values())
        write_json(self.channel / 'status.json', dict(
            state=state, request=self.request, module=self.spec.id,
            busy=active, snapshot=snapshot(self.app, self.spec),
            errors=self.errors, **language, **self.status_extra))

    def schedule_hide_language(self, _event=None):
        if not self.closing and self.hide_job is None:
            self.hide_job = self.root.after_idle(self.finish_hide_language)

    def finish_hide_language(self):
        self.hide_job = None
        if not self.closing:
            hide_shared_controls(self.app)

    def publish_permission_change(self):
        language = self.language_status()
        signature = (busy(self.app, self.spec.id), *language.values())
        if signature != self.permission_signature:
            self.publish(self.last_state)

    def callback_error(self, kind, error, tb):
        self.errors.append(''.join(traceback.format_exception(kind, error, tb)))
        self.publish('callback_error')
        if not self.closing:
            self.closing = True
            self.app.close()

    def poll(self):
        command = read_json(self.channel / 'command.json', {})
        if command.get('request', 0) > self.request:
            self.request = command['request']
            action = command.get('action')
            if action in ('close', 'deactivate'):
                if action == 'deactivate' and busy(self.app, self.spec.id):
                    self.publish('blocked')
                else:
                    self.closing = True
                    self.publish('closing')
                    self.app.close()
                    return
            elif action == 'snapshot':
                self.publish('ready')
            elif action == 'language':
                value = command.get('language')
                accepted = value in LANGUAGES and language_enabled(self.app)
                if accepted:
                    change_language(self.app, self.spec.id, value)
                    if self.capture_active:
                        suspend_shortcuts(self.app, self.spec.id, self.capture_target)
                self.publish('ready', language_accepted=accepted)
            elif action == 'capture':
                enabled = bool(command.get('enabled'))
                target = command.get('target', 'start')
                accepted = (not enabled or target in ('start', 'stop') and
                            shortcuts_enabled(self.app, self.spec.id, shared_capture=self.capture_active))
                if accepted:
                    if enabled:
                        self.capture_active = True
                        self.capture_target = target
                        suspend_shortcuts(self.app, self.spec.id, target)
                    elif self.capture_active:
                        self.capture_active = False
                        resume_shortcuts(self.app, self.spec.id)
                self.publish('ready', capture_accepted=accepted)
            elif action == 'settings':
                settings = command.get('settings', command)
                accepted = shortcuts_enabled(self.app, self.spec.id, shared_capture=self.capture_active)
                accepted = accepted and language_enabled(self.app)
                problem = None
                if accepted:
                    try:
                        apply_shared_settings(self.app, self.spec.id, settings.get('language'),
                                              settings.get('start_key'), settings.get('stop_key'))
                        self.capture_active = False
                    except (ValueError, TypeError, AttributeError) as error:
                        accepted, problem = False, str(error)
                self.publish('ready', settings_accepted=accepted, settings_error=problem)
            elif action == 'set_fields' and self.smoke:
                restore(self.app, self.spec, command['fields'])
                self.publish('ready')
            elif action == 'dialog' and self.smoke:
                # Test original help dialogs, without starting any automation.
                method = {'high_low': 'show_strategy_help', 'fishing': 'show_developer_help',
                          'jump_rope': 'show_help', 'cooking': 'show_model_help'}[self.spec.id]
                getattr(self.app, method)()
                self.root.after(150, self.close_dialogs)
        if not self.closing:
            if self.capture_active and busy(self.app, self.spec.id):
                self.capture_active = False
                resume_shortcuts(self.app, self.spec.id)
            if self.capture_active:
                suspend_shortcuts(self.app, self.spec.id, self.capture_target)
            self.publish_permission_change()
            self.root.after(75, self.poll)

    def close_dialogs(self):
        import tkinter as tk
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel):
                protocol = child.protocol('WM_DELETE_WINDOW')
                if protocol:
                    child.tk.call(protocol)
                else:
                    child.destroy()
        self.publish('ready', dialog_checked=True)


def embedded_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--embedded', choices=BY_ID, required=True)
    parser.add_argument('--container', required=True)
    parser.add_argument('--channel', type=Path, required=True)
    parser.add_argument('--language', choices=LANGUAGES, default='繁體中文')
    parser.add_argument('--start-key', default='F8')
    parser.add_argument('--stop-key', default='INSERT')
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    dpi_awareness()
    try:
        spec = activate_source(args.embedded)
        upstream = importlib.import_module(spec.entry)
        import tkinter as tk
        if args.smoke:
            class NoHotkey:
                def __init__(self, *a, **k): pass
                def start(self): pass
                def configure(self, *a, **k): pass
                def close(self): pass
            upstream.GlobalHotkey = NoHotkey
            if spec.id == 'high_low':
                original = upstream.HololiveBotUI.__init__
                upstream.HololiveBotUI.__init__ = lambda self, root: original(self, root, hotkey_factory=NoHotkey)
        root = tk.Tk(use=args.container)
        if spec.id == 'high_low':
            upstream.prepare_user_data(upstream.auto_bot.APP_DIR)
        app = getattr(upstream, spec.app_class)(root)
        saved = read_json(args.channel / 'restore.json', {})
        if saved:
            restore(app, spec, saved)
        apply_shared_settings(app, spec.id, args.language, args.start_key, args.stop_key)
        session = EmbeddedSession(root, app, spec, args.channel, smoke=args.smoke)
        root.mainloop()
        write_json(args.channel / 'status.json', dict(state='closed', request=session.request,
                   module=spec.id, errors=session.errors,
                   error='\n'.join(session.errors),
                   snapshot=read_json(args.channel / 'status.json', {}).get('snapshot', {})))
        if session.errors:
            raise SystemExit(1)
    except Exception:
        write_json(args.channel / 'status.json', {'state': 'error', 'error': traceback.format_exc()})
        # The host owns error presentation. An uncaught frozen exception would
        # open a second modal window and prevent the failed process from exiting.
        raise SystemExit(1)
