from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp
import math

# ---------------- AI 胜率评估引擎 ----------------
class GomokuAI:
    PATTERN_SCORES = {
        'FIVE': 10000000,
        'LIVE_FOUR': 1000000,
        'RUSH_FOUR': 100000,
        'LIVE_THREE': 10000,
        'SLEEP_THREE': 1000,
        'LIVE_TWO': 1000,
        'SLEEP_TWO': 100,
        'LIVE_ONE': 10,
    }

    def __init__(self, board_size=15):
        self.board_size = board_size

    def _evaluate_direction(self, board, row, col, dr, dc, player):
        count_pos = 0
        r, c = row + dr, col + dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
            count_pos += 1
            r += dr
            c += dc
        pos_blocked = not (0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == 0)

        count_neg = 0
        r, c = row - dr, col - dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
            count_neg += 1
            r -= dr
            c -= dc
        neg_blocked = not (0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == 0)

        total = count_pos + count_neg + 1
        blocked = (1 if pos_blocked else 0) + (1 if neg_blocked else 0)
        return self._get_pattern_score(total, blocked)

    def _get_pattern_score(self, total, blocked):
        if total >= 5:
            return self.PATTERN_SCORES['FIVE']
        if total == 4:
            if blocked == 0:
                return self.PATTERN_SCORES['LIVE_FOUR']
            elif blocked == 1:
                return self.PATTERN_SCORES['RUSH_FOUR']
        if total == 3:
            if blocked == 0:
                return self.PATTERN_SCORES['LIVE_THREE']
            elif blocked == 1:
                return self.PATTERN_SCORES['SLEEP_THREE']
        if total == 2:
            if blocked == 0:
                return self.PATTERN_SCORES['LIVE_TWO']
            elif blocked == 1:
                return self.PATTERN_SCORES['SLEEP_TWO']
        if total == 1 and blocked == 0:
            return self.PATTERN_SCORES['LIVE_ONE']
        return 0

    def evaluate_board(self, board, for_player):
        total_score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] == for_player:
                    for dr, dc in directions:
                        pr, pc = row - dr, col - dc
                        if 0 <= pr < self.board_size and 0 <= pc < self.board_size and board[pr][pc] == for_player:
                            continue
                        total_score += self._evaluate_direction(board, row, col, dr, dc, for_player)
        return total_score

    def estimate_win_rate(self, board, row, col, player):
        board[row][col] = player
        if self._check_five(board, row, col, player):
            board[row][col] = 0
            return 1.0

        my_score = self.evaluate_board(board, player)
        opp_score = self.evaluate_board(board, 3 - player)

        my_pos = 0
        opp_pos = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            my_pos += self._evaluate_direction(board, row, col, dr, dc, player)
            opp_pos += self._evaluate_direction(board, row, col, dr, dc, 3 - player)

        board[row][col] = 0

        combined_my = my_score + my_pos * 0.5
        combined_opp = opp_score + opp_pos * 0.5
        diff = combined_my - combined_opp
        rate = 1 / (1 + math.exp(-diff / 50000))
        return max(0.05, min(0.95, rate))

    def _check_five(self, board, row, col, player):
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return True
        return False


# ---------------- 棋盘控件 ----------------
class BoardWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.BOARD_SIZE = 15
        self.board = [[0] * 15 for _ in range(15)]
        self.current_player = 1  # 1黑 2白
        self.game_over = False
        self.last_move = None
        self.winner_line = None
        self.ai = GomokuAI(15)
        self.hover_cell = None
        self.margin = dp(20)
        self.cell_size = 0
        self.board_pixel_size = 0
        self.offset_x = 0
        self.offset_y = 0

        self.bind(size=self.on_resize, pos=self.on_resize)

    def on_resize(self, *args):
        w = min(self.width, self.height)
        self.board_pixel_size = w - self.margin * 2
        self.cell_size = self.board_pixel_size / (self.BOARD_SIZE - 1)
        self.offset_x = (self.width - self.board_pixel_size) / 2
        self.offset_y = (self.height - self.board_pixel_size) / 2
        self.redraw()

    def cell_to_pixel(self, row, col):
        x = self.offset_x + col * self.cell_size
        y = self.height - (self.offset_y + row * self.cell_size)
        return x, y

    def pixel_to_cell(self, x, y):
        col = round((x - self.offset_x) / self.cell_size)
        row = round((self.height - y - self.offset_y) / self.cell_size)
        return row, col

    def reset(self):
        self.board = [[0] * 15 for _ in range(15)]
        self.current_player = 1
        self.game_over = False
        self.last_move = None
        self.winner_line = None
        self.hover_cell = None
        self.redraw()
        app = App.get_running_app()
        if app:
            app.update_status("当前：黑棋", (0, 0, 0, 1))
            app.update_win_rate(None)

    def redraw(self):
        self.canvas.clear()
        if self.cell_size <= 0:
            return

        with self.canvas:
            # 背景
            Color(0.87, 0.72, 0.53, 1)
            Rectangle(pos=self.pos, size=self.size)

            # 棋盘线
            Color(0, 0, 0, 1)
            for i in range(self.BOARD_SIZE):
                x1, y1 = self.cell_to_pixel(i, 0)
                x2, y2 = self.cell_to_pixel(i, self.BOARD_SIZE - 1)
                Line(points=[x1, y1, x2, y2], width=1.2)

                x1, y1 = self.cell_to_pixel(0, i)
                x2, y2 = self.cell_to_pixel(self.BOARD_SIZE - 1, i)
                Line(points=[x1, y1, x2, y2], width=1.2)

            # 星位
            star_points = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
            for r, c in star_points:
                x, y = self.cell_to_pixel(r, c)
                r_px = self.cell_size * 0.1
                Ellipse(pos=(x - r_px, y - r_px), size=(r_px * 2, r_px * 2))

            # 棋子
            piece_r = self.cell_size * 0.42
            for row in range(self.BOARD_SIZE):
                for col in range(self.BOARD_SIZE):
                    p = self.board[row][col]
                    if p == 0:
                        continue
                    x, y = self.cell_to_pixel(row, col)
                    if p == 1:
                        Color(0, 0, 0, 1)
                        Ellipse(pos=(x - piece_r, y - piece_r),
                                size=(piece_r * 2, piece_r * 2))
                        Color(0.3, 0.3, 0.3, 1)
                        Ellipse(pos=(x - piece_r * 0.5, y + piece_r * 0.2),
                                size=(piece_r * 0.6, piece_r * 0.6))
                    else:
                        Color(1, 1, 1, 1)
                        Ellipse(pos=(x - piece_r, y - piece_r),
                                size=(piece_r * 2, piece_r * 2))
                        Color(0.85, 0.85, 0.85, 1)
                        Ellipse(pos=(x - piece_r * 0.5, y + piece_r * 0.2),
                                size=(piece_r * 0.6, piece_r * 0.6))

            # 最后一步标记
            if self.last_move:
                r, c = self.last_move
                x, y = self.cell_to_pixel(r, c)
                Color(1, 0, 0, 1)
                Line(rectangle=(x - piece_r, y - piece_r, piece_r * 2, piece_r * 2),
                     width=2)

            # 悬停预览
            if self.hover_cell and not self.game_over:
                r, c = self.hover_cell
                if 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == 0:
                    rate = self.ai.estimate_win_rate(self.board, r, c, self.current_player)
                    if rate >= 0.6:
                        Color(0.3, 0.7, 0.3, 0.55)
                    elif rate <= 0.4:
                        Color(0.9, 0.3, 0.3, 0.55)
                    else:
                        if self.current_player == 1:
                            Color(0.2, 0.2, 0.2, 0.55)
                        else:
                            Color(0.8, 0.8, 0.8, 0.55)
                    x, y = self.cell_to_pixel(r, c)
                    Ellipse(pos=(x - piece_r, y - piece_r),
                            size=(piece_r * 2, piece_r * 2))

            # 获胜连线
            if self.winner_line:
                p1 = self.winner_line[0]
                p2 = self.winner_line[-1]
                x1, y1 = self.cell_to_pixel(*p1)
                x2, y2 = self.cell_to_pixel(*p2)
                Color(1, 0, 0, 1)
                Line(points=[x1, y1, x2, y2], width=4)

    def place_piece(self, row, col):
        if self.game_over:
            return
        if self.board[row][col] != 0:
            return

        self.board[row][col] = self.current_player
        self.last_move = (row, col)
        self.hover_cell = None

        win = self.check_win(row, col)
        if win:
            self.game_over = True
            self.winner_line = win['line']
            self.redraw()
            app = App.get_running_app()
            name = "黑棋" if self.current_player == 1 else "白棋"
            if app:
                app.update_status(f"游戏结束 - {name}获胜！", (1, 0, 0, 1))
                app.update_win_rate(None)
                app.show_popup(f"{name}获胜！")
            return

        if self.is_full():
            self.game_over = True
            self.redraw()
            app = App.get_running_app()
            if app:
                app.update_status("游戏结束 - 平局！", (0, 0, 1, 1))
                app.update_win_rate(None)
                app.show_popup("平局！")
            return

        self.current_player = 2 if self.current_player == 1 else 1
        self.redraw()

        app = App.get_running_app()
        if app:
            name = "黑棋" if self.current_player == 1 else "白棋"
            color = (0, 0, 0, 1) if self.current_player == 1 else (0.4, 0.4, 0.4, 1)
            app.update_status(f"当前：{name}", color)
            app.update_win_rate(None)

    def check_win(self, row, col):
        player = self.board[row][col]
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            line = [(row, col)]
            r, c = row + dr, col + dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == player:
                line.append((r, c))
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == player:
                line.insert(0, (r, c))
                r -= dr
                c -= dc
            if len(line) >= 5:
                for i in range(len(line) - 4):
                    seg = line[i:i + 5]
                    dr2 = seg[1][0] - seg[0][0]
                    dc2 = seg[1][1] - seg[0][1]
                    ok = True
                    for j in range(1, 5):
                        if seg[j][0] - seg[j - 1][0] != dr2 or seg[j][1] - seg[j - 1][1] != dc2:
                            ok = False
                            break
                    if ok:
                        return {'player': player, 'line': seg}
        return None

    def is_full(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

    def undo(self):
        if self.game_over:
            return
        # 简化版：找最后一步并清除（为了演示 Kivy 结构）
        # 完整悔棋需要维护 move_history，这里从略
        pass

    # ---------- 触摸事件 ----------
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.game_over:
            return True
        if self.cell_size <= 0:
            return True
        row, col = self.pixel_to_cell(touch.x, touch.y)
        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            self.place_piece(row, col)
        return True

    def on_touch_move(self, touch):
        # 桌面上鼠标拖动时也更新悬停；手机上手指移动同理
        if not self.collide_point(*touch.pos):
            return False
        if self.game_over or self.cell_size <= 0:
            return True
        row, col = self.pixel_to_cell(touch.x, touch.y)
        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            if self.board[row][col] == 0:
                self.hover_cell = (row, col)
                self.redraw()
                app = App.get_running_app()
                if app:
                    rate = self.ai.estimate_win_rate(self.board, row, col, self.current_player)
                    app.update_win_rate((row, col, rate))
        return True

    def on_touch_up(self, touch):
        return False


# ---------------- 主界面 ----------------
class GomokuRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # 顶部状态栏
        top_bar = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(8), spacing=dp(8))
        self.status_label = Label(text="当前：黑棋", font_size=dp(18), bold=True,
                                  color=(0, 0, 0, 1))
        top_bar.add_widget(self.status_label)

        self.black_rate_label = Label(text="黑:50%", font_size=dp(14), color=(0, 0, 0, 1))
        self.white_rate_label = Label(text="白:50%", font_size=dp(14), color=(0.3, 0.3, 0.3, 1))
        top_bar.add_widget(self.black_rate_label)
        top_bar.add_widget(self.white_rate_label)

        self.add_widget(top_bar)

        # 棋盘
        self.board_widget = BoardWidget()
        self.add_widget(self.board_widget)

        # 底部按钮
        bottom_bar = BoxLayout(size_hint_y=None, height=dp(55), padding=dp(8), spacing=dp(8))
        restart_btn = Button(text="重新开始", font_size=dp(16),
                             background_color=(0.3, 0.7, 0.3, 1))
        restart_btn.bind(on_press=lambda *a: self.board_widget.reset())
        bottom_bar.add_widget(restart_btn)

        self.add_widget(bottom_bar)

    def update_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    def update_win_rate(self, info):
        if info is None:
            # 显示当前棋盘全局胜率
            board = self.board_widget.board
            ai = self.board_widget.ai
            my = ai.evaluate_board(board, 1)
            opp = ai.evaluate_board(board, 2)
            diff = my - opp
            black_rate = 1 / (1 + math.exp(-diff / 50000))
            black_rate = max(0.05, min(0.95, black_rate))
        else:
            row, col, rate = info
            if self.board_widget.current_player == 1:
                black_rate = rate
            else:
                black_rate = 1 - rate

        white_rate = 1 - black_rate
        self.black_rate_label.text = f"黑:{black_rate*100:.0f}%"
        self.white_rate_label.text = f"白:{white_rate*100:.0f}%"

    def show_popup(self, msg):
        from kivy.uix.popup import Popup
        popup = Popup(title="游戏结束", content=Label(text=msg, font_size=dp(20)),
                      size_hint=(0.7, 0.3))
        popup.open()


class GomokuApp(App):
    def build(self):
        self.title = "五子棋"
        self.root_widget = GomokuRoot()
        return self.root_widget

    def update_status(self, text, color):
        if hasattr(self, 'root_widget'):
            self.root_widget.update_status(text, color)

    def update_win_rate(self, info):
        if hasattr(self, 'root_widget'):
            self.root_widget.update_win_rate(info)

    def show_popup(self, msg):
        if hasattr(self, 'root_widget'):
            self.root_widget.show_popup(msg)


if __name__ == '__main__':
    GomokuApp().run()