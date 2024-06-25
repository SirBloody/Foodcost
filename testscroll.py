import tkinter as tk
from tkinter import ttk


class ScrollableFrame(tk.Frame):
    def __init__(self, container, width=300, height=330, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, width=width, height=height)
        self.canvas.config(highlightthickness=0)
        self.canvas.configure(background="#B0B781")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.configure(background="#B0B781")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel event to canvas scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", self.bind_to_mousewheel)
        self.canvas.bind("<Leave>", self.unbind_from_mousewheel)
    def bind_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def unbind_from_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")


    def _on_mousewheel(self, event):
        scroll_region = self.canvas.bbox("all")
        viewable_region = self.canvas.yview()

        # Calculate the scroll step and direction
        scroll_step = int(-1 * (event.delta / 120))

        # Determine if the view is at the top or bottom limit
        at_top_limit = viewable_region[0] <= 0 and scroll_step < 0
        at_bottom_limit = viewable_region[1] >= 1 and scroll_step > 0

        # Only scroll if not at the top or bottom limit
        if not at_top_limit and not at_bottom_limit:
            self.canvas.yview_scroll(scroll_step, "units")