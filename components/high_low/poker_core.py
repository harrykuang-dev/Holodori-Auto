from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numba import njit

ENTRY_FEE = 50.0
ENGINE_VERSION = "1.0.0"
CATEGORY_NAMES = (
    "未中奖／一对",
    "两对",
    "三条",
    "顺子",
    "同花",
    "葫芦",
    "四条",
    "同花顺",
    "五条",
    "皇家同花顺",
)
PRIZES = np.array([0, 200, 200, 400, 700, 800, 1500, 3000, 7000, 10000], dtype=np.int64)
RANK_LABELS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
SUIT_SYMBOLS = ("♠", "♥", "♦", "♣")
SUIT_NAMES = ("黑桃", "红桃", "方块", "梅花")

# 0..51：普通牌，点数优先、花色次序 ♠♥♦♣；52：王。
JOKER_ID = 52


@dataclass(frozen=True)
class StrategyResult:
    mask: int
    held_indices: tuple[int, ...]
    discarded_indices: tuple[int, ...]
    total_outcomes: int
    category_counts: tuple[int, ...]
    win_probability: float
    expected_payout: float
    expected_net: float
    return_rate: float


def card_id(rank: str, suit: str) -> int:
    if rank.upper() in {"JOKER", "王"}:
        return JOKER_ID
    rank = rank.upper()
    suit = suit.upper()
    return RANK_LABELS.index(rank) * 4 + ("S", "H", "D", "C").index(suit)


def card_text(cid: int) -> str:
    if cid == JOKER_ID:
        return "王"
    return f"{SUIT_SYMBOLS[cid % 4]}{RANK_LABELS[cid // 4]}"


def card_text_console(cid: int) -> str:
    """ASCII-safe card label for Windows consoles using legacy code pages."""
    if cid == JOKER_ID:
        return "JOKER"
    return f"{('S', 'H', 'D', 'C')[cid % 4]}{RANK_LABELS[cid // 4]}"


@njit(cache=False)
def _evaluate_category5(c0: int, c1: int, c2: int, c3: int, c4: int) -> int:
    cards = (c0, c1, c2, c3, c4)
    rank_counts = np.zeros(15, dtype=np.int8)
    suit_counts = np.zeros(4, dtype=np.int8)
    jokers = 0
    ordinary_count = 0
    rank_mask = 0

    for cid in cards:
        if cid == 52:
            jokers += 1
        else:
            rank = 2 + cid // 4
            suit = cid % 4
            rank_counts[rank] += 1
            suit_counts[suit] += 1
            rank_mask |= 1 << rank
            ordinary_count += 1

    unique_ranks = 0
    max_count = 0
    pair_ranks = 0
    singleton_ranks = 0
    has_three = False
    has_two = False
    for r in range(2, 15):
        count = int(rank_counts[r])
        if count:
            unique_ranks += 1
            if count > max_count:
                max_count = count
            if count >= 2:
                pair_ranks += 1
            if count == 1:
                singleton_ranks += 1
            if count == 3:
                has_three = True
            if count == 2:
                has_two = True

    flush_possible = False
    for s in range(4):
        if int(suit_counts[s]) + jokers == 5:
            flush_possible = True
            break

    straight_possible = False
    if unique_ranks == ordinary_count and unique_ranks + jokers == 5:
        # A2345
        target = (1 << 14) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)
        if rank_mask & ~target == 0:
            straight_possible = True
        if not straight_possible:
            for low in range(2, 11):
                target = 0
                for r in range(low, low + 5):
                    target |= 1 << r
                if rank_mask & ~target == 0:
                    straight_possible = True
                    break

    royal_mask = (1 << 10) | (1 << 11) | (1 << 12) | (1 << 13) | (1 << 14)
    if flush_possible and unique_ranks == ordinary_count and unique_ranks + jokers == 5:
        if rank_mask & ~royal_mask == 0:
            return 9

    if jokers > 0 and max_count + jokers >= 5:
        return 8
    if flush_possible and straight_possible:
        return 7
    if max_count + jokers >= 4:
        return 6

    if jokers == 0:
        if has_three and has_two:
            return 5
    elif jokers == 1:
        first = 0
        second = 0
        for r in range(2, 15):
            count = int(rank_counts[r])
            if count > first:
                second = first
                first = count
            elif count > second:
                second = count
        if (first == 3 and second == 1) or (first == 2 and second == 2):
            return 5

    if flush_possible:
        return 4
    if straight_possible:
        return 3
    if max_count + jokers >= 3:
        return 2
    if pair_ranks >= 2 or (jokers == 1 and pair_ranks >= 1 and singleton_ranks >= 1):
        return 1
    return 0


@njit(cache=False)
def _record(cards: np.ndarray, counts: np.ndarray) -> tuple[int, int]:
    category = _evaluate_category5(cards[0], cards[1], cards[2], cards[3], cards[4])
    counts[category] += 1
    return int(PRIZES[category]), 1 if category > 0 else 0


@njit(cache=False)
def _evaluate_mask(initial: np.ndarray, mask: int, standard_mode: bool):
    held = np.empty(5, dtype=np.int16)
    held_count = 0
    for i in range(5):
        if mask & (1 << i):
            held[held_count] = initial[i]
            held_count += 1

    excluded = np.zeros(53, dtype=np.uint8)
    if standard_mode:
        for i in range(5):
            excluded[initial[i]] = 1
    else:
        for i in range(held_count):
            excluded[held[i]] = 1

    pool = np.empty(53, dtype=np.int16)
    pool_count = 0
    for cid in range(53):
        if excluded[cid] == 0:
            pool[pool_count] = cid
            pool_count += 1

    cards = np.empty(5, dtype=np.int16)
    for i in range(held_count):
        cards[i] = held[i]

    draw_count = 5 - held_count
    counts = np.zeros(10, dtype=np.int64)
    payout_sum = np.int64(0)
    wins = np.int64(0)
    total = np.int64(0)

    if draw_count == 0:
        p, w = _record(cards, counts)
        payout_sum += p
        wins += w
        total += 1
    elif draw_count == 1:
        for a in range(pool_count):
            cards[held_count] = pool[a]
            p, w = _record(cards, counts)
            payout_sum += p
            wins += w
            total += 1
    elif draw_count == 2:
        for a in range(pool_count - 1):
            cards[held_count] = pool[a]
            for b in range(a + 1, pool_count):
                cards[held_count + 1] = pool[b]
                p, w = _record(cards, counts)
                payout_sum += p
                wins += w
                total += 1
    elif draw_count == 3:
        for a in range(pool_count - 2):
            cards[held_count] = pool[a]
            for b in range(a + 1, pool_count - 1):
                cards[held_count + 1] = pool[b]
                for c in range(b + 1, pool_count):
                    cards[held_count + 2] = pool[c]
                    p, w = _record(cards, counts)
                    payout_sum += p
                    wins += w
                    total += 1
    elif draw_count == 4:
        for a in range(pool_count - 3):
            cards[held_count] = pool[a]
            for b in range(a + 1, pool_count - 2):
                cards[held_count + 1] = pool[b]
                for c in range(b + 1, pool_count - 1):
                    cards[held_count + 2] = pool[c]
                    for d in range(c + 1, pool_count):
                        cards[held_count + 3] = pool[d]
                        p, w = _record(cards, counts)
                        payout_sum += p
                        wins += w
                        total += 1
    else:
        for a in range(pool_count - 4):
            cards[0] = pool[a]
            for b in range(a + 1, pool_count - 3):
                cards[1] = pool[b]
                for c in range(b + 1, pool_count - 2):
                    cards[2] = pool[c]
                    for d in range(c + 1, pool_count - 1):
                        cards[3] = pool[d]
                        for e in range(d + 1, pool_count):
                            cards[4] = pool[e]
                            p, w = _record(cards, counts)
                            payout_sum += p
                            wins += w
                            total += 1

    return total, payout_sum, wins, counts


@njit(cache=False)
def _all_strategies(initial: np.ndarray, standard_mode: bool):
    totals = np.zeros(32, dtype=np.int64)
    payouts = np.zeros(32, dtype=np.int64)
    wins = np.zeros(32, dtype=np.int64)
    distributions = np.zeros((32, 10), dtype=np.int64)
    for mask in range(32):
        total, payout, win, counts = _evaluate_mask(initial, mask, standard_mode)
        totals[mask] = total
        payouts[mask] = payout
        wins[mask] = win
        distributions[mask, :] = counts
    return totals, payouts, wins, distributions


def calculate_best(cards: Sequence[int], draw_mode: str = "standard") -> tuple[StrategyResult, list[StrategyResult]]:
    if len(cards) != 5:
        raise ValueError("必须正好输入5张牌。")
    if len(set(cards)) != 5:
        raise ValueError("检测到重复牌。")
    if sum(1 for c in cards if c == JOKER_ID) > 1:
        raise ValueError("这套规则只有1张王。")
    if any(c < 0 or c > 52 for c in cards):
        raise ValueError("牌ID超出范围。")

    initial = np.asarray(cards, dtype=np.int16)
    standard_mode = draw_mode.lower() == "standard"
    totals, payouts, wins, distributions = _all_strategies(initial, standard_mode)

    results: list[StrategyResult] = []
    for mask in range(32):
        total = int(totals[mask])
        expected_payout = float(payouts[mask]) / total
        held = tuple(i for i in range(5) if mask & (1 << i))
        discarded = tuple(i for i in range(5) if not (mask & (1 << i)))
        result = StrategyResult(
            mask=mask,
            held_indices=held,
            discarded_indices=discarded,
            total_outcomes=total,
            category_counts=tuple(int(x) for x in distributions[mask]),
            win_probability=float(wins[mask]) / total,
            expected_payout=expected_payout,
            expected_net=expected_payout - ENTRY_FEE,
            return_rate=expected_payout / ENTRY_FEE,
        )
        results.append(result)

    results.sort(
        key=lambda r: (r.expected_payout, r.win_probability, -len(r.held_indices)),
        reverse=True,
    )
    return results[0], results



def verify_engine() -> None:
    """Fail fast if the optimizer is stale or returns a non-maximal strategy."""
    tests = [
        (
            [card_id("2", "S"), card_id("7", "S"), card_id("9", "D"), card_id("6", "D"), card_id("9", "S")],
            (2, 4),
            84.78839037927844,
        ),
        (
            [card_id("10", "S"), card_id("5", "D"), card_id("2", "S"), card_id("Q", "C"), card_id("A", "C")],
            (3, 4),
            29.914431082331173,
        ),
    ]
    for cards, expected_hold, expected_payout in tests:
        best, all_results = calculate_best(cards, "standard")
        independently_best = max(
            all_results,
            key=lambda r: (r.expected_payout, r.win_probability, -len(r.held_indices)),
        )
        if best != independently_best:
            raise RuntimeError("策略排序自检失败：返回结果不是最高数学期望。")
        if best.held_indices != expected_hold:
            raise RuntimeError(
                f"策略引擎自检失败：{tuple(card_text(c) for c in cards)} "
                f"应保留{expected_hold}，实际为{best.held_indices}。"
            )
        if abs(best.expected_payout - expected_payout) > 1e-9:
            raise RuntimeError(
                f"策略引擎自检失败：期望返奖应为{expected_payout:.12f}，"
                f"实际为{best.expected_payout:.12f}。"
            )

    # Explicitly verify that the zero-card hold (replace all five cards) is
    # present and evaluated. Standard draw excludes the original five cards,
    # so it must enumerate C(48, 5) = 1,712,304 possible replacement hands.
    audit_hand = [
        card_id("2", "S"), card_id("5", "H"), card_id("8", "D"),
        card_id("J", "C"), card_id("A", "S"),
    ]
    _, audit_results = calculate_best(audit_hand, "standard")
    all_change = next((r for r in audit_results if r.mask == 0), None)
    if all_change is None:
        raise RuntimeError("策略引擎自检失败：32种方案中缺少‘全部更换’。")
    if all_change.held_indices != () or all_change.discarded_indices != (0, 1, 2, 3, 4):
        raise RuntimeError("策略引擎自检失败：‘全部更换’的留牌索引错误。")
    if all_change.total_outcomes != 1712304:
        raise RuntimeError(
            f"策略引擎自检失败：‘全部更换’应枚举1712304种结果，"
            f"实际为{all_change.total_outcomes}。"
        )


def warm_up() -> None:
    # v2.0 intentionally disables Numba disk caching. This prevents an old
    # compiled evaluator/paytable from surviving when users overwrite a prior
    # version in the same folder. Compile once in memory, then run self-tests.
    calculate_best([card_id("2", "S"), card_id("5", "H"), card_id("8", "D"), card_id("J", "C"), card_id("A", "S")])
    verify_engine()
