"""Fluent-style host for four original Tk interfaces."""
from __future__ import annotations

import os
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk
from holodori import __version__
from holodori.channel import read_json, write_json
from holodori.modules import MODULES, BY_ID, ROOT, versions
from holodori.runtime import dpi_awareness
from holodori.settings import load_settings, save_settings, captured_hotkey, hotkeys_conflict

BG, TEXT, MUTED = '#F5F5F5', '#242424', '#616161'
SELECTED_BACKGROUNDS = {
    'high_low': '#EDE5F6', 'fishing': '#E5F2FC',
    'jump_rope': '#FFF7D1', 'cooking': '#FDE9EA',
}
LABELS = {
    '繁體中文': ('比大小', '釣魚', '跳繩', '料理', '載入中…', '請先停止目前功能，再切換。', '正在停止，請稍候…', '重新載入', '載入失敗'),
    'English': ('High & Low', 'Fishing', 'Jump Rope', 'Cooking', 'Loading…', 'Stop the current function before switching.', 'Stopping, please wait…', 'Reload', 'Unable to load'),
    '日本語': ('ハイ＆ロー', '釣り', '縄跳び', '料理', '読込中…', '現在の機能を停止してから切り替えてください。', '停止中…', '再読込', '読込失敗'),
    '한국어': ('하이&로', '낚시', '줄넘기', '요리', '불러오는 중…', '현재 기능을 중지한 후 전환하세요.', '중지 중…', '새로 고침', '불러오기 실패'),
    'Indonesian': ('High & Low', 'Memancing', 'Lompat Tali', 'Memasak', 'Memuat…', 'Hentikan fungsi aktif sebelum beralih.', 'Menghentikan…', 'Muat ulang', 'Gagal memuat'),
    '简体中文': ('猜高低', '钓鱼', '跳绳', '料理', '加载中…', '请先停止当前功能，再切换。', '正在停止，请稍候…', '重新加载', '加载失败'),
}
SETTING_LABELS = {
    '繁體中文': ('語言 / Language', '開始快捷鍵', '停止快捷鍵', '請按下快捷鍵…', '開始與停止快捷鍵不能相同或互相包含。'),
    'English': ('Language', 'Start shortcut', 'Stop shortcut', 'Press a shortcut…', 'Start and stop shortcuts must not overlap.'),
    '日本語': ('言語 / Language', '開始キー', '停止キー', 'キーを押してください…', '開始キーと停止キーは重複できません。'),
    '한국어': ('언어 / Language', '시작 단축키', '중지 단축키', '단축키를 누르세요…', '시작과 중지 단축키는 중복할 수 없습니다.'),
    'Indonesian': ('Bahasa / Language', 'Pintasan mulai', 'Pintasan berhenti', 'Tekan pintasan…', 'Pintasan mulai dan berhenti tidak boleh tumpang tindih.'),
    '简体中文': ('语言 / Language', '开始快捷键', '停止快捷键', '请按下快捷键…', '开始与停止快捷键不能相同或互相包含。'),
}


def family_theme(root, px):
    path = BY_ID['high_low'].path / 'fluent_theme.py'
    spec = importlib.util.spec_from_file_location('holodori_family_theme', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FluentTheme(root, px)


def child_command(module_id, container, channel, *, smoke=False, executable=None, settings=None):
    command = [str(executable or sys.executable)]
    if executable is None and not getattr(sys, 'frozen', False):
        command.append(str(ROOT / 'main.py'))
    command += ['--embedded', module_id, '--container', hex(container), '--channel', str(channel)]
    if settings:
        command += ['--language', settings['language'], '--start-key', settings['start_key'],
                    '--stop-key', settings['stop_key']]
    if smoke:
        command.append('--smoke')
    return command


class HolodoriApp:
    def __init__(self, root, *, initial='high_low', smoke=False, session_dir=None, child_executable=None):
        self.root, self.smoke = root, smoke
        self.child_executable = child_executable
        self.temporary = tempfile.TemporaryDirectory(prefix='holodori-', dir=session_dir)
        self.session_dir = Path(self.temporary.name)
        self.process = self.stream = None
        self.active = self.pending = None
        self.channel = None
        self.sequence = 0
        self.snapshots = {}
        self.closing = False
        self.ready = False
        self.waiting_switch = False
        self.last_status = {}
        self.last_error = None
        self.icons = []
        self.source_versions = versions()
        # Each module and its nested workers share one job. A replacement
        # module waits until the previous job has no live processes.
        self.job = None
        self._session_draining = False
        self._job_termination_requested = False
        self._cleanup_error_reported = False
        self._finished_status = {}
        self._finished_code = None
        self._startup_error = None
        self.settings = load_settings()
        self.pending_settings = None
        self.capture_target = None
        self.capture_ready = False
        self.capture_request = None
        self.scale = root.winfo_fpixels('1i') / 96
        self.px = lambda n: round(n*self.scale)
        root.title('Holodori-Auto')
        root.configure(bg=BG)
        root.geometry(f'{min(self.px(500), root.winfo_screenwidth()-60)}x{min(self.px(930), root.winfo_screenheight()-80)}')
        root.minsize(self.px(400), min(self.px(740), root.winfo_screenheight()-80))
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.tk.call('tk', 'scaling', self.scale*96/72)
        self.theme = family_theme(root, self.px)
        header = tk.Frame(root, bg=BG)
        header.pack(fill='x', padx=self.px(20), pady=(self.px(14), self.px(8)))
        tk.Label(header, text='Holodori-Auto', bg=BG, fg=TEXT,
                 font=('Segoe UI', 17, 'bold')).pack(side='left')
        self.language = tk.StringVar(root, self.settings['language'])
        self.shared_card = ttk.Frame(root, style='Card.TFrame', padding=self.px(12))
        self.shared_card.pack(fill='x', padx=self.px(20), pady=(0,self.px(8)))
        self.shared_card.columnconfigure(1, weight=1)
        self.setting_labels = []
        for row in range(3):
            label = ttk.Label(self.shared_card, style='Card.TLabel')
            label.grid(row=row, column=0, sticky='w', padx=(0,self.px(16)), pady=self.px(4))
            self.setting_labels.append(label)
        self.language_choice = ttk.Combobox(self.shared_card, textvariable=self.language,
            values=tuple(LABELS), state='disabled', width=14, font=('Segoe UI',10))
        self.language_choice.grid(row=0, column=1, sticky='ew', pady=self.px(4))
        self.language_choice.bind('<<ComboboxSelected>>', self.change_language)
        self.shortcut_displays, self.shortcut_entries, self.shortcut_frames = {}, {}, {}
        for row, kind in ((1,'start'),(2,'stop')):
            display = tk.StringVar(root, self.settings[kind+'_key'])
            field = ttk.Frame(self.shared_card, style='Field.TFrame',
                padding=(self.px(8),self.px(4)))
            field.grid(row=row,column=1,sticky='ew',pady=self.px(4))
            entry = tk.Entry(field,textvariable=display,state='readonly',width=14,
                background='white',readonlybackground='white',foreground=TEXT,
                relief='flat',borderwidth=0,highlightthickness=0,font=('Segoe UI',10),cursor='hand2')
            entry.pack(fill='x',expand=True)
            entry.bind('<Button-1>',lambda event,target=kind:self.begin_capture(target))
            entry.bind('<KeyPress>',self.capture_key)
            entry.bind('<Alt-KeyPress>',self.capture_key)
            entry.bind('<FocusOut>',self.capture_focus_out)
            self.shortcut_displays[kind],self.shortcut_entries[kind],self.shortcut_frames[kind] = display,entry,field
            field.pack_propagate(False)
        self.shared_card.bind('<Configure>', self.match_control_heights, add='+')
        root.after_idle(self.match_control_heights)
        root.bind('<Button-1>', self.cancel_capture_on_click, add='+')
        self.navigation = tk.Frame(root, bg=BG)
        self.navigation.pack(fill='x', padx=self.px(16), pady=(0, self.px(8)))
        self.buttons = {}
        for index, module in enumerate(MODULES):
            self.navigation.columnconfigure(index, weight=1, uniform='tab')
            button = tk.Button(self.navigation, bg=BG, fg=TEXT, activeforeground=TEXT,
                               activebackground='#E8E8E8', relief='flat', bd=0,
                               font=('Segoe UI', 10), cursor='hand2',
                               padx=self.px(4), pady=self.px(9), takefocus=True,
                               command=lambda mid=module.id: self.select(mid))
            button.grid(row=0, column=index, sticky='ew', padx=self.px(3))
            icon_path = module.path / module.icon
            if icon_path.is_file():
                with Image.open(icon_path) as source:
                    source = source.convert('RGBA')
                    source.thumbnail((self.px(22), self.px(22)), Image.Resampling.LANCZOS)
                    icon = ImageTk.PhotoImage(source, master=root)
                self.icons.append(icon)
                button.configure(image=icon, compound='top')
            self.buttons[module.id] = button
        self.body = tk.Frame(root, bg=BG)
        self.body.pack(fill='both', expand=True)
        self.container = None
        self.placeholder = tk.Frame(self.body, bg=BG)
        self.placeholder.place(relx=.5, rely=.45, anchor='center')
        self.progress = tk.Label(self.placeholder, bg=BG, fg=MUTED, font=('Segoe UI', 11))
        self.progress.pack()
        self.reload = tk.Button(self.placeholder, command=self.retry, relief='flat', bg='#E8E8E8',
                                fg=TEXT, font=('Segoe UI', 10), padx=14, pady=6)
        self.footer = tk.Frame(root, bg=BG)
        self.footer.pack(side='bottom', before=self.body, fill='x', padx=self.px(20),
                         pady=(self.px(4), self.px(8)))
        tk.Label(self.footer, text='v'+__version__, bg=BG, fg=MUTED,
                 font=('Segoe UI', 9)).pack(side='left')
        self.note = tk.Label(self.footer, bg=BG, fg=MUTED, font=('Segoe UI', 9), anchor='e')
        self.note.pack(side='right', fill='x', expand=True)
        self.translate()
        try:
            root.iconbitmap(default=str(BY_ID['high_low'].path / 'icon.ico'))
        except tk.TclError:
            pass
        root.after(50, lambda: self.select(initial))
        root.after(100, self.poll)

    def translate(self):
        labels = LABELS[self.language.get()]
        for index, module in enumerate(MODULES):
            self.buttons[module.id].configure(text=labels[index])
        self.reload.configure(text=labels[7])
        if hasattr(self,'setting_labels'):
            for label, text in zip(self.setting_labels, SETTING_LABELS[self.language.get()]):
                label.configure(text=text)
        if not self.ready and not self.last_error:
            self.progress.configure(text=labels[4])

    def change_language(self, _event=None):
        candidate = dict(self.settings, language=self.language.get())
        self.apply_settings(candidate, language_only=True)

    def match_control_heights(self, _event=None):
        height = self.language_choice.winfo_reqheight()
        for field in self.shortcut_frames.values():
            if int(field.cget('height')) != height:
                field.configure(height=height)

    def apply_settings(self, candidate, *, language_only=False):
        if self.pending_settings or not self.ready:
            self.language.set(self.settings['language'])
            return
        self.translate()
        if language_only:
            self.request('language', language=candidate['language'])
        else:
            self.request('settings', **candidate)
        self.pending_settings = (self.sequence, candidate)
        self.update_shared_controls()

    def begin_capture(self, target):
        if not self.ready or self.pending_settings or not self.last_status.get('shortcuts_enabled', False):
            return 'break'
        self.capture_target, self.capture_ready = target, False
        self.request('capture', enabled=True, target=target)
        self.capture_request = self.sequence
        self.shortcut_displays[target].set('…')
        self.shortcut_frames[target].configure(style='FocusField.TFrame')
        self.shortcut_entries[target].focus_set()
        return 'break'

    def capture_key(self, event):
        if not self.capture_target:
            return
        if not self.capture_ready:
            return 'break'
        if event.keysym == 'Escape' and not event.state & 0x20005:
            self.end_capture()
            return 'break'
        value = captured_hotkey(event.keysym, event.state, event.keycode)
        if value:
            target = self.capture_target
            candidate = dict(self.settings, **{target+'_key': value})
            if hotkeys_conflict(candidate['start_key'],candidate['stop_key']):
                messagebox.showerror('Holodori-Auto', SETTING_LABELS[self.language.get()][4], parent=self.root)
                self.end_capture()
            else:
                self.clear_capture()
                self.apply_settings(candidate)
        return 'break'

    def clear_capture(self):
        self.capture_target, self.capture_ready, self.capture_request = None, False, None
        for kind in ('start','stop'):
            self.shortcut_displays[kind].set(self.settings[kind+'_key'])
            self.shortcut_frames[kind].configure(style='Field.TFrame')

    def end_capture(self):
        active = self.capture_target is not None
        self.clear_capture()
        if active and self.process is not None and self.process.poll() is None:
            self.request('capture', enabled=False)

    def capture_focus_out(self, event):
        if self.capture_target and event.widget is self.shortcut_entries[self.capture_target]:
            self.end_capture()

    def cancel_capture_on_click(self, event):
        if self.capture_target and event.widget not in self.shortcut_entries.values():
            self.end_capture()

    def update_shared_controls(self):
        if not hasattr(self,'language_choice'):
            return
        editable = self.ready and not self.closing and not self.pending_settings and not self.waiting_switch
        self.language_choice.configure(state='readonly' if editable and self.last_status.get('language_enabled',False)
                                       and not self.capture_target else 'disabled')
        for entry in self.shortcut_entries.values():
            entry.configure(state='readonly' if editable and self.last_status.get('shortcuts_enabled',False)
                            or self.capture_target else 'disabled')

    def accept_settings_status(self, status):
        if self.capture_request == status.get('request') and status.get('capture_active'):
            self.capture_ready = True
            self.shortcut_displays[self.capture_target].set(SETTING_LABELS[self.language.get()][3])
        elif self.capture_request == status.get('request') and status.get('capture_accepted') is False:
            self.clear_capture()
        if self.pending_settings and self.pending_settings[0] == status.get('request'):
            candidate = self.pending_settings[1]
            accepted = status.get('language') == candidate['language'] and (
                status.get('start_key') == candidate['start_key'] and status.get('stop_key') == candidate['stop_key'])
            self.pending_settings = None
            if accepted:
                self.settings = candidate
                save_settings(candidate)
            self.language.set(self.settings['language'])
            self.clear_capture()
            self.translate()
        self.update_shared_controls()

    def request(self, action, **extra):
        self.sequence += 1
        write_json(self.channel / 'command.json', dict(request=self.sequence, action=action, **extra))

    def select(self, module_id):
        if self.closing or self.pending or self.waiting_switch or getattr(self,'pending_settings',None):
            return
        if getattr(self,'capture_target',None):
            self.clear_capture()
        if self.process is not None or self.job is not None or self._session_draining:
            if self.process is not None and self.process.poll() is None:
                if module_id == self.active or not self.ready:
                    return
                self.pending = module_id
                self.waiting_switch = True
                self.request('deactivate')
                return
            # The GUI may exit between poll callbacks; its workers can still
            # belong to the previous job until cleanup verifies their exit.
            self.pending = module_id
            self.waiting_switch = True
        else:
            self.launch(module_id)

    def launch(self, module_id):
        if self.process is not None or self.job is not None or self._session_draining:
            raise RuntimeError('The previous module session has not finished closing.')
        self.active = module_id
        self.ready = False
        self.pending = None
        self.waiting_switch = False
        self.last_error = None
        self.last_status = {}
        self.sequence = 0
        self._job_termination_requested = False
        self._cleanup_error_reported = False
        self._finished_status = {}
        self._finished_code = None
        self._startup_error = None
        self.channel = self.session_dir / f'{module_id}-{os.urandom(6).hex()}'
        self.channel.mkdir()
        write_json(self.channel / 'restore.json', self.snapshots.get(module_id, {}))
        if self.container:
            self.container.destroy()
        self.container = tk.Frame(self.body, container=True, bg=BG)
        self.container.pack(fill='both', expand=True)
        self.root.update_idletasks()
        self.placeholder.lift()
        self.reload.pack_forget()
        self.progress.configure(text=LABELS[self.language.get()][4])
        self.note.configure(text='')
        for module in MODULES:
            self.buttons[module.id].configure(
                bg=SELECTED_BACKGROUNDS[module.id] if module.id == module_id else BG, fg=TEXT)
        self.stream = (self.channel / 'startup.txt').open('w', encoding='utf-8')
        try:
            import win32job
            self.job = win32job.CreateJobObject(None, '')
            job_info = win32job.QueryInformationJobObject(
                self.job, win32job.JobObjectExtendedLimitInformation)
            job_info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(
                self.job, win32job.JobObjectExtendedLimitInformation, job_info)
            self.process = subprocess.Popen(
                child_command(module_id, self.container.winfo_id(), self.channel, smoke=self.smoke,
                              executable=self.child_executable, settings=getattr(self,'settings',None)),
                cwd=ROOT, stdout=self.stream, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
            win32job.AssignProcessToJobObject(self.job, int(self.process._handle))
        except Exception as error:
            # pywintypes.error is not an OSError. Retain a failed child until
            # it has exited, including one whose job assignment failed.
            self._startup_error = str(error)
            self._session_draining = True
            if self.process is not None and self.process.poll() is None:
                try:
                    self.process.terminate()
                except Exception as stop_error:
                    self._startup_error += f'\nUnable to stop the failed launch: {stop_error}'
            if self.process is None:
                self._close_stream()
            self.fail(self._startup_error)

    def fail(self, error):
        self.ready = False
        self.last_error = error
        self.placeholder.lift()
        self.progress.configure(text=LABELS[self.language.get()][8])
        self.reload.pack(pady=self.px(12))
        self.note.configure(text=LABELS[self.language.get()][8])
        if not self.smoke:
            messagebox.showerror('Holodori-Auto', error, parent=self.root)

    def retry(self):
        if self.process is None and self.job is None and not self._session_draining:
            self.launch(self.active)
        elif self._session_draining or (self.process is not None and self.process.poll() is not None):
            self.pending = self.active
            self.waiting_switch = True

    def _close_stream(self):
        if self.stream is not None:
            try:
                self.stream.close()
            finally:
                self.stream = None

    def _read_status(self):
        status = read_json(self.channel / 'status.json', {})
        self.last_status = status
        if status.get('snapshot'):
            self.snapshots[self.active] = status['snapshot']
        return status

    def _drain_job(self):
        if self.job is None:
            return True
        try:
            import win32job
            count = win32job.QueryInformationJobObject(
                self.job, win32job.JobObjectBasicAccountingInformation)['ActiveProcesses']
            if count:
                if not self._job_termination_requested:
                    # Original normal close waits for workers. Processes still
                    # alive after GUI exit are orphaned module descendants.
                    win32job.TerminateJobObject(self.job, 1)
                    self._job_termination_requested = True
                self.note.configure(text=LABELS[self.language.get()][6])
                return False
            self.job.Close()
            self.job = None
            return True
        except Exception as error:
            # Block replacement until cleanup is verified, and report once.
            if not self._cleanup_error_reported:
                self._cleanup_error_reported = True
                self.fail(f'Unable to finish closing the module process tree: {error}')
            return False

    def _finish_session(self):
        if self.process is not None or not self._drain_job():
            return False
        self._session_draining = False
        if self.closing:
            self.finish_close()
            return True
        if self.pending:
            self.launch(self.pending)
        elif not self.last_error:
            detail = self._startup_error or self._finished_status.get('error')
            if not detail:
                detail = (self.channel / 'startup.txt').read_text(encoding='utf-8', errors='replace')
            self.fail(detail[-12000:] or f'Module exited ({self._finished_code}).')
        return False

    def poll(self):
        if self.process is not None:
            status = self._read_status()
            if hasattr(self,'pending_settings'):
                self.accept_settings_status(status)
            state = status.get('state')
            if state == 'blocked' and self.waiting_switch:
                self.pending = None
                self.waiting_switch = False
                self.note.configure(text=LABELS[self.language.get()][5])
            elif state == 'ready' and not self.closing and not self.waiting_switch and not self._session_draining:
                self.ready = True
                self.placeholder.lower()
                version = self.source_versions.get(self.active, {}).get('version') or ''
                self.note.configure(text=('v'+version) if version else '')
            elif state == 'closing':
                self.ready = False
                self.note.configure(text=LABELS[self.language.get()][6])
            code = self.process.poll()
            if code is not None:
                # Preserve a final snapshot written between the first status
                # read and process exit.
                self._finished_status = self._read_status()
                self._finished_code = code
                self._close_stream()
                self.process = None
                self.ready = False
                self._session_draining = True
        if self._session_draining and self.process is None:
            if self._finish_session():
                return
        self.root.after(100, self.poll)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.note.configure(text=LABELS[self.language.get()][6])
        for button in self.buttons.values():
            button.configure(state='disabled')
        if self.process is not None and self.process.poll() is None:
            if not self._session_draining:
                self.request('close')
        elif self.process is not None or self.job is not None or self._session_draining:
            self._session_draining = True
        else:
            self.finish_close()

    def finish_close(self):
        if self.process is not None or self.job is not None:
            return
        self._close_stream()
        self.root.destroy()
        self.temporary.cleanup()


def main():
    if sys.platform != 'win32':
        raise SystemExit('Holodori-Auto requires Windows 10/11.')
    dpi_awareness()
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Holodori.Auto')
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    HolodoriApp(root)
    root.mainloop()
