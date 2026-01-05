"""Main window for sBitx Branch Manager"""

import tkinter as tk
from tkinter import ttk
import threading
import queue
from typing import List, Optional

from models.repository import Repository
from core.config_manager import ConfigManager, ConfigError
from core.git_manager import GitManager, GitError, DirectoryStatus
from core.build_manager import BuildManager, BuildError
from gui.components import StatusBar, ProgressDialog, show_error, show_info, show_warning


class MainWindow(tk.Tk):
    """Main application window"""

    TARGET_PATH = "/home/pi/sbitx"

    def __init__(self):
        super().__init__()

        self.title("sBitx Branch Manager")
        self.geometry("500x363")
        self.resizable(True, True)

        # Initialize managers
        self.config_manager = ConfigManager()
        self.git_manager = GitManager()
        self.build_manager = BuildManager()

        # Queue for thread communication
        self.task_queue = queue.Queue()

        # Current state
        self.repositories: List[Repository] = []
        self.current_branches: List[str] = []
        self.selected_repo: Optional[Repository] = None
        self.selected_branch: Optional[str] = None

        # Track current repo and branch in target directory
        self.current_repo_url: Optional[str] = None
        self.current_branch_name: Optional[str] = None

        # Progress dialog
        self.progress_dialog: Optional[ProgressDialog] = None

        # Setup UI
        self.setup_ui()

        # Load repositories
        self.load_repositories()

        # Update current status
        self.update_current_status()

        # Auto-fetch branches for selected repository
        if self.selected_repo:
            self.on_fetch_branches()

        # Start queue polling
        self.check_queue()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        """Setup the user interface"""
        # Main container with minimal padding
        main_frame = ttk.Frame(self, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Repository Management Section
        self.setup_repository_section(main_frame)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)

        # Branch Selection Section
        self.setup_branch_section(main_frame)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)

        # Actions Section
        self.setup_actions_section(main_frame)

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def setup_repository_section(self, parent):
        """Setup repository management section"""
        repo_frame = ttk.LabelFrame(parent, text="Repositories (active highlighted)", padding="5")
        repo_frame.pack(fill=tk.X)

        # Repository listbox with scrollbar
        list_frame = ttk.Frame(repo_frame)
        list_frame.pack(fill=tk.X, pady=2)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.repo_listbox = tk.Listbox(
            list_frame,
            height=6,
            yscrollcommand=scrollbar.set,
            font=('Arial', 9),
            exportselection=False
        )
        self.repo_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.repo_listbox.bind('<<ListboxSelect>>', self.on_repo_listbox_select)
        scrollbar.config(command=self.repo_listbox.yview)

        # Add repository frame
        add_frame = ttk.Frame(repo_frame)
        add_frame.pack(fill=tk.X, pady=2)

        ttk.Label(add_frame, text="Add:", font=('Arial', 9)).pack(side=tk.LEFT, padx=2)

        self.repo_entry = ttk.Entry(add_frame, width=35, font=('Arial', 9))
        self.repo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.repo_entry.bind('<Return>', lambda e: self.on_add_repository())

        self.add_repo_btn = ttk.Button(
            add_frame,
            text="Add",
            command=self.on_add_repository
        )
        self.add_repo_btn.pack(side=tk.LEFT, padx=2)

        self.remove_repo_btn = ttk.Button(
            add_frame,
            text="Remove",
            command=self.on_remove_repository
        )
        self.remove_repo_btn.pack(side=tk.LEFT, padx=2)

    def setup_branch_section(self, parent):
        """Setup branch selection section"""
        branch_frame = ttk.LabelFrame(parent, text="Branch Selection", padding="5")
        branch_frame.pack(fill=tk.X)

        # Branch dropdown and fetch button on same row
        branch_select_frame = ttk.Frame(branch_frame)
        branch_select_frame.pack(fill=tk.X, pady=2)

        ttk.Label(branch_select_frame, text="Branch:", width=10, font=('Arial', 9)).pack(side=tk.LEFT, padx=2)

        self.branch_combo = ttk.Combobox(branch_select_frame, state='readonly', width=30, font=('Arial', 9))
        self.branch_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.branch_combo.bind('<<ComboboxSelected>>', self.on_branch_combo_selected)

        self.fetch_branches_btn = ttk.Button(
            branch_select_frame,
            text="Fetch Branches",
            command=self.on_fetch_branches,
            width=12
        )
        self.fetch_branches_btn.pack(side=tk.LEFT, padx=2)

    def setup_actions_section(self, parent):
        """Setup actions section"""
        actions_frame = ttk.LabelFrame(parent, text="Actions", padding="5")
        actions_frame.pack(fill=tk.X)

        # Button and info on same row
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill=tk.X, pady=3)

        # Checkout and build button
        self.checkout_build_btn = ttk.Button(
            btn_frame,
            text="Checkout and Build",
            command=self.on_checkout_and_build
        )
        self.checkout_build_btn.pack(side=tk.LEFT, padx=2)

        # Current repo/branch display
        current_frame = ttk.Frame(actions_frame)
        current_frame.pack(fill=tk.X, pady=2)

        ttk.Label(
            current_frame,
            text="Current:",
            font=('Arial', 8, 'bold')
        ).pack(side=tk.LEFT, padx=2)

        self.current_status_label = ttk.Label(
            current_frame,
            text="Unknown",
            font=('Arial', 8),
            foreground='#17a2b8'
        )
        self.current_status_label.pack(side=tk.LEFT, padx=2)

    def load_repositories(self):
        """Load repositories from config and auto-add current repo if needed"""
        try:
            # First, detect current repo and branch in target directory
            self.detect_current_repo_branch()

            # Load repositories from config
            self.repositories = self.config_manager.load_repositories()

            # Auto-add current repository if not in list
            if self.current_repo_url:
                repo_urls = [repo.url for repo in self.repositories]
                if self.current_repo_url not in repo_urls:
                    # Create and add the current repository
                    from models.repository import Repository
                    current_repo = Repository.create_new(self.current_repo_url)
                    if current_repo:
                        self.config_manager.add_repository(current_repo)
                        self.repositories.append(current_repo)

            self.update_repository_list()
        except ConfigError as e:
            show_error(self, "Configuration Error", str(e))

    def detect_current_repo_branch(self):
        """Detect current repository and branch in target directory"""
        try:
            status = self.git_manager.check_directory_status(self.TARGET_PATH)

            if status == DirectoryStatus.GIT_REPO:
                self.current_repo_url = self.git_manager.get_current_remote(self.TARGET_PATH)
                self.current_branch_name = self.git_manager.get_current_branch(self.TARGET_PATH)
            else:
                self.current_repo_url = None
                self.current_branch_name = None
        except Exception:
            self.current_repo_url = None
            self.current_branch_name = None

    def update_repository_list(self):
        """Update the repository listbox with branch info and highlighting"""
        self.repo_listbox.delete(0, tk.END)

        for i, repo in enumerate(self.repositories):
            # Check if this is the current repo
            is_current = (self.current_repo_url and repo.url == self.current_repo_url)

            # Format display text
            if is_current and self.current_branch_name:
                display_text = f"{repo.display_name} @ {self.current_branch_name}"
            else:
                display_text = repo.display_name

            self.repo_listbox.insert(tk.END, display_text)

            # Highlight current repo with different background color
            if is_current:
                self.repo_listbox.itemconfig(i, bg='#d4edda', fg='#155724')  # Light green background, dark green text
                # Auto-select the current repo in the listbox
                self.repo_listbox.selection_clear(0, tk.END)
                self.repo_listbox.selection_set(i)
                self.repo_listbox.see(i)
                self.selected_repo = repo

    def on_add_repository(self):
        """Handle add repository button click"""
        url = self.repo_entry.get().strip()

        if not url:
            show_warning(self, "Invalid Input", "Please enter a repository URL")
            return

        # Create and validate repository
        repo = Repository.create_new(url)
        if not repo:
            show_error(
                self,
                "Invalid URL",
                f"Invalid repository URL: {url}\n\n"
                "Supported formats:\n"
                "  - owner/repo\n"
                "  - github.com/owner/repo\n"
                "  - https://github.com/owner/repo\n"
                "  - git@github.com:owner/repo.git"
            )
            return

        # Add to config
        if self.config_manager.add_repository(repo):
            self.repositories.append(repo)
            self.update_repository_list()
            # Select the newly added repository in the listbox
            new_index = len(self.repositories) - 1
            self.repo_listbox.selection_clear(0, tk.END)
            self.repo_listbox.selection_set(new_index)
            self.repo_listbox.see(new_index)
            self.selected_repo = repo
            self.repo_entry.delete(0, tk.END)
            self.status_bar.set_status(f"Added repository: {repo.display_name}", "success")
        else:
            show_info(self, "Duplicate", f"Repository {repo.display_name} already exists")

    def on_remove_repository(self):
        """Handle remove repository button click"""
        selection = self.repo_listbox.curselection()

        if not selection:
            show_warning(self, "No Selection", "Please select a repository to remove")
            return

        index = selection[0]
        repo = self.repositories[index]

        # Check if it's a default repository
        if self.config_manager.is_default_repository(repo.url):
            show_info(
                self,
                "Cannot Remove",
                f"{repo.display_name} is a default repository and cannot be removed."
            )
            return

        if self.config_manager.remove_repository(repo.url):
            self.repositories.pop(index)
            # Clear selection if we're removing the selected repo
            if self.selected_repo and self.selected_repo.url == repo.url:
                self.selected_repo = None
                self.branch_combo.set('')
                self.current_branches = []
            self.update_repository_list()
            self.status_bar.set_status(f"Removed repository: {repo.display_name}", "success")

    def on_repo_listbox_select(self, event):
        """Handle repository selection from listbox"""
        selection = self.repo_listbox.curselection()
        if selection:
            selected_index = selection[0]
            self.selected_repo = self.repositories[selected_index]
            # Clear branch selection
            self.branch_combo.set('')
            self.current_branches = []
            self.selected_branch = None
            self.status_bar.set_status(f"Selected: {self.selected_repo.display_name}", "info")

            # Automatically fetch branches
            self.on_fetch_branches()

    def on_fetch_branches(self):
        """Handle fetch branches button click"""
        if not self.selected_repo:
            show_warning(self, "No Repository", "Please select a repository first")
            return

        # Run in background thread
        self.disable_controls()
        self.status_bar.set_status("Fetching branches...", "working")

        thread = threading.Thread(
            target=self._fetch_branches_thread,
            args=(self.selected_repo.url,)
        )
        thread.daemon = True
        thread.start()

    def _fetch_branches_thread(self, repo_url: str):
        """Background thread for fetching branches"""
        try:
            branches = self.git_manager.fetch_branches(repo_url)
            self.task_queue.put(('branches_fetched', branches))
        except GitError as e:
            self.task_queue.put(('error', str(e)))

    def on_checkout_and_build(self):
        """Handle checkout and build button click"""
        if not self.selected_repo:
            show_warning(self, "No Repository", "Please select a repository")
            return

        if not self.selected_branch:
            show_warning(self, "No Branch", "Please select a branch")
            return

        # Show progress dialog
        self.progress_dialog = ProgressDialog(
            self,
            "Checkout and Build",
            "Checking out repository and branch..."
        )

        # Disable controls
        self.disable_controls()

        # Run in background thread
        thread = threading.Thread(
            target=self._checkout_and_build_thread,
            args=(self.selected_repo.url, self.selected_branch)
        )
        thread.daemon = True
        thread.start()

    def _checkout_and_build_thread(self, repo_url: str, branch: str):
        """Background thread for checkout and build"""
        try:
            # Check directory status
            status = self.git_manager.check_directory_status(self.TARGET_PATH)

            if status == DirectoryStatus.NON_GIT:
                self.task_queue.put((
                    'error',
                    f"{self.TARGET_PATH} exists but is not a git repository.\n"
                    "Please backup and remove the directory first."
                ))
                return

            # Clone or change remote
            if status == DirectoryStatus.DOES_NOT_EXIST:
                self.task_queue.put(('progress', 'Cloning repository...'))
                self.git_manager.clone_repository(repo_url, self.TARGET_PATH)
            else:
                self.task_queue.put(('progress', 'Changing remote and fetching...'))
                self.git_manager.change_remote(repo_url, self.TARGET_PATH)

            # Checkout branch
            self.task_queue.put(('progress', f'Checking out branch {branch}...'))
            self.git_manager.checkout_branch(branch, self.TARGET_PATH)

            # Update submodules
            self.task_queue.put(('progress', 'Updating submodules...'))
            self.git_manager.update_submodules(self.TARGET_PATH)

            # Build
            self.task_queue.put(('progress', 'Building sBitx... (this may take several minutes)'))
            build_result = self.build_manager.run_build(self.TARGET_PATH)

            if build_result.success:
                # Save last used
                self.config_manager.set_last_used(repo_url, branch)
                self.task_queue.put(('build_success', 'Build completed successfully!'))
            else:
                self.task_queue.put((
                    'build_error',
                    f"Build failed with exit code {build_result.returncode}.\n\n"
                    "Check the terminal output for details."
                ))

        except GitError as e:
            self.task_queue.put(('error', f"Git error: {e}"))
        except BuildError as e:
            self.task_queue.put(('error', f"Build error: {e}"))
        except Exception as e:
            self.task_queue.put(('error', f"Unexpected error: {e}"))

    def check_queue(self):
        """Check task queue for messages from background threads"""
        try:
            while True:
                msg_type, msg_data = self.task_queue.get_nowait()

                if msg_type == 'branches_fetched':
                    self.current_branches = msg_data
                    self.branch_combo['values'] = msg_data

                    # Auto-select current branch if it exists in the list
                    if msg_data:
                        if self.current_branch_name and self.current_branch_name in msg_data:
                            # Select the current branch
                            index = msg_data.index(self.current_branch_name)
                            self.branch_combo.current(index)
                            self.selected_branch = self.current_branch_name
                        else:
                            # Default to first branch
                            self.branch_combo.current(0)
                            self.selected_branch = msg_data[0]

                    self.status_bar.set_status(f"Found {len(msg_data)} branches", "success")
                    self.enable_controls()

                elif msg_type == 'progress':
                    if self.progress_dialog:
                        self.progress_dialog.update_message(msg_data)

                elif msg_type == 'build_success':
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    self.status_bar.set_status(msg_data, "success")
                    # Update current repo/branch tracking
                    self.detect_current_repo_branch()
                    self.update_repository_list()  # Refresh list with new highlighting
                    self.update_current_status()  # Update current repo/branch display
                    self.enable_controls()
                    show_info(self, "Success", msg_data)

                elif msg_type == 'build_error':
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    self.status_bar.set_status("Build failed", "error")
                    # Update current repo/branch even if build failed
                    # (branch was still checked out successfully)
                    self.detect_current_repo_branch()
                    self.update_repository_list()
                    self.update_current_status()
                    self.enable_controls()
                    show_error(self, "Build Failed", msg_data)

                elif msg_type == 'error':
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    self.status_bar.set_status("Operation failed", "error")
                    # Try to update current status in case branch was checked out
                    # before the error occurred
                    try:
                        self.detect_current_repo_branch()
                        self.update_repository_list()
                        self.update_current_status()
                    except:
                        pass  # Ignore errors during status update
                    self.enable_controls()
                    show_error(self, "Error", msg_data)

        except queue.Empty:
            pass
        finally:
            # Poll every 100ms
            self.after(100, self.check_queue)

    def disable_controls(self):
        """Disable all interactive controls"""
        self.add_repo_btn.config(state=tk.DISABLED)
        self.remove_repo_btn.config(state=tk.DISABLED)
        self.fetch_branches_btn.config(state=tk.DISABLED)
        self.checkout_build_btn.config(state=tk.DISABLED)
        self.repo_listbox.config(state=tk.DISABLED)
        self.branch_combo.config(state=tk.DISABLED)

    def enable_controls(self):
        """Enable all interactive controls"""
        self.add_repo_btn.config(state=tk.NORMAL)
        self.remove_repo_btn.config(state=tk.NORMAL)
        self.fetch_branches_btn.config(state=tk.NORMAL)
        self.checkout_build_btn.config(state=tk.NORMAL)
        self.repo_listbox.config(state=tk.NORMAL)
        self.branch_combo.config(state='readonly')

    def update_current_status(self):
        """Update display showing current repo and branch in target directory"""
        try:
            # Check if directory exists and is a git repo
            status = self.git_manager.check_directory_status(self.TARGET_PATH)

            if status != DirectoryStatus.GIT_REPO:
                self.current_status_label.config(
                    text="No git repository at target path",
                    foreground='gray'
                )
                return

            # Get current remote and branch
            remote = self.git_manager.get_current_remote(self.TARGET_PATH)
            branch = self.git_manager.get_current_branch(self.TARGET_PATH)

            if remote and branch:
                # Extract repo name from remote URL
                import re
                match = re.search(r'github\.com[/:]([\w-]+/[\w-]+)', remote)
                if match:
                    repo_name = match.group(1)
                else:
                    repo_name = remote

                self.current_status_label.config(
                    text=f"{repo_name} @ {branch}",
                    foreground='#28a745'  # Green color
                )
            else:
                self.current_status_label.config(
                    text="Unknown",
                    foreground='gray'
                )

        except Exception as e:
            self.current_status_label.config(
                text="Error reading status",
                foreground='#dc3545'  # Red color
            )

    def on_close(self):
        """Handle window close event"""
        self.destroy()

    def on_branch_combo_selected(self, event):
        """Handle branch selection from dropdown"""
        selection = self.branch_combo.get()
        if selection:
            self.selected_branch = selection
