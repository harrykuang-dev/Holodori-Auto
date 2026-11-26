# Raft Chess / 浮台棋

The Raft Chess feature is implemented in [`components/puka_puka`](../components/puka_puka). Its navigation label and the in-game name used in the instructions are localized independently.

- `win_window.py` verifies the foreground game process and keeps the client geometry fixed while capturing or clicking. The Start shortcut activates the game before capture. It restores a minimized game with Windows and checks that its client is visible in a supported 16:9 layout.
- `stages.py` identifies the solo lobby, stage cards, results, rewards, event settlement pages and the energy dialog from visual controls. The event page uses the common Next button and settlement controls, so identifying it does not depend on event artwork or text. Normal stages take priority while available. A refill requires the user to enable the checkbox and the panel to show the default one-item selection.
- `vision.py` reads move diagrams, tile marks and hat colors. It uses the legal candidate set to reconcile partial observations and requires visible support at changed tiles.
- `pilot.py` revalidates the confirmed position before selecting a piece and waits for the correct selection and destination highlight before clicking. A missed source click can be retried once after verifying the same position.
- `solver.py` searches for proven moves locally. Standard eight-piece positions can also use the public Animal Shogi tablebase. The request contains the abstract board, reserves and side to move.

```powershell
python -m unittest discover -s tests -p 'test_puka*.py' -v
```

When diagnosing a pause, capture the game and the program's status together. Include the feature version, game language, resolution and display scale. Replays and fixtures can exercise recognition without clicking the game.
