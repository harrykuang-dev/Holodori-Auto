"""Embedded page for consecutive solo Puka Puka Fight matches."""

from queue import Empty, SimpleQueue
from threading import Event, Thread
import tkinter as tk
from tkinter import ttk
import traceback

from holodori.app import PUKA_LABELS, family_theme
from holodori.settings import parse_stop_hotkey
from pilot import StopPlay, run
from vision import VisionError
from win_window import GameWindow, key


COPY = {
    '繁體中文': (
        '先進入{game}，再點擊「開始」',
        '局數上限', '本次完成', '開始', '停止', '等待開始', '正在切換到遊戲…',
        '遊玩中', '正在停止', '已停止', '已達局數上限', '請輸入 1 至 9999 局。',
        '等待單人入口或關卡選單…', '等待棋盤…', '等待結算與領獎…',
        '落子 {moves}（{plies} 手）', '依照遊戲流程前進，兩種模式合計局數。', '關閉',
        '自動補充能量', '正在補充能量…'),
    'English': (
        'Open {game}, then click Start.',
        'Match limit', 'Completed this run', 'Start', 'Stop', 'Ready', 'Switching to the game…',
        'Playing', 'Stopping', 'Stopped', 'Match limit reached', 'Enter 1 to 9999 matches.',
        'Waiting for the solo lobby or stage menu…', 'Waiting for the board…', 'Waiting for results and rewards…',
        'Move {moves} ({plies} plies)', 'The match limit applies across both modes.', 'Close',
        'Automatically refill energy', 'Refilling energy…'),
    '日本語': (
        '「{game}」を開いてから「開始」をクリックしてください。',
        '対局数の上限', '今回のクリア数', '開始', '停止', '待機中', 'ゲームに切り替え中…',
        '対局中', '停止中', '停止しました', '設定した対局数に到達', '1〜9999の対局数を入力してください。',
        'ソロ画面またはステージ選択を待機中…', '盤面を待機中…', '結果と報酬を待機中…',
        '着手 {moves}（{plies}手）', '対局数の上限は両モードの合計です。', '閉じる',
        'エネルギーを自動回復', 'エネルギーを回復中…'),
    '한국어': (
        '{game}에 입장한 뒤 ‘시작’을 클릭하세요.',
        '대국 수 제한', '이번 실행 완료', '시작', '중지', '준비', '게임으로 전환 중…',
        '진행 중', '중지 중', '중지됨', '대국 수 제한에 도달', '1~9999 사이의 대국 수를 입력하세요.',
        '솔로 화면 또는 스테이지 선택 대기 중…', '게임판 대기 중…', '결과 및 보상 대기 중…',
        '착수 {moves} ({plies}수)', '두 모드의 대국 수를 합산합니다.', '닫기',
        '에너지 자동 충전', '에너지 충전 중…'),
    'Indonesian': (
        'Buka {game}, lalu klik Mulai.',
        'Batas pertandingan', 'Selesai sesi ini', 'Mulai', 'Berhenti', 'Siap', 'Beralih ke game…',
        'Sedang bermain', 'Menghentikan', 'Berhenti', 'Batas pertandingan tercapai', 'Masukkan 1 hingga 9999 pertandingan.',
        'Menunggu lobi solo atau menu level…', 'Menunggu papan…', 'Menunggu hasil dan hadiah…',
        'Langkah {moves} ({plies} giliran)', 'Batas dihitung untuk kedua mode.', 'Tutup',
        'Isi ulang energi otomatis', 'Mengisi ulang energi…'),
    '简体中文': (
        '先进入{game}，再点击「开始」',
        '局数上限', '本次完成', '开始', '停止', '等待开始', '正在切换到游戏…',
        '游玩中', '正在停止', '已停止', '已达局数上限', '请输入 1 至 9999 局。',
        '等待单人入口或关卡菜单…', '等待棋盘…', '等待结算和领奖…',
        '落子 {moves}（{plies} 手）', '按游戏进度推进，两种模式合计局数。', '关闭',
        '自动补充能量', '正在补充能量…'),
}
TEXT_FIELDS = ('instructions', 'limit', 'progress', 'start', 'stop', 'ready', 'starting',
               'playing', 'stopping', 'stopped', 'finished', 'invalid',
               'waiting_entry', 'waiting_board', 'waiting_result', 'move', 'help', 'close',
               'auto_refill', 'refilling')


def match_limit(value):
    if not value.isascii() or not value.isdecimal() or len(value) > 4 or not 1 <= int(value) <= 9999:
        raise ValueError('Expected a match limit from 1 to 9999')
    return int(value)


def shortcut_down(shortcut):
    modifiers, keycode = shortcut
    return bool(key(keycode) & 0x8000) and all(key(modifier) & 0x8000 for modifier in modifiers)


class PukaPukaApp:
    def __init__(self, root, *, smoke=False):
        self.root = root
        self.smoke = smoke
        self.worker = None
        self.closing = False
        self.capturing = False
        self.help_dialog = None
        self.stop_event = Event()
        self.messages = SimpleQueue()
        self.completed = 0
        self.target = None
        self.state = 'ready'
        self.detail_event = None
        self.shortcuts = None
        self.held = (False, False)
        self.language = tk.StringVar(root, '繁體中文')
        self.start_key = tk.StringVar(root, 'F8')
        self.stop_key = tk.StringVar(root, 'INSERT')
        self.rounds = tk.StringVar(root, '1')
        self.auto_refill = tk.BooleanVar(root, False)
        scale = root.winfo_fpixels('1i') / 96
        self.px = lambda value: round(value*scale)
        root.geometry(f'{self.px(500)}x{self.px(780)}')
        root.minsize(self.px(400), self.px(580))
        root.configure(bg='#F5F5F5')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.theme = family_theme(root, self.px)
        self.main = ttk.Frame(root, padding=(self.px(20), 0))
        self.main.grid(sticky='nsew')
        self.main.columnconfigure(0, weight=1)
        self.instructions = ttk.Label(root)
        self.status = tk.Label(root, fg='#117D85')

        settings = ttk.Frame(self.main, style='Card.TFrame', padding=self.px(16))
        settings.grid(row=1, column=0, sticky='ew', pady=(0, self.px(12)))
        settings.columnconfigure(1, weight=1)
        self.limit_label = ttk.Label(settings, style='Card.TLabel')
        self.limit_label.grid(row=0, column=0, padx=(0, self.px(12)), sticky='w')
        round_field = self.theme.rounded
        style = self.theme.style
        inset = self.px(5) + 1
        style.element_create('MatchLimit.field', 'image', round_field('#FFFFFF', '#D1D1D1', 4, '#FFFFFF'),
                             ('disabled', round_field('#F0F0F0', '#E5E5E5', 4, '#FFFFFF')),
                             ('focus', round_field('#FFFFFF', '#6D43AA', 4, '#FFFFFF')),
                             border=(self.px(6), inset, self.px(6), inset),
                             width=self.px(13), height=2*inset+1, sticky='nswe')
        style.layout('MatchLimit.TEntry', [('MatchLimit.field', {'sticky': 'nswe', 'children': [
            ('Entry.padding', {'sticky': 'nswe', 'children': [('Entry.textarea', {'sticky': 'nswe'})]})]})])
        style.configure('MatchLimit.TEntry', padding=(self.px(8), 0), borderwidth=0)
        self.entry = ttk.Entry(settings, style='MatchLimit.TEntry', textvariable=self.rounds,
                               width=12, font=('Segoe UI', 10))
        self.entry.grid(row=0, column=1, sticky='ew', pady=self.px(6))
        help_button = ttk.Button(settings, style='Info.TButton', image=self.theme.help_icon, command=self.show_help)
        help_button.grid(row=0, column=2, padx=(self.px(8), 0))
        style.configure('Card.TCheckbutton', background=style.lookup('Card.TFrame', 'background'))
        self.refill_checkbox = ttk.Checkbutton(settings, style='Card.TCheckbutton', variable=self.auto_refill)
        self.refill_checkbox.grid(row=1, column=0, columnspan=3, sticky='w', pady=(self.px(6), 0))

        progress = ttk.Frame(self.main, style='Card.TFrame', padding=self.px(16))
        progress.grid(row=0, column=0, sticky='ew', pady=(0, self.px(12)))
        progress.columnconfigure(0, weight=1)
        self.progress_label = ttk.Label(progress, style='CardMuted.TLabel')
        self.progress_label.grid(row=0, column=0, sticky='w')
        self.count_label = ttk.Label(progress, style='Count.TLabel')
        self.count_label.grid(row=1, column=0, sticky='w')
        self.detail = ttk.Label(progress, style='CardMuted.TLabel', justify='left')
        self.detail.grid(row=2, column=0, sticky='ew', pady=(self.px(4), 0))
        progress.bind('<Configure>', lambda event: self.detail.configure(wraplength=max(1, event.width-self.px(32))))

        controls = ttk.Frame(self.main)
        controls.grid(row=2, column=0, sticky='ew')
        controls.columnconfigure((0, 1), weight=1, uniform='puka')
        self.start_button = ttk.Button(controls, style='Primary.TButton', command=self.start,
                                       image=(self.theme.play_icons['normal'], 'disabled', self.theme.play_icons['disabled']),
                                       compound='left')
        self.start_button.grid(row=0, column=0, sticky='nsew', padx=(0, self.px(6)))
        self.stop_button = ttk.Button(controls, style='Secondary.TButton', command=self.stop,
                                      image=(self.theme.stop_icons['normal'], 'disabled', self.theme.stop_icons['disabled']),
                                      compound='left')
        self.stop_button.grid(row=0, column=1, sticky='nsew', padx=(self.px(6), 0))
        self.rounds.trace_add('write', lambda *_: self.refresh())
        self.translate()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(50, self.poll)

    def translate(self):
        language = self.language.get()
        self.text = dict(zip(TEXT_FIELDS, COPY[language]))
        self.instructions.configure(text=self.text['instructions'].format(game=PUKA_LABELS[language]))
        self.limit_label.configure(text=self.text['limit'])
        self.refill_checkbox.configure(text=self.text['auto_refill'])
        self.progress_label.configure(text=self.text['progress'])
        self.start_button.configure(text=self.text['start'])
        self.stop_button.configure(text=self.text['stop'])
        self.refresh()

    def refresh(self):
        detail = ''
        if self.detail_event:
            event, *args = self.detail_event
            if event == 'error':
                detail = args[0]
            elif event == 'move':
                detail = self.text[event].format(moves=args[0], plies=args[2])
            else:
                detail = self.text[event]
        self.detail.configure(text=detail)
        if detail:
            self.detail.grid()
        else:
            self.detail.grid_remove()
        self.status.configure(text=self.text[self.state])
        goal = self.target if self.target is not None else self.rounds.get() or '–'
        self.count_label.configure(text=f'{self.completed} / {goal}')
        active = self.worker is not None
        self.entry.configure(state='disabled' if active else 'normal')
        self.refill_checkbox.configure(state='disabled' if active else 'normal')
        self.start_button.configure(state='disabled' if active or self.smoke else 'normal')
        self.stop_button.configure(state='normal' if active and not self.stop_event.is_set() else 'disabled')

    def begin_capture(self):
        self.capturing = True

    def end_capture(self):
        self.shortcuts = tuple(parse_stop_hotkey(var.get()) for var in (self.start_key, self.stop_key))
        if not self.smoke:
            self.held = tuple(shortcut_down(shortcut) for shortcut in self.shortcuts)
        self.capturing = False

    def start(self, *, from_shortcut=False):
        if self.worker is not None or self.smoke or self.closing or self.capturing or self.help_dialog:
            return
        try:
            target = match_limit(self.rounds.get().strip())
        except ValueError:
            self.detail_event = ('invalid',)
            self.refresh()
            return
        self.completed, self.target = 0, target
        self.detail_event = None
        self.stop_event.clear()
        self.state = 'starting'
        self.worker = Thread(target=self.play, args=(target,),
                             kwargs={'activate': not from_shortcut, 'auto_refill': self.auto_refill.get()},
                             name='puka-puka-play')
        self.worker.start()
        self.refresh()

    def play(self, target, *, activate, auto_refill):
        def notify(kind, *args):
            self.messages.put((kind, *args))

        try:
            game = GameWindow(self.stop_event.is_set, activate=activate)
            notify('playing')
            run(game, target, notify, auto_refill=auto_refill)
        except InterruptedError:
            notify('stopped')
        except (OSError, StopPlay, VisionError) as error:
            notify('error', str(error))
        except Exception as error:
            traceback.print_exc()
            notify('error', str(error))
        else:
            notify('finished')

    def stop(self):
        if self.worker is not None:
            self.stop_event.set()
            self.state = 'stopping'
            self.refresh()

    def poll(self):
        try:
            while True:
                event, *args = self.messages.get_nowait()
                if event in ('finished', 'stopped', 'playing'):
                    self.state = event
                elif event == 'completed':
                    self.completed = args[0]
                elif event in ('move', 'waiting_entry', 'waiting_board', 'waiting_result', 'refilling', 'error'):
                    self.detail_event = (event, *args)
                    if event == 'error':
                        self.state = 'stopped'
                self.refresh()
        except Empty:
            pass
        if self.worker is not None and not self.worker.is_alive():
            self.worker = None
            self.refresh()
        if self.closing and self.worker is None:
            self.root.destroy()
            return
        if not self.smoke and self.shortcuts:
            pressed = tuple(shortcut_down(shortcut) for shortcut in self.shortcuts)
            start, stop = (now and not before for now, before in zip(pressed, self.held))
            self.held = pressed
            if not self.capturing and not self.help_dialog and not self.closing:
                if stop:
                    self.stop()
                elif start:
                    self.start(from_shortcut=True)
        self.root.after(50, self.poll)

    def show_help(self):
        if self.help_dialog is not None:
            self.help_dialog.lift()
            return
        dialog = self.help_dialog = tk.Toplevel(self.root)
        dialog.title(self.text['limit'])
        panel = ttk.Frame(dialog, padding=self.px(16))
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text=self.text['help'], wraplength=self.px(280), justify='left').pack(anchor='w')
        ttk.Button(panel, text=self.text['close'], command=self.close_help).pack(anchor='e', pady=(self.px(12), 0))
        dialog.protocol('WM_DELETE_WINDOW', self.close_help)
        dialog.bind('<Escape>', lambda _event: self.close_help())

    def close_help(self):
        if self.help_dialog is not None:
            self.help_dialog.destroy()
            self.help_dialog = None

    def close(self):
        self.closing = True
        self.close_help()
        self.stop()
