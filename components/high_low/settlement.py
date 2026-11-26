"""Confirm result amounts after the count-up animation, without game strategy."""


class SettlementReader:
    def __init__(self):
        self.reset()

    def reset(self):
        self.started = None
        self.candidate = None
        self.since = None
        self.samples = 0

    def observe(self, amount, now, expected=None):
        if self.started is None:
            self.started = now
        # Never reuse samples collected during the initial animation window.
        if (now - self.started < 1.5 or amount <= 0
                or (expected is not None and amount != expected)):
            self.candidate = self.since = None
            self.samples = 0
        elif amount != self.candidate:
            self.candidate, self.since, self.samples = amount, now, 1
        else:
            self.samples += 1
        if self.samples >= 3 and now - self.since >= .6:
            return self.candidate
        if now - self.started >= 8:
            raise RuntimeError('结算金额未能稳定确认，已停止且未将此笔入账。请核对结算画面与今日累计。')
        return None
