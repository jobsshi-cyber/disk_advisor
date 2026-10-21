import os
import shutil
import threading
import tkinter as tk
from collections.abc import Callable
from contextlib import suppress
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .classifier import refine_risk
from .reporter import write_html_report
from .scanner import FileRecord, scan_tree

FORBIDDEN_MOVE_EXT = {".dll", ".exe", ".sys", ".drv", ".vhd", ".vhdx"}


class ProgressWindow:
    """执行清理/迁移时的进度提示窗口"""

    def __init__(self, parent: tk.Tk, title: str) -> None:
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry("400x100")
        self.win.transient(parent)
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止关闭

        self.label = ttk.Label(self.win, text="正在准备...")
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(
            self.win, orient="horizontal", length=350, mode="determinate"
        )
        self.progress.pack(pady=10)

    def update_progress(self, current: int, total: int, text: str) -> None:
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.label.config(text=text)
        self.win.update_idletasks()

    def close(self) -> None:
        self.win.destroy()


class SelectionWindow:
    """扫描结果选择窗口（带复选框的表格）"""

    def __init__(
        self,
        parent: tk.Tk,
        records: list[FileRecord],
        on_complete: Callable[[list[str], list[str], Path | None], None],
    ) -> None:
        self.parent = parent
        self.records = records
        self.on_complete = on_complete
        self.win = tk.Toplevel(parent)
        self.win.title("选择要处理的项目")
        self.win.geometry("900x600")
        self.win.transient(parent)
        self.win.grab_set()

        self.notebook: Any = ttk.Notebook(self.win)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.junk_tab = ttk.Frame(self.notebook)
        self.large_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.junk_tab, text="清理垃圾 (按目录)")
        self.notebook.add(self.large_tab, text="迁移大文件")

        self.junk_data: dict[str, dict[str, int]] = {}  # dir_path -> {"size": int, "count": int}
        self.large_data: list[FileRecord] = []  # FileRecord

        self.process_data()

        # 构建 UI
        self.junk_tree = self.create_tree(self.junk_tab, ["选中", "目录路径", "文件数", "总大小"])
        self.populate_junk_tree()

        self.large_tree = self.create_tree(self.large_tab, ["选中", "文件路径", "大小", "建议"])
        self.populate_large_tree()

        # 底部操作按钮
        btn_frame = ttk.Frame(self.win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全不选", command=self.select_none).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="执行选中操作", command=self.execute).pack(side=tk.RIGHT, padx=5)

    def process_data(self) -> None:
        junk_files = [r for r in self.records if r.category == "junk"]
        large_files = [r for r in self.records if r.category == "large"]

        # 聚合垃圾文件（按父目录）
        for r in junk_files:
            p = str(Path(r.path).parent)
            if p not in self.junk_data:
                self.junk_data[p] = {"size": 0, "count": 0}
            self.junk_data[p]["size"] += r.size
            self.junk_data[p]["count"] += 1

        self.large_data = large_files

    def create_tree(self, parent: ttk.Frame, headers: list[str]) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=list(range(len(headers))), show="headings")
        for i, h in enumerate(headers):
            tree.heading(i, text=h)
            if "路径" in h:
                tree.column(i, width=550)
            elif "建议" in h:
                tree.column(i, width=150)
            else:
                tree.column(i, width=100, anchor="center" if "选中" in h else "e")

        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<ButtonRelease-1>", partial(self.toggle_check, tree=tree))
        return tree

    def populate_junk_tree(self) -> None:
        for path, info in sorted(self.junk_data.items(), key=lambda x: -x[1]["size"]):
            size_mb = info["size"] / (1024 * 1024)
            self.junk_tree.insert(
                "", tk.END, values=("☑", path, info["count"], f"{size_mb:.1f} MB")
            )

    def populate_large_tree(self) -> None:
        for r in sorted(self.large_data, key=lambda x: -x.size):
            size_mb = r.size / (1024 * 1024)
            self.large_tree.insert(
                "", tk.END, values=("☑", r.path, f"{size_mb:.1f} MB", "建议迁移")
            )

    def toggle_check(self, event: tk.Event[tk.Misc], tree: Any) -> None:
        """点击第一列切换勾选状态"""
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            if column == "#1":
                item = tree.identify_row(event.y)
                if item:
                    vals = list(tree.item(item, "values"))
                    vals[0] = "☐" if vals[0] == "☑" else "☑"
                    tree.item(item, values=vals)

    def select_all(self) -> None:
        current = self.notebook.index(self.notebook.select())
        tree = self.junk_tree if current == 0 else self.large_tree
        for item in tree.get_children():
            vals = list(tree.item(item, "values"))
            vals[0] = "☑"
            tree.item(item, values=vals)

    def select_none(self) -> None:
        current = self.notebook.index(self.notebook.select())
        tree = self.junk_tree if current == 0 else self.large_tree
        for item in tree.get_children():
            vals = list(tree.item(item, "values"))
            vals[0] = "☐"
            tree.item(item, values=vals)

    def execute(self) -> None:
        dirs_to_clean = []
        for item in self.junk_tree.get_children():
            if self.junk_tree.item(item, "values")[0] == "☑":
                dirs_to_clean.append(self.junk_tree.item(item, "values")[1])

        files_to_move = []
        for item in self.large_tree.get_children():
            if self.large_tree.item(item, "values")[0] == "☑":
                files_to_move.append(self.large_tree.item(item, "values")[1])

        if not dirs_to_clean and not files_to_move:
            messagebox.showinfo("提示", "没有选中任何操作项。", parent=self.win)
            return

        target_dir = None
        if files_to_move:
            target = filedialog.askdirectory(title="请选择大文件迁移的目标文件夹", parent=self.win)
            if not target:
                messagebox.showwarning(
                    "取消", "未选择目标文件夹，将跳过文件迁移。", parent=self.win
                )
                files_to_move = []  # 清空，防止误操作
            else:
                target_dir = Path(target)

        self.win.destroy()
        self.on_complete(dirs_to_clean, files_to_move, target_dir)


class DiskAdvisorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("磁盘清理顾问")
        self.root.geometry("500x250")
        self.root.resizable(False, False)

        self.dir_var = tk.StringVar(value="C:\\")
        self.size_var = tk.IntVar(value=500)

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="扫描目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.dir_var, width=35).grid(row=0, column=1, pady=5)
        ttk.Button(frame, text="浏览...", command=self.browse_dir).grid(
            row=0, column=2, padx=5, pady=5
        )

        ttk.Label(frame, text="大文件阈值(MB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.size_var, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(frame, textvariable=self.status_var, foreground="#666").grid(
            row=2, column=0, columnspan=3, pady=15
        )

        self.start_btn = ttk.Button(frame, text="开始扫描", command=self.start_scan)
        self.start_btn.grid(row=3, column=0, columnspan=3, ipadx=20, ipady=5)

    def browse_dir(self) -> None:
        path = filedialog.askdirectory(title="选择要扫描的文件夹")
        if path:
            self.dir_var.set(path)

    def start_scan(self) -> None:
        target_dir = self.dir_var.get().strip()
        if not target_dir or not Path(target_dir).exists():
            messagebox.showerror("错误", "请选择有效的扫描目录！")
            return

        try:
            threshold_mb = self.size_var.get()
        except tk.TclError:
            messagebox.showerror("错误", "阈值必须是数字！")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.status_var.set("正在扫描中，请稍候...")
        self.root.update()

        threading.Thread(target=self.run_scan, args=(target_dir, threshold_mb), daemon=True).start()

    def run_scan(self, target_dir: str, threshold_mb: int) -> None:
        try:
            records = [
                refine_risk(r)
                for r in scan_tree(target_dir, threshold_mb * 1024 * 1024, report_junk_files=True)
            ]
            out_path = Path("disk_report.html").resolve()
            write_html_report(records, str(out_path))

            self.root.after(0, self.scan_finished, records, out_path)
        except Exception as e:

            def show_error(error: Exception = e) -> None:
                messagebox.showerror("扫描失败", str(error))

            self.root.after(0, show_error)
            self.root.after(0, self.reset_ui)

    def scan_finished(self, records: list[FileRecord], out_path: Path) -> None:
        self.status_var.set("扫描完成！")
        self.reset_ui()

        if not records:
            messagebox.showinfo("完成", "未发现符合条件的文件。报告已生成。")
            return

        # 打开选择窗口
        SelectionWindow(self.root, records, self.execute_operations)

    def reset_ui(self) -> None:
        self.start_btn.config(state=tk.NORMAL)

    def execute_operations(
        self, dirs_to_clean: list[str], files_to_move: list[str], target_dir: Path | None
    ) -> None:
        total_tasks = len(dirs_to_clean) + len(files_to_move)
        if total_tasks == 0:
            return

        pw = ProgressWindow(self.root, "正在执行操作")

        def worker() -> None:
            current = 0
            deleted_files = 0
            moved_files = 0

            # 1. 清理垃圾目录
            for d in dirs_to_clean:
                pw.update_progress(current, total_tasks, f"正在清理: {os.path.basename(d)}")
                # 删除目录下的文件
                for root, _, files in os.walk(d):
                    for f in files:
                        try:
                            os.unlink(os.path.join(root, f))
                            deleted_files += 1
                        except Exception:
                            pass
                # 尝试删空目录本身
                with suppress(Exception):
                    shutil.rmtree(d, ignore_errors=True)
                current += 1

            # 2. 迁移大文件
            if target_dir:
                for f in files_to_move:
                    src = Path(f)
                    ext = src.suffix.lower()
                    if ext in FORBIDDEN_MOVE_EXT or ("wsl" in src.parts and ext == ".vhdx"):
                        current += 1
                        continue

                    dest = target_dir / src.name
                    pw.update_progress(current, total_tasks, f"正在迁移: {src.name}")
                    if not dest.exists():
                        try:
                            shutil.move(str(src), str(dest))
                            moved_files += 1
                        except Exception:
                            pass
                    current += 1

            # 操作完成
            self.root.after(0, lambda: pw.close())
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "完成",
                    f"操作结束：\n清理了 {deleted_files} 个文件。\n迁移了 {moved_files} 个文件。",
                ),
            )

        threading.Thread(target=worker, daemon=True).start()


def start_gui() -> None:
    root = tk.Tk()
    _app = DiskAdvisorApp(root)
    root.mainloop()
