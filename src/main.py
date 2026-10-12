import flet as ft
from datetime import datetime

class Container:
    def __init__(self):
        self.items = {}

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, key):
        return key in self.items

    def __str__(self):
        return str(self.items)

    def values(self):
        return list(self.items.values())

class Abstract:
    
    def info(self):
        raise NotImplementedError("Нужно переопределить info()")

    def __str__(self):
        return self.info()

class Tip(Abstract):
    def __init__(self, bill, interest):
        if bill < 0:
            raise ValueError("Сумма не может быть меньше нуля")
        if interest < 0 or interest > 100:
            raise ValueError("Процент должен быть от 0 до 100")
        self.bill = bill
        self.interest = interest

    def tip(self):
        return self.bill * self.interest / 100

    def total(self):
        return self.bill + self.tip()

    def info(self):
        return (f"{self.bill:.2f} + {self.interest}% = "
                f"{self.tip():.2f} (итого {self.total():.2f})")

    def __eq__(self, other):
        return self.total() == other.total()

    def __lt__(self, other):
        return self.total() < other.total()

    def __add__(self, other):
        return Tip(self.bill + other.bill, self.interest)

    def __repr__(self):
        return f"Tip({self.bill}, {self.interest})"

class User(Abstract):
    def __init__(self, login):
        self.login = login
        self.history = []

    def add_tip(self, tip):
        self.history.append(tip)

    def clear(self):
        self.history = []

    def total_tips(self):
        return sum(t.tip() for t in self.history)

    def info(self):
        return f"{self.login}: расчётов {len(self)}, чаевых {self.total_tips():.2f}"

    def __len__(self):
        return len(self.history)

    def __iter__(self):
        return iter(self.history)

    def __getitem__(self, i):
        return self.history[i]

    def __eq__(self, other):
        return self.login == other.login

    def __lt__(self, other):
        return self.total_tips() < other.total_tips()

    def __repr__(self):
        return f"User({self.login})"

class Session(Abstract):
    def __init__(self, user):
        self.user = user
        self.start = datetime.now()
        self.end = None
        self.count = 0

    def close(self):
        if self.end is None:
            self.end = datetime.now()

    def duration(self):
        end = self.end or datetime.now()
        return (end - self.start).total_seconds()

    def info(self):
        start = self.start.strftime("%H:%M:%S")
        end = self.end.strftime("%H:%M:%S") if self.end else "-"
        return (f"{self.user.login}: {start} - {end}, "
                f"{self.duration():.0f} сек, расчётов {self.count}")

    def __repr__(self):
        return f"Session({self.user.login})"

def write_report(users, sessions):
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write("Отчёт " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

        f.write("Пользователи:\n")
        for u in sorted(users.values(), reverse=True):
            f.write("  " + str(u) + "\n")
            for t in u: f.write("    " + str(t) + "\n")

        f.write("\nСессии:\n")
        for s in sessions: f.write("  " + str(s) + "\n")

class Title(ft.Text):
    def __init__(self, text):
        super().__init__(text, size=28, weight="bold")

class BillField(ft.TextField):
    def __init__(self):
        super().__init__(label="Сумма счёта", width=250)

class CalcButton(ft.FilledButton):
    def __init__(self, on_click):
        super().__init__("Посчитать", on_click=on_click, width=250)
class ClearButton(ft.OutlinedButton):
    def __init__(self, on_click):
        super().__init__("Очистить историю", on_click=on_click, width=250)

class StatusText(ft.Text):
    def __init__(self):
        super().__init__("Выберите пользователя", size=14, color="pink")

class ResultText(ft.Text):
    def __init__(self):
        super().__init__("", size=22)

class UserDropdown(ft.Dropdown):
    def __init__(self, logins, on_change):
        opts = []
        for login in logins:
            opts.append(ft.dropdown.Option(login))
        super().__init__(
            label="Официант",
            width=250,
            options=opts,
            value=logins[0] if logins else None
        )
        self.on_select = on_change

class PercentDropdown(ft.Dropdown):
    def __init__(self):
        opts = [ft.dropdown.Option("5"), ft.dropdown.Option("10"),
                ft.dropdown.Option("15"), ft.dropdown.Option("20")]
        super().__init__(label="Процент", width=250, options=opts, value="10")

class HistoryItem(ft.Text):
    def __init__(self, login, tip):
        super().__init__(f"{login}: {tip}", size=13)

class HistoryList(ft.ListView):
    def __init__(self):
        super().__init__(height=200, width=350, spacing=5)

class MainColumn(ft.Column):
    def __init__(self, controls):
        super().__init__(controls, spacing=12, horizontal_alignment="center")

LOGINS = ["Vkysno i tochka", "mommy", "Vera", "Polina", "Nikita",
          "Kirril", "CBO", "USA", "IVAN005", "Nata"]

users = Container()
for login in LOGINS:
    users[login] = User(login)

sessions = []
current_user = None
current_session = None

def main(page: ft.Page):
    global current_user, current_session
    
    page.title = "Калькулятор чаевых"
    page.window.width = 400
    page.window.height = 750
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"

    title = Title("Сколько хотите оставить на чай?")
    bill_field = BillField()
    percent_dd = PercentDropdown()
    result = ResultText()
    status = StatusText()
    history = HistoryList()

# обновление истории 
    def update_history():
        history.controls.clear()
        if current_user is not None:
            for t in current_user:
                history.controls.append(HistoryItem(current_user.login, t))
        page.update()

# обработчик изменения пользователя
    def on_user_change(e):
        global current_user, current_session
        
        selected_login = e.control.value
        if selected_login is None:
            return
        
        # закрываем предыдущую сессию
        if current_session is not None:
            current_session.close()
        
        # создаём новую сессию
        current_user = users[selected_login]
        current_session = Session(current_user)
        sessions.append(current_session)
        
        result.value = ""
        status.value = current_user.info()
        update_history()
        page.update()

    def on_calc(e):
        if current_user is None:
            status.value = "Сначала выберите пользователя"
            page.update()
            return
        
        try:
            # проверка пустого поля
            if not bill_field.value or bill_field.value.strip() == "":
                status.value = "Введите сумму счёта"
                page.update()
                return
            
            bill = float(bill_field.value.replace(",", "."))
            percent = float(percent_dd.value)
            
            # роверка значений внутри
            tip = Tip(bill, percent)
            current_user.add_tip(tip)
            current_session.count += 1
            
            result.value = f"Чаевые: {tip.tip():.2f} / итого: {tip.total():.2f}"
            status.value = current_user.info()
            bill_field.value = ""
            
        except ValueError as err:
            error_msg = str(err)
            if "could not convert" in error_msg or "неудалось преобразовать" in error_msg:
                status.value = "Введите корректное число"
            else:
                status.value = error_msg
        
        update_history()
        page.update()

# oбработчик очистки истории
    def on_clear(e):
        if current_user is not None:
            current_user.clear()
            result.value = ""
            status.value = current_user.info()
        update_history()
        page.update()

#oбработчик события закрытия окна
    def on_window_event(e):
        if e.data == "close":
            for s in sessions:
                s.close()
            write_report(users, sessions)
            page.window.destroy()

    user_dd = UserDropdown(LOGINS, on_user_change)
    calc_btn = CalcButton(on_calc)
    clear_btn = ClearButton(on_clear)

    page.window.prevent_close = True
    page.window.on_event = on_window_event

    current_user = users[LOGINS[0]]
    current_session = Session(current_user)
    sessions.append(current_session)
    status.value = current_user.info()
    update_history()

    page.add(MainColumn([
        title,
        user_dd,
        percent_dd,
        bill_field,
        calc_btn,
        clear_btn,
        result,
        status,
        history,
    ]))

ft.run(main)










