"""Embedded page for consecutive solo Puka Puka Fight matches."""

from queue import Empty, SimpleQueue
from threading import Event, Thread
import tkinter as tk
from tkinter import ttk

from holodori.app import family_theme
from holodori.global_hotkey import GlobalHotkey
from holodori.modules import BY_ID
from holodori.settings import parse_stop_hotkey
from pilot import run
from win_window import GameWindow, key


ACCENT = BY_ID['puka_puka'].accent
GAME_NAMES = {
    '繁體中文': '漂漂大亂鬥', 'English': 'Puka Puka Fight', '日本語': 'ぷかぷかファイト',
    '한국어': '둥실둥실 파이트', 'Indonesian': 'Puka Puka Fight', '简体中文': '浮排大战',
}
COPY = {
    '繁體中文': (
        '先進入{game}，再點擊「開始」',
        '局數上限', '已完成：{done} / {target} 局', '開始', '停止', '等待開始', '正在切換到遊戲…',
        '遊玩中', '正在停止', '已停止', '已達局數上限', '請輸入 1 至 9999 局。',
        '等待單人入口或關卡選單…', '等待棋盤…', '等待結算與領獎…',
        '落子 {moves}（{plies} 手）', '依照遊戲流程前進，兩種模式合計局數。', '關閉',
        '自動補充能量', '正在補充能量…', '無法註冊 {key}，請更換開始快捷鍵或點擊「開始」。',
        '估算走法 {moves}', '已確認對手落子'),
    'English': (
        'Open {game}, then click Start.',
        'Match limit', 'Completed: {done} / {target} rounds', 'Start', 'Stop', 'Ready', 'Switching to the game…',
        'Playing', 'Stopping', 'Stopped', 'Match limit reached', 'Enter 1 to 9999 matches.',
        'Waiting for the solo lobby or stage menu…', 'Waiting for the board…', 'Waiting for results and rewards…',
        'Move {moves} ({plies} plies)', 'The match limit applies across both modes.', 'Close',
        'Automatically refill energy', 'Refilling energy…', 'Could not register {key}. Choose another shortcut or click Start.',
        'Estimated best move {moves}', 'Confirmed the opponent’s move'),
    '日本語': (
        '「{game}」を開いてから「開始」をクリックしてください。',
        '対局数の上限', '完了：{done} / {target} 回', '開始', '停止', '待機中', 'ゲームに切り替え中…',
        '対局中', '停止中', '停止しました', '設定した対局数に到達', '1〜9999の対局数を入力してください。',
        'ソロ画面またはステージ選択を待機中…', '盤面を待機中…', '結果と報酬を待機中…',
        '着手 {moves}（{plies}手）', '対局数の上限は両モードの合計です。', '閉じる',
        'エネルギーを自動回復', 'エネルギーを回復中…', '{key} を登録できません。別のキーか開始ボタンを使ってください。',
        '探索で選んだ手 {moves}', '相手の着手を確認しました'),
    '한국어': (
        '{game}에 입장한 뒤 ‘시작’을 클릭하세요.',
        '대국 수 제한', '완료: {done} / {target} 라운드', '시작', '중지', '준비', '게임으로 전환 중…',
        '진행 중', '중지 중', '중지됨', '대국 수 제한에 도달', '1~9999 사이의 대국 수를 입력하세요.',
        '솔로 화면 또는 스테이지 선택 대기 중…', '게임판 대기 중…', '결과 및 보상 대기 중…',
        '착수 {moves} ({plies}수)', '두 모드의 대국 수를 합산합니다.', '닫기',
        '에너지 자동 충전', '에너지 충전 중…', '{key} 등록 실패. 다른 단축키나 시작 버튼을 사용하세요.',
        '탐색으로 고른 수 {moves}', '상대의 착수를 확인했습니다'),
    'Indonesian': (
        'Buka {game}, lalu klik Mulai.',
        'Batas pertandingan', 'Selesai: {done} / {target} ronde', 'Mulai', 'Berhenti', 'Siap', 'Beralih ke game…',
        'Sedang bermain', 'Menghentikan', 'Berhenti', 'Batas pertandingan tercapai', 'Masukkan 1 hingga 9999 pertandingan.',
        'Menunggu lobi solo atau menu level…', 'Menunggu papan…', 'Menunggu hasil dan hadiah…',
        'Langkah {moves} ({plies} giliran)', 'Batas dihitung untuk kedua mode.', 'Tutup',
        'Isi ulang energi otomatis', 'Mengisi ulang energi…', 'Tidak dapat mendaftarkan {key}. Gunakan pintasan lain atau klik Mulai.',
        'Perkiraan langkah terbaik {moves}', 'Langkah lawan terkonfirmasi'),
    '简体中文': (
        '先进入{game}，再点击「开始」',
        '局数上限', '已完成：{done} / {target} 局', '开始', '停止', '等待开始', '正在切换到游戏…',
        '游玩中', '正在停止', '已停止', '已达局数上限', '请输入 1 至 9999 局。',
        '等待单人入口或关卡菜单…', '等待棋盘…', '等待结算和领奖…',
        '落子 {moves}（{plies} 手）', '按游戏进度推进，两种模式合计局数。', '关闭',
        '自动补充能量', '正在补充能量…', '无法注册 {key}，请更换开始快捷键或点击「开始」。',
        '估算走法 {moves}', '已确认对手落子'),
}
TEXT_FIELDS = ('instructions', 'limit', 'progress', 'start', 'stop', 'ready', 'starting',
               'playing', 'stopping', 'stopped', 'finished', 'invalid',
               'waiting_entry', 'waiting_board', 'waiting_result', 'move', 'help', 'close',
               'auto_refill', 'refilling', 'shortcut_unavailable', 'estimated_move', 'reply')


def match_limit(value):
    if not value.isascii() or not value.isdecimal() or len(value) > 4 or not 1 <= int(value) <= 9999:
        raise ValueError('Expected a match limit from 1 to 9999')
    return int(value)


def shortcut_down(shortcut):
    modifiers, keycode = shortcut
    return bool(key(keycode) & 0x8000) and all(key(modifier) & 0x8000 for modifier in modifiers)


def configure_card_checkbox(theme):
    style = theme.style
    surface = style.lookup('Card.TFrame', 'background')

    def indicator(selected=False, disabled=False):
        def paint(draw, size, _unit):
            w, h = size
            unit = w/18
            fill = '#E5E5E5' if disabled else ACCENT if selected else surface
            border = fill if selected or disabled else '#D1D1D1'
            draw.rounded_rectangle((unit, unit, w-unit, h-unit), radius=3*unit,
                                   fill=fill, outline=border, width=round(unit))
            if selected:
                draw.line([(w*.25, h*.5), (w*.43, h*.68), (w*.76, h*.32)],
                          fill='#A0A0A0' if disabled else '#FFFFFF', width=round(unit*1.5))
        return theme.raster((18, 18), paint)

    style.element_create('Puka.check', 'image', indicator(),
                         ('disabled', 'selected', indicator(True, True)),
                         ('disabled', indicator(disabled=True)), ('selected', indicator(True)), sticky='')
    style.layout('Card.TCheckbutton', [('Checkbutton.padding', {'sticky': 'nswe', 'children': [
        ('Puka.check', {'side': 'left'}), ('Checkbutton.focus', {'side': 'left', 'sticky': 'nswe',
         'children': [('Checkbutton.label', {'sticky': 'nswe'})]})]})])
    style.configure('Card.TCheckbutton', background=surface, padding=0,
                    indicatormargin=(0, 0, theme.px(6), 0))
    style.map('Card.TCheckbutton', background=[('disabled', surface), ('active', surface)],
              foreground=[('disabled', '#A0A0A0')])


def configure_start_button(theme):
    style = theme.style
    background = style.lookup('Primary.TButton', 'background')
    [(_, layout)] = style.layout('Primary.TButton')

    def tile(fill, border=None):
        return theme.rounded(fill, border or fill, 6, background)

    style.element_create('Puka.start', 'image', tile(ACCENT),
                         ('disabled', tile('#F0F0F0', '#EEEEEE')),
                         ('pressed', tile('#0C6168')), ('active', tile('#0E7077')),
                         ('focus', tile(ACCENT, '#084A50')), border=theme.px(6),
                         width=theme.px(17), height=theme.px(17), sticky='nswe')
    style.layout('Puka.Primary.TButton', [('Puka.start', layout)])


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
        self.stop_shortcut = None
        self.stop_held = False
        self.start_generation = 0
        self.start_listener = None
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
        self.main.rowconfigure(3, weight=1)
        self.instructions = ttk.Label(root)
        self.status = tk.Label(root, fg=ACCENT)

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
                             ('focus', round_field('#FFFFFF', ACCENT, 4, '#FFFFFF')),
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
        configure_card_checkbox(self.theme)
        self.refill_checkbox = ttk.Checkbutton(settings, style='Card.TCheckbutton', variable=self.auto_refill)
        self.refill_checkbox.grid(row=1, column=0, columnspan=3, sticky='w', pady=(self.px(6), 0))

        progress = ttk.Frame(self.main, style='Card.TFrame', padding=self.px(16))
        progress.grid(row=0, column=0, sticky='ew', pady=(0, self.px(12)))
        progress.columnconfigure(0, weight=1)
        self.count_label = ttk.Label(progress, style='Count.TLabel', justify='left')
        self.count_label.grid(row=0, column=0, sticky='ew')
        progress.bind('<Configure>', lambda event: self.count_label.configure(
            wraplength=max(1, event.width-self.px(32))))

        controls = ttk.Frame(self.main)
        controls.grid(row=2, column=0, sticky='ew')
        controls.columnconfigure((0, 1), weight=1, uniform='puka')
        configure_start_button(self.theme)
        self.start_button = ttk.Button(controls, style='Puka.Primary.TButton', command=self.start,
                                       image=(self.theme.play_icons['normal'], 'disabled', self.theme.play_icons['disabled']),
                                       compound='left')
        self.start_button.grid(row=0, column=0, sticky='nsew', padx=(0, self.px(6)))
        self.stop_button = ttk.Button(controls, style='Secondary.TButton', command=self.stop,
                                      image=(self.theme.stop_icons['normal'], 'disabled', self.theme.stop_icons['disabled']),
                                      compound='left')
        self.stop_button.grid(row=0, column=1, sticky='nsew', padx=(self.px(6), 0))

        log_card = ttk.Frame(self.main, style='Card.TFrame', padding=self.px(12))
        log_card.grid(row=3, column=0, sticky='nsew', pady=(self.px(12), 0))
        self.log = tk.Text(log_card, height=1, width=1, wrap='word', state='disabled',
                           bg='#FFFFFF', fg='#242424', font=('Segoe UI', 10), relief='flat',
                           borderwidth=0, highlightthickness=0, padx=self.px(4), pady=self.px(4),
                           spacing3=self.px(4))
        scroll = ttk.Scrollbar(log_card, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y', padx=(self.px(8), 0))
        self.log.pack(fill='both', expand=True)

        self.rounds.trace_add('write', lambda *_: self.refresh())
        self.translate()
        root.protocol('WM_DELETE_WINDOW', self.close)
        if not self.smoke:
            self.start_listener = GlobalHotkey(
                lambda: self.messages.put(('start_shortcut', self.start_generation)),
                lambda value, ok, _error: self.messages.put(
                    ('shortcut_status', self.start_generation, value, ok)),
            )
            self.start_listener.configure(enabled=False)
            self.start_listener.start()
        root.after(50, self.poll)

    def translate(self):
        language = self.language.get()
        self.text = dict(zip(TEXT_FIELDS, COPY[language]))
        self.instructions.configure(text=self.text['instructions'].format(game=GAME_NAMES[language]))
        self.limit_label.configure(text=self.text['limit'])
        self.refill_checkbox.configure(text=self.text['auto_refill'])
        self.start_button.configure(text=self.text['start'])
        self.stop_button.configure(text=self.text['stop'])
        self.refresh()

    def refresh(self):
        self.status.configure(text=self.text[self.state])
        goal = self.target if self.target is not None else self.rounds.get() or '–'
        self.count_label.configure(text=self.text['progress'].format(done=self.completed, target=goal))
        active = self.worker is not None
        self.entry.configure(state='disabled' if active else 'normal')
        self.refill_checkbox.configure(state='disabled' if active else 'normal')
        self.start_button.configure(state='disabled' if active or self.smoke else 'normal')
        self.stop_button.configure(state='normal' if active and not self.stop_event.is_set() else 'disabled')

    def log_event(self, event, *args):
        if event == 'error':
            message = args[0]
        elif event == 'move':
            template = 'estimated_move' if args[1] is None else 'move'
            message = self.text[template].format(moves=args[0], plies=args[2])
        elif event == 'shortcut_status':
            message = self.text['shortcut_unavailable'].format(key=args[0])
        elif event == 'completed':
            message = self.text['progress'].format(done=args[0], target=args[1])
        elif event == 'reply':
            message = f"{self.text['reply']}  {args[1]}".rstrip()
        else:
            message = self.text[event]

        self.log.configure(state='normal')
        self.log.insert('end', message + '\n')
        if int(self.log.index('end-1c').split('.')[0]) > 500:
            self.log.delete('1.0', '101.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def configure_start_shortcut(self):
        if self.start_listener is not None:
            enabled = not (self.closing or self.capturing or self.help_dialog or self.worker)
            self.start_listener.configure(value=self.start_key.get(), enabled=enabled)

    def begin_capture(self):
        self.capturing = True
        self.start_generation += 1
        self.configure_start_shortcut()

    def end_capture(self):
        self.stop_shortcut = parse_stop_hotkey(self.stop_key.get())
        if not self.smoke:
            self.stop_held = shortcut_down(self.stop_shortcut)
        self.capturing = False
        self.configure_start_shortcut()

    def start(self):
        if self.worker is not None or self.smoke or self.closing or self.capturing or self.help_dialog:
            return
        try:
            target = match_limit(self.rounds.get().strip())
        except ValueError:
            self.log_event('invalid')
            return
        self.completed, self.target = 0, target
        self.stop_event.clear()
        self.state = 'starting'
        self.log_event('starting')
        self.worker = Thread(target=self.play, args=(target,),
                             kwargs={'auto_refill': self.auto_refill.get()}, name='puka-puka-play')
        self.start_generation += 1
        self.configure_start_shortcut()
        self.worker.start()
        self.refresh()

    def play(self, target, *, auto_refill):
        def notify(kind, *args):
            self.messages.put((kind, *args))

        try:
            game = GameWindow(self.stop_event.is_set)
            notify('playing')
            run(game, target, notify, auto_refill=auto_refill)
        except InterruptedError:
            notify('stopped')
        except Exception as error:
            notify('error', str(error) or type(error).__name__)
        else:
            notify('finished')

    def stop(self):
        if self.worker is not None and not self.stop_event.is_set():
            self.stop_event.set()
            self.state = 'stopping'
            self.log_event('stopping')
            self.refresh()

    def poll(self):
        start_requested = False
        try:
            while True:
                event, *args = self.messages.get_nowait()
                if event == 'start_shortcut':
                    start_requested |= args[0] == self.start_generation
                    continue
                if event == 'shortcut_status':
                    generation, value, ok = args
                    if (not ok and generation == self.start_generation and value == self.start_key.get()
                            and not (self.capturing or self.help_dialog or self.closing or self.worker)):
                        self.log_event(event, value)
                    continue
                if event in ('finished', 'stopped', 'playing'):
                    self.state = event
                elif event == 'completed':
                    self.completed = args[0]
                elif event == 'error':
                    self.state = 'stopped'
                self.log_event(event, *args)
                self.refresh()
        except Empty:
            pass
        if self.worker is not None and not self.worker.is_alive():
            self.worker = None
            self.configure_start_shortcut()
            self.refresh()
        if self.closing and self.worker is None:
            self.root.destroy()
            return
        if not self.smoke and self.stop_shortcut:
            pressed = shortcut_down(self.stop_shortcut)
            stop_requested = pressed and not self.stop_held
            self.stop_held = pressed
            if not (self.capturing or self.help_dialog or self.closing):
                if stop_requested:
                    self.stop()
                elif start_requested:
                    self.start()
        self.root.after(50, self.poll)

    def show_help(self):
        if self.help_dialog is not None:
            self.help_dialog.lift()
            return
        dialog = self.help_dialog = tk.Toplevel(self.root)
        self.start_generation += 1
        self.configure_start_shortcut()
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
            self.configure_start_shortcut()

    def close(self):
        self.closing = True
        if self.start_listener is not None:
            self.start_listener.close()
        self.close_help()
        self.stop()
