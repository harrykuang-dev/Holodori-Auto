"""Validate and stabilize challenge OCR before any strategy sees a number."""

PRIZES = (200, 400, 700, 800, 1500, 3000, 7000, 10000)


def valid_next_reward(value):
    return any(value == prize * 2**n for prize in PRIZES for n in range(1, 33))


class ChallengeRewardReader:
    def __init__(self):
        self.reset_round()

    def reset_round(self):
        self.last = None
        self.reset_prompt()

    def reset_prompt(self):
        self.started = self.candidate = self.since = None
        self.samples = 0

    def observe(self, value, now):
        if self.started is None:
            self.started = now
        plausible = valid_next_reward(value)
        if self.last is not None:
            plausible = plausible and value in (self.last, self.last * 2)
        if not plausible:
            self.candidate = self.since = None
            self.samples = 0
        elif self.candidate != value:
            self.candidate, self.since, self.samples = value, now, 1
        else:
            self.samples += 1
        if self.samples >= 2 and now - self.since >= .25:
            self.last = value
            return value
        if now - self.started >= 8:
            raise RuntimeError('挑战奖金无法确认，已停止。不会用错误金额或默认金额决定翻倍，请核对游戏画面。')
        return None
