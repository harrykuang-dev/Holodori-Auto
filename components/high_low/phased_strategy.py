"""Three phases driven by confirmed wins, never by ongoing reward OCR."""
from challenge_reward import PRIZES


class PhasedStrategy:
    def __init__(self, stage=0):
        if type(stage) is not int or not 0 <= stage <= 3:
            raise ValueError('Invalid saved strategy stage')
        self.stage = stage
        self.reset_round()

    @property
    def complete(self):
        return self.stage == 3

    def reset_round(self):
        self.base_cash = None
        self.successes = 0
        self.pending_guess = False
        self.target_wins = None
        self.settling = False

    def start_round(self, base_cash, coins):
        if base_cash not in PRIZES:
            raise ValueError('Unconfirmed initial poker reward')
        if self.base_cash is not None:
            return
        self.base_cash = base_cash
        if self.stage == 1:
            candidates = [n for n in range(32) if coins + base_cash * 2**n < 20000]
            if not candidates:
                raise RuntimeError('本局起手奖金已无法保留第三阶段，请手动处理。')
            self.target_wins = min(candidates, key=lambda n: (abs(base_cash * 2**n - 6400), n))

    @property
    def expected_cash(self):
        return None if self.base_cash is None else self.base_cash * 2**self.successes

    def guess_clicked(self):
        if self.base_cash is None:
            raise RuntimeError('尚未确认本局起手奖励，无法安全计数。请从新一局开始。')
        self.pending_guess = True

    def confirm_success(self):
        # Repeated success frames and repeated clicks consume one pending guess.
        if self.pending_guess:
            self.successes += 1
            self.pending_guess = False

    def begin_settlement(self, cashout_requested):
        if not self.settling:
            # At the game limit, the final win leads straight to RESULT.
            if not cashout_requested:
                self.confirm_success()
            self.settling = True

    def decide(self):
        if self.complete:
            return 'stop'
        if self.base_cash is None:
            raise RuntimeError('尚未确认本局起手奖励。')
        if self.stage == 1 and self.successes >= self.target_wins:
            return 'cashout'
        return 'challenge'

    def stage_after_credit(self, earned):
        # A confirmed successful settlement advances the phase independently
        # of the numeric target. The settlement reader verifies the amount.
        return min(3, self.stage + 1)
