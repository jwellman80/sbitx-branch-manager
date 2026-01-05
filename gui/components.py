"""Reusable GUI components for sBitx Branch Manager"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class StatusBar(ttk.Frame):
    """Status bar widget showing current operation status"""

    def __init__(self, parent):
        super().__init__(parent)
        self.label = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X, expand=True, padx=2, pady=2)

    def set_status(self, message: str, status_type: str = "info"):
        """
        Set status message

        Args:
            message: Status message to display
            status_type: Type of status (info, success, error, warning)
        """
        self.label.config(text=message)

        # Color coding based on status type
        colors = {
            'info': '#17a2b8',
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'working': '#fd7e14'
        }

        fg_color = colors.get(status_type, '#000000')
        self.label.config(foreground=fg_color)


class ProgressDialog(tk.Toplevel):
    """Modal dialog showing progress message"""

    def __init__(self, parent, title: str = "Please Wait", message: str = "Operation in progress..."):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        # Center on parent - smaller size
        self.geometry("350x120")
        self._center_on_parent(parent)

        # Make it non-resizable
        self.resizable(False, False)

        # Message label
        self.message_label = ttk.Label(
            self,
            text=message,
            font=('Arial', 9),
            wraplength=320
        )
        self.message_label.pack(pady=15, padx=15)

        # Progress indicator
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=320
        )
        self.progress.pack(pady=10)
        self.progress.start(10)

        # Prevent closing
        self.protocol("WM_DELETE_WINDOW", lambda: None)

    def _center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.geometry(f"+{x}+{y}")

    def update_message(self, message: str):
        """Update the progress message"""
        self.message_label.config(text=message)

    def close(self):
        """Close the dialog"""
        self.progress.stop()
        self.grab_release()
        self.destroy()


class ConfirmDialog(tk.Toplevel):
    """Confirmation dialog for destructive operations"""

    def __init__(
        self,
        parent,
        title: str = "Confirm",
        message: str = "Are you sure?",
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.result = False
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        # Center on parent - smaller size
        self.geometry("350x130")
        self._center_on_parent(parent)

        # Make it non-resizable
        self.resizable(False, False)

        # Message label
        message_label = ttk.Label(
            self,
            text=message,
            font=('Arial', 9),
            wraplength=320
        )
        message_label.pack(pady=15, padx=15)

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        # Confirm button
        confirm_btn = ttk.Button(
            button_frame,
            text="Yes",
            command=self._on_confirm,
            width=10
        )
        confirm_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="No",
            command=self._on_cancel,
            width=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Set focus to cancel button (safer default)
        cancel_btn.focus_set()

        # Bind escape key to cancel
        self.bind('<Escape>', lambda e: self._on_cancel())

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.geometry(f"+{x}+{y}")

    def _on_confirm(self):
        """Handle confirm button click"""
        self.result = True
        self.grab_release()
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

    def _on_cancel(self):
        """Handle cancel button click"""
        self.result = False
        self.grab_release()
        self.destroy()
        if self.on_cancel:
            self.on_cancel()


def show_error(parent, title: str, message: str):
    """
    Show an error message dialog

    Args:
        parent: Parent window
        title: Dialog title
        message: Error message
    """
    from tkinter import messagebox
    messagebox.showerror(title, message, parent=parent)


def show_info(parent, title: str, message: str):
    """
    Show an info message dialog

    Args:
        parent: Parent window
        title: Dialog title
        message: Info message
    """
    from tkinter import messagebox
    messagebox.showinfo(title, message, parent=parent)


def show_warning(parent, title: str, message: str):
    """
    Show a warning message dialog

    Args:
        parent: Parent window
        title: Dialog title
        message: Warning message
    """
    from tkinter import messagebox
    messagebox.showwarning(title, message, parent=parent)
