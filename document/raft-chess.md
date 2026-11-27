# Raft Chess / 浮台棋

The Raft Chess feature is implemented in [`components/puka_puka`](../components/puka_puka). Its navigation label and the in-game name used in the instructions are localized independently.

- `win_window.py` verifies the foreground game process and keeps the client geometry fixed while capturing or clicking. The Start shortcut activates the game before capture. It restores a minimized game with Windows and checks that its client is visible in a supported 16:9 layout.
- `stages.py` identifies the solo lobby, stage cards, results, rewards, event settlement pages and the energy dialog from visual controls. Normal and Challenge both start from the center card once the game makes it available. The event page uses the common Next button and settlement controls. A refill requires the user to enable the checkbox and the panel to show the default one-item selection.
- `vision.py` checks raft edges to distinguish three- and four-row boards when entering a match. The confirmed row count supplies the geometry for both the ordinary and selected views until that match ends. Raft colors, edge patterns and hat shapes identify pieces. A warning banner can cover the back-row hats, so reading resumes when it clears. During play, the reader compares observations with legal replies and observed reserves. It can retain one temporarily hidden piece in an unchanged square. A relocation needs visible evidence at its destination and a deployment also needs the matching reserve to disappear.
- `pilot.py` revalidates the confirmed position before selecting a piece and waits for the correct selection and destination highlight before clicking. A missed source click can be retried once after verifying the same position. Wins, draws and losses all complete the result flow and count toward the selected match limit.
- `solver.py` uses the same rules for both board sizes. The public Animal Shogi tablebase covers eligible standard eight-piece positions on the three-row board. The request contains the abstract board, reserves and side to move. Local search handles four-row boards and positions without a tablebase result. When it cannot prove an outcome, the program uses the best move from its last completed depth-limited search and displays it as an estimate.

```powershell
python -m unittest discover -s tests -p 'test_puka*.py' -v
```

When diagnosing a pause, capture the game and the program's status together. Include the feature version, game language, resolution and display scale. Replays and fixtures can exercise recognition without clicking the game.

Use `python tools/calibrate_raft_hats.py <annotated-captures.npz>` to regenerate the compact hat references from labeled square crops. The tool writes silhouettes and highlight descriptors.
