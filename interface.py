import json
import os
from datetime import date, datetime
from typing import Any

import expectations
import task as task_module
import flet as ft

TASK_TYPES: list[str] = task_module.TASK_TYPES
TASKS_FILE: str = "tasks.json"

HEADERS: dict[str, str] = {
    "deadline":          "Дедлайн",
    "time_required":     "Время (ч)",
    "type":              "Тип",
    "min_cont_interval": "Мин. интервал (ч)",
    "is_done":           "Выполнено",
}


def task_to_dict(t: task_module.Task) -> dict[str, Any]:
    return {
        "deadline":          t.deadline.isoformat() if t.deadline else None,
        "time_required":     t.time_required,
        "type":              t.type,
        "min_cont_interval": t.min_cont_interval,
        "is_done":           t.is_done,
    }


def task_from_dict(d: dict[str, Any]) -> task_module.Task:
    raw: Any = d.get("deadline")
    if not raw:
        deadline: date = date.today()
    else:
        try:
            deadline = datetime.fromisoformat(raw).date()
        except Exception:
            deadline = date.fromisoformat(str(raw)[:10])

    kwargs: dict[str, Any] = dict(
        deadline=deadline,
        time_required=int(d.get("time_required", 0)),
        type=d.get("type", TASK_TYPES[1]),
        min_cont_interval=int(d.get("min_cont_interval", 0)),
        is_done=bool(d.get("is_done", False)),
    )
    t_type: str = kwargs["type"]
    if t_type == "учёба":
        return task_module.Learning(**kwargs)
    elif t_type == "хобби":
        return task_module.Hobby(**kwargs)
    else:
        return task_module.Work(**kwargs)


def load_tasks_from_file() -> list[task_module.Task]:
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
            return [task_from_dict(d) for d in data]
        except Exception as e:
            print(f"[ОШИБКА] Не удалось загрузить задачи: {e}")
    return []


def save_tasks_to_file(tasks: list[task_module.Task]):
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump([task_to_dict(t) for t in tasks], f, ensure_ascii=False, indent=2)
        print(f"[ЛОГ] Сохранено {len(tasks)} задач(и) в {TASKS_FILE}")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось сохранить задачи: {e}")


def main(page: ft.Page):
    page.title = "Менеджер задач"
    page.scroll = ft.ScrollMode.AUTO

    tasks: list[task_module.Task] = load_tasks_from_file()
    print(f"[ЛОГ] Загружено задач: {len(tasks)}")

    main_content: ft.Column = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    bottom_bar: ft.Container = ft.Container(padding=10)

    def show_main_buttons():
        bottom_bar.content = ft.Row([
            ft.Button("Добавить задачу", on_click=on_add_task_click),
            ft.Button("Список задач",    on_click=on_show_tasks_click),
        ])
        page.update()

    def on_add_task_click(e: ft.ControlEvent):
        main_content.controls.clear()

        deadline_display: ft.TextField = ft.TextField(
            label="Дедлайн",
            hint_text="не выбран",
            read_only=True,
            expand=True,
        )
        time_field: ft.TextField = ft.TextField(
            label="Время на выполнение (ч)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0",
        )
        interval_field: ft.TextField = ft.TextField(
            label="Мин. непрерывный интервал (ч)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0",
        )
        type_dropdown: ft.Dropdown = ft.Dropdown(
            label="Тип задачи",
            options=[ft.dropdown.Option(t) for t in TASK_TYPES],
            value=TASK_TYPES[1],
            expand=True,
        )
        error_text: ft.Text = ft.Text("", color=ft.Colors.RED)

        selected_date: dict[str, Any] = {"value": None}

        def on_date_change(ev: ft.ControlEvent):
            raw: Any = ev.control.value
            if raw:
                d: date = raw.date() if hasattr(raw, "date") else date.fromisoformat(str(raw)[:10])
                selected_date["value"] = d
                deadline_display.value = d.strftime("%d.%m.%Y")
            page.update()

        date_picker: ft.DatePicker = ft.DatePicker(on_change=on_date_change)
        page.overlay.append(date_picker)

        def open_date_picker(ev: ft.ControlEvent):
            date_picker.open = True
            page.update()

        def save_task(ev: ft.ControlEvent):
            error_text.value = ""
            try:
                time_req: int     = int(time_field.value or 0)
                min_interval: int = int(interval_field.value or 0)
            except ValueError:
                error_text.value = "Время и интервал должны быть целыми числами."
                page.update()
                return

            dl: date = selected_date["value"] or date.today()

            new_task: task_module.Task = task_from_dict({
                "deadline":          dl.isoformat(),
                "time_required":     time_req,
                "type":              type_dropdown.value or TASK_TYPES[1],
                "min_cont_interval": min_interval,
                "is_done":           False,
            })
            tasks.append(new_task)
            save_tasks_to_file(tasks)
            print(f"[ЛОГ] Добавлена задача: {task_to_dict(new_task)}")

            page.overlay.remove(date_picker)
            main_content.controls.clear()
            page.update()
            show_main_buttons()

        def cancel(ev: ft.ControlEvent):
            page.overlay.remove(date_picker)
            main_content.controls.clear()
            page.update()

        form: ft.Column = ft.Column(
            [
                ft.Text("Новая задача", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    deadline_display,
                    ft.Button("Выбрать дату", on_click=open_date_picker),
                ]),
                time_field,
                interval_field,
                type_dropdown,
                error_text,
                ft.Divider(),
                ft.Row([
                    ft.Button("Сохранить", on_click=save_task),
                    ft.Button("Отмена",    on_click=cancel),
                ]),
            ],
            spacing=12,
        )

        main_content.controls.append(form)
        page.update()

    def on_show_tasks_click(e: ft.ControlEvent):
        main_content.controls.clear()

        if not tasks:
            main_content.controls.append(
                ft.Text("Список задач пуст.", italic=True, color=ft.Colors.GREY)
            )
            page.update()
            return

        field_keys: list[str] = list(HEADERS.keys())

        columns: list[ft.DataColumn] = [
            ft.DataColumn(ft.Text(HEADERS[k], weight=ft.FontWeight.BOLD))
            for k in field_keys
        ]

        rows: list[ft.DataRow] = []
        for t in tasks:
            d: dict[str, Any] = task_to_dict(t)
            cells: list[ft.DataCell] = []
            for k in field_keys:
                val: Any = d[k]
                if k == "deadline":
                    val = date.fromisoformat(val).strftime("%d.%m.%Y") if val else "—"
                elif k == "is_done":
                    val = "да" if val else "нет"
                else:
                    val = str(val)
                cells.append(ft.DataCell(ft.Text(val)))
            rows.append(ft.DataRow(cells=cells))

        table: ft.DataTable = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            horizontal_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        )

        def hide_table(ev: ft.ControlEvent):
            main_content.controls.clear()
            page.update()

        main_content.controls.append(
            ft.Button("Скрыть", on_click=hide_table, color=ft.Colors.RED)
        )
        main_content.controls.append(ft.Text(f"Всего задач: {len(tasks)}", italic=True))
        main_content.controls.append(table)
        page.update()

    def on_disconnect(e: ft.ControlEvent):
        save_tasks_to_file(tasks)

    page.on_disconnect = on_disconnect

    page.add(
        main_content,
        ft.Divider(),
        bottom_bar,
    )

    show_main_buttons()


ft.run(main)