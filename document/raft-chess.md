# Raft Chess / 浮台棋

The Raft Chess feature is implemented in [`components/puka_puka`](../components/puka_puka). Its navigation label and the in-game name used in the instructions are localized independently.

- `win_window.py` verifies the foreground game process and keeps the client geometry fixed while capturing or clicking. The Start shortcut activates the game before capture. It restores a minimized game with Windows and checks that its client is visible in a supported 16:9 layout.
- `stages.py` identifies the solo lobby, stage cards, results, rewards, event settlement pages and the energy dialog from visual controls. Normal and Challenge both start from the center card once the game makes it available. The event page uses the common Next button and settlement controls. A refill requires the user to enable the checkbox and the panel to show the default one-item selection.
- `vision.py` checks raft edges to distinguish three- and four-row boards when entering a match. The confirmed row count supplies the geometry for both the ordinary and selected views until that match ends. Hat shapes and the color and pattern of the raft markings identify pieces. The reader checks visible white edges when nearby art overlaps an empty raft and uses matching colored marks to confirm clipped hats. A warning banner can cover the back row, so reading resumes when it clears.
- `hat_side_model.py` uses a small CPU model to resolve an uncertain side for a known non-leader hat on a direct board read. Agreeing raft markings and hat profiles take priority. Reply tracking compares observations with legal replies and visible reserves, and can retain one temporarily hidden piece in an unchanged square. A relocation needs visible evidence at its destination and a deployment also needs the matching reserve to disappear.
- `pilot.py` waits for a stable re-read of the confirmed position before selecting a piece and checks the selection and destination highlight before clicking. A missed source click can be retried once after verifying the same position. Wins, draws and losses all complete the result flow and count toward the selected match limit.
- `puka_ui.py` displays the localized completed-round count and appends run events to the scrollable log below Start and Stop. The log stays in memory and clears when the feature closes.
- `solver.py` uses the same rules for both board sizes. The public Animal Shogi tablebase covers eligible standard eight-piece positions on the three-row board. The request contains the abstract board, reserves and side to move. Local search handles four-row boards and positions without a tablebase result. When it cannot prove an outcome, the program uses the best move from its last completed depth-limited search and displays it as an estimate.

```powershell
python -m unittest discover -s tests -p 'test_puka*.py' -v
```

For a recognition report, include the full game window with reserves visible and the last lines of the run log. For a pause after a move or screen transition, include a short recording from the last action to the pause. Recordings and snapshots are collected manually. Replays and fixtures can exercise recognition without clicking the game.

Use `python tools/calibrate_raft_hats.py <annotated-captures.npz>` to regenerate the compact hat references from labeled square crops. The tool writes silhouettes and highlight descriptors.

## 繁體中文

- 浮台棋在進入對局時確認三排或四排，並沿用該尺寸至本局結束。辨識依據包括棋帽的形狀、朝向，以及浮台標記的顏色和圖案。空白浮台會檢查可見白邊，帽子遭遮擋時會比對可見的同陣營標記。一般讀盤遇到棋種已確認、陣營不明的非隊長棋子時，可用本機模型輔助判斷。
- 對手回應依合法走法與畫面中的候補棋子核對。落子前會重讀棋盤，畫面穩定後再確認選子和落點高亮。勝、和、負都會在結算後計入局數上限。
- 開始與停止按鈕下方的可捲動記錄會顯示落子、結算與錯誤。記錄只在記憶體中，關閉浮台棋即清空。辨識問題請提供含候補棋子的完整畫面與最後幾行記錄。若在落子或轉場後停住，短錄影從最後一次操作錄到停住即可。
