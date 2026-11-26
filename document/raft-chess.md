# Raft Chess / 浮台棋

The Raft Chess feature is implemented in [`components/puka_puka`](../components/puka_puka). Its navigation label and the in-game name used in the instructions are localized independently.

- `win_window.py` verifies the foreground game process and keeps the client geometry fixed while capturing or clicking. The Start shortcut activates the game before capture. It restores a minimized game with Windows and checks that its client is visible in a supported 16:9 layout.
- `stages.py` identifies the solo lobby, stage cards, results, rewards, event settlement pages and the energy dialog from visual controls. Normal and Challenge both start from the center card once the game makes it available. The event page uses the common Next button and settlement controls. A refill requires the user to enable the checkbox and the panel to show the default one-item selection.
- `vision.py` combines raft colors and edge patterns with hat shapes. A wide whale crop can confirm an occupied raft when its markings agree with the hat type. During play, it compares the observations with legal replies and the observed reserves. It can retain one temporarily hidden piece in an unchanged square. A relocation needs visible evidence at its destination and a deployment also needs the matching reserve to disappear.
- `pilot.py` revalidates the confirmed position before selecting a piece and waits for the correct selection and destination highlight before clicking. A missed source click can be retried once after verifying the same position. Wins, draws and losses all complete the result flow and count toward the selected match limit.
- `solver.py` checks for provable moves and can use the public Animal Shogi tablebase for standard eight-piece positions. The request contains the abstract board, reserves and side to move. When neither source proves an outcome, the program uses the best move from its last completed depth-limited search. These moves are shown as estimates.

```powershell
python -m unittest discover -s tests -p 'test_puka*.py' -v
```

When diagnosing a pause, capture the game and the program's status together. Include the feature version, game language, resolution and display scale. Replays and fixtures can exercise recognition without clicking the game.

Use `python tools/calibrate_raft_hats.py <annotated-captures.npz>` to regenerate the compact hat references from labeled square crops. The tool writes silhouettes and highlight descriptors.
